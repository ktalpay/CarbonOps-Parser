import builtins
import inspect
import sqlite3
import urllib.request

import carbonfactor_parser.persistence.postgresql_connection_session_contract as session_module
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PostgreSQLConnectionSession,
    PostgreSQLPersistenceRepository,
    PostgreSQLStatementExecutionContract,
    PostgreSQLTransactionBoundary,
    PostgreSQLTransactionMode,
    PostgreSQLTransactionOwnership,
    describe_postgresql_connection_session_contract,
)
from carbonfactor_parser.persistence.repository import PersistenceResultStatus


class FakeCallerProvidedSession:
    provider_name = "fake-postgresql-session"

    def run_statement(
        self,
        statement: PostgreSQLStatementExecutionContract,
    ) -> object:
        return {
            "provider_name": self.provider_name,
            "sql": statement.sql,
            "parameters": statement.parameters,
        }


def test_connection_session_contract_imports_from_public_api() -> None:
    description = describe_postgresql_connection_session_contract()

    assert description.driver_neutral is True
    assert description.caller_provided is True
    assert description.opens_connection is False
    assert description.runs_sql is False


def test_fake_caller_provided_session_satisfies_protocol() -> None:
    fake_session = FakeCallerProvidedSession()

    assert isinstance(fake_session, PostgreSQLConnectionSession)
    assert fake_session.provider_name == "fake-postgresql-session"


def test_statement_execution_contract_preserves_sql_and_parameters() -> None:
    statement = PostgreSQLStatementExecutionContract(
        sql="INSERT INTO normalized_records (source_id) VALUES (%s)",
        parameters=("defra_desnz",),
        statement_metadata={"boundary": "contract-only"},
    )

    assert statement.sql == "INSERT INTO normalized_records (source_id) VALUES (%s)"
    assert statement.parameters == ("defra_desnz",)
    assert statement.statement_metadata == {"boundary": "contract-only"}


def test_transaction_boundary_preserves_descriptive_markers() -> None:
    boundary = PostgreSQLTransactionBoundary(
        ownership=PostgreSQLTransactionOwnership.REPOSITORY_OWNED_FUTURE,
        mode=PostgreSQLTransactionMode.SINGLE_BATCH_FUTURE,
        rollback_on_failure=True,
    )

    description = describe_postgresql_connection_session_contract(
        transaction_boundary=boundary,
    )

    assert description.transaction_boundary == boundary
    assert description.transaction_boundary.ownership == (
        PostgreSQLTransactionOwnership.REPOSITORY_OWNED_FUTURE
    )
    assert description.transaction_boundary.mode == (
        PostgreSQLTransactionMode.SINGLE_BATCH_FUTURE
    )


def test_description_helper_has_no_external_side_effects(monkeypatch) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("contract description must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    description = describe_postgresql_connection_session_contract()

    assert description.opens_connection is False
    assert description.loads_environment is False
    assert description.loads_config_files is False
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


def test_connection_session_contract_module_has_no_db_driver_or_runtime_behavior() -> None:
    module_source = inspect.getsource(session_module)
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
