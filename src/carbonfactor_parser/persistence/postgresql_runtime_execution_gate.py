"""PostgreSQL runtime execution enablement gate without execution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PostgreSQLRuntimeExecutionGateStatus(str, Enum):
    """Status values for runtime execution enablement gate decisions."""

    DISABLED = "disabled"
    BLOCKED = "blocked"
    NOT_ENABLED = "not_enabled"


@dataclass(frozen=True)
class PostgreSQLRuntimeExecutionGateIssue:
    """Issue explaining a runtime execution gate decision."""

    code: str
    message: str
    field_name: str | None = None
    severity: str = "warning"


@dataclass(frozen=True)
class PostgreSQLRuntimeExecutionGate:
    """Caller-provided runtime execution intent metadata only."""

    requested: bool = False
    safety_gate_approved: bool = False
    runtime_adapter_available: bool = False
    caller_provided_session_available: bool = False
    integration_test_opt_in_complete: bool = False
    repository_runtime_enabled: bool = False


@dataclass(frozen=True)
class PostgreSQLRuntimeExecutionGateDecision:
    """Structured runtime execution gate decision without DB behavior."""

    status: PostgreSQLRuntimeExecutionGateStatus
    requested: bool
    reason: str
    no_execution: bool
    runtime_enabled: bool
    connection_required_now: bool
    session_required_now: bool
    required_future_components: tuple[str, ...]
    safe_operational_notes: tuple[str, ...]
    issues: tuple[PostgreSQLRuntimeExecutionGateIssue, ...] = ()


@dataclass(frozen=True)
class PostgreSQLRuntimeExecutionGateDescription:
    """Side-effect-free description of the runtime execution gate."""

    default_status: PostgreSQLRuntimeExecutionGateStatus
    disabled_by_default: bool
    accepts_caller_intent: bool
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
    changes_repository_persist_behavior: bool
    notes: tuple[str, ...]


def evaluate_postgresql_runtime_execution_gate(
    gate: PostgreSQLRuntimeExecutionGate | None = None,
) -> PostgreSQLRuntimeExecutionGateDecision:
    """Evaluate runtime execution intent without enabling execution."""

    active_gate = gate or PostgreSQLRuntimeExecutionGate()
    required_components = _required_future_components(active_gate)

    if not active_gate.requested:
        return PostgreSQLRuntimeExecutionGateDecision(
            status=PostgreSQLRuntimeExecutionGateStatus.DISABLED,
            requested=False,
            reason="PostgreSQL runtime execution is disabled by default.",
            no_execution=True,
            runtime_enabled=False,
            connection_required_now=False,
            session_required_now=False,
            required_future_components=required_components,
            safe_operational_notes=_safe_operational_notes(),
            issues=(
                PostgreSQLRuntimeExecutionGateIssue(
                    code="POSTGRESQL_RUNTIME_EXECUTION_DISABLED_BY_DEFAULT",
                    message=(
                        "Runtime PostgreSQL execution requires explicit "
                        "future enablement and remains disabled."
                    ),
                ),
            ),
        )

    ready_metadata_only = not required_components
    return PostgreSQLRuntimeExecutionGateDecision(
        status=(
            PostgreSQLRuntimeExecutionGateStatus.NOT_ENABLED
            if ready_metadata_only
            else PostgreSQLRuntimeExecutionGateStatus.BLOCKED
        ),
        requested=True,
        reason=_requested_reason(ready_metadata_only),
        no_execution=True,
        runtime_enabled=False,
        connection_required_now=False,
        session_required_now=False,
        required_future_components=required_components,
        safe_operational_notes=_safe_operational_notes(),
        issues=tuple(_requested_issues(required_components)),
    )


def describe_postgresql_runtime_execution_gate() -> (
    PostgreSQLRuntimeExecutionGateDescription
):
    """Describe the runtime execution gate without side effects."""

    return PostgreSQLRuntimeExecutionGateDescription(
        default_status=PostgreSQLRuntimeExecutionGateStatus.DISABLED,
        disabled_by_default=True,
        accepts_caller_intent=True,
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
        changes_repository_persist_behavior=False,
        notes=(
            "Runtime execution gate metadata only.",
            "Default decision is disabled/no-execution.",
            "Requested runtime execution remains blocked in this boundary.",
            "PostgreSQLPersistenceRepository.persist remains unsupported.",
        ),
    )


def _required_future_components(
    gate: PostgreSQLRuntimeExecutionGate,
) -> tuple[str, ...]:
    required_components: list[str] = []
    if not gate.safety_gate_approved:
        required_components.append("postgresql_implementation_safety_gate")
    if not gate.runtime_adapter_available:
        required_components.append("postgresql_runtime_execution_adapter")
    if not gate.caller_provided_session_available:
        required_components.append("caller_provided_postgresql_session")
    if not gate.integration_test_opt_in_complete:
        required_components.append("explicit_postgresql_integration_test_opt_in")
    if not gate.repository_runtime_enabled:
        required_components.append("repository_runtime_persistence_task")
    return tuple(required_components)


def _requested_issues(
    required_components: tuple[str, ...],
) -> list[PostgreSQLRuntimeExecutionGateIssue]:
    if required_components:
        return [
            PostgreSQLRuntimeExecutionGateIssue(
                code="POSTGRESQL_RUNTIME_EXECUTION_BLOCKED",
                message=(
                    "Runtime PostgreSQL execution remains blocked until "
                    "future safety-gated components are complete."
                ),
                field_name="requested",
            ),
        ]

    return [
        PostgreSQLRuntimeExecutionGateIssue(
            code="POSTGRESQL_RUNTIME_EXECUTION_NOT_ENABLED",
            message=(
                "All supplied gate metadata is marked complete, but this "
                "boundary still does not enable repository execution."
            ),
            field_name="requested",
        ),
    ]


def _requested_reason(ready_metadata_only: bool) -> str:
    if ready_metadata_only:
        return (
            "PostgreSQL runtime execution was requested, but this boundary "
            "does not enable repository execution."
        )
    return (
        "PostgreSQL runtime execution was requested, but this boundary "
        "does not enable execution and required future components are not "
        "complete."
    )


def _safe_operational_notes() -> tuple[str, ...]:
    return (
        "No PostgreSQL connection is opened.",
        "No cursor or SQL runtime is created.",
        "No records are written.",
        "No transaction is started, finished, or rolled back.",
        "No environment, config file, or credential loading occurs.",
    )
