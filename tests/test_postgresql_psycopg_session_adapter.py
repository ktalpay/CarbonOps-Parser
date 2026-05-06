import builtins
import inspect
import sqlite3
import urllib.request

import carbonfactor_parser.persistence.postgresql_psycopg_session_adapter as adapter_module
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PsycopgPostgreSQLSessionAdapter,
    PsycopgPostgreSQLSessionAdapterStatus,
    PostgreSQLExecutionStatus,
    PostgreSQLInsertStatement,
    PostgreSQLPersistenceRepository,
    build_postgresql_execution_plan,
    build_psycopg_session_adapter_metadata,
    validate_psycopg_session_adapter_boundary,
)
from carbonfactor_parser.persistence import ddl_preview
from carbonfactor_parser.persistence import postgresql_connection_session_contract
from carbonfactor_parser.persistence import postgresql_execution_adapter_boundary
from carbonfactor_parser.persistence import postgresql_idempotency_conflict_strategy
from carbonfactor_parser.persistence import postgresql_insert_builder
from carbonfactor_parser.persistence import postgresql_persistence_preview
from carbonfactor_parser.persistence import postgresql_repository
from carbonfactor_parser.persistence import postgresql_transaction_policy
from carbonfactor_parser.persistence import schema
from carbonfactor_parser.persistence.repository import PersistenceResultStatus


PURE_PERSISTENCE_MODULES = (
    ddl_preview,
    postgresql_connection_session_contract,
    postgresql_execution_adapter_boundary,
    postgresql_idempotency_conflict_strategy,
    postgresql_insert_builder,
    postgresql_persistence_preview,
    postgresql_repository,
    postgresql_transaction_policy,
    schema,
)


def _statement() -> PostgreSQLInsertStatement:
    return PostgreSQLInsertStatement(
        sql=(
            "INSERT INTO normalized_records "
            "(source_family, source_id) VALUES (%s, %s)"
        ),
        parameters=(("defra_desnz", "fixture-2024"),),
        target_table_name="normalized_records",
        column_names=("source_family", "source_id"),
        record_count=1,
        idempotency_key_fields=("source_family", "source_id", "record_id"),
        conflict_target_fields=("source_family", "source_id", "record_id"),
    )


class ExplodingSessionReference:
    def __getattribute__(self, name):
        raise AssertionError("session reference must not be inspected")


def test_psycopg_session_adapter_imports_from_public_api() -> None:
    metadata = build_psycopg_session_adapter_metadata()

    assert metadata.provider_name == "postgresql_psycopg"
    assert metadata.driver_name == "psycopg"
    assert metadata.caller_provided_session_required is True
    assert metadata.session_reference_provided is False
    assert metadata.opens_connection is False
    assert metadata.creates_cursor is False
    assert metadata.runs_sql is False
    assert metadata.writes_records is False
    assert metadata.starts_transaction is False
    assert metadata.commits_transaction is False
    assert metadata.rolls_back_transaction is False
    assert metadata.loads_environment is False
    assert metadata.loads_config_files is False
    assert metadata.loads_credentials is False
    assert metadata.runtime_enabled is False


def test_caller_provided_session_reference_is_not_touched() -> None:
    adapter = PsycopgPostgreSQLSessionAdapter(
        session_reference=ExplodingSessionReference(),
    )

    metadata = adapter.describe_capabilities()
    result = adapter.validate_adapter_boundary()

    assert metadata.session_reference_provided is True
    assert result.status == PsycopgPostgreSQLSessionAdapterStatus.DISABLED
    assert result.metadata.session_reference_provided is True


def test_adapter_boundary_validation_returns_disabled_no_execution_result() -> None:
    result = validate_psycopg_session_adapter_boundary()

    assert result.status == PsycopgPostgreSQLSessionAdapterStatus.DISABLED
    assert result.metadata.opens_connection is False
    assert result.metadata.creates_cursor is False
    assert result.metadata.runs_sql is False
    assert result.metadata.writes_records is False
    assert [issue.code for issue in result.issues] == [
        "PSYCOPG_SESSION_ADAPTER_NO_EXECUTION",
    ]


def test_disabled_execution_result_preserves_plan_metadata_without_running_sql() -> None:
    plan_result = build_postgresql_execution_plan(_statement())
    assert plan_result.plan is not None
    adapter = PsycopgPostgreSQLSessionAdapter()

    result = adapter.build_disabled_execution_result(plan_result.plan)

    assert result.status == PostgreSQLExecutionStatus.DISABLED
    assert result.affected_record_count == 0
    assert result.statement_count == 1
    assert result.plan == plan_result.plan
    assert result.plan.target_table_name == "normalized_records"
    assert result.plan.parameter_rows == (("defra_desnz", "fixture-2024"),)
    assert [issue.code for issue in result.issues] == [
        "PSYCOPG_SESSION_ADAPTER_DISABLED",
    ]


def test_adapter_metadata_has_no_external_side_effects(monkeypatch) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("adapter skeleton must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    adapter = PsycopgPostgreSQLSessionAdapter()
    metadata = adapter.describe_capabilities()
    result = adapter.validate_adapter_boundary()

    assert metadata.runtime_enabled is False
    assert result.status == PsycopgPostgreSQLSessionAdapterStatus.DISABLED


def test_adapter_module_import_boundary_is_psycopg_only_and_no_execution() -> None:
    source = inspect.getsource(adapter_module)
    lower_source = source.lower()

    assert "import psycopg" in source
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


def test_pure_persistence_modules_remain_psycopg_free() -> None:
    for module in PURE_PERSISTENCE_MODULES:
        source = inspect.getsource(module)

        assert "import psycopg" not in source
        assert "from psycopg" not in source


def test_repository_skeleton_remains_unsupported_no_execution() -> None:
    repository = PostgreSQLPersistenceRepository()

    result = repository.persist(
        PersistenceInput(
            source_family="defra_desnz",
            source_id="defra_desnz",
            records=(),
        ),
    )

    assert result.status == PersistenceResultStatus.UNSUPPORTED
    assert result.persisted_record_count == 0
    assert result.repository_metadata["database_connection"] is False
    assert result.repository_metadata["runtime_write"] is False
