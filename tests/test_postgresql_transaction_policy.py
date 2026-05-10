import builtins
import inspect
import sqlite3
import urllib.request
from dataclasses import replace

import carbonfactor_parser.persistence.postgresql_transaction_policy as policy_module
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PostgreSQLBatchTransactionMode,
    PostgreSQLInsertStatement,
    PostgreSQLPartialSuccessPolicy,
    PostgreSQLPersistenceRepository,
    PostgreSQLTransactionFailurePolicy,
    PostgreSQLTransactionPolicyIssue,
    PostgreSQLTransactionMode,
    PostgreSQLTransactionOwnership,
    PostgreSQLTransactionPolicyStatus,
    PostgreSQLTransactionRuntimeBoundary,
    build_default_postgresql_transaction_policy,
    build_postgresql_execution_plan,
    build_postgresql_transaction_plan,
    create_postgresql_transaction_runtime_boundary,
    describe_postgresql_transaction_policy_boundary,
    validate_postgresql_transaction_policy,
    validate_postgresql_transaction_runtime_boundary,
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


def _execution_plan():
    result = build_postgresql_execution_plan(_statement())
    assert result.plan is not None
    return result.plan


def test_default_transaction_policy_imports_from_public_api() -> None:
    policy = build_default_postgresql_transaction_policy()

    assert policy.batch_mode == (
        PostgreSQLBatchTransactionMode.SINGLE_BATCH_TRANSACTION
    )
    assert policy.partial_success_policy == (
        PostgreSQLPartialSuccessPolicy.NO_PARTIAL_SUCCESS_FOR_PHASE_1
    )
    assert policy.failure_policy == (
        PostgreSQLTransactionFailurePolicy.ROLLBACK_FULL_BATCH_ON_FUTURE_FAILURE
    )
    assert policy.caller_provided_session_required is True
    assert policy.deterministic_failure_reporting is True
    assert policy.runtime_enabled is False
    assert validate_postgresql_transaction_policy(policy).is_valid is True


def test_default_policy_uses_phase_1_transaction_boundary_metadata() -> None:
    policy = build_default_postgresql_transaction_policy()

    assert policy.transaction_boundary.ownership == (
        PostgreSQLTransactionOwnership.CALLER_OWNED
    )
    assert policy.transaction_boundary.mode == (
        PostgreSQLTransactionMode.SINGLE_BATCH_FUTURE
    )
    assert policy.transaction_boundary.rollback_on_failure is True


def test_transaction_plan_preserves_execution_plan_counts_as_metadata() -> None:
    execution_plan = _execution_plan()

    result = build_postgresql_transaction_plan(execution_plan)

    assert result.status == PostgreSQLTransactionPolicyStatus.READY
    assert result.issues == ()
    assert result.plan is not None
    assert result.plan.record_count == execution_plan.record_count
    assert result.plan.statement_count == execution_plan.statement_count
    assert result.plan.runtime_enabled is False


def test_transaction_plan_preserves_default_policy_metadata() -> None:
    result = build_postgresql_transaction_plan(_execution_plan())

    assert result.plan is not None
    assert result.plan.policy == build_default_postgresql_transaction_policy()
    assert result.plan.transaction_boundary == (
        build_default_postgresql_transaction_policy().transaction_boundary
    )


def test_transaction_runtime_boundary_is_no_execution_metadata() -> None:
    policy = build_default_postgresql_transaction_policy()

    boundary = create_postgresql_transaction_runtime_boundary(policy)

    assert boundary == PostgreSQLTransactionRuntimeBoundary(
        policy=policy,
        caller_provided_session_required=True,
        runtime_enabled=False,
        opens_connection=False,
        runs_sql=False,
        writes_records=False,
        starts_real_transaction=False,
        commits_real_transaction=False,
        rolls_back_real_transaction=False,
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
        safe_to_execute_now=False,
        required_future_components=(
            "caller_provided_postgresql_session",
            "postgresql_runtime_execution_gate",
            "postgresql_runtime_adapter",
        ),
        notes=(
            "Runtime transaction boundary metadata only.",
            "No PostgreSQL transaction is started, committed, or rolled back.",
            "Future runtime work must use caller-provided sessions.",
        ),
    )
    assert validate_postgresql_transaction_runtime_boundary(boundary).is_valid


def test_transaction_policy_validation_fails_closed_for_unsafe_policy() -> None:
    policy = replace(
        build_default_postgresql_transaction_policy(),
        transaction_boundary=replace(
            build_default_postgresql_transaction_policy().transaction_boundary,
            ownership=PostgreSQLTransactionOwnership.REPOSITORY_OWNED_FUTURE,
            mode=PostgreSQLTransactionMode.CALLER_MANAGED,
            rollback_on_failure=False,
        ),
        caller_provided_session_required=False,
        deterministic_failure_reporting=False,
        runtime_enabled=True,
        notes=(),
    )

    validation = validate_postgresql_transaction_policy(policy)

    assert validation.status is PostgreSQLTransactionPolicyStatus.BLOCKED
    assert validation.is_valid is False
    assert _issue_codes(validation.issues) == (
        "POSTGRESQL_TRANSACTION_POLICY_OWNERSHIP_UNSAFE",
        "POSTGRESQL_TRANSACTION_POLICY_MODE_UNSAFE",
        "POSTGRESQL_TRANSACTION_POLICY_ROLLBACK_MARKER_REQUIRED",
        "POSTGRESQL_TRANSACTION_POLICY_CALLER_SESSION_REQUIRED",
        "POSTGRESQL_TRANSACTION_POLICY_DETERMINISTIC_REPORTING_REQUIRED",
        "POSTGRESQL_TRANSACTION_POLICY_RUNTIME_NOT_ALLOWED",
        "POSTGRESQL_TRANSACTION_POLICY_MISSING_NOTES",
    )


def test_transaction_runtime_boundary_fails_closed_for_runtime_flags() -> None:
    boundary = replace(
        create_postgresql_transaction_runtime_boundary(),
        caller_provided_session_required=False,
        runtime_enabled=True,
        opens_connection=True,
        runs_sql=True,
        writes_records=True,
        starts_real_transaction=True,
        commits_real_transaction=True,
        rolls_back_real_transaction=True,
        loads_environment=True,
        loads_config_files=True,
        loads_credentials=True,
        safe_to_execute_now=True,
        required_future_components=(),
        notes=(),
    )

    validation = validate_postgresql_transaction_runtime_boundary(boundary)

    assert validation.status is PostgreSQLTransactionPolicyStatus.BLOCKED
    assert _issue_codes(validation.issues) == (
        "POSTGRESQL_TRANSACTION_RUNTIME_CALLER_SESSION_REQUIRED",
        "POSTGRESQL_TRANSACTION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_TRANSACTION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_TRANSACTION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_TRANSACTION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_TRANSACTION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_TRANSACTION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_TRANSACTION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_TRANSACTION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_TRANSACTION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_TRANSACTION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_TRANSACTION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_TRANSACTION_RUNTIME_MISSING_FUTURE_COMPONENTS",
        "POSTGRESQL_TRANSACTION_RUNTIME_MISSING_NOTES",
    )


def test_missing_execution_plan_returns_no_statement_status() -> None:
    result = build_postgresql_transaction_plan(None)

    assert result.status == PostgreSQLTransactionPolicyStatus.NO_STATEMENT
    assert result.plan is None
    assert [issue.code for issue in result.issues] == [
        "POSTGRESQL_TRANSACTION_NO_EXECUTION_PLAN",
    ]


def test_transaction_plan_blocks_unsafe_policy() -> None:
    unsafe_policy = replace(
        build_default_postgresql_transaction_policy(),
        runtime_enabled=True,
    )

    result = build_postgresql_transaction_plan(
        _execution_plan(),
        policy=unsafe_policy,
    )

    assert result.status is PostgreSQLTransactionPolicyStatus.BLOCKED
    assert result.plan is None
    assert _issue_codes(result.issues) == (
        "POSTGRESQL_TRANSACTION_POLICY_RUNTIME_NOT_ALLOWED",
    )


def test_transaction_policy_description_has_no_runtime_behavior() -> None:
    description = describe_postgresql_transaction_policy_boundary()

    assert description.driver_neutral is True
    assert description.opens_connection is False
    assert description.runs_sql is False
    assert description.writes_records is False
    assert description.starts_real_transaction is False
    assert description.commits_real_transaction is False
    assert description.rolls_back_real_transaction is False
    assert description.loads_credentials is False
    assert description.runtime_boundary == (
        create_postgresql_transaction_runtime_boundary(description.policy)
    )
    assert validate_postgresql_transaction_runtime_boundary(
        description.runtime_boundary,
    ).is_valid


def test_transaction_policy_helpers_have_no_external_side_effects(monkeypatch) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("transaction policy must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    description = describe_postgresql_transaction_policy_boundary()
    boundary = create_postgresql_transaction_runtime_boundary()
    result = build_postgresql_transaction_plan(_execution_plan())

    assert description.opens_connection is False
    assert validate_postgresql_transaction_runtime_boundary(boundary).is_valid
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


def test_transaction_policy_module_has_no_driver_or_runtime_behavior() -> None:
    module_source = inspect.getsource(policy_module)
    lower_source = module_source.lower()

    assert "psycopg" not in lower_source
    assert "asyncpg" not in lower_source
    assert "sqlalchemy" not in lower_source
    assert "create_engine" not in module_source
    assert "connect(" not in module_source
    assert "cursor(" not in module_source
    assert "execute(" not in module_source
    assert "os.environ" not in module_source
    assert "getenv" not in module_source


def _issue_codes(
    issues: tuple[PostgreSQLTransactionPolicyIssue, ...],
) -> tuple[str, ...]:
    return tuple(issue.code for issue in issues)
