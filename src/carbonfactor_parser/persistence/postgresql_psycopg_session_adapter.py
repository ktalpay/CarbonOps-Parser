"""psycopg-specific PostgreSQL session adapter skeleton without connection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Mapping

from carbonfactor_parser.persistence.postgresql_execution_adapter_boundary import (
    PostgreSQLExecutionIssue,
    PostgreSQLExecutionPlan,
    PostgreSQLExecutionResult,
    PostgreSQLExecutionStatus,
)

if TYPE_CHECKING:
    import psycopg


class PsycopgPostgreSQLSessionAdapterStatus(str, Enum):
    """Status values for the psycopg session adapter skeleton."""

    DISABLED = "disabled"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


@dataclass(frozen=True)
class PsycopgPostgreSQLSessionAdapterMetadata:
    """No-execution capability metadata for the psycopg adapter skeleton."""

    provider_name: str
    driver_name: str
    caller_provided_session_required: bool
    session_reference_provided: bool
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
    runtime_enabled: bool
    notes: tuple[str, ...]


@dataclass(frozen=True)
class PsycopgPostgreSQLSessionAdapterBoundaryResult:
    """Structured no-execution result for adapter boundary checks."""

    status: PsycopgPostgreSQLSessionAdapterStatus
    metadata: PsycopgPostgreSQLSessionAdapterMetadata
    issues: tuple[PostgreSQLExecutionIssue, ...] = ()


@dataclass(frozen=True)
class PsycopgPostgreSQLSessionAdapter:
    """Skeleton wrapper for a future caller-provided psycopg session."""

    session_reference: Any | None = None
    adapter_metadata: Mapping[str, object] | None = None

    @property
    def provider_name(self) -> str:
        """Return the deterministic provider identity for this skeleton."""

        return "postgresql_psycopg"

    @property
    def runtime_enabled(self) -> bool:
        """Return False because this skeleton never runs SQL."""

        return False

    def describe_capabilities(
        self,
    ) -> PsycopgPostgreSQLSessionAdapterMetadata:
        """Describe adapter capabilities without using the session reference."""

        return build_psycopg_session_adapter_metadata(
            session_reference_provided=self.session_reference is not None,
        )

    def build_disabled_execution_result(
        self,
        plan: PostgreSQLExecutionPlan | None = None,
    ) -> PostgreSQLExecutionResult:
        """Return disabled execution metadata without touching PostgreSQL."""

        return PostgreSQLExecutionResult(
            status=PostgreSQLExecutionStatus.DISABLED,
            affected_record_count=0,
            statement_count=plan.statement_count if plan is not None else 0,
            plan=plan,
            issues=(
                PostgreSQLExecutionIssue(
                    code="PSYCOPG_SESSION_ADAPTER_DISABLED",
                    message=(
                        "PsycopgPostgreSQLSessionAdapter is a no-connection "
                        "skeleton and does not run SQL."
                    ),
                    severity="warning",
                ),
            ),
        )

    def validate_adapter_boundary(
        self,
    ) -> PsycopgPostgreSQLSessionAdapterBoundaryResult:
        """Return disabled boundary metadata without runtime validation."""

        return PsycopgPostgreSQLSessionAdapterBoundaryResult(
            status=PsycopgPostgreSQLSessionAdapterStatus.DISABLED,
            metadata=self.describe_capabilities(),
            issues=(
                PostgreSQLExecutionIssue(
                    code="PSYCOPG_SESSION_ADAPTER_NO_EXECUTION",
                    message=(
                        "psycopg dependency is available for future adapter "
                        "work, but this skeleton does not connect or run SQL."
                    ),
                    severity="warning",
                ),
            ),
        )


def build_psycopg_session_adapter_metadata(
    *,
    session_reference_provided: bool = False,
) -> PsycopgPostgreSQLSessionAdapterMetadata:
    """Build deterministic no-execution psycopg adapter metadata."""

    return PsycopgPostgreSQLSessionAdapterMetadata(
        provider_name="postgresql_psycopg",
        driver_name="psycopg",
        caller_provided_session_required=True,
        session_reference_provided=session_reference_provided,
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
        runtime_enabled=False,
        notes=(
            "Dedicated psycopg adapter skeleton only.",
            "Future runtime work must receive caller-provided sessions.",
            "This skeleton does not create cursors or run statements.",
            "PostgreSQLPersistenceRepository remains unsupported.",
        ),
    )


def validate_psycopg_session_adapter_boundary(
    adapter: PsycopgPostgreSQLSessionAdapter | None = None,
) -> PsycopgPostgreSQLSessionAdapterBoundaryResult:
    """Validate the skeleton boundary without connecting to PostgreSQL."""

    active_adapter = adapter or PsycopgPostgreSQLSessionAdapter()
    return active_adapter.validate_adapter_boundary()
