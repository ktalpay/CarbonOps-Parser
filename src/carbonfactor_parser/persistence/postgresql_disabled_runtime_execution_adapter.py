"""Disabled PostgreSQL runtime execution adapter boundary without SQL."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.persistence.postgresql_execution_adapter_boundary import (
    PostgreSQLExecutionIssue,
    PostgreSQLExecutionPlan,
    build_postgresql_execution_plan,
)
from carbonfactor_parser.persistence.postgresql_idempotency_conflict_strategy import (
    PostgreSQLConflictStrategyPlan,
    PostgreSQLIdempotencyConflictStrategy,
    build_postgresql_conflict_strategy_plan,
)
from carbonfactor_parser.persistence.postgresql_insert_builder import (
    PostgreSQLInsertStatement,
)
from carbonfactor_parser.persistence.postgresql_transaction_policy import (
    PostgreSQLTransactionPlan,
    PostgreSQLTransactionPolicy,
    build_postgresql_transaction_plan,
)


class PostgreSQLDisabledRuntimeExecutionStatus(str, Enum):
    """Status values for the disabled runtime adapter boundary."""

    DISABLED = "disabled"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"
    NO_STATEMENT = "no_statement"


@dataclass(frozen=True)
class PostgreSQLDisabledRuntimeExecutionMetadata:
    """Explicit disabled runtime behavior markers."""

    no_execution: bool
    opens_connection: bool
    creates_cursor: bool
    runs_sql: bool
    writes_records: bool
    starts_transaction: bool
    commits_transaction: bool
    rolls_back_transaction: bool
    creates_tables: bool
    runs_migrations: bool
    loads_environment: bool
    loads_config_files: bool
    loads_credentials: bool
    runtime_enabled: bool


@dataclass(frozen=True)
class PostgreSQLDisabledRuntimeExecutionResult:
    """Structured disabled runtime adapter result without DB behavior."""

    status: PostgreSQLDisabledRuntimeExecutionStatus
    reason: str
    no_execution: bool
    target_table_name: str | None = None
    record_count: int = 0
    statement_count: int = 0
    sql_preview: str | None = None
    execution_plan: PostgreSQLExecutionPlan | None = None
    transaction_plan: PostgreSQLTransactionPlan | None = None
    conflict_strategy_plan: PostgreSQLConflictStrategyPlan | None = None
    session_adapter_metadata: object | None = None
    runtime_metadata: PostgreSQLDisabledRuntimeExecutionMetadata | None = None
    issues: tuple[PostgreSQLExecutionIssue, ...] = ()


@dataclass(frozen=True)
class PostgreSQLDisabledRuntimeExecutionDescription:
    """Side-effect-free description of the disabled runtime adapter."""

    status: PostgreSQLDisabledRuntimeExecutionStatus
    consumes_insert_statement: bool
    consumes_execution_plan: bool
    consumes_transaction_policy: bool
    consumes_conflict_strategy: bool
    consumes_session_adapter_metadata: bool
    opens_connection: bool
    creates_cursor: bool
    runs_sql: bool
    writes_records: bool
    starts_transaction: bool
    commits_transaction: bool
    rolls_back_transaction: bool
    loads_environment: bool
    loads_config_files: bool
    loads_credentials: bool
    notes: tuple[str, ...]


@dataclass(frozen=True)
class PostgreSQLDisabledRuntimeExecutionAdapter:
    """Adapter that reports disabled runtime metadata only."""

    adapter_name: str = "postgresql_disabled_runtime_execution_adapter"
    runtime_enabled: bool = False

    def build_result(
        self,
        *,
        statement: PostgreSQLInsertStatement | None = None,
        execution_plan: PostgreSQLExecutionPlan | None = None,
        transaction_policy: PostgreSQLTransactionPolicy | None = None,
        conflict_strategy: PostgreSQLIdempotencyConflictStrategy | None = None,
        session_adapter_metadata: object | None = None,
    ) -> PostgreSQLDisabledRuntimeExecutionResult:
        """Build disabled runtime metadata without touching PostgreSQL."""

        return build_postgresql_disabled_runtime_execution_result(
            statement=statement,
            execution_plan=execution_plan,
            transaction_policy=transaction_policy,
            conflict_strategy=conflict_strategy,
            session_adapter_metadata=session_adapter_metadata,
        )


def build_postgresql_disabled_runtime_execution_result(
    *,
    statement: PostgreSQLInsertStatement | None = None,
    execution_plan: PostgreSQLExecutionPlan | None = None,
    transaction_policy: PostgreSQLTransactionPolicy | None = None,
    conflict_strategy: PostgreSQLIdempotencyConflictStrategy | None = None,
    session_adapter_metadata: object | None = None,
) -> PostgreSQLDisabledRuntimeExecutionResult:
    """Compose disabled runtime metadata without SQL execution."""

    plan = execution_plan
    issues: list[PostgreSQLExecutionIssue] = []

    if plan is None:
        plan_result = build_postgresql_execution_plan(statement)
        if plan_result.plan is None:
            return PostgreSQLDisabledRuntimeExecutionResult(
                status=PostgreSQLDisabledRuntimeExecutionStatus.NO_STATEMENT,
                reason=(
                    "A PostgreSQL insert statement or execution plan is "
                    "required before disabled runtime metadata can be built."
                ),
                no_execution=True,
                session_adapter_metadata=session_adapter_metadata,
                runtime_metadata=_disabled_runtime_metadata(),
                issues=tuple(plan_result.issues),
            )
        plan = plan_result.plan
        issues.extend(plan_result.issues)

    active_statement = statement or _statement_from_plan(plan)
    transaction_plan = _transaction_plan(plan, transaction_policy, issues)
    conflict_plan = _conflict_strategy_plan(
        active_statement,
        conflict_strategy,
        issues,
    )

    issues.append(
        PostgreSQLExecutionIssue(
            code="POSTGRESQL_RUNTIME_EXECUTION_DISABLED",
            message=(
                "PostgreSQL runtime execution is disabled; SQL text is "
                "preview metadata only and is not run."
            ),
            severity="warning",
        ),
    )

    return PostgreSQLDisabledRuntimeExecutionResult(
        status=PostgreSQLDisabledRuntimeExecutionStatus.DISABLED,
        reason=(
            "PostgreSQL runtime execution adapter is disabled and returns "
            "metadata only."
        ),
        no_execution=True,
        target_table_name=plan.target_table_name,
        record_count=plan.record_count,
        statement_count=plan.statement_count,
        sql_preview=plan.statement_contract.sql,
        execution_plan=plan,
        transaction_plan=transaction_plan,
        conflict_strategy_plan=conflict_plan,
        session_adapter_metadata=session_adapter_metadata,
        runtime_metadata=_disabled_runtime_metadata(),
        issues=tuple(issues),
    )


def describe_postgresql_disabled_runtime_execution() -> (
    PostgreSQLDisabledRuntimeExecutionDescription
):
    """Describe the disabled runtime adapter boundary without side effects."""

    return PostgreSQLDisabledRuntimeExecutionDescription(
        status=PostgreSQLDisabledRuntimeExecutionStatus.DISABLED,
        consumes_insert_statement=True,
        consumes_execution_plan=True,
        consumes_transaction_policy=True,
        consumes_conflict_strategy=True,
        consumes_session_adapter_metadata=True,
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
        notes=(
            "Disabled runtime adapter boundary only.",
            "SQL text is preserved as preview metadata.",
            "No PostgreSQL connection, cursor, transaction, or write occurs.",
            "PostgreSQLPersistenceRepository remains unsupported.",
        ),
    )


def _statement_from_plan(
    plan: PostgreSQLExecutionPlan,
) -> PostgreSQLInsertStatement:
    return PostgreSQLInsertStatement(
        sql=plan.statement_contract.sql,
        parameters=plan.parameter_rows,
        target_table_name=plan.target_table_name,
        column_names=plan.column_names,
        record_count=plan.record_count,
        idempotency_key_fields=plan.idempotency_key_fields,
        conflict_target_fields=plan.conflict_target_fields,
    )


def _transaction_plan(
    plan: PostgreSQLExecutionPlan,
    policy: PostgreSQLTransactionPolicy | None,
    issues: list[PostgreSQLExecutionIssue],
) -> PostgreSQLTransactionPlan | None:
    result = build_postgresql_transaction_plan(plan, policy=policy)
    if result.plan is None:
        issues.extend(
            PostgreSQLExecutionIssue(
                code=issue.code,
                message=issue.message,
                field_name=issue.field_name,
                severity=issue.severity,
            )
            for issue in result.issues
        )
        return None
    return result.plan


def _conflict_strategy_plan(
    statement: PostgreSQLInsertStatement,
    strategy: PostgreSQLIdempotencyConflictStrategy | None,
    issues: list[PostgreSQLExecutionIssue],
) -> PostgreSQLConflictStrategyPlan | None:
    result = build_postgresql_conflict_strategy_plan(
        statement,
        strategy=strategy,
    )
    if result.plan is None:
        issues.extend(
            PostgreSQLExecutionIssue(
                code=issue.code,
                message=issue.message,
                field_name=issue.field_name,
                severity=issue.severity,
            )
            for issue in result.issues
        )
        return None
    return result.plan


def _disabled_runtime_metadata() -> PostgreSQLDisabledRuntimeExecutionMetadata:
    return PostgreSQLDisabledRuntimeExecutionMetadata(
        no_execution=True,
        opens_connection=False,
        creates_cursor=False,
        runs_sql=False,
        writes_records=False,
        starts_transaction=False,
        commits_transaction=False,
        rolls_back_transaction=False,
        creates_tables=False,
        runs_migrations=False,
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
        runtime_enabled=False,
    )
