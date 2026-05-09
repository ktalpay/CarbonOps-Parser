import builtins
import inspect
import sqlite3
import urllib.request
from dataclasses import replace

import carbonfactor_parser.persistence.postgresql_connection_session_contract as session_module
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PostgreSQLConnectionSession,
    PostgreSQLConnectionSessionContractIssue,
    PostgreSQLConnectionSessionContractStatus,
    PostgreSQLConnectionSessionContractValidationResult,
    PostgreSQLConnectionSessionRuntimeContract,
    PostgreSQLPersistenceRepository,
    PostgreSQLStatementExecutionContract,
    PostgreSQLTransactionBoundary,
    PostgreSQLTransactionMode,
    PostgreSQLTransactionOwnership,
    create_postgresql_connection_session_runtime_contract,
    describe_postgresql_connection_session_contract,
    validate_postgresql_connection_session_runtime_contract,
    validate_postgresql_statement_execution_contract,
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
    assert description.runtime_contract == (
        create_postgresql_connection_session_runtime_contract()
    )
    assert (
        validate_postgresql_connection_session_runtime_contract(
            description.runtime_contract,
        ).is_valid
        is True
    )


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
    assert validate_postgresql_statement_execution_contract(statement).is_valid is True


def test_statement_execution_contract_fails_closed_for_unsafe_shape() -> None:
    blank_sql = validate_postgresql_statement_execution_contract(
        PostgreSQLStatementExecutionContract(sql=" "),
    )
    text_parameters = validate_postgresql_statement_execution_contract(
        PostgreSQLStatementExecutionContract(
            sql="SELECT %s",
            parameters="not-a-parameter-sequence",
        ),
    )
    unsafe_metadata = validate_postgresql_statement_execution_contract(
        PostgreSQLStatementExecutionContract(
            sql="SELECT %s",
            parameters=(1,),
            statement_metadata=("not", "mapping"),  # type: ignore[arg-type]
        ),
    )

    assert blank_sql.status is PostgreSQLConnectionSessionContractStatus.BLOCKED
    assert _issue_codes(blank_sql.issues) == (
        "POSTGRESQL_CONNECTION_SESSION_STATEMENT_MISSING_SQL",
    )
    assert _issue_codes(text_parameters.issues) == (
        "POSTGRESQL_CONNECTION_SESSION_STATEMENT_PARAMETERS_UNSAFE",
    )
    assert _issue_codes(unsafe_metadata.issues) == (
        "POSTGRESQL_CONNECTION_SESSION_STATEMENT_METADATA_UNSAFE",
    )


def test_connection_session_runtime_contract_is_no_execution_by_default() -> None:
    contract = create_postgresql_connection_session_runtime_contract()

    assert contract == PostgreSQLConnectionSessionRuntimeContract(
        provider_name="caller_provided_postgresql_session",
        statement_method_name="run_statement",
        caller_provided=True,
        runtime_enabled=False,
        opens_connection=False,
        creates_cursor=False,
        runs_sql=False,
        writes_records=False,
        starts_transaction=False,
        commits_transaction=False,
        rolls_back_transaction=False,
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
        transaction_boundary=PostgreSQLTransactionBoundary(),
    )
    validation = validate_postgresql_connection_session_runtime_contract(contract)
    assert validation == PostgreSQLConnectionSessionContractValidationResult(
        status=PostgreSQLConnectionSessionContractStatus.READY,
    )


def test_connection_session_runtime_contract_fails_closed_for_runtime_flags() -> None:
    contract = replace(
        create_postgresql_connection_session_runtime_contract(provider_name=" "),
        statement_method_name="statement",
        caller_provided=False,
        runtime_enabled=True,
        opens_connection=True,
        creates_cursor=True,
        runs_sql=True,
        writes_records=True,
        starts_transaction=True,
        commits_transaction=True,
        rolls_back_transaction=True,
        loads_environment=True,
        loads_config_files=True,
        loads_credentials=True,
        transaction_boundary=PostgreSQLTransactionBoundary(
            ownership=PostgreSQLTransactionOwnership.REPOSITORY_OWNED_FUTURE,
            mode=PostgreSQLTransactionMode.SINGLE_BATCH_FUTURE,
            rollback_on_failure=False,
        ),
    )

    validation = validate_postgresql_connection_session_runtime_contract(contract)

    assert validation.is_valid is False
    assert validation.status is PostgreSQLConnectionSessionContractStatus.BLOCKED
    assert _issue_codes(validation.issues) == (
        "POSTGRESQL_CONNECTION_SESSION_MISSING_PROVIDER_NAME",
        "POSTGRESQL_CONNECTION_SESSION_STATEMENT_METHOD_MISMATCH",
        "POSTGRESQL_CONNECTION_SESSION_CALLER_PROVIDED_REQUIRED",
        "POSTGRESQL_CONNECTION_SESSION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_CONNECTION_SESSION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_CONNECTION_SESSION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_CONNECTION_SESSION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_CONNECTION_SESSION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_CONNECTION_SESSION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_CONNECTION_SESSION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_CONNECTION_SESSION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_CONNECTION_SESSION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_CONNECTION_SESSION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_CONNECTION_SESSION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_CONNECTION_SESSION_TRANSACTION_OWNERSHIP_UNSAFE",
        "POSTGRESQL_CONNECTION_SESSION_TRANSACTION_MODE_UNSAFE",
        "POSTGRESQL_CONNECTION_SESSION_ROLLBACK_MARKER_REQUIRED",
    )
    assert tuple(issue.field_name for issue in validation.issues[3:14]) == (
        "runtime_enabled",
        "opens_connection",
        "creates_cursor",
        "runs_sql",
        "writes_records",
        "starts_transaction",
        "commits_transaction",
        "rolls_back_transaction",
        "loads_environment",
        "loads_config_files",
        "loads_credentials",
    )


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


def test_connection_session_validation_has_no_external_side_effects(
    monkeypatch,
) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("session validation must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    contract = create_postgresql_connection_session_runtime_contract()
    statement = PostgreSQLStatementExecutionContract(sql="SELECT %s", parameters=(1,))

    assert validate_postgresql_connection_session_runtime_contract(contract).is_valid
    assert validate_postgresql_statement_execution_contract(statement).is_valid


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


def _issue_codes(
    issues: tuple[PostgreSQLConnectionSessionContractIssue, ...],
) -> tuple[str, ...]:
    return tuple(issue.code for issue in issues)
