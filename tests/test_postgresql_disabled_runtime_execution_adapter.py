import builtins
import dataclasses
import inspect
import sqlite3
import urllib.request

import carbonfactor_parser.persistence.postgresql_disabled_runtime_execution_adapter as adapter_module
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PostgreSQLDisabledRuntimeExecutionAdapter,
    PostgreSQLDisabledRuntimeExecutionStatus,
    PostgreSQLInsertStatement,
    PostgreSQLPersistenceRepository,
    build_default_postgresql_idempotency_conflict_strategy,
    build_default_postgresql_transaction_policy,
    build_postgresql_disabled_runtime_execution_result,
    build_postgresql_execution_plan,
    build_psycopg_session_adapter_metadata,
    describe_postgresql_disabled_runtime_execution,
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


def test_disabled_runtime_execution_adapter_imports_from_public_api() -> None:
    description = describe_postgresql_disabled_runtime_execution()

    assert description.status == PostgreSQLDisabledRuntimeExecutionStatus.DISABLED
    assert description.consumes_insert_statement is True
    assert description.consumes_execution_plan is True
    assert description.consumes_transaction_policy is True
    assert description.consumes_conflict_strategy is True
    assert description.consumes_session_adapter_metadata is True
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


def test_disabled_result_preserves_statement_and_policy_metadata() -> None:
    transaction_policy = build_default_postgresql_transaction_policy()
    conflict_strategy = build_default_postgresql_idempotency_conflict_strategy()
    session_metadata = build_psycopg_session_adapter_metadata(
        session_reference_provided=True,
    )

    result = build_postgresql_disabled_runtime_execution_result(
        statement=_statement(),
        transaction_policy=transaction_policy,
        conflict_strategy=conflict_strategy,
        session_adapter_metadata=session_metadata,
    )

    assert result.status == PostgreSQLDisabledRuntimeExecutionStatus.DISABLED
    assert result.reason == (
        "PostgreSQL runtime execution adapter is disabled and returns "
        "metadata only."
    )
    assert result.no_execution is True
    assert result.target_table_name == "normalized_records"
    assert result.record_count == 1
    assert result.statement_count == 1
    assert result.sql_preview == _statement().sql
    assert result.execution_plan is not None
    assert result.execution_plan.parameter_rows == (
        ("defra_desnz", "fixture-2024"),
    )
    assert result.transaction_plan is not None
    assert result.transaction_plan.policy == transaction_policy
    assert result.transaction_plan.record_count == 1
    assert result.transaction_plan.statement_count == 1
    assert result.conflict_strategy_plan is not None
    assert result.conflict_strategy_plan.strategy == conflict_strategy
    assert result.conflict_strategy_plan.idempotency_key_fields == (
        "source_family",
        "source_id",
        "record_id",
    )
    assert result.conflict_strategy_plan.sql_mutation_enabled is False
    assert result.session_adapter_metadata == session_metadata
    assert [issue.code for issue in result.issues] == [
        "POSTGRESQL_RUNTIME_EXECUTION_DISABLED",
    ]


def test_disabled_adapter_accepts_existing_execution_plan() -> None:
    plan_result = build_postgresql_execution_plan(_statement())
    assert plan_result.plan is not None

    result = PostgreSQLDisabledRuntimeExecutionAdapter().build_result(
        execution_plan=plan_result.plan,
    )

    assert result.status == PostgreSQLDisabledRuntimeExecutionStatus.DISABLED
    assert result.execution_plan == plan_result.plan
    assert result.target_table_name == plan_result.plan.target_table_name
    assert result.record_count == plan_result.plan.record_count
    assert result.statement_count == plan_result.plan.statement_count
    assert result.sql_preview == plan_result.plan.statement_contract.sql
    assert result.no_execution is True
    assert result.runtime_metadata is not None
    assert result.runtime_metadata.no_execution is True
    assert result.runtime_metadata.runtime_enabled is False


def test_no_statement_returns_no_statement_without_ready_runtime_metadata() -> None:
    result = build_postgresql_disabled_runtime_execution_result()

    assert result.status == PostgreSQLDisabledRuntimeExecutionStatus.NO_STATEMENT
    assert result.no_execution is True
    assert result.target_table_name is None
    assert result.record_count == 0
    assert result.statement_count == 0
    assert result.sql_preview is None
    assert result.runtime_metadata is not None
    assert result.runtime_metadata.no_execution is True
    assert [issue.code for issue in result.issues] == [
        "POSTGRESQL_EXECUTION_NO_STATEMENT",
    ]


def test_disabled_result_does_not_report_runtime_success_semantics() -> None:
    result = build_postgresql_disabled_runtime_execution_result(
        statement=_statement(),
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
    assert result.status == PostgreSQLDisabledRuntimeExecutionStatus.DISABLED
    assert result.no_execution is True
    assert result.runtime_metadata is not None
    assert result.runtime_metadata.runs_sql is False
    assert result.runtime_metadata.writes_records is False
    assert result.runtime_metadata.commits_transaction is False
    assert result.runtime_metadata.rolls_back_transaction is False


def test_disabled_runtime_execution_has_no_external_side_effects(monkeypatch) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("disabled adapter must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    result = build_postgresql_disabled_runtime_execution_result(
        statement=_statement(),
    )

    assert result.no_execution is True
    assert result.runtime_metadata is not None
    assert result.runtime_metadata.opens_connection is False


def test_disabled_runtime_adapter_module_has_no_driver_or_runtime_calls() -> None:
    source = inspect.getsource(adapter_module)
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
