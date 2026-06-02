from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
import json
import os
from pathlib import Path
import uuid

import pytest

from carbonfactor_parser.parsers.file_content_input import ParserFileContentInput
from carbonfactor_parser.parsers.input_artifact_contract import (
    create_phase1_parser_input_artifact,
)
from carbonfactor_parser.parsers.normalized_output_row_contract import (
    ParserNormalizedOutputRowStatus,
    create_parser_normalized_output_batch,
    create_parser_normalized_output_row,
)
from carbonfactor_parser.parsers.defra_desnz_content_parser import (
    parse_defra_desnz_file_content,
)
from carbonfactor_parser.parsers.ghg_protocol_content_parser import (
    parse_ghg_protocol_file_content,
)
from carbonfactor_parser.parsers.ipcc_efdb_content_parser import (
    parse_ipcc_efdb_file_content,
)
from carbonfactor_parser.persistence import (
    POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR,
    POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR,
)
from carbonfactor_parser.persistence.parsed_factor_persistence_writer import (
    ParsedFactorPersistenceStatus,
    build_parsed_factor_persistence_command,
    persist_parsed_factor_records,
)
from carbonfactor_parser.persistence.postgresql_runtime_schema_bootstrap import (
    bootstrap_postgresql_phase1_schema,
)
from carbonfactor_parser.persistence.postgresql_source_family_sql import (
    detail_insert_sql,
    master_insert_sql,
)
from carbonfactor_parser.persistence.postgresql_source_family_ids import (
    detail_uuid,
    ingestion_run_uuid,
    master_uuid,
    source_document_uuid,
)
from carbonfactor_parser.persistence.postgresql_source_family_parameters import (
    detail_parameters,
    json_payload,
    json_safe,
    master_parameters,
)
from carbonfactor_parser.persistence.postgresql_source_family_repository import (
    PostgreSQLSourceFamilyRuntimeRepository,
    PostgreSQLSourceSpecificFactorInsertStatus,
)


class _FakeCursor:
    def __init__(self, row: tuple[object, ...] | None = None) -> None:
        self._row = row

    def fetchone(self) -> tuple[object, ...] | None:
        return self._row


class _FakeConnection:
    def __init__(self) -> None:
        self.statements: list[tuple[str, object | None]] = []
        self.master_keys: set[tuple[object, ...]] = set()
        self.detail_keys: set[tuple[object, ...]] = set()
        self.commit_count = 0
        self.rollback_count = 0

    def execute(self, statement: str, parameters: object | None = None) -> _FakeCursor:
        self.statements.append((statement, parameters))
        normalized = " ".join(statement.split()).lower()
        if "_emission_factor_masters" in normalized and normalized.startswith("insert"):
            assert isinstance(parameters, tuple)
            key = (parameters[1], parameters[2], parameters[3], parameters[8])
            if key in self.master_keys:
                return _FakeCursor()
            self.master_keys.add(key)
            return _FakeCursor((parameters[0],))
        if "_emission_factor_details" in normalized and normalized.startswith("insert"):
            assert isinstance(parameters, tuple)
            key = (parameters[1], parameters[2])
            if key in self.detail_keys:
                return _FakeCursor()
            self.detail_keys.add(key)
            return _FakeCursor((parameters[0],))
        return _FakeCursor()

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1



def test_postgresql_source_family_stable_uuid_helpers_match_legacy_payloads() -> None:
    command = build_parsed_factor_persistence_command(_payload("ghg_protocol"))
    master = command.master_records[0]
    detail = command.detail_records[0]

    assert source_document_uuid(master) == _legacy_stable_uuid(
        "source_document",
        "ghg_protocol",
        master.source_document_id,
    )
    ingestion_source = master.ingestion_run_id or master.run_id
    if ingestion_source is None:
        ingestion_source = (
            f"ghg_protocol:{master.source_year}:{master.source_version}"
        )
    assert ingestion_run_uuid(master) == _legacy_stable_uuid(
        "ingestion_run",
        "ghg_protocol",
        ingestion_source,
    )
    assert master_uuid(master.source_family, master.source_family_master_id) == (
        _legacy_stable_uuid(
            "master",
            "ghg_protocol",
            master.source_family_master_id,
        )
    )
    assert detail_uuid(detail.source_family, detail.source_family_detail_id) == (
        _legacy_stable_uuid(
            "detail",
            "ghg_protocol",
            detail.source_family_detail_id,
        )
    )
    assert source_document_uuid(master) == source_document_uuid(master)
    assert ingestion_run_uuid(master) == ingestion_run_uuid(master)


def test_postgresql_source_family_ingestion_run_uuid_fallback_is_deterministic() -> None:
    command = build_parsed_factor_persistence_command(_payload("defra_desnz"))
    master = replace(command.master_records[0], ingestion_run_id=None, run_id=None)

    expected = _legacy_stable_uuid(
        "ingestion_run",
        "defra_desnz",
        f"defra_desnz:{master.source_year}:{master.source_version}",
    )

    assert ingestion_run_uuid(master) == expected
    assert ingestion_run_uuid(master) == ingestion_run_uuid(master)


@pytest.mark.parametrize(
    ("source_family", "master_table", "master_id"),
    (
        ("ghg_protocol", "ghg_emission_factor_masters", "ghg_emission_factor_master_id"),
        ("defra_desnz", "defra_emission_factor_masters", "defra_emission_factor_master_id"),
        ("ipcc_efdb", "ipcc_emission_factor_masters", "ipcc_emission_factor_master_id"),
    ),
)
def test_postgresql_source_family_master_insert_sql_compatibility(
    source_family: str,
    master_table: str,
    master_id: str,
) -> None:
    sql = _normalized_sql(master_insert_sql(source_family))

    assert f"INSERT INTO {master_table}" in sql
    assert (
        "ON CONFLICT (source_family, source_year, source_version, master_external_key)"
        in sql
    )
    assert f"RETURNING {master_id}" in sql
    assert "metadata" in sql
    assert "%s::jsonb" in sql


@pytest.mark.parametrize(
    ("source_family", "detail_table", "master_id", "detail_id"),
    (
        (
            "ghg_protocol",
            "ghg_emission_factor_details",
            "ghg_emission_factor_master_id",
            "ghg_emission_factor_detail_id",
        ),
        (
            "defra_desnz",
            "defra_emission_factor_details",
            "defra_emission_factor_master_id",
            "defra_emission_factor_detail_id",
        ),
        (
            "ipcc_efdb",
            "ipcc_emission_factor_details",
            "ipcc_emission_factor_master_id",
            "ipcc_emission_factor_detail_id",
        ),
    ),
)
def test_postgresql_source_family_detail_insert_sql_compatibility(
    source_family: str,
    detail_table: str,
    master_id: str,
    detail_id: str,
) -> None:
    sql = _normalized_sql(detail_insert_sql(source_family))

    assert f"INSERT INTO {detail_table}" in sql
    assert f"ON CONFLICT ({master_id}, detail_external_key)" in sql
    assert f"RETURNING {detail_id}" in sql
    assert "raw_fields" in sql
    assert "normalized_fields" in sql
    assert sql.count("%s::jsonb") == 2


def test_postgresql_source_family_master_parameters_compatibility() -> None:
    command = build_parsed_factor_persistence_command(_payload("ghg_protocol"))
    master = command.master_records[0]

    parameters = master_parameters(master)

    assert len(parameters) == 18
    assert parameters[0] == str(
        master_uuid(master.source_family, master.source_family_master_id)
    )
    assert parameters[1] == "ghg_protocol"
    assert parameters[2] == master.source_year
    assert parameters[3] == master.source_version
    assert parameters[5] == str(source_document_uuid(master))
    assert parameters[6] == str(ingestion_run_uuid(master))
    assert parameters[8] == master.master_external_key
    assert parameters[16] == master.record_checksum_sha256
    assert parameters[17] == json.dumps(
        json_safe(master.metadata), sort_keys=True, separators=(",", ":")
    )
    assert ": " not in str(parameters[17])
    assert ", " not in str(parameters[17])


def test_postgresql_source_family_detail_parameters_compatibility() -> None:
    command = build_parsed_factor_persistence_command(_payload("defra_desnz"))
    detail = command.detail_records[0]

    parameters = detail_parameters(detail)

    assert len(parameters) == 12
    assert parameters[0] == str(
        detail_uuid(detail.source_family, detail.source_family_detail_id)
    )
    assert parameters[1] == str(
        master_uuid(detail.source_family, detail.source_family_master_id)
    )
    assert parameters[2] == detail.detail_external_key
    assert parameters[3] == detail.source_row_number
    assert parameters[4] == detail.factor_id
    assert parameters[6] == str(Decimal(str(detail.factor_value)))
    assert parameters[9] == detail.record_checksum_sha256
    assert parameters[10] == json.dumps(
        json_safe(detail.raw_fields), sort_keys=True, separators=(",", ":")
    )
    assert parameters[11] == json.dumps(
        json_safe(detail.normalized_fields), sort_keys=True, separators=(",", ":")
    )
    assert ": " not in str(parameters[10])
    assert ", " not in str(parameters[10])
    assert ": " not in str(parameters[11])
    assert ", " not in str(parameters[11])


def test_postgresql_source_family_json_helpers_preserve_legacy_behavior() -> None:
    payload = {
        2: (Decimal("1.20"), [Decimal("3.40"), {"b": 2, "a": Decimal("5")}]),
        "10": "ten",
        "a": None,
    }

    safe_payload = json_safe(payload)

    assert safe_payload == {
        "10": "ten",
        "2": ["1.20", ["3.40", {"a": "5", "b": 2}]],
        "a": None,
    }
    assert json_payload(payload) == (
        '{"10":"ten","2":["1.20",["3.40",{"a":"5","b":2}]],"a":null}'
    )


def test_postgresql_source_family_repository_inserts_and_skips_idempotently() -> None:
    connection = _FakeConnection()
    repository = PostgreSQLSourceFamilyRuntimeRepository(connection)
    payload = _payload("defra_desnz")

    first = persist_parsed_factor_records(payload, repository)
    second = persist_parsed_factor_records(payload, repository)

    assert first.status is ParsedFactorPersistenceStatus.DECLARED
    assert first.persisted_master_count == 1
    assert first.persisted_detail_count == len(payload.records)
    assert first.skipped_master_count == 0
    assert second.persisted_master_count == 0
    assert second.persisted_detail_count == 0
    assert second.skipped_master_count == 1
    assert second.skipped_detail_count == len(payload.records)
    assert connection.commit_count == 2
    assert any(
        "INSERT INTO defra_emission_factor_masters" in statement
        for statement, _parameters in connection.statements
    )
    assert any(
        "INSERT INTO defra_emission_factor_details" in statement
        for statement, _parameters in connection.statements
    )


def test_writer_result_exposes_master_detail_summary_counts() -> None:
    connection = _FakeConnection()
    repository = PostgreSQLSourceFamilyRuntimeRepository(connection)
    payload = _payload("ghg_protocol")

    first = persist_parsed_factor_records(payload, repository)
    second = persist_parsed_factor_records(payload, repository)

    assert first.master_inserted_count == 1
    assert first.detail_inserted_count == len(payload.records)
    assert second.master_skipped_count == 1
    assert second.detail_skipped_count == len(payload.records)
    assert second.validation_failure_count == 0
    assert second.final_status == "declared"


def test_insert_normalized_factor_records_returns_user_visible_counts() -> None:
    connection = _FakeConnection()
    repository = PostgreSQLSourceFamilyRuntimeRepository(connection)
    artifact = create_phase1_parser_input_artifact(
        source_family="ghg_protocol",
        artifact_reference="artifact://ghg/factors.csv",
        reporting_year=2024,
    )
    batch = create_parser_normalized_output_batch(
        (
            create_parser_normalized_output_row(
                artifact=artifact,
                row_id="ghg-row-001",
                source_row_number=2,
                status=ParserNormalizedOutputRowStatus.VALIDATED,
                normalized_fields={
                    "source_year": 2024,
                    "source_version": "ghg-2024",
                    "factor_id": "GHG-001",
                    "factor_value": Decimal("1.25"),
                    "factor_unit": "kgco2e",
                    "source_checksum_sha256": "c" * 64,
                },
            ),
        )
    )

    first = repository.insert_normalized_factor_records(batch)
    second = repository.insert_normalized_factor_records(batch)

    assert first.status is PostgreSQLSourceSpecificFactorInsertStatus.INSERTED
    assert first.master_inserted == 1
    assert first.detail_inserted == 1
    assert first.validation_error_count == 0
    assert second.master_skipped == 1
    assert second.detail_skipped == 1
    assert second.skipped_duplicate == 1


@pytest.mark.parametrize(
    ("source_family", "master_table", "detail_table"),
    (
        (
            "ghg_protocol",
            "ghg_emission_factor_masters",
            "ghg_emission_factor_details",
        ),
        (
            "defra_desnz",
            "defra_emission_factor_masters",
            "defra_emission_factor_details",
        ),
        (
            "ipcc_efdb",
            "ipcc_emission_factor_masters",
            "ipcc_emission_factor_details",
        ),
    ),
)
def test_repository_targets_all_source_specific_table_pairs(
    source_family: str,
    master_table: str,
    detail_table: str,
) -> None:
    connection = _FakeConnection()
    repository = PostgreSQLSourceFamilyRuntimeRepository(connection)

    result = persist_parsed_factor_records(_payload(source_family), repository)

    assert result.persisted_master_count == 1
    assert result.persisted_detail_count >= 1
    assert any(f"INSERT INTO {master_table}" in s for s, _ in connection.statements)
    assert any(f"INSERT INTO {detail_table}" in s for s, _ in connection.statements)


@pytest.mark.postgresql_integration
def test_docker_postgresql_source_specific_master_detail_tables_integration() -> None:
    if os.getenv(POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR) != "1":
        pytest.skip("PostgreSQL integration test opt-in is not enabled.")
    dsn = os.getenv(POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR)
    if not dsn:
        pytest.skip("PostgreSQL integration test DSN was not provided.")

    import psycopg

    schema_name = f"carbonops_ph020_{uuid.uuid4().hex}"
    with psycopg.connect(dsn) as connection:
        connection.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        connection.execute(f"SET search_path TO {schema_name}")
        bootstrap_postgresql_phase1_schema(connection)
        repository = PostgreSQLSourceFamilyRuntimeRepository(connection)

        for source_family in ("ghg_protocol", "defra_desnz", "ipcc_efdb"):
            first = persist_parsed_factor_records(_payload(source_family), repository)
            second = persist_parsed_factor_records(_payload(source_family), repository)
            assert first.persisted_master_count == 1
            assert first.persisted_detail_count >= 1
            assert second.skipped_master_count == 1
            assert second.skipped_detail_count >= 1

        table_counts = {
            table_name: connection.execute(
                f"SELECT COUNT(*) FROM {table_name}",
            ).fetchone()[0]
            for table_name in (
                "ghg_emission_factor_masters",
                "ghg_emission_factor_details",
                "defra_emission_factor_masters",
                "defra_emission_factor_details",
                "ipcc_emission_factor_masters",
                "ipcc_emission_factor_details",
            )
        }
        assert all(count > 0 for count in table_counts.values())


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
    fixture_path = Path("tests/fixtures/source_documents") / fixture_name
    return ParserFileContentInput(
        source_family=source_family,
        source_id=source_family,
        content=fixture_path.read_text(encoding="utf-8"),
        artifact_reference=str(fixture_path),
        checksum_sha256="c" * 64,
        content_type="text/csv",
        format_hint="csv",
    )


def test_source_family_repository_redacts_database_errors() -> None:
    private_dsn = "postgresql://carbonops:secret@example.invalid:5432/carbonops"
    connection = _FailingConnection(
        RuntimeError(f"could not connect dsn={private_dsn} password=secret token=abc")
    )
    repository = PostgreSQLSourceFamilyRuntimeRepository(connection)

    command = build_parsed_factor_persistence_command(_payload("ghg_protocol"))

    result = repository.persist_source_family_records(
        command.master_records,
        command.detail_records,
    )

    assert result.status.value == "failed_database"
    assert connection.rollback_count == 1
    message = result.issues[0].message
    assert "secret" not in message
    assert private_dsn not in message
    assert "password=***" in message
    assert "token=***" in message


class _FailingConnection(_FakeConnection):
    def __init__(self, exc: Exception) -> None:
        super().__init__()
        self._exc = exc

    def execute(self, statement: str, parameters: object | None = None) -> _FakeCursor:
        raise self._exc



def _legacy_stable_uuid(*values: object) -> uuid.UUID:
    payload = json.dumps(tuple(str(value) for value in values), separators=(",", ":"))
    return uuid.uuid5(uuid.NAMESPACE_URL, payload)


def _normalized_sql(statement: str) -> str:
    return " ".join(statement.split())
