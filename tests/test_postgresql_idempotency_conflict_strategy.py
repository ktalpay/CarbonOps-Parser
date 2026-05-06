import builtins
import inspect
import sqlite3
import urllib.request

import carbonfactor_parser.persistence.postgresql_idempotency_conflict_strategy as strategy_module
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PersistenceInputRecord,
    PostgreSQLConflictAction,
    PostgreSQLConflictStrategyStatus,
    PostgreSQLIdempotencyRequirement,
    PostgreSQLInsertStatement,
    PostgreSQLPersistenceRepository,
    build_default_postgresql_idempotency_conflict_strategy,
    build_postgresql_conflict_strategy_plan,
    build_postgresql_insert_statement,
    describe_postgresql_idempotency_conflict_strategy_boundary,
)
from carbonfactor_parser.persistence.repository import PersistenceResultStatus


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


def _persistence_input() -> PersistenceInput:
    return PersistenceInput(
        source_family="defra_desnz",
        source_id="defra_desnz",
        records=(
            PersistenceInputRecord(
                source_family="defra_desnz",
                source_id="defra_desnz",
                record_id="defra_desnz:defra_desnz:record-001",
                normalized_fields=(("factor_id", "F1"),),
            ),
        ),
    )


def test_default_conflict_strategy_imports_from_public_api() -> None:
    strategy = build_default_postgresql_idempotency_conflict_strategy()

    assert strategy.conflict_action == PostgreSQLConflictAction.FAIL_ON_CONFLICT
    assert strategy.idempotency_requirement == (
        PostgreSQLIdempotencyRequirement.IDEMPOTENCY_FIELDS_REQUIRED
    )
    assert strategy.silent_skip_enabled is False
    assert strategy.upsert_enabled is False
    assert strategy.sql_mutation_enabled is False
    assert strategy.runtime_enabled is False


def test_conflict_strategy_plan_preserves_statement_metadata_only() -> None:
    statement = _statement()

    result = build_postgresql_conflict_strategy_plan(statement)

    assert result.status == PostgreSQLConflictStrategyStatus.READY
    assert result.issues == ()
    assert result.plan is not None
    assert result.plan.target_table_name == statement.target_table_name
    assert result.plan.record_count == statement.record_count
    assert result.plan.idempotency_key_fields == statement.idempotency_key_fields
    assert result.plan.conflict_target_fields == statement.conflict_target_fields
    assert result.plan.insert_sql == statement.sql
    assert result.plan.sql_mutation_enabled is False
    assert result.plan.runtime_enabled is False


def test_no_statement_returns_no_statement_status_without_plan() -> None:
    result = build_postgresql_conflict_strategy_plan(None)

    assert result.status == PostgreSQLConflictStrategyStatus.NO_STATEMENT
    assert result.plan is None
    assert [issue.code for issue in result.issues] == [
        "POSTGRESQL_CONFLICT_STRATEGY_NO_STATEMENT",
    ]


def test_missing_idempotency_metadata_returns_failed_result() -> None:
    result = build_postgresql_conflict_strategy_plan(
        PostgreSQLInsertStatement(
            sql="INSERT INTO normalized_records (source_family) VALUES (%s)",
            parameters=(("defra_desnz",),),
            target_table_name="normalized_records",
            column_names=("source_family",),
            record_count=1,
            idempotency_key_fields=(),
            conflict_target_fields=(),
        ),
    )

    assert result.status == PostgreSQLConflictStrategyStatus.FAILED
    assert result.plan is None
    assert [issue.code for issue in result.issues] == [
        "POSTGRESQL_IDEMPOTENCY_FIELDS_MISSING",
        "POSTGRESQL_CONFLICT_TARGET_FIELDS_MISSING",
    ]


def test_strategy_does_not_change_insert_builder_output() -> None:
    before = build_postgresql_insert_statement(_persistence_input())
    assert before.statement is not None

    strategy_result = build_postgresql_conflict_strategy_plan(before.statement)
    after = build_postgresql_insert_statement(_persistence_input())

    assert after.statement is not None
    assert strategy_result.plan is not None
    assert after.statement.sql == before.statement.sql
    assert after.statement.parameters == before.statement.parameters
    assert after.statement.column_names == before.statement.column_names
    assert strategy_result.plan.insert_sql == before.statement.sql
    assert "ON CONFLICT" not in after.statement.sql
    assert "DO NOTHING" not in after.statement.sql
    assert "DO UPDATE" not in after.statement.sql


def test_strategy_description_has_no_runtime_behavior() -> None:
    description = describe_postgresql_idempotency_conflict_strategy_boundary()

    assert description.driver_neutral is True
    assert description.opens_connection is False
    assert description.runs_sql is False
    assert description.writes_records is False
    assert description.mutates_insert_sql is False
    assert description.generates_conflict_sql is False
    assert description.uses_existing_idempotency_metadata is True
    assert description.loads_credentials is False


def test_strategy_helpers_have_no_external_side_effects(monkeypatch) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("conflict strategy must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    description = describe_postgresql_idempotency_conflict_strategy_boundary()
    result = build_postgresql_conflict_strategy_plan(_statement())

    assert description.opens_connection is False
    assert result.plan is not None
    assert result.plan.runtime_enabled is False


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


def test_conflict_strategy_module_has_no_driver_or_runtime_behavior() -> None:
    module_source = inspect.getsource(strategy_module)
    lower_source = module_source.lower()

    assert "psycopg" not in lower_source
    assert "asyncpg" not in lower_source
    assert "sqlalchemy" not in lower_source
    assert "create_engine" not in module_source
    assert "connect(" not in module_source
    assert "cursor(" not in module_source
    assert "execute(" not in module_source
    assert "commit(" not in module_source
    assert "rollback(" not in module_source
    assert "ON CONFLICT" not in module_source
    assert "DO NOTHING" not in module_source
    assert "DO UPDATE" not in module_source
    assert "os.environ" not in module_source
    assert "getenv" not in module_source
