"""Driver-neutral PostgreSQL execution adapter boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from carbonfactor_parser.persistence.postgresql_connection_session_contract import (
    PostgreSQLConnectionSessionContractDescription,
    PostgreSQLStatementExecutionContract,
    PostgreSQLTransactionBoundary,
    describe_postgresql_connection_session_contract,
)
from carbonfactor_parser.persistence.postgresql_insert_builder import (
    PostgreSQLInsertStatement,
)


class PostgreSQLExecutionStatus(str, Enum):
    """Status values for future PostgreSQL execution adapter boundaries."""

    READY = "ready"
    DISABLED = "disabled"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"
    NO_STATEMENT = "no_statement"


@dataclass(frozen=True)
class PostgreSQLExecutionIssue:
    """Issue reported by the execution adapter boundary."""

    code: str
    message: str
    field_name: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class PostgreSQLExecutionPlan:
    """Future PostgreSQL execution plan metadata without execution."""

    statement_contract: PostgreSQLStatementExecutionContract
    target_table_name: str
    column_names: tuple[str, ...]
    parameter_rows: tuple[tuple[object, ...], ...]
    record_count: int
    statement_count: int
    idempotency_key_fields: tuple[str, ...]
    conflict_target_fields: tuple[str, ...]
    transaction_boundary: PostgreSQLTransactionBoundary
    session_provider_name: str | None = None
    runtime_enabled: bool = False


@dataclass(frozen=True)
class PostgreSQLExecutionPlanResult:
    """Structured result for building a future execution plan."""

    status: PostgreSQLExecutionStatus
    plan: PostgreSQLExecutionPlan | None = None
    issues: tuple[PostgreSQLExecutionIssue, ...] = ()


@dataclass(frozen=True)
class PostgreSQLExecutionResult:
    """No-execution result shape for future adapter reporting."""

    status: PostgreSQLExecutionStatus
    affected_record_count: int = 0
    statement_count: int = 0
    issues: tuple[PostgreSQLExecutionIssue, ...] = ()
    plan: PostgreSQLExecutionPlan | None = None


@dataclass(frozen=True)
class PostgreSQLExecutionBoundaryDescription:
    """Side-effect-free description of the execution adapter boundary."""

    driver_neutral: bool
    opens_connection: bool
    runs_sql: bool
    writes_records: bool
    creates_tables: bool
    runs_migrations: bool
    loads_environment: bool
    loads_config_files: bool
    loads_credentials: bool
    consumes_insert_statement: bool
    consumes_session_contract: bool
    default_status: PostgreSQLExecutionStatus
    notes: tuple[str, ...]


@runtime_checkable
class PostgreSQLExecutionAdapterProtocol(Protocol):
    """Protocol shape for future execution adapters without implementation."""

    adapter_name: str
    runtime_enabled: bool

    def build_plan(
        self,
        statement: PostgreSQLInsertStatement,
    ) -> PostgreSQLExecutionPlan:
        """Return future plan metadata without running the statement."""
        ...


def build_postgresql_execution_plan(
    statement: PostgreSQLInsertStatement | None,
    *,
    session_contract_description: (
        PostgreSQLConnectionSessionContractDescription | None
    ) = None,
    session_provider_name: str | None = None,
) -> PostgreSQLExecutionPlanResult:
    """Build future execution plan metadata without running SQL."""

    if statement is None:
        return PostgreSQLExecutionPlanResult(
            status=PostgreSQLExecutionStatus.NO_STATEMENT,
            issues=(
                PostgreSQLExecutionIssue(
                    code="POSTGRESQL_EXECUTION_NO_STATEMENT",
                    message=(
                        "A PostgreSQL insert statement is required before an "
                        "execution plan boundary can be built."
                    ),
                    field_name="statement",
                    severity="warning",
                ),
            ),
        )

    active_session_description = (
        session_contract_description
        if session_contract_description is not None
        else describe_postgresql_connection_session_contract()
    )

    plan = PostgreSQLExecutionPlan(
        statement_contract=PostgreSQLStatementExecutionContract(
            sql=statement.sql,
            parameters=statement.parameters,
            statement_metadata={
                "target_table_name": statement.target_table_name,
                "column_names": statement.column_names,
                "record_count": statement.record_count,
                "idempotency_key_fields": statement.idempotency_key_fields,
                "conflict_target_fields": statement.conflict_target_fields,
                "boundary": "postgresql_execution_adapter_no_execution",
            },
        ),
        target_table_name=statement.target_table_name,
        column_names=statement.column_names,
        parameter_rows=statement.parameters,
        record_count=statement.record_count,
        statement_count=1,
        idempotency_key_fields=statement.idempotency_key_fields,
        conflict_target_fields=statement.conflict_target_fields,
        transaction_boundary=active_session_description.transaction_boundary,
        session_provider_name=session_provider_name,
        runtime_enabled=False,
    )

    return PostgreSQLExecutionPlanResult(
        status=PostgreSQLExecutionStatus.READY,
        plan=plan,
    )


def build_disabled_postgresql_execution_result(
    plan: PostgreSQLExecutionPlan | None,
) -> PostgreSQLExecutionResult:
    """Return a disabled no-execution result for a future plan."""

    return PostgreSQLExecutionResult(
        status=PostgreSQLExecutionStatus.DISABLED,
        affected_record_count=0,
        statement_count=plan.statement_count if plan is not None else 0,
        plan=plan,
        issues=(
            PostgreSQLExecutionIssue(
                code="POSTGRESQL_EXECUTION_DISABLED",
                message=(
                    "PostgreSQL runtime execution is disabled; this boundary "
                    "does not connect to PostgreSQL or run SQL."
                ),
                severity="warning",
            ),
        ),
    )


def describe_postgresql_execution_adapter_boundary() -> (
    PostgreSQLExecutionBoundaryDescription
):
    """Describe the PostgreSQL execution adapter boundary without side effects."""

    return PostgreSQLExecutionBoundaryDescription(
        driver_neutral=True,
        opens_connection=False,
        runs_sql=False,
        writes_records=False,
        creates_tables=False,
        runs_migrations=False,
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
        consumes_insert_statement=True,
        consumes_session_contract=True,
        default_status=PostgreSQLExecutionStatus.DISABLED,
        notes=(
            "Boundary metadata only.",
            "Future adapters must consume insert-builder output.",
            "Future adapters must use caller-provided session contracts.",
            "Runtime execution remains behind the safety gate.",
        ),
    )
