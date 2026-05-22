from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import os
from pathlib import Path
import uuid

import pytest

from carbonfactor_parser.parsers.defra_desnz_content_parser import (
    parse_defra_desnz_file_content,
)
from carbonfactor_parser.parsers.file_content_input import ParserFileContentInput
from carbonfactor_parser.parsers.ghg_protocol_content_parser import (
    parse_ghg_protocol_file_content,
)
from carbonfactor_parser.parsers.ipcc_efdb_content_parser import (
    parse_ipcc_efdb_file_content,
)
from carbonfactor_parser.persistence import (
    POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR,
    POSTGRESQL_INTEGRATION_TEST_MARKER,
    POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR,
)
from carbonfactor_parser.persistence.parsed_factor_persistence_writer import (
    build_parsed_factor_persistence_command,
    persist_parsed_factor_records,
)
from carbonfactor_parser.persistence.postgresql_runtime_schema_bootstrap import (
    bootstrap_postgresql_phase1_schema,
)
from carbonfactor_parser.persistence.postgresql_schema_catalog import SourceFamily
from carbonfactor_parser.persistence.postgresql_source_family_repository import (
    PostgreSQLSourceFamilyRuntimeRepository,
)
from carbonfactor_parser.persistence.postgresql_year_state_repository import (
    PostgreSQLSourceFamilyYearStateRepository,
)
from carbonfactor_parser.persistence.source_family_repository import (
    SourceFamilyDetailRecord,
    SourceFamilyMasterRecord,
    source_family_repository_table_names,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPOSITORY_ROOT / "tests" / "fixtures" / "source_documents"
PHASE1_SOURCE_FAMILY_INPUTS = ("ghg_protocol", "defra_desnz", "ipcc_efdb")


@dataclass(frozen=True)
class PersistedSourceFamilySnapshot:
    masters: tuple[tuple[object, ...], ...]
    details: tuple[tuple[object, ...], ...]


def test_persisted_parity_validation_is_opt_in_and_uses_canonical_controls() -> None:
    assert POSTGRESQL_INTEGRATION_TEST_MARKER == "postgresql_integration"
    assert POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR == (
        "CARBONOPS_RUN_POSTGRESQL_INTEGRATION"
    )
    assert POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR == "CARBONOPS_POSTGRESQL_TEST_DSN"


@pytest.mark.parametrize("source_family_input", PHASE1_SOURCE_FAMILY_INPUTS)
def test_expected_source_family_snapshot_matches_writer_command(
    source_family_input: str,
) -> None:
    payload = _payload(source_family_input)
    command = build_parsed_factor_persistence_command(payload)

    assert command.issues == ()
    assert _expected_master_rows(command.master_records)
    assert _expected_detail_rows(command.detail_records)
    assert len(_expected_master_rows(command.master_records)) == 1
    assert len(_expected_detail_rows(command.detail_records)) == len(payload.records)


@pytest.mark.postgresql_integration
def test_opt_in_postgresql_persisted_source_family_parity_validation() -> None:
    if os.getenv(POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR) != "1":
        pytest.skip("PostgreSQL integration test opt-in is not enabled.")
    dsn = os.getenv(POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR)
    if not dsn:
        pytest.skip("PostgreSQL integration test DSN was not provided.")

    import psycopg

    schema_name = f"carbonops_prod010_{uuid.uuid4().hex}"
    with psycopg.connect(dsn) as connection:
        connection.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        connection.execute(f"SET search_path TO {schema_name}")
        bootstrap = bootstrap_postgresql_phase1_schema(connection)
        repository = PostgreSQLSourceFamilyRuntimeRepository(connection)
        year_state_repository = PostgreSQLSourceFamilyYearStateRepository(connection)

        assert bootstrap.missing_table_names == ()

        for source_family_input in PHASE1_SOURCE_FAMILY_INPUTS:
            payload = _payload(source_family_input)
            command = build_parsed_factor_persistence_command(payload)
            family = command.master_records[0].source_family
            master_table, detail_table = source_family_repository_table_names(family)

            assert command.issues == ()
            assert year_state_repository.latest_ingested_year(family) is None
            assert year_state_repository.next_target_year(family) == 2024

            first = persist_parsed_factor_records(payload, repository)
            persisted_after_first = _fetch_source_family_snapshot(
                connection,
                family,
                master_table,
                detail_table,
            )

            assert first.persisted_master_count == len(command.master_records)
            assert first.persisted_detail_count == len(command.detail_records)
            assert persisted_after_first.masters == _expected_master_rows(
                command.master_records,
            )
            assert persisted_after_first.details == _expected_detail_rows(
                command.detail_records,
            )

            year_state_repository.record_ingested_year(family, 2024)
            year_state_repository.record_ingested_year(family, 2024)

            assert year_state_repository.latest_ingested_year(family) == 2024
            assert year_state_repository.next_target_year(family) == 2025
            assert _year_state_count(connection, family, 2024) == 1

            second = persist_parsed_factor_records(payload, repository)
            persisted_after_second = _fetch_source_family_snapshot(
                connection,
                family,
                master_table,
                detail_table,
            )

            assert second.persisted_master_count == 0
            assert second.persisted_detail_count == 0
            assert second.skipped_master_count == len(command.master_records)
            assert second.skipped_detail_count == len(command.detail_records)
            assert persisted_after_second == persisted_after_first


def _fetch_source_family_snapshot(
    connection: object,
    source_family: SourceFamily,
    master_table: str,
    detail_table: str,
) -> PersistedSourceFamilySnapshot:
    master_id_column = f"{source_family.value}_emission_factor_master_id"
    masters = tuple(
        connection.execute(
            f"""
            SELECT
                source_family,
                source_year,
                source_version,
                source_release,
                run_id,
                master_external_key,
                status,
                artifact_reference,
                artifact_checksum_sha256,
                archive_reference,
                archive_checksum_sha256,
                effective_from::text,
                effective_to::text,
                record_checksum_sha256,
                metadata
            FROM {master_table}
            ORDER BY master_external_key
            """,
        ).fetchall(),
    )
    details = tuple(
        connection.execute(
            f"""
            SELECT
                detail_external_key,
                source_row_number,
                factor_id,
                factor_name,
                factor_value,
                factor_unit,
                status,
                record_checksum_sha256,
                raw_fields,
                normalized_fields
            FROM {detail_table}
            ORDER BY {master_id_column}, detail_external_key
            """,
        ).fetchall(),
    )
    return PersistedSourceFamilySnapshot(masters=masters, details=details)


def _expected_master_rows(
    master_records: tuple[SourceFamilyMasterRecord, ...],
) -> tuple[tuple[object, ...], ...]:
    return tuple(
        sorted(
            (
                (
                    record.source_family.value,
                    record.source_year,
                    record.source_version,
                    record.source_release,
                    record.run_id,
                    record.master_external_key,
                    record.status,
                    record.artifact_reference,
                    record.artifact_checksum_sha256,
                    record.archive_reference,
                    record.archive_checksum_sha256,
                    record.effective_from,
                    record.effective_to,
                    record.record_checksum_sha256,
                    record.metadata,
                )
                for record in master_records
            ),
            key=lambda row: row[5],
        ),
    )


def _expected_detail_rows(
    detail_records: tuple[SourceFamilyDetailRecord, ...],
) -> tuple[tuple[object, ...], ...]:
    return tuple(
        sorted(
            (
                (
                    record.detail_external_key,
                    record.source_row_number,
                    record.factor_id,
                    record.factor_name,
                    Decimal(str(record.factor_value)),
                    record.factor_unit,
                    record.status,
                    record.record_checksum_sha256,
                    record.raw_fields,
                    record.normalized_fields,
                )
                for record in detail_records
            ),
            key=lambda row: row[0],
        ),
    )


def _year_state_count(
    connection: object,
    source_family: SourceFamily,
    ingested_year: int,
) -> int:
    row = connection.execute(
        """
        SELECT COUNT(*)
        FROM source_family_year_states
        WHERE source_family = %s
          AND ingested_year = %s
        """,
        (source_family.value, ingested_year),
    ).fetchone()
    return int(row[0])


def _payload(source_family: str):
    if source_family == "ghg_protocol":
        result = parse_ghg_protocol_file_content(_content_input(source_family))
    elif source_family == "defra_desnz":
        result = parse_defra_desnz_file_content(_content_input(source_family))
    elif source_family == "ipcc_efdb":
        result = parse_ipcc_efdb_file_content(_content_input(source_family))
    else:
        raise ValueError(source_family)
    assert result.raw_record_payload is not None
    return result.raw_record_payload


def _content_input(source_family: str) -> ParserFileContentInput:
    fixture_name = {
        "ghg_protocol": "ghg_protocol/ghg_protocol_sample_factors.csv",
        "defra_desnz": "defra_desnz/defra_desnz_normalized_factors.csv",
        "ipcc_efdb": "ipcc_efdb/ipcc_efdb_sample_factors.csv",
    }[source_family]
    fixture_path = FIXTURE_ROOT / fixture_name
    return ParserFileContentInput(
        source_family=source_family,
        source_id=source_family,
        content=fixture_path.read_text(encoding="utf-8"),
        artifact_reference=str(fixture_path),
        checksum_sha256="c" * 64,
        content_type="text/csv",
        format_hint="csv",
    )
