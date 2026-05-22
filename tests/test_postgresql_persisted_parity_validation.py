from __future__ import annotations

from dataclasses import replace
import hashlib
import os
from pathlib import Path
import subprocess
import uuid

import pytest

from carbonfactor_parser.parsers.normalized_output_row_contract import (
    ParserNormalizedOutputBatch,
)
from carbonfactor_parser.persistence import (
    POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR,
    POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR,
)
from carbonfactor_parser.persistence.postgresql_runtime_schema_bootstrap import (
    bootstrap_postgresql_phase1_schema,
)
from carbonfactor_parser.persistence.postgresql_source_family_repository import (
    PostgreSQLSourceFamilyRuntimeRepository,
)
from carbonfactor_parser.persistence.postgresql_year_state_repository import (
    PostgreSQLSourceFamilyYearStateRepository,
)
from carbonfactor_parser.pipeline.defra_desnz_production_e2e import (
    DEFRA_DESNZ_SOURCE_FAMILY,
    DefraDesnzProductionParserBoundary,
)
from carbonfactor_parser.pipeline.ghg_protocol_production_e2e import (
    GHG_PROTOCOL_SOURCE_FAMILY,
    GHGProtocolProductionParserBoundary,
)
from carbonfactor_parser.pipeline.ipcc_efdb_production_e2e import (
    IPCC_EFDB_SOURCE_FAMILY,
    IpccEfdbProductionParserBoundary,
)
from carbonfactor_parser.pipeline.production_e2e_year_orchestrator import (
    ProductionE2EDownloadedArtifact,
)


PERSISTED_PARITY_OPT_IN_ENV_VAR = "CARBONOPS_RUN_PERSISTED_PARITY_VALIDATION"
DOTNET_POSTGRESQL_SCHEMA_ENV_VAR = "CARBONOPS_DOTNET_POSTGRESQL_TEST_SCHEMA"
DOTNET_POSTGRESQL_DSN_ENV_VAR = "CARBONOPS_DOTNET_POSTGRESQL_TEST_DSN"
DOTNET_POSTGRESQL_OPT_IN_ENV_VAR = "CARBONOPS_RUN_DOTNET_POSTGRESQL_INTEGRATION"
PARITY_SOURCE_VERSION = "prod009-prod010-parity"
PARITY_RUN_ID = "prod009-prod010-parity"
SOURCE_FAMILIES = (
    GHG_PROTOCOL_SOURCE_FAMILY,
    DEFRA_DESNZ_SOURCE_FAMILY,
    IPCC_EFDB_SOURCE_FAMILY,
)


def test_persisted_parity_validation_is_opt_in_by_default() -> None:
    assert not _parity_enabled({})


@pytest.mark.postgresql_integration
def test_postgresql_persisted_output_matches_dotnet_baseline_when_enabled(
    tmp_path: Path,
) -> None:
    if not _parity_enabled(os.environ):
        pytest.skip("Persisted parity validation opt-in is not enabled.")
    dsn = os.getenv(POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR)
    if not dsn:
        pytest.skip("PostgreSQL integration test DSN was not provided.")

    import psycopg

    repository_root = Path(__file__).resolve().parents[1]
    python_schema = f"carbonops_prod010_py_{uuid.uuid4().hex}"
    dotnet_schema = f"carbonops_prod010_dotnet_{uuid.uuid4().hex}"

    with psycopg.connect(dsn) as connection:
        _create_schema(connection, python_schema)
        _create_schema(connection, dotnet_schema)
        _populate_python_schema(connection, python_schema)

    _populate_dotnet_schema(repository_root, dsn, dotnet_schema)

    with psycopg.connect(dsn) as connection:
        python_snapshot = _snapshot_schema(connection, python_schema)
        dotnet_snapshot = _snapshot_schema(connection, dotnet_schema)

    assert python_snapshot == dotnet_snapshot


def _parity_enabled(environment: dict[str, str] | os._Environ[str]) -> bool:
    return environment.get(PERSISTED_PARITY_OPT_IN_ENV_VAR) == "1"


def _create_schema(connection: object, schema_name: str) -> None:
    connection.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
    connection.commit()


def _populate_python_schema(connection: object, schema_name: str) -> None:
    connection.execute(f"SET search_path TO {schema_name}")
    bootstrap_postgresql_phase1_schema(connection)
    repository = PostgreSQLSourceFamilyRuntimeRepository(connection)
    year_state = PostgreSQLSourceFamilyYearStateRepository(connection)

    for source_family in SOURCE_FAMILIES:
        batch = _rewritten_batch(_parse_fixture(source_family))
        first = repository.insert_normalized_factor_records(batch)
        second = repository.insert_normalized_factor_records(batch)
        assert first.master_inserted > 0
        assert first.detail_inserted > 0
        assert second.master_inserted == 0
        assert second.detail_inserted == 0
        assert second.master_skipped > 0
        assert second.detail_skipped > 0
        year_state.record_ingested_year(source_family, 2024)
        year_state.record_ingested_year(source_family, 2024)


def _populate_dotnet_schema(repository_root: Path, dsn: str, schema_name: str) -> None:
    environment = dict(os.environ)
    environment[POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR] = "1"
    environment[DOTNET_POSTGRESQL_OPT_IN_ENV_VAR] = "1"
    environment[DOTNET_POSTGRESQL_DSN_ENV_VAR] = dsn
    environment[DOTNET_POSTGRESQL_SCHEMA_ENV_VAR] = schema_name
    result = subprocess.run(
        [
            "dotnet",
            "test",
            "tests/dotnet/CarbonOps.Parser.Contracts.Tests/"
            "CarbonOps.Parser.Contracts.Tests.csproj",
            "--configuration",
            "Release",
            "--no-restore",
            "--filter",
            "FullyQualifiedName~PersistedParityFixtureBaselineWhenEnabled",
        ],
        cwd=repository_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, _redacted_dotnet_output(result)


def _parse_fixture(source_family: str) -> ParserNormalizedOutputBatch:
    fixture_path = _fixture_path(source_family)
    artifact = ProductionE2EDownloadedArtifact(
        source_family=source_family,
        source_year=2024,
        artifact_reference=str(fixture_path),
        checksum_sha256=hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
        content_type="text/csv",
        format_hint="csv",
    )
    parser = {
        GHG_PROTOCOL_SOURCE_FAMILY: GHGProtocolProductionParserBoundary(),
        DEFRA_DESNZ_SOURCE_FAMILY: DefraDesnzProductionParserBoundary(),
        IPCC_EFDB_SOURCE_FAMILY: IpccEfdbProductionParserBoundary(),
    }[source_family]
    batch = parser.parse(artifact)
    assert batch.row_count > 0
    return batch


def _rewritten_batch(batch: ParserNormalizedOutputBatch) -> ParserNormalizedOutputBatch:
    rows = []
    for row in batch.rows:
        fields = {
            key: value
            for key, value in dict(row.normalized_fields).items()
            if key
            not in {
                "source_year",
                "source_version",
                "run_id",
                "provenance_checksum_value",
                "master_external_key",
                "source_family_master_id",
                "source_family_detail_id",
            }
        }
        factor_id = str(fields.get("factor_id") or row.row_id)
        fields.update(
            {
                "source_year": "2024",
                "source_version": PARITY_SOURCE_VERSION,
                "run_id": PARITY_RUN_ID,
                "provenance_checksum_value": _artifact_checksum(row.artifact_reference),
                "master_external_key": f"2024:{PARITY_SOURCE_VERSION}:{factor_id}",
            }
        )
        rows.append(
            replace(
                row,
                normalized_fields=tuple(sorted(fields.items(), key=lambda item: item[0])),
                reporting_year=2024,
            )
        )
    return ParserNormalizedOutputBatch(rows=tuple(rows))


def _snapshot_schema(connection: object, schema_name: str) -> dict[str, object]:
    connection.execute(f"SET search_path TO {schema_name}")
    return {
        "year_state": _fetchall(
            connection,
            """
            SELECT
              source_family,
              max(ingested_year) AS latest_year,
              max(ingested_year) + 1 AS next_target_year,
              count(*) AS state_rows
            FROM source_family_year_states
            GROUP BY source_family
            ORDER BY source_family
            """,
        ),
        "families": {
            source_family: _source_family_snapshot(connection, source_family)
            for source_family in SOURCE_FAMILIES
        },
    }


def _source_family_snapshot(connection: object, source_family: str) -> dict[str, object]:
    prefix = {
        GHG_PROTOCOL_SOURCE_FAMILY: "ghg",
        DEFRA_DESNZ_SOURCE_FAMILY: "defra",
        IPCC_EFDB_SOURCE_FAMILY: "ipcc",
    }[source_family]
    master_table = f"{prefix}_emission_factor_masters"
    detail_table = f"{prefix}_emission_factor_details"
    master_id = f"{prefix}_emission_factor_master_id"
    return {
        "counts": _fetchall(
            connection,
            f"""
            SELECT
              (SELECT count(*) FROM {master_table} WHERE source_version = %s),
              (SELECT count(*)
               FROM {detail_table} d
               JOIN {master_table} m ON m.{master_id} = d.{master_id}
               WHERE m.source_version = %s)
            """,
            (PARITY_SOURCE_VERSION, PARITY_SOURCE_VERSION),
        ),
        "masters": _fetchall(
            connection,
            f"""
            SELECT source_family, source_year, source_version, master_external_key, status
            FROM {master_table}
            WHERE source_version = %s
            ORDER BY source_family, source_year, source_version, master_external_key
            """,
            (PARITY_SOURCE_VERSION,),
        ),
        "details": _fetchall(
            connection,
            f"""
            SELECT
              m.source_family,
              m.source_year,
              m.source_version,
              m.master_external_key,
              d.detail_external_key,
              d.factor_id,
              d.factor_name,
              d.factor_value::text,
              d.factor_unit,
              d.status
            FROM {detail_table} d
            JOIN {master_table} m ON m.{master_id} = d.{master_id}
            WHERE m.source_version = %s
            ORDER BY
              m.source_family,
              m.source_year,
              m.source_version,
              m.master_external_key,
              d.detail_external_key
            """,
            (PARITY_SOURCE_VERSION,),
        ),
    }


def _fetchall(
    connection: object,
    statement: str,
    parameters: tuple[object, ...] | None = None,
) -> tuple[tuple[object, ...], ...]:
    cursor = connection.execute(statement, parameters)
    return tuple(tuple(row) for row in cursor.fetchall())


def _fixture_path(source_family: str) -> Path:
    family_directory, file_name = {
        GHG_PROTOCOL_SOURCE_FAMILY: ("ghg_protocol", "ghg_protocol_sample_factors.csv"),
        DEFRA_DESNZ_SOURCE_FAMILY: ("defra_desnz", "defra_desnz_normalized_factors.csv"),
        IPCC_EFDB_SOURCE_FAMILY: ("ipcc_efdb", "ipcc_efdb_sample_factors.csv"),
    }[source_family]
    return (
        Path(__file__).resolve().parent
        / "fixtures"
        / "source_documents"
        / family_directory
        / file_name
    )


def _artifact_checksum(artifact_reference: str) -> str:
    return hashlib.sha256(Path(artifact_reference).read_bytes()).hexdigest()


def _redacted_dotnet_output(result: subprocess.CompletedProcess[str]) -> str:
    rendered = "\n".join([result.stdout, result.stderr])
    dsn = os.getenv(POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR)
    if dsn:
        rendered = rendered.replace(dsn, "<redacted-postgresql-dsn>")
    return rendered
