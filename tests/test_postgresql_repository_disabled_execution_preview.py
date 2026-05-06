import builtins
import dataclasses
import inspect
import sqlite3
import urllib.request

import carbonfactor_parser.persistence.postgresql_repository_disabled_execution_preview as preview_module
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PersistenceInputRecord,
    PersistenceResultStatus,
    PostgreSQLDisabledRuntimeExecutionStatus,
    PostgreSQLInsertBuildStatus,
    PostgreSQLPersistenceRepository,
    PostgreSQLRepositoryDisabledExecutionPreviewStatus,
    build_postgresql_repository_disabled_execution_preview,
    describe_postgresql_repository_disabled_execution_preview,
)
from carbonfactor_parser.persistence import ddl_preview
from carbonfactor_parser.persistence import postgresql_connection_session_contract
from carbonfactor_parser.persistence import postgresql_disabled_runtime_execution_adapter
from carbonfactor_parser.persistence import postgresql_execution_adapter_boundary
from carbonfactor_parser.persistence import postgresql_idempotency_conflict_strategy
from carbonfactor_parser.persistence import postgresql_insert_builder
from carbonfactor_parser.persistence import postgresql_persistence_preview
from carbonfactor_parser.persistence import postgresql_repository
from carbonfactor_parser.persistence import postgresql_transaction_policy
from carbonfactor_parser.persistence import schema


PURE_PERSISTENCE_MODULES = (
    ddl_preview,
    postgresql_connection_session_contract,
    postgresql_disabled_runtime_execution_adapter,
    postgresql_execution_adapter_boundary,
    postgresql_idempotency_conflict_strategy,
    postgresql_insert_builder,
    postgresql_persistence_preview,
    postgresql_repository,
    postgresql_transaction_policy,
    schema,
)

EXPECTED_INSERT_SQL = (
    "INSERT INTO normalized_records "
    "(source_family, source_id, record_id, record_index, row_number, "
    "normalized_fields, source_reference, source_artifact_reference, "
    "source_checksum_sha256, parser_metadata, normalization_metadata, "
    "created_at, updated_at) VALUES "
    "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
)


def _persistence_input(
    records: tuple[PersistenceInputRecord, ...] | None = None,
) -> PersistenceInput:
    return PersistenceInput(
        source_family="defra_desnz",
        source_id="fixture-2024",
        records=records
        if records is not None
        else (
            _persistence_record("fixture-2024-1", 1),
            _persistence_record("fixture-2024-2", 2),
        ),
        parser_metadata={"source_artifact_reference": "examples/fixtures.csv"},
        normalization_metadata={"normalizer": "minimal_fixture"},
    )


def _persistence_record(record_id: str, row_number: int) -> PersistenceInputRecord:
    return PersistenceInputRecord(
        source_family="defra_desnz",
        source_id="fixture-2024",
        record_id=record_id,
        normalized_fields=(
            ("activity", f"activity-{row_number}"),
            ("factor_value", row_number * 1.25),
            ("unit", "kgCO2e"),
        ),
        record_index=row_number - 1,
        row_number=row_number,
        source_reference=f"row:{row_number}",
        parser_metadata={
            "source_artifact_reference": "examples/fixtures.csv",
            "source_checksum_sha256": f"checksum-{row_number}",
        },
        normalization_metadata={"normalizer": "minimal_fixture"},
    )


def test_repository_disabled_execution_preview_imports_from_public_api() -> None:
    description = describe_postgresql_repository_disabled_execution_preview()

    assert description.accepts_persistence_input is True
    assert description.builds_insert_statement is True
    assert description.builds_disabled_runtime_result is True
    assert description.returns_persistence_result is False
    assert description.opens_connection is False
    assert description.creates_cursor is False
    assert description.runs_sql is False
    assert description.writes_records is False
    assert description.starts_transaction is False
    assert description.commits_transaction is False
    assert description.rolls_back_transaction is False
    assert description.loads_environment is False
    assert description.loads_config_files is False
    assert description.loads_credentials is False
    assert description.persist_behavior_changed is False


def test_valid_input_builds_disabled_no_execution_preview_metadata() -> None:
    result = build_postgresql_repository_disabled_execution_preview(
        _persistence_input(),
    )

    assert result.status == PostgreSQLRepositoryDisabledExecutionPreviewStatus.DISABLED
    assert result.reason == (
        "PostgreSQL repository disabled execution preview was built; "
        "runtime persistence remains unsupported."
    )
    assert result.no_execution is True
    assert result.source_family == "defra_desnz"
    assert result.source_id == "fixture-2024"
    assert result.attempted_record_count == 2
    assert result.insert_build_status == PostgreSQLInsertBuildStatus.READY
    assert result.disabled_runtime_result is not None
    runtime_result = result.disabled_runtime_result
    assert runtime_result.status == PostgreSQLDisabledRuntimeExecutionStatus.DISABLED
    assert runtime_result.no_execution is True
    assert runtime_result.target_table_name == "normalized_records"
    assert runtime_result.record_count == 2
    assert runtime_result.statement_count == 1
    assert runtime_result.sql_preview == EXPECTED_INSERT_SQL
    assert runtime_result.execution_plan is not None
    assert runtime_result.execution_plan.column_names == (
        "source_family",
        "source_id",
        "record_id",
        "record_index",
        "row_number",
        "normalized_fields",
        "source_reference",
        "source_artifact_reference",
        "source_checksum_sha256",
        "parser_metadata",
        "normalization_metadata",
        "created_at",
        "updated_at",
    )
    assert runtime_result.execution_plan.parameter_rows[0] == (
        "defra_desnz",
        "fixture-2024",
        "fixture-2024-1",
        0,
        1,
        (
            ("activity", "activity-1"),
            ("factor_value", 1.25),
            ("unit", "kgCO2e"),
        ),
        "row:1",
        "examples/fixtures.csv",
        "checksum-1",
        (
            ("source_artifact_reference", "examples/fixtures.csv"),
            ("source_checksum_sha256", "checksum-1"),
        ),
        (("normalizer", "minimal_fixture"),),
        None,
        None,
    )
    assert runtime_result.transaction_plan is not None
    assert runtime_result.transaction_plan.runtime_enabled is False
    assert runtime_result.conflict_strategy_plan is not None
    assert runtime_result.conflict_strategy_plan.sql_mutation_enabled is False
    assert runtime_result.conflict_strategy_plan.idempotency_key_fields == (
        "source_family",
        "source_id",
        "record_id",
        "source_artifact_reference",
        "source_checksum_sha256",
    )
    assert runtime_result.runtime_metadata is not None
    assert runtime_result.runtime_metadata.opens_connection is False
    assert runtime_result.runtime_metadata.runs_sql is False
    assert runtime_result.runtime_metadata.writes_records is False
    assert [issue.code for issue in result.issues] == [
        "POSTGRESQL_REPOSITORY_DISABLED_EXECUTION_PREVIEW",
    ]


def test_no_records_input_returns_deterministic_no_execution_preview() -> None:
    result = build_postgresql_repository_disabled_execution_preview(
        _persistence_input(records=()),
    )

    assert result.status == PostgreSQLRepositoryDisabledExecutionPreviewStatus.NO_RECORDS
    assert result.no_execution is True
    assert result.attempted_record_count == 0
    assert result.insert_build_status == PostgreSQLInsertBuildStatus.NO_RECORDS
    assert result.disabled_runtime_result is not None
    assert (
        result.disabled_runtime_result.status
        == PostgreSQLDisabledRuntimeExecutionStatus.NO_STATEMENT
    )
    assert result.disabled_runtime_result.sql_preview is None
    assert [issue.code for issue in result.issues] == [
        "POSTGRESQL_INSERT_NO_RECORDS",
    ]


def test_invalid_record_shape_returns_failed_no_execution_preview() -> None:
    invalid_record = PersistenceInputRecord(
        source_family="defra_desnz",
        source_id="fixture-2024",
        record_id="",
        normalized_fields=(("activity", "activity-1"),),
    )

    result = build_postgresql_repository_disabled_execution_preview(
        _persistence_input(records=(invalid_record,)),
    )

    assert result.status == PostgreSQLRepositoryDisabledExecutionPreviewStatus.FAILED
    assert result.no_execution is True
    assert result.attempted_record_count == 1
    assert result.insert_build_status == PostgreSQLInsertBuildStatus.FAILED
    assert result.disabled_runtime_result is not None
    assert (
        result.disabled_runtime_result.status
        == PostgreSQLDisabledRuntimeExecutionStatus.NO_STATEMENT
    )
    assert result.disabled_runtime_result.sql_preview is None
    assert [issue.code for issue in result.issues] == [
        "POSTGRESQL_INSERT_MISSING_RECORD_ID",
    ]


def test_preview_does_not_report_runtime_success_semantics() -> None:
    result = build_postgresql_repository_disabled_execution_preview(
        _persistence_input(),
    )

    result_fields = {field.name for field in dataclasses.fields(result)}
    forbidden_fields = {
        "persisted_record_count",
        "written_record_count",
        "committed_record_count",
        "rolled_back_record_count",
        "skipped_record_count",
        "upserted_record_count",
        "executed_statement_count",
    }

    assert forbidden_fields.isdisjoint(result_fields)
    assert not hasattr(result, "persisted_record_count")
    assert result.no_execution is True
    assert result.disabled_runtime_result is not None
    assert result.disabled_runtime_result.no_execution is True
    assert result.disabled_runtime_result.runtime_metadata is not None
    assert result.disabled_runtime_result.runtime_metadata.runs_sql is False


def test_preview_has_no_external_side_effects(monkeypatch) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("repository preview must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    result = build_postgresql_repository_disabled_execution_preview(
        _persistence_input(),
    )

    assert result.no_execution is True
    assert result.disabled_runtime_result is not None
    assert result.disabled_runtime_result.runtime_metadata is not None
    assert result.disabled_runtime_result.runtime_metadata.opens_connection is False


def test_repository_persist_remains_unsupported_no_execution() -> None:
    repository = PostgreSQLPersistenceRepository()

    result = repository.persist(_persistence_input())

    assert result.status == PersistenceResultStatus.UNSUPPORTED
    assert result.persisted_record_count == 0
    assert result.attempted_record_count == 2
    assert result.repository_metadata is not None
    assert result.repository_metadata["runtime_write"] is False
    assert result.repository_metadata["database_connection"] is False
    assert result.repository_metadata["migration_runtime"] is False


def test_preview_module_has_no_driver_or_runtime_calls() -> None:
    source = inspect.getsource(preview_module)
    lower_source = source.lower()

    assert "import psycopg" not in source
    assert "from psycopg" not in source
    assert "asyncpg" not in lower_source
    assert "sqlalchemy" not in lower_source
    assert "create_engine" not in source
    assert "psycopg.connect" not in source
    assert "connect(" not in source
    assert "cursor(" not in source
    assert "execute(" not in source
    assert "commit(" not in source
    assert "rollback(" not in source
    assert "begin(" not in source
    assert "os.environ" not in source
    assert "getenv" not in source
    assert "ON CONFLICT" not in source
    assert "DO NOTHING" not in source
    assert "DO UPDATE" not in source


def test_pure_persistence_modules_remain_psycopg_free() -> None:
    for module in PURE_PERSISTENCE_MODULES:
        source = inspect.getsource(module)

        assert "import psycopg" not in source
        assert "from psycopg" not in source
