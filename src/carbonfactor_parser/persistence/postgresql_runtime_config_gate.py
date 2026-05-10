"""PostgreSQL runtime configuration gate metadata without configuration loading."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PostgreSQLRuntimeConfigGateStatus(str, Enum):
    """Status values for runtime configuration gate decisions."""

    DISABLED = "disabled"
    BLOCKED = "blocked"
    NOT_ENABLED = "not_enabled"


@dataclass(frozen=True)
class PostgreSQLRuntimeConfigGateIssue:
    """Issue describing a runtime configuration gate decision."""

    code: str
    message: str
    field_name: str | None = None
    severity: str = "warning"


@dataclass(frozen=True)
class PostgreSQLRuntimeConfigGate:
    """Caller-provided runtime configuration intent metadata only."""

    requested: bool = False
    safety_gate_approved: bool = False
    options_contract_available: bool = False
    explicit_runtime_opt_in: bool = False
    secret_source_approved: bool = False


@dataclass(frozen=True)
class PostgreSQLRuntimeConfigGateDecision:
    """Structured runtime configuration gate decision without runtime effects."""

    status: PostgreSQLRuntimeConfigGateStatus
    requested: bool
    reason: str
    config_loading_enabled: bool
    runtime_enabled: bool
    loads_environment: bool
    loads_config_files: bool
    loads_credentials: bool
    required_future_components: tuple[str, ...]
    safe_operational_notes: tuple[str, ...]
    issues: tuple[PostgreSQLRuntimeConfigGateIssue, ...] = ()


@dataclass(frozen=True)
class PostgreSQLRuntimeConfigGateDescription:
    """Side-effect-free description of the runtime configuration gate."""

    default_status: PostgreSQLRuntimeConfigGateStatus
    disabled_by_default: bool
    accepts_caller_intent: bool
    loads_environment: bool
    loads_config_files: bool
    loads_credentials: bool
    opens_connection: bool
    runs_sql: bool
    notes: tuple[str, ...]


def evaluate_postgresql_runtime_config_gate(
    gate: PostgreSQLRuntimeConfigGate | None = None,
) -> PostgreSQLRuntimeConfigGateDecision:
    """Evaluate runtime configuration intent without configuration loading."""

    active_gate = gate or PostgreSQLRuntimeConfigGate()
    required_components = _required_future_components(active_gate)

    if not active_gate.requested:
        return PostgreSQLRuntimeConfigGateDecision(
            status=PostgreSQLRuntimeConfigGateStatus.DISABLED,
            requested=False,
            reason="PostgreSQL runtime configuration loading is disabled by default.",
            config_loading_enabled=False,
            runtime_enabled=False,
            loads_environment=False,
            loads_config_files=False,
            loads_credentials=False,
            required_future_components=required_components,
            safe_operational_notes=_safe_operational_notes(),
            issues=(
                PostgreSQLRuntimeConfigGateIssue(
                    code="POSTGRESQL_RUNTIME_CONFIG_DISABLED_BY_DEFAULT",
                    message=(
                        "Runtime PostgreSQL configuration loading requires explicit "
                        "future enablement and remains disabled."
                    ),
                ),
            ),
        )

    ready_metadata_only = not required_components
    return PostgreSQLRuntimeConfigGateDecision(
        status=(
            PostgreSQLRuntimeConfigGateStatus.NOT_ENABLED
            if ready_metadata_only
            else PostgreSQLRuntimeConfigGateStatus.BLOCKED
        ),
        requested=True,
        reason=_requested_reason(ready_metadata_only),
        config_loading_enabled=False,
        runtime_enabled=False,
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
        required_future_components=required_components,
        safe_operational_notes=_safe_operational_notes(),
        issues=tuple(_requested_issues(required_components)),
    )


def describe_postgresql_runtime_config_gate() -> PostgreSQLRuntimeConfigGateDescription:
    """Describe runtime configuration gate behavior without side effects."""

    return PostgreSQLRuntimeConfigGateDescription(
        default_status=PostgreSQLRuntimeConfigGateStatus.DISABLED,
        disabled_by_default=True,
        accepts_caller_intent=True,
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
        opens_connection=False,
        runs_sql=False,
        notes=(
            "Runtime configuration gate metadata only.",
            "Default decision is disabled/no-loading.",
            "Requested runtime configuration remains blocked in this boundary.",
            "No environment/config file/credential loading occurs.",
        ),
    )


def _required_future_components(gate: PostgreSQLRuntimeConfigGate) -> tuple[str, ...]:
    required_components: list[str] = []
    if not gate.safety_gate_approved:
        required_components.append("postgresql_implementation_safety_gate")
    if not gate.options_contract_available:
        required_components.append("postgresql_persistence_options_contract")
    if not gate.explicit_runtime_opt_in:
        required_components.append("explicit_runtime_configuration_opt_in")
    if not gate.secret_source_approved:
        required_components.append("approved_secret_source")
    return tuple(required_components)


def _requested_issues(
    required_components: tuple[str, ...],
) -> list[PostgreSQLRuntimeConfigGateIssue]:
    if required_components:
        return [
            PostgreSQLRuntimeConfigGateIssue(
                code="POSTGRESQL_RUNTIME_CONFIG_BLOCKED",
                message=(
                    "Runtime PostgreSQL configuration loading remains blocked until "
                    "future safety-gated components are complete."
                ),
                field_name="requested",
            ),
        ]

    return [
        PostgreSQLRuntimeConfigGateIssue(
            code="POSTGRESQL_RUNTIME_CONFIG_NOT_ENABLED",
            message=(
                "All supplied gate metadata is marked complete, but this "
                "boundary still does not enable runtime config loading."
            ),
            field_name="requested",
        ),
    ]


def _requested_reason(ready_metadata_only: bool) -> str:
    if ready_metadata_only:
        return (
            "PostgreSQL runtime configuration was requested, but this boundary "
            "does not enable runtime config loading."
        )
    return (
        "PostgreSQL runtime configuration was requested, but this boundary does "
        "not enable config loading and required future components are not complete."
    )


def _safe_operational_notes() -> tuple[str, ...]:
    return (
        "No environment variables are loaded.",
        "No config files are read.",
        "No credentials are loaded.",
        "No PostgreSQL connection is opened.",
        "No SQL runtime is created.",
    )
