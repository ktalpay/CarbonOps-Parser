"""PostgreSQL repository skeleton without runtime database behavior."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from carbonfactor_parser.persistence.input import PersistenceInput
from carbonfactor_parser.persistence.postgresql_options import (
    PostgreSQLPersistenceOptions,
)
from carbonfactor_parser.persistence.postgresql_runtime_execution_gate import (
    PostgreSQLRuntimeExecutionGate,
    PostgreSQLRuntimeExecutionGateDecision,
    evaluate_postgresql_runtime_execution_gate,
)


class PostgreSQLRepositoryRuntimeSafetyGateStatus(str, Enum):
    """Status values for repository runtime safety gate decisions."""

    DISABLED = "disabled"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class PostgreSQLRepositoryRuntimeSafetyGateIssue:
    """Issue explaining a repository runtime safety gate decision."""

    code: str
    message: str
    field_name: str | None = None
    severity: str = "warning"


@dataclass(frozen=True)
class PostgreSQLRepositoryRuntimeSafetyGate:
    """Repository-level runtime persistence intent metadata only."""

    requested: bool = False
    allow_repository_runtime_persistence: bool = False
    runtime_execution_gate: PostgreSQLRuntimeExecutionGate = field(
        default_factory=PostgreSQLRuntimeExecutionGate,
    )


@dataclass(frozen=True)
class PostgreSQLRepositoryRuntimeSafetyGateDecision:
    """Repository-level no-execution safety decision."""

    status: PostgreSQLRepositoryRuntimeSafetyGateStatus
    requested: bool
    no_execution: bool
    repository_runtime_enabled: bool
    persist_behavior_changed: bool
    opens_connection: bool
    runs_sql: bool
    writes_records: bool
    starts_transaction: bool
    commits_transaction: bool
    rolls_back_transaction: bool
    loads_environment: bool
    loads_config_files: bool
    loads_credentials: bool
    required_future_components: tuple[str, ...]
    runtime_gate_decision: PostgreSQLRuntimeExecutionGateDecision
    issues: tuple[PostgreSQLRepositoryRuntimeSafetyGateIssue, ...] = ()


@dataclass(frozen=True)
class PostgreSQLRepositoryRuntimeSafetyGateDescription:
    """Side-effect-free description of repository runtime safety gating."""

    disabled_by_default: bool
    protects_repository_persist: bool
    accepts_runtime_intent: bool
    opens_connection: bool
    runs_sql: bool
    writes_records: bool
    starts_transaction: bool
    commits_transaction: bool
    rolls_back_transaction: bool
    loads_environment: bool
    loads_config_files: bool
    loads_credentials: bool
    protected_metadata_keys: tuple[str, ...]
    notes: tuple[str, ...]
from carbonfactor_parser.persistence.repository import (
    PersistenceIssue,
    PersistenceIssueSeverity,
    PersistenceResult,
    PersistenceResultStatus,
    create_persistence_result,
)


@dataclass(frozen=True)
class PostgreSQLPersistenceRepository:
    """Skeleton repository that satisfies the persistence protocol."""

    options: PostgreSQLPersistenceOptions | None = None
    repository_metadata: Mapping[str, object] | None = None
    runtime_safety_gate: PostgreSQLRepositoryRuntimeSafetyGate = field(
        default_factory=PostgreSQLRepositoryRuntimeSafetyGate,
    )

    @property
    def provider_name(self) -> str:
        """Return the deterministic provider identity for this skeleton."""

        return "postgresql"

    def persist(self, persistence_input: PersistenceInput) -> PersistenceResult:
        """Return unsupported; runtime PostgreSQL persistence is deferred."""

        safety_decision = evaluate_postgresql_repository_runtime_safety_gate(
            self.runtime_safety_gate,
        )
        return create_persistence_result(
            status=PersistenceResultStatus.UNSUPPORTED,
            attempted_record_count=len(persistence_input.records),
            persisted_record_count=0,
            issues=(
                PersistenceIssue(
                    code="POSTGRESQL_REPOSITORY_NOT_IMPLEMENTED",
                    message=(
                        "PostgreSQLPersistenceRepository is a skeleton and "
                        "does not connect to PostgreSQL or write records."
                    ),
                    severity=PersistenceIssueSeverity.ERROR,
                ),
            ),
            repository_metadata=_safe_repository_metadata(
                provider_name=self.provider_name,
                options_provided=self.options is not None,
                caller_metadata=self.repository_metadata,
                safety_decision=safety_decision,
            ),
        )


def evaluate_postgresql_repository_runtime_safety_gate(
    gate: PostgreSQLRepositoryRuntimeSafetyGate | None = None,
) -> PostgreSQLRepositoryRuntimeSafetyGateDecision:
    """Evaluate repository runtime persistence intent without enabling it."""

    active_gate = gate or PostgreSQLRepositoryRuntimeSafetyGate()
    runtime_gate_decision = evaluate_postgresql_runtime_execution_gate(
        active_gate.runtime_execution_gate,
    )
    requested = (
        active_gate.requested
        or active_gate.allow_repository_runtime_persistence
        or active_gate.runtime_execution_gate.requested
    )
    required_components = tuple(
        dict.fromkeys(
            (
                *runtime_gate_decision.required_future_components,
                "repository_runtime_persistence_task",
                "repository_runtime_review",
            )
        )
    )
    issues = [
        PostgreSQLRepositoryRuntimeSafetyGateIssue(
            code=(
                "POSTGRESQL_REPOSITORY_RUNTIME_REQUEST_BLOCKED"
                if requested
                else "POSTGRESQL_REPOSITORY_RUNTIME_DISABLED_BY_DEFAULT"
            ),
            message=(
                "PostgreSQL repository runtime persistence remains blocked; "
                "this boundary does not connect to PostgreSQL or write records."
            ),
            field_name="requested" if requested else None,
        )
    ]
    if active_gate.allow_repository_runtime_persistence:
        issues.append(
            PostgreSQLRepositoryRuntimeSafetyGateIssue(
                code="POSTGRESQL_REPOSITORY_RUNTIME_ALLOW_FLAG_NOT_SUPPORTED",
                message=(
                    "allow_repository_runtime_persistence is metadata only "
                    "and cannot enable repository runtime writes."
                ),
                field_name="allow_repository_runtime_persistence",
            )
        )

    return PostgreSQLRepositoryRuntimeSafetyGateDecision(
        status=(
            PostgreSQLRepositoryRuntimeSafetyGateStatus.BLOCKED
            if requested
            else PostgreSQLRepositoryRuntimeSafetyGateStatus.DISABLED
        ),
        requested=requested,
        no_execution=True,
        repository_runtime_enabled=False,
        persist_behavior_changed=False,
        opens_connection=False,
        runs_sql=False,
        writes_records=False,
        starts_transaction=False,
        commits_transaction=False,
        rolls_back_transaction=False,
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
        required_future_components=required_components,
        runtime_gate_decision=runtime_gate_decision,
        issues=tuple(issues),
    )


def describe_postgresql_repository_runtime_safety_gate() -> (
    PostgreSQLRepositoryRuntimeSafetyGateDescription
):
    """Describe repository runtime safety gating without side effects."""

    return PostgreSQLRepositoryRuntimeSafetyGateDescription(
        disabled_by_default=True,
        protects_repository_persist=True,
        accepts_runtime_intent=True,
        opens_connection=False,
        runs_sql=False,
        writes_records=False,
        starts_transaction=False,
        commits_transaction=False,
        rolls_back_transaction=False,
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
        protected_metadata_keys=_protected_repository_metadata_keys(),
        notes=(
            "Repository runtime persistence is disabled by default.",
            "PostgreSQLPersistenceRepository.persist remains unsupported.",
            "Caller metadata cannot override no-execution safety metadata.",
        ),
    )


def _safe_repository_metadata(
    *,
    provider_name: str,
    options_provided: bool,
    caller_metadata: Mapping[str, object] | None,
    safety_decision: PostgreSQLRepositoryRuntimeSafetyGateDecision,
) -> dict[str, object]:
    metadata = dict(caller_metadata) if caller_metadata is not None else {}
    metadata.update(
        {
            "provider_name": provider_name,
            "skeleton": True,
            "options_provided": options_provided,
            "database_connection": False,
            "runtime_write": False,
            "migration_runtime": False,
            "repository_runtime_enabled": False,
            "repository_runtime_safety_gate_status": safety_decision.status.value,
            "repository_runtime_requested": safety_decision.requested,
            "repository_runtime_no_execution": True,
            "repository_runtime_persist_behavior_changed": False,
        }
    )
    return metadata


def _protected_repository_metadata_keys() -> tuple[str, ...]:
    return (
        "provider_name",
        "skeleton",
        "options_provided",
        "database_connection",
        "runtime_write",
        "migration_runtime",
        "repository_runtime_enabled",
        "repository_runtime_safety_gate_status",
        "repository_runtime_requested",
        "repository_runtime_no_execution",
        "repository_runtime_persist_behavior_changed",
    )
