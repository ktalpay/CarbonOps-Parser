from __future__ import annotations

from decimal import Decimal
import os
import uuid

import pytest

from carbonfactor_parser.parsers.input_artifact_contract import (
    create_phase1_parser_input_artifact,
)
from carbonfactor_parser.parsers.normalized_output_row_contract import (
    ParserNormalizedOutputBatch,
    ParserNormalizedOutputRowStatus,
    create_parser_normalized_output_batch,
    create_parser_normalized_output_row,
)
from carbonfactor_parser.persistence import (
    POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR,
    POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR,
)
from carbonfactor_parser.persistence.postgresql_normalized_factor_repository import (
    NORMALIZED_FACTOR_RECORDS_TABLE_NAME,
    PostgreSQLNormalizedFactorInsertStatus,
    PostgreSQLNormalizedFactorRuntimeRepository,
    insert_postgresql_normalized_factor_records,
)
from carbonfactor_parser.persistence.postgresql_runtime_config import (
    POSTGRESQL_RUNTIME_DSN_ENV_VAR,
    load_postgresql_runtime_config,
)
from carbonfactor_parser.persistence.postgresql_runtime_schema_bootstrap import (
    bootstrap_postgresql_phase1_schema,
)
from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    get_required_table_names,
)


class _FakeCursor:
    def __init__(self, row: tuple[object, ...] | None = None) -> None:
        self._row = row

    def fetchone(self) -> tuple[object, ...] | None:
        return self._row

    def fetchall(self) -> list[tuple[object, ...]]:
        return []


class _FakeConnection:
    def __init__(self, *, fail_with: Exception | None = None) -> None:
        self.fail_with = fail_with
        self.seen_idempotency_keys: set[str] = set()
        self.statements: list[tuple[str, object | None]] = []
        self.commit_count = 0
        self.rollback_count = 0

    def execute(self, statement: str, parameters: object | None = None) -> _FakeCursor:
        self.statements.append((statement, parameters))
        if self.fail_with is not None:
            raise self.fail_with
        key = parameters[1]  # type: ignore[index]
        if str(key) in self.seen_idempotency_keys:
            return _FakeCursor(None)
        self.seen_idempotency_keys.add(str(key))
        return _FakeCursor(("inserted",))

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


def test_runtime_repository_inserts_normalized_factor_records() -> None:
    connection = _FakeConnection()
    repository = PostgreSQLNormalizedFactorRuntimeRepository(connection)

    summary = repository.insert_normalized_factor_records(_batch())

    assert summary.status is PostgreSQLNormalizedFactorInsertStatus.INSERTED
    assert summary.attempted == 1
    assert summary.inserted == 1
    assert summary.skipped_duplicate == 0
    assert summary.failed == 0
    assert summary.validation_error_count == 0
    assert connection.commit_count == 1
    statement, parameters = connection.statements[0]
    assert f"INSERT INTO {NORMALIZED_FACTOR_RECORDS_TABLE_NAME}" in statement
    assert "ON CONFLICT (idempotency_key_sha256) DO NOTHING" in statement
    assert parameters is not None
    assert parameters[2] == "defra_desnz"  # type: ignore[index]
    assert parameters[4] == 2024  # type: ignore[index]
    assert parameters[13] == Decimal("0.20705")  # type: ignore[index]
    assert parameters[14] == "kWh"  # type: ignore[index]
    assert "local-only-run-001" in parameters  # type: ignore[operator]


def test_runtime_repository_repeated_insert_is_idempotent() -> None:
    connection = _FakeConnection()
    repository = PostgreSQLNormalizedFactorRuntimeRepository(connection)

    first = repository.insert_normalized_factor_records(_batch())
    second = repository.insert_normalized_factor_records(_batch())

    assert first.inserted == 1
    assert first.skipped_duplicate == 0
    assert second.status is PostgreSQLNormalizedFactorInsertStatus.INSERTED
    assert second.attempted == 1
    assert second.inserted == 0
    assert second.skipped_duplicate == 1
    assert len(connection.statements) == 2


def test_runtime_repository_reports_validation_failure_without_database_call() -> None:
    connection = _FakeConnection()
    repository = PostgreSQLNormalizedFactorRuntimeRepository(connection)
    malformed_batch = _batch(normalized_fields={"factor_id": "DEFRA-2024-ELEC"})

    summary = repository.insert_normalized_factor_records(malformed_batch)

    assert summary.status is PostgreSQLNormalizedFactorInsertStatus.FAILED_VALIDATION
    assert summary.attempted == 1
    assert summary.inserted == 0
    assert summary.failed == 1
    assert summary.validation_error_count >= 1
    assert [issue.code for issue in summary.issues] == [
        "POSTGRESQL_NORMALIZED_FACTOR_MISSING_FACTOR_VALUE",
        "POSTGRESQL_NORMALIZED_FACTOR_MISSING_FACTOR_UNIT",
    ]
    assert connection.statements == []


def test_runtime_repository_redacts_database_errors() -> None:
    private_dsn = "postgresql://carbonops:secret@example.invalid:5432/carbonops"
    connection = _FakeConnection(
        fail_with=RuntimeError(
            f"could not connect dsn={private_dsn} password=secret"
        ),
    )
    repository = PostgreSQLNormalizedFactorRuntimeRepository(connection)

    summary = repository.insert_normalized_factor_records(_batch())

    assert summary.status is PostgreSQLNormalizedFactorInsertStatus.FAILED_DATABASE
    assert summary.failed == 1
    assert summary.inserted == 0
    assert connection.rollback_count == 1
    message = summary.issues[0].message
    assert "secret" not in message
    assert private_dsn not in message
    assert "password=***" in message


def test_runtime_insert_with_missing_config_fails_closed() -> None:
    config_result = load_postgresql_runtime_config({})
    called = False

    def connection_factory(_config):
        nonlocal called
        called = True
        return _FakeConnection()

    summary = insert_postgresql_normalized_factor_records(
        _batch(),
        config_result=config_result,
        connection_factory=connection_factory,
    )

    assert summary.status is PostgreSQLNormalizedFactorInsertStatus.FAILED_VALIDATION
    assert summary.attempted == 1
    assert summary.failed == 1
    assert summary.validation_error_count == 4
    assert called is False


def test_runtime_insert_with_ready_config_uses_explicit_connection_factory() -> None:
    config_result = load_postgresql_runtime_config(
        {POSTGRESQL_RUNTIME_DSN_ENV_VAR: "postgresql://example.invalid/carbonops"},
    )
    connection = _FakeConnection()

    summary = insert_postgresql_normalized_factor_records(
        _batch(),
        config_result=config_result,
        connection_factory=lambda _config: connection,
    )

    assert summary.status is PostgreSQLNormalizedFactorInsertStatus.INSERTED
    assert summary.inserted == 1
    assert len(connection.statements) == 1


def test_phase1_bootstrap_includes_normalized_factor_runtime_table() -> None:
    assert NORMALIZED_FACTOR_RECORDS_TABLE_NAME in get_required_table_names()


@pytest.mark.postgresql_integration
def test_docker_postgresql_normalized_factor_insert_integration() -> None:
    if os.getenv(POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR) != "1":
        pytest.skip("PostgreSQL integration test opt-in is not enabled.")
    dsn = os.getenv(POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR)
    if not dsn:
        pytest.skip("PostgreSQL integration test DSN was not provided.")

    import psycopg

    schema_name = f"carbonops_ph012_{uuid.uuid4().hex}"
    with psycopg.connect(dsn) as connection:
        connection.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        connection.execute(f"SET search_path TO {schema_name}")
        bootstrap = bootstrap_postgresql_phase1_schema(connection)
        repository = PostgreSQLNormalizedFactorRuntimeRepository(connection)

        first = repository.insert_normalized_factor_records(_batch())
        second = repository.insert_normalized_factor_records(_batch())
        cursor = connection.execute(
            "SELECT COUNT(*) FROM normalized_factor_records",
        )

        assert bootstrap.missing_table_names == ()
        assert first.inserted == 1
        assert second.inserted == 0
        assert second.skipped_duplicate == 1
        assert cursor.fetchone()[0] == 1


def _batch(
    *,
    normalized_fields: dict[str, object] | None = None,
) -> ParserNormalizedOutputBatch:
    artifact = create_phase1_parser_input_artifact(
        source_family="defra_desnz",
        artifact_reference="artifact://defra/conversion-factors-2024.csv",
        checksum_sha256="a" * 64,
        reporting_year=2024,
    )
    fields = {
        "source_year": 2024,
        "source_version": "conversion-factors-2024",
        "source_checksum_sha256": "a" * 64,
        "source_document_id": "defra-document-2024",
        "factor_id": "DEFRA-2024-ELEC",
        "factor_name": "Electricity generated",
        "factor_value": Decimal("0.20705"),
        "factor_unit": "kWh",
        "run_id": "local-only-run-001",
    }
    if normalized_fields is not None:
        fields = normalized_fields
    return create_parser_normalized_output_batch(
        (
            create_parser_normalized_output_row(
                artifact=artifact,
                row_id="defra-row-001",
                source_row_number=2,
                status=ParserNormalizedOutputRowStatus.DECLARED,
                normalized_fields=fields,
            ),
        ),
    )
