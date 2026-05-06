import builtins
import inspect
import os
import sqlite3
import urllib.request

import carbonfactor_parser.persistence.postgresql_runtime_execution_gate as gate_module
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PersistenceInputRecord,
    PersistenceResultStatus,
    PostgreSQLPersistenceRepository,
    PostgreSQLRuntimeExecutionGate,
    PostgreSQLRuntimeExecutionGateStatus,
    describe_postgresql_runtime_execution_gate,
    evaluate_postgresql_runtime_execution_gate,
)
from carbonfactor_parser.persistence import ddl_preview
from carbonfactor_parser.persistence import postgresql_connection_session_contract
from carbonfactor_parser.persistence import postgresql_disabled_runtime_execution_adapter
from carbonfactor_parser.persistence import postgresql_execution_adapter_boundary
from carbonfactor_parser.persistence import postgresql_idempotency_conflict_strategy
from carbonfactor_parser.persistence import postgresql_insert_builder
from carbonfactor_parser.persistence import postgresql_persistence_preview
from carbonfactor_parser.persistence import postgresql_repository
from carbonfactor_parser.persistence import postgresql_repository_disabled_execution_preview
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
    postgresql_repository_disabled_execution_preview,
    postgresql_transaction_policy,
    schema,
)


def _persistence_input() -> PersistenceInput:
    return PersistenceInput(
        source_family="defra_desnz",
        source_id="fixture-2024",
        records=(
            PersistenceInputRecord(
                source_family="defra_desnz",
                source_id="fixture-2024",
                record_id="fixture-2024-1",
                normalized_fields=(("activity", "activity-1"),),
            ),
        ),
    )


def test_runtime_execution_gate_imports_from_public_api() -> None:
    description = describe_postgresql_runtime_execution_gate()

    assert description.default_status == PostgreSQLRuntimeExecutionGateStatus.DISABLED
    assert description.disabled_by_default is True
    assert description.accepts_caller_intent is True
    assert description.opens_connection is False
    assert description.creates_cursor is False
    assert description.runs_sql is False
    assert description.writes_records is False
    assert description.starts_transaction is False
    assert description.commits_transaction is False
    assert description.rolls_back_transaction is False
    assert description.creates_tables is False
    assert description.runs_migrations is False
    assert description.loads_environment is False
    assert description.loads_config_files is False
    assert description.loads_credentials is False
    assert description.changes_repository_persist_behavior is False


def test_default_gate_decision_is_disabled_no_execution() -> None:
    decision = evaluate_postgresql_runtime_execution_gate()

    assert decision.status == PostgreSQLRuntimeExecutionGateStatus.DISABLED
    assert decision.requested is False
    assert decision.reason == "PostgreSQL runtime execution is disabled by default."
    assert decision.no_execution is True
    assert decision.runtime_enabled is False
    assert decision.connection_required_now is False
    assert decision.session_required_now is False
    assert decision.required_future_components == (
        "postgresql_implementation_safety_gate",
        "postgresql_runtime_execution_adapter",
        "caller_provided_postgresql_session",
        "explicit_postgresql_integration_test_opt_in",
        "repository_runtime_persistence_task",
    )
    assert [issue.code for issue in decision.issues] == [
        "POSTGRESQL_RUNTIME_EXECUTION_DISABLED_BY_DEFAULT",
    ]


def test_requested_false_returns_disabled_no_execution() -> None:
    decision = evaluate_postgresql_runtime_execution_gate(
        PostgreSQLRuntimeExecutionGate(requested=False),
    )

    assert decision.status == PostgreSQLRuntimeExecutionGateStatus.DISABLED
    assert decision.requested is False
    assert decision.no_execution is True
    assert decision.runtime_enabled is False


def test_requested_true_without_components_returns_blocked_metadata() -> None:
    decision = evaluate_postgresql_runtime_execution_gate(
        PostgreSQLRuntimeExecutionGate(requested=True),
    )

    assert decision.status == PostgreSQLRuntimeExecutionGateStatus.BLOCKED
    assert decision.requested is True
    assert decision.no_execution is True
    assert decision.runtime_enabled is False
    assert decision.connection_required_now is False
    assert decision.session_required_now is False
    assert decision.required_future_components == (
        "postgresql_implementation_safety_gate",
        "postgresql_runtime_execution_adapter",
        "caller_provided_postgresql_session",
        "explicit_postgresql_integration_test_opt_in",
        "repository_runtime_persistence_task",
    )
    assert [issue.code for issue in decision.issues] == [
        "POSTGRESQL_RUNTIME_EXECUTION_BLOCKED",
    ]


def test_requested_true_with_future_metadata_still_not_enabled() -> None:
    decision = evaluate_postgresql_runtime_execution_gate(
        PostgreSQLRuntimeExecutionGate(
            requested=True,
            safety_gate_approved=True,
            runtime_adapter_available=True,
            caller_provided_session_available=True,
            integration_test_opt_in_complete=True,
            repository_runtime_enabled=True,
        ),
    )

    assert decision.status == PostgreSQLRuntimeExecutionGateStatus.NOT_ENABLED
    assert decision.requested is True
    assert decision.no_execution is True
    assert decision.runtime_enabled is False
    assert decision.required_future_components == ()
    assert [issue.code for issue in decision.issues] == [
        "POSTGRESQL_RUNTIME_EXECUTION_NOT_ENABLED",
    ]


def test_gate_has_no_external_side_effects(monkeypatch) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("runtime execution gate must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(os, "getenv", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    decision = evaluate_postgresql_runtime_execution_gate(
        PostgreSQLRuntimeExecutionGate(requested=True),
    )

    assert decision.no_execution is True
    assert decision.runtime_enabled is False


def test_repository_persist_remains_unsupported_no_execution() -> None:
    result = PostgreSQLPersistenceRepository().persist(_persistence_input())

    assert result.status == PersistenceResultStatus.UNSUPPORTED
    assert result.persisted_record_count == 0
    assert result.attempted_record_count == 1
    assert result.repository_metadata is not None
    assert result.repository_metadata["runtime_write"] is False
    assert result.repository_metadata["database_connection"] is False
    assert result.repository_metadata["migration_runtime"] is False


def test_gate_module_has_no_driver_or_runtime_calls() -> None:
    source = inspect.getsource(gate_module)
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


def test_pure_persistence_modules_remain_driver_free() -> None:
    for module in PURE_PERSISTENCE_MODULES:
        source = inspect.getsource(module)

        assert "import psycopg" not in source
        assert "from psycopg" not in source
