"""PostgreSQL transaction policy boundary without runtime transactions."""

from __future__ import annotations

from dataclasses import dataclass
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
