"""PostgreSQL idempotency and conflict strategy boundary without SQL changes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.persistence.postgresql_insert_builder import (
    PostgreSQLInsertStatement,
)


class PostgreSQLConflictStrategyStatus(str, Enum):
    """Status values for idempotency and conflict strategy planning."""

    READY = "ready"
    DISABLED = "disabled"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"
    NO_STATEMENT = "no_statement"


class PostgreSQLConflictAction(str, Enum):
    """Future duplicate-handling action metadata."""

    FAIL_ON_CONFLICT = "fail_on_conflict"
    SKIP_EXISTING_FUTURE = "skip_existing_future"
    UPSERT_FUTURE = "upsert_future"
    CONFLICT_STRATEGY_NOT_CONFIGURED = "conflict_strategy_not_configured"


class PostgreSQLIdempotencyRequirement(str, Enum):
    """Idempotency field requirement metadata."""

    IDEMPOTENCY_FIELDS_REQUIRED = "idempotency_fields_required"
    IDEMPOTENCY_FIELDS_MISSING = "idempotency_fields_missing"


@dataclass(frozen=True)
class PostgreSQLIdempotencyConflictStrategy:
    """Descriptive idempotency/conflict strategy without SQL mutation."""

    conflict_action: PostgreSQLConflictAction
    idempotency_requirement: PostgreSQLIdempotencyRequirement
    silent_skip_enabled: bool
    upsert_enabled: bool
    sql_mutation_enabled: bool
    runtime_enabled: bool
    notes: tuple[str, ...]


@dataclass(frozen=True)
class PostgreSQLConflictStrategyIssue:
    """Issue reported by the idempotency/conflict strategy boundary."""

    code: str
    message: str
    field_name: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class PostgreSQLConflictStrategyPlan:
    """Conflict strategy metadata for a future insert execution path."""

    strategy: PostgreSQLIdempotencyConflictStrategy
    target_table_name: str
    record_count: int
    idempotency_key_fields: tuple[str, ...]
    conflict_target_fields: tuple[str, ...]
    insert_sql: str
    sql_mutation_enabled: bool = False
    runtime_enabled: bool = False


@dataclass(frozen=True)
class PostgreSQLConflictStrategyPlanResult:
    """Structured result for building conflict strategy plan metadata."""

    status: PostgreSQLConflictStrategyStatus
    plan: PostgreSQLConflictStrategyPlan | None = None
    issues: tuple[PostgreSQLConflictStrategyIssue, ...] = ()


@dataclass(frozen=True)
class PostgreSQLIdempotencyConflictStrategyDescription:
    """Side-effect-free description of the strategy boundary."""

    strategy: PostgreSQLIdempotencyConflictStrategy
    driver_neutral: bool
    opens_connection: bool
    runs_sql: bool
    writes_records: bool
    mutates_insert_sql: bool
    generates_conflict_sql: bool
    uses_existing_idempotency_metadata: bool
    loads_environment: bool
    loads_config_files: bool
    loads_credentials: bool


def build_default_postgresql_idempotency_conflict_strategy() -> (
    PostgreSQLIdempotencyConflictStrategy
):
    """Return deterministic Phase 1 conflict strategy metadata."""

    return PostgreSQLIdempotencyConflictStrategy(
        conflict_action=PostgreSQLConflictAction.FAIL_ON_CONFLICT,
        idempotency_requirement=(
            PostgreSQLIdempotencyRequirement.IDEMPOTENCY_FIELDS_REQUIRED
        ),
        silent_skip_enabled=False,
        upsert_enabled=False,
        sql_mutation_enabled=False,
        runtime_enabled=False,
        notes=(
            "Fail-on-conflict is the safest Phase 1 runtime strategy.",
            "Existing idempotency metadata is required before runtime work.",
            "Silent skip behavior remains deferred.",
            "Upsert behavior remains deferred.",
            "Insert SQL is not changed by this boundary.",
        ),
    )


def build_postgresql_conflict_strategy_plan(
    statement: PostgreSQLInsertStatement | None,
    *,
    strategy: PostgreSQLIdempotencyConflictStrategy | None = None,
) -> PostgreSQLConflictStrategyPlanResult:
    """Build idempotency/conflict metadata without changing SQL."""

    if statement is None:
        return PostgreSQLConflictStrategyPlanResult(
            status=PostgreSQLConflictStrategyStatus.NO_STATEMENT,
            issues=(
                PostgreSQLConflictStrategyIssue(
                    code="POSTGRESQL_CONFLICT_STRATEGY_NO_STATEMENT",
                    message=(
                        "A PostgreSQL insert statement is required before an "
                        "idempotency/conflict strategy plan can be built."
                    ),
                    field_name="statement",
                    severity="warning",
                ),
            ),
        )

    issues = _statement_metadata_issues(statement)
    if issues:
        return PostgreSQLConflictStrategyPlanResult(
            status=PostgreSQLConflictStrategyStatus.FAILED,
            issues=tuple(issues),
        )

    active_strategy = (
        strategy or build_default_postgresql_idempotency_conflict_strategy()
    )
    return PostgreSQLConflictStrategyPlanResult(
        status=PostgreSQLConflictStrategyStatus.READY,
        plan=PostgreSQLConflictStrategyPlan(
            strategy=active_strategy,
            target_table_name=statement.target_table_name,
            record_count=statement.record_count,
            idempotency_key_fields=statement.idempotency_key_fields,
            conflict_target_fields=statement.conflict_target_fields,
            insert_sql=statement.sql,
            sql_mutation_enabled=False,
            runtime_enabled=False,
        ),
    )


def describe_postgresql_idempotency_conflict_strategy_boundary() -> (
    PostgreSQLIdempotencyConflictStrategyDescription
):
    """Describe the idempotency/conflict boundary without side effects."""

    return PostgreSQLIdempotencyConflictStrategyDescription(
        strategy=build_default_postgresql_idempotency_conflict_strategy(),
        driver_neutral=True,
        opens_connection=False,
        runs_sql=False,
        writes_records=False,
        mutates_insert_sql=False,
        generates_conflict_sql=False,
        uses_existing_idempotency_metadata=True,
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
    )


def _statement_metadata_issues(
    statement: PostgreSQLInsertStatement,
) -> list[PostgreSQLConflictStrategyIssue]:
    issues: list[PostgreSQLConflictStrategyIssue] = []
    if not statement.idempotency_key_fields:
        issues.append(
            PostgreSQLConflictStrategyIssue(
                code="POSTGRESQL_IDEMPOTENCY_FIELDS_MISSING",
                message=(
                    "PostgreSQL insert statement idempotency metadata is "
                    "required before conflict strategy planning."
                ),
                field_name="idempotency_key_fields",
            ),
        )
    if not statement.conflict_target_fields:
        issues.append(
            PostgreSQLConflictStrategyIssue(
                code="POSTGRESQL_CONFLICT_TARGET_FIELDS_MISSING",
                message=(
                    "PostgreSQL insert statement conflict target metadata is "
                    "required before conflict strategy planning."
                ),
                field_name="conflict_target_fields",
            ),
        )
    return issues
