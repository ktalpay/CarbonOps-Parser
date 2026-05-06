import builtins
import inspect
import sqlite3
import urllib.request

import carbonfactor_parser.persistence.postgresql_execution_adapter_boundary as boundary_module
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PostgreSQLExecutionAdapterProtocol,
    PostgreSQLExecutionStatus,
    PostgreSQLInsertStatement,
    PostgreSQLPersistenceRepository,
    PostgreSQLTransactionBoundary,
    PostgreSQLTransactionMode,
    PostgreSQLTransactionOwnership,
    build_disabled_postgresql_execution_result,
    build_postgresql_execution_plan,
    describe_postgresql_connection_session_contract,
    describe_postgresql_execution_adapter_boundary,
)
from carbonfactor_parser.persistence.repository import PersistenceResultStatus


class FakeBoundaryAdapter:
    adapter_name = "fake-boundary-adapter"
    runtime_enabled = False

    def build_plan(self, statement: PostgreSQLInsertStatement):
        result = build_postgresql_execution_plan(statement)
        assert result.plan is not None
        return result.plan


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


def test_execution_adapter_boundary_imports_from_public_api() -> None:
    description = describe_postgresql_execution_adapter_boundary()

    assert description.driver_neutral is True
    assert description.opens_connection is False
    assert description.runs_sql is False
    assert description.default_status == PostgreSQLExecutionStatus.DISABLED


def test_fake_boundary_adapter_satisfies_protocol_without_runtime_behavior() -> None:
    fake_adapter = FakeBoundaryAdapter()

    assert isinstance(fake_adapter, PostgreSQLExecutionAdapterProtocol)
    assert fake_adapter.runtime_enabled is False
    assert fake_adapter.build_plan(_statement()).runtime_enabled is False


def test_execution_plan_can_be_built_from_insert_statement() -> None:
    result = build_postgresql_execution_plan(
        _statement(),
        session_provider_name="caller-provided-future-session",
    )

    assert result.status == PostgreSQLExecutionStatus.READY
    assert result.issues == ()
    assert result.plan is not None
    assert result.plan.target_table_name == "normalized_records"
    assert result.plan.column_names == ("source_family", "source_id")
    assert result.plan.parameter_rows == (("defra_desnz", "fixture-2024"),)
    assert result.plan.record_count == 1
    assert result.plan.statement_count == 1
    assert result.plan.idempotency_key_fields == (
        "source_family",
        "source_id",
        "record_id",
    )
    assert result.plan.conflict_target_fields == (
        "source_family",
        "source_id",
        "record_id",
    )
    assert result.plan.session_provider_name == "caller-provided-future-session"
    assert result.plan.runtime_enabled is False


def test_execution_plan_preserves_statement_contract_metadata() -> None:
    result = build_postgresql_execution_plan(_statement())

    assert result.plan is not None
    statement_contract = result.plan.statement_contract
    assert statement_contract.sql == _statement().sql
    assert statement_contract.parameters == _statement().parameters
    assert statement_contract.statement_metadata == {
        "target_table_name": "normalized_records",
        "column_names": ("source_family", "source_id"),
        "record_count": 1,
        "idempotency_key_fields": (
            "source_family",
            "source_id",
            "record_id",
        ),
        "conflict_target_fields": (
            "source_family",
            "source_id",
            "record_id",
        ),
        "boundary": "postgresql_execution_adapter_no_execution",
    }


def test_execution_plan_uses_descriptive_transaction_boundary() -> None:
    session_description = describe_postgresql_connection_session_contract(
        transaction_boundary=PostgreSQLTransactionBoundary(
            ownership=PostgreSQLTransactionOwnership.REPOSITORY_OWNED_FUTURE,
            mode=PostgreSQLTransactionMode.SINGLE_BATCH_FUTURE,
            rollback_on_failure=True,
        ),
    )

    result = build_postgresql_execution_plan(
        _statement(),
        session_contract_description=session_description,
    )

    assert result.plan is not None
    assert result.plan.transaction_boundary == (
        session_description.transaction_boundary
    )


def test_no_statement_returns_no_statement_status_without_plan() -> None:
    result = build_postgresql_execution_plan(None)

    assert result.status == PostgreSQLExecutionStatus.NO_STATEMENT
    assert result.plan is None
    assert [issue.code for issue in result.issues] == [
        "POSTGRESQL_EXECUTION_NO_STATEMENT",
    ]


def test_disabled_execution_result_does_not_report_affected_records() -> None:
    plan_result = build_postgresql_execution_plan(_statement())
    assert plan_result.plan is not None

    result = build_disabled_postgresql_execution_result(plan_result.plan)

    assert result.status == PostgreSQLExecutionStatus.DISABLED
    assert result.affected_record_count == 0
    assert result.statement_count == 1
    assert [issue.code for issue in result.issues] == [
        "POSTGRESQL_EXECUTION_DISABLED",
    ]


def test_boundary_description_has_no_external_side_effects(monkeypatch) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("boundary description must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    description = describe_postgresql_execution_adapter_boundary()

    assert description.opens_connection is False
    assert description.runs_sql is False
    assert description.writes_records is False
    assert description.loads_credentials is False


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


def test_execution_adapter_boundary_module_has_no_driver_or_runtime_behavior() -> None:
    module_source = inspect.getsource(boundary_module)
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
    assert "os.environ" not in module_source
    assert "getenv" not in module_source
