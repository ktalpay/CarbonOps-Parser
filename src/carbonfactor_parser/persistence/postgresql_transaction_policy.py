"""PostgreSQL transaction policy boundary without runtime transactions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from carbonfactor_parser.persistence.postgresql_connection_session_contract import (
    PostgreSQLTransactionBoundary,
    PostgreSQLTransactionMode,
    PostgreSQLTransactionOwnership,
)
from carbonfactor_parser.persistence.postgresql_execution_adapter_boundary import (
    PostgreSQLExecutionPlan,
    PostgreSQLExecutionStatus,
)


class PostgreSQLTransactionPolicyStatus(str, Enum):
    """Status values for transaction policy plan boundaries."""

    READY = "ready"
    BLOCKED = "blocked"
    DISABLED = "disabled"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"
    NO_STATEMENT = "no_statement"


class PostgreSQLBatchTransactionMode(str, Enum):
    """Future batch transaction mode policy values."""

    SINGLE_BATCH_TRANSACTION = "single_batch_transaction"


class PostgreSQLPartialSuccessPolicy(str, Enum):
    """Future partial success policy values."""

    NO_PARTIAL_SUCCESS_FOR_PHASE_1 = "no_partial_success_for_phase_1"


class PostgreSQLTransactionFailurePolicy(str, Enum):
    """Future transaction failure policy values."""

    FAIL_FAST = "fail_fast"
    ROLLBACK_FULL_BATCH_ON_FUTURE_FAILURE = (
        "rollback_full_batch_on_future_failure"
    )


@dataclass(frozen=True)
class PostgreSQLTransactionPolicy:
    """Descriptive future transaction policy without runtime behavior."""

    transaction_boundary: PostgreSQLTransactionBoundary
    batch_mode: PostgreSQLBatchTransactionMode
    partial_success_policy: PostgreSQLPartialSuccessPolicy
    failure_policy: PostgreSQLTransactionFailurePolicy
    caller_provided_session_required: bool
    deterministic_failure_reporting: bool
    runtime_enabled: bool
    notes: tuple[str, ...]


@dataclass(frozen=True)
class PostgreSQLTransactionPolicyIssue:
    """Issue reported by the transaction policy boundary."""

    code: str
    message: str
    field_name: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class PostgreSQLTransactionPolicyValidationResult:
    """Fail-closed validation result for transaction policy metadata."""

    status: PostgreSQLTransactionPolicyStatus
    issues: tuple[PostgreSQLTransactionPolicyIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return (
            self.status is PostgreSQLTransactionPolicyStatus.READY
            and not self.issues
        )


@dataclass(frozen=True)
class PostgreSQLTransactionRuntimeBoundary:
    """No-execution runtime boundary for future transaction handling."""

    policy: PostgreSQLTransactionPolicy
    caller_provided_session_required: bool
    runtime_enabled: bool
    opens_connection: bool
    runs_sql: bool
    writes_records: bool
    starts_real_transaction: bool
    commits_real_transaction: bool
    rolls_back_real_transaction: bool
    loads_environment: bool
    loads_config_files: bool
    loads_credentials: bool
    safe_to_execute_now: bool
    required_future_components: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class PostgreSQLTransactionPlan:
    """Transaction plan metadata for a future execution plan."""

    policy: PostgreSQLTransactionPolicy
    execution_status: PostgreSQLExecutionStatus
    record_count: int
    statement_count: int
    transaction_boundary: PostgreSQLTransactionBoundary
    runtime_enabled: bool = False


@dataclass(frozen=True)
class PostgreSQLTransactionPlanResult:
    """Structured result for building transaction plan metadata."""

    status: PostgreSQLTransactionPolicyStatus
    plan: PostgreSQLTransactionPlan | None = None
    issues: tuple[PostgreSQLTransactionPolicyIssue, ...] = ()


@dataclass(frozen=True)
class PostgreSQLTransactionPolicyDescription:
    """Side-effect-free description of the transaction policy boundary."""

    policy: PostgreSQLTransactionPolicy
    driver_neutral: bool
    opens_connection: bool
    runs_sql: bool
    writes_records: bool
    starts_real_transaction: bool
    commits_real_transaction: bool
    rolls_back_real_transaction: bool
    loads_environment: bool
    loads_config_files: bool
    loads_credentials: bool
    runtime_boundary: PostgreSQLTransactionRuntimeBoundary = field(
        default_factory=lambda: create_postgresql_transaction_runtime_boundary(),
    )


def build_default_postgresql_transaction_policy() -> PostgreSQLTransactionPolicy:
    """Return the deterministic Phase 1 transaction policy metadata."""

    return PostgreSQLTransactionPolicy(
        transaction_boundary=PostgreSQLTransactionBoundary(
            ownership=PostgreSQLTransactionOwnership.CALLER_OWNED,
            mode=PostgreSQLTransactionMode.SINGLE_BATCH_FUTURE,
            rollback_on_failure=True,
        ),
        batch_mode=PostgreSQLBatchTransactionMode.SINGLE_BATCH_TRANSACTION,
        partial_success_policy=(
            PostgreSQLPartialSuccessPolicy.NO_PARTIAL_SUCCESS_FOR_PHASE_1
        ),
        failure_policy=(
            PostgreSQLTransactionFailurePolicy
            .ROLLBACK_FULL_BATCH_ON_FUTURE_FAILURE
        ),
        caller_provided_session_required=True,
        deterministic_failure_reporting=True,
        runtime_enabled=False,
        notes=(
            "Single batch policy metadata only.",
            "Caller-provided session required for future runtime work.",
            "No partial success for Phase 1.",
            "Future failures should report deterministic counts and issues.",
        ),
    )


def create_postgresql_transaction_runtime_boundary(
    policy: PostgreSQLTransactionPolicy | None = None,
) -> PostgreSQLTransactionRuntimeBoundary:
    """Create deterministic no-execution transaction runtime metadata."""

    active_policy = policy or build_default_postgresql_transaction_policy()
    return PostgreSQLTransactionRuntimeBoundary(
        policy=active_policy,
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


def validate_postgresql_transaction_policy(
    policy: PostgreSQLTransactionPolicy,
) -> PostgreSQLTransactionPolicyValidationResult:
    """Validate transaction policy metadata without transaction behavior."""

    issues: list[PostgreSQLTransactionPolicyIssue] = []
    if policy.transaction_boundary.ownership is not (
        PostgreSQLTransactionOwnership.CALLER_OWNED
    ):
        issues.append(
            PostgreSQLTransactionPolicyIssue(
                code="POSTGRESQL_TRANSACTION_POLICY_OWNERSHIP_UNSAFE",
                message="transaction ownership must remain caller_owned.",
                field_name="transaction_boundary.ownership",
            )
        )
    if policy.transaction_boundary.mode is not (
        PostgreSQLTransactionMode.SINGLE_BATCH_FUTURE
    ):
        issues.append(
            PostgreSQLTransactionPolicyIssue(
                code="POSTGRESQL_TRANSACTION_POLICY_MODE_UNSAFE",
                message="transaction mode must remain single_batch_future.",
                field_name="transaction_boundary.mode",
            )
        )
    _validate_true(
        policy.transaction_boundary.rollback_on_failure,
        "transaction_boundary.rollback_on_failure",
        "POSTGRESQL_TRANSACTION_POLICY_ROLLBACK_MARKER_REQUIRED",
        "rollback_on_failure must remain True.",
        issues,
    )
    if policy.batch_mode is not PostgreSQLBatchTransactionMode.SINGLE_BATCH_TRANSACTION:
        issues.append(
            PostgreSQLTransactionPolicyIssue(
                code="POSTGRESQL_TRANSACTION_POLICY_BATCH_MODE_UNSAFE",
                message="batch_mode must remain single_batch_transaction.",
                field_name="batch_mode",
            )
        )
    if policy.partial_success_policy is not (
        PostgreSQLPartialSuccessPolicy.NO_PARTIAL_SUCCESS_FOR_PHASE_1
    ):
        issues.append(
            PostgreSQLTransactionPolicyIssue(
                code="POSTGRESQL_TRANSACTION_POLICY_PARTIAL_SUCCESS_UNSAFE",
                message=(
                    "partial_success_policy must remain "
                    "no_partial_success_for_phase_1."
                ),
                field_name="partial_success_policy",
            )
        )
    if policy.failure_policy is not (
        PostgreSQLTransactionFailurePolicy.ROLLBACK_FULL_BATCH_ON_FUTURE_FAILURE
    ):
        issues.append(
            PostgreSQLTransactionPolicyIssue(
                code="POSTGRESQL_TRANSACTION_POLICY_FAILURE_POLICY_UNSAFE",
                message=(
                    "failure_policy must remain "
                    "rollback_full_batch_on_future_failure."
                ),
                field_name="failure_policy",
            )
        )
    _validate_true(
        policy.caller_provided_session_required,
        "caller_provided_session_required",
        "POSTGRESQL_TRANSACTION_POLICY_CALLER_SESSION_REQUIRED",
        "caller_provided_session_required must remain True.",
        issues,
    )
    _validate_true(
        policy.deterministic_failure_reporting,
        "deterministic_failure_reporting",
        "POSTGRESQL_TRANSACTION_POLICY_DETERMINISTIC_REPORTING_REQUIRED",
        "deterministic_failure_reporting must remain True.",
        issues,
    )
    _validate_false(
        policy.runtime_enabled,
        "runtime_enabled",
        "POSTGRESQL_TRANSACTION_POLICY_RUNTIME_NOT_ALLOWED",
        "runtime_enabled must remain False.",
        issues,
    )
    if not policy.notes:
        issues.append(
            PostgreSQLTransactionPolicyIssue(
                code="POSTGRESQL_TRANSACTION_POLICY_MISSING_NOTES",
                message="transaction policy must include boundary notes.",
                field_name="notes",
            )
        )

    return PostgreSQLTransactionPolicyValidationResult(
        status=(
            PostgreSQLTransactionPolicyStatus.BLOCKED
            if issues
            else PostgreSQLTransactionPolicyStatus.READY
        ),
        issues=tuple(issues),
    )


def validate_postgresql_transaction_runtime_boundary(
    boundary: PostgreSQLTransactionRuntimeBoundary,
) -> PostgreSQLTransactionPolicyValidationResult:
    """Validate transaction runtime boundary metadata without execution."""

    issues = list(validate_postgresql_transaction_policy(boundary.policy).issues)
    _validate_true(
        boundary.caller_provided_session_required,
        "caller_provided_session_required",
        "POSTGRESQL_TRANSACTION_RUNTIME_CALLER_SESSION_REQUIRED",
        "caller_provided_session_required must remain True.",
        issues,
    )
    for field_name, value in (
        ("runtime_enabled", boundary.runtime_enabled),
        ("opens_connection", boundary.opens_connection),
        ("runs_sql", boundary.runs_sql),
        ("writes_records", boundary.writes_records),
        ("starts_real_transaction", boundary.starts_real_transaction),
        ("commits_real_transaction", boundary.commits_real_transaction),
        ("rolls_back_real_transaction", boundary.rolls_back_real_transaction),
        ("loads_environment", boundary.loads_environment),
        ("loads_config_files", boundary.loads_config_files),
        ("loads_credentials", boundary.loads_credentials),
        ("safe_to_execute_now", boundary.safe_to_execute_now),
    ):
        _validate_false(
            value,
            field_name,
            "POSTGRESQL_TRANSACTION_RUNTIME_FLAG_NOT_ALLOWED",
            f"{field_name} must remain False for this boundary.",
            issues,
        )
    if not boundary.required_future_components:
        issues.append(
            PostgreSQLTransactionPolicyIssue(
                code="POSTGRESQL_TRANSACTION_RUNTIME_MISSING_FUTURE_COMPONENTS",
                message="runtime boundary must list future required components.",
                field_name="required_future_components",
            )
        )
    if not boundary.notes:
        issues.append(
            PostgreSQLTransactionPolicyIssue(
                code="POSTGRESQL_TRANSACTION_RUNTIME_MISSING_NOTES",
                message="runtime boundary must include notes.",
                field_name="notes",
            )
        )

    return PostgreSQLTransactionPolicyValidationResult(
        status=(
            PostgreSQLTransactionPolicyStatus.BLOCKED
            if issues
            else PostgreSQLTransactionPolicyStatus.READY
        ),
        issues=tuple(issues),
    )


def build_postgresql_transaction_plan(
    execution_plan: PostgreSQLExecutionPlan | None,
    *,
    policy: PostgreSQLTransactionPolicy | None = None,
) -> PostgreSQLTransactionPlanResult:
    """Build transaction policy metadata without transaction behavior."""

    if execution_plan is None:
        return PostgreSQLTransactionPlanResult(
            status=PostgreSQLTransactionPolicyStatus.NO_STATEMENT,
            issues=(
                PostgreSQLTransactionPolicyIssue(
                    code="POSTGRESQL_TRANSACTION_NO_EXECUTION_PLAN",
                    message=(
                        "A PostgreSQL execution plan is required before a "
                        "transaction policy plan can be built."
                    ),
                    field_name="execution_plan",
                    severity="warning",
                ),
            ),
        )

    active_policy = policy or build_default_postgresql_transaction_policy()
    policy_validation = validate_postgresql_transaction_policy(active_policy)
    if not policy_validation.is_valid:
        return PostgreSQLTransactionPlanResult(
            status=PostgreSQLTransactionPolicyStatus.BLOCKED,
            issues=policy_validation.issues,
        )

    return PostgreSQLTransactionPlanResult(
        status=PostgreSQLTransactionPolicyStatus.READY,
        plan=PostgreSQLTransactionPlan(
            policy=active_policy,
            execution_status=PostgreSQLExecutionStatus.READY,
            record_count=execution_plan.record_count,
            statement_count=execution_plan.statement_count,
            transaction_boundary=active_policy.transaction_boundary,
            runtime_enabled=False,
        ),
    )


def describe_postgresql_transaction_policy_boundary() -> (
    PostgreSQLTransactionPolicyDescription
):
    """Describe the transaction policy boundary without side effects."""

    return PostgreSQLTransactionPolicyDescription(
        policy=build_default_postgresql_transaction_policy(),
        runtime_boundary=create_postgresql_transaction_runtime_boundary(),
        driver_neutral=True,
        opens_connection=False,
        runs_sql=False,
        writes_records=False,
        starts_real_transaction=False,
        commits_real_transaction=False,
        rolls_back_real_transaction=False,
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
    )


def _validate_true(
    value: bool,
    field_name: str,
    code: str,
    message: str,
    issues: list[PostgreSQLTransactionPolicyIssue],
) -> None:
    if value is not True:
        issues.append(
            PostgreSQLTransactionPolicyIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )


def _validate_false(
    value: bool,
    field_name: str,
    code: str,
    message: str,
    issues: list[PostgreSQLTransactionPolicyIssue],
) -> None:
    if value is not False:
        issues.append(
            PostgreSQLTransactionPolicyIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )
