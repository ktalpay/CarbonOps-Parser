"""Driver-neutral PostgreSQL connection/session contract boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable


class PostgreSQLTransactionOwnership(str, Enum):
    """Future transaction ownership boundary values."""

    CALLER_OWNED = "caller_owned"
    REPOSITORY_OWNED_FUTURE = "repository_owned_future"


class PostgreSQLTransactionMode(str, Enum):
    """Future transaction mode boundary values."""

    CALLER_MANAGED = "caller_managed"
    SINGLE_BATCH_FUTURE = "single_batch_future"


class PostgreSQLConnectionSessionContractStatus(str, Enum):
    """Status values for connection/session contract validation."""

    READY = "ready"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class PostgreSQLTransactionBoundary:
    """Descriptive transaction boundary metadata without runtime behavior."""

    ownership: PostgreSQLTransactionOwnership = (
        PostgreSQLTransactionOwnership.CALLER_OWNED
    )
    mode: PostgreSQLTransactionMode = PostgreSQLTransactionMode.CALLER_MANAGED
    rollback_on_failure: bool = True


@dataclass(frozen=True)
class PostgreSQLStatementExecutionContract:
    """Parameterized statement shape for a future runtime adapter."""

    sql: str
    parameters: Sequence[Any] | Mapping[str, Any] | None = None
    statement_metadata: Mapping[str, object] | None = None


@dataclass(frozen=True)
class PostgreSQLConnectionSessionContractIssue:
    """Validation issue for the connection/session runtime contract."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class PostgreSQLConnectionSessionContractValidationResult:
    """Fail-closed validation result for connection/session contracts."""

    status: PostgreSQLConnectionSessionContractStatus
    issues: tuple[PostgreSQLConnectionSessionContractIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return (
            self.status is PostgreSQLConnectionSessionContractStatus.READY
            and not self.issues
        )


@dataclass(frozen=True)
class PostgreSQLConnectionSessionRuntimeContract:
    """No-execution runtime contract for caller-provided PostgreSQL sessions."""

    provider_name: str
    statement_method_name: str = "run_statement"
    caller_provided: bool = True
    runtime_enabled: bool = False
    opens_connection: bool = False
    creates_cursor: bool = False
    runs_sql: bool = False
    writes_records: bool = False
    starts_transaction: bool = False
    commits_transaction: bool = False
    rolls_back_transaction: bool = False
    loads_environment: bool = False
    loads_config_files: bool = False
    loads_credentials: bool = False
    transaction_boundary: PostgreSQLTransactionBoundary = field(
        default_factory=PostgreSQLTransactionBoundary,
    )


@runtime_checkable
class PostgreSQLConnectionSession(Protocol):
    """Protocol for caller-provided future PostgreSQL session objects."""

    provider_name: str

    def run_statement(
        self,
        statement: PostgreSQLStatementExecutionContract,
    ) -> object:
        """Future statement handoff point; no implementation is provided here."""
        ...


@dataclass(frozen=True)
class PostgreSQLConnectionSessionContractDescription:
    """Side-effect-free description of the PostgreSQL session boundary."""

    driver_neutral: bool
    caller_provided: bool
    opens_connection: bool
    runs_sql: bool
    loads_environment: bool
    loads_config_files: bool
    loads_credentials: bool
    statement_method_name: str
    transaction_boundary: PostgreSQLTransactionBoundary
    notes: tuple[str, ...]
    runtime_contract: PostgreSQLConnectionSessionRuntimeContract = field(
        default_factory=lambda: PostgreSQLConnectionSessionRuntimeContract(
            provider_name="caller_provided_postgresql_session",
        ),
    )


def create_postgresql_connection_session_runtime_contract(
    *,
    provider_name: str = "caller_provided_postgresql_session",
    transaction_boundary: PostgreSQLTransactionBoundary | None = None,
) -> PostgreSQLConnectionSessionRuntimeContract:
    """Create no-execution runtime contract metadata for a caller session."""

    return PostgreSQLConnectionSessionRuntimeContract(
        provider_name=provider_name,
        transaction_boundary=(
            transaction_boundary
            if transaction_boundary is not None
            else PostgreSQLTransactionBoundary()
        ),
    )


def describe_postgresql_connection_session_contract(
    *,
    transaction_boundary: PostgreSQLTransactionBoundary | None = None,
) -> PostgreSQLConnectionSessionContractDescription:
    """Describe the future session contract without creating a connection."""

    active_transaction_boundary = (
        transaction_boundary
        if transaction_boundary is not None
        else PostgreSQLTransactionBoundary()
    )
    runtime_contract = create_postgresql_connection_session_runtime_contract(
        transaction_boundary=active_transaction_boundary,
    )
    return PostgreSQLConnectionSessionContractDescription(
        driver_neutral=True,
        caller_provided=True,
        opens_connection=False,
        runs_sql=False,
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
        statement_method_name="run_statement",
        transaction_boundary=active_transaction_boundary,
        runtime_contract=runtime_contract,
        notes=(
            "Protocol shape only.",
            "Future runtime adapters must stay behind the safety gate.",
            "Pure preview modules must remain driver-free.",
        ),
    )


def validate_postgresql_connection_session_runtime_contract(
    contract: PostgreSQLConnectionSessionRuntimeContract,
) -> PostgreSQLConnectionSessionContractValidationResult:
    """Validate session contract metadata without touching PostgreSQL."""

    issues: list[PostgreSQLConnectionSessionContractIssue] = []
    _validate_required_text(
        contract.provider_name,
        "provider_name",
        "POSTGRESQL_CONNECTION_SESSION_MISSING_PROVIDER_NAME",
        "provider_name must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        contract.statement_method_name,
        "statement_method_name",
        "POSTGRESQL_CONNECTION_SESSION_MISSING_STATEMENT_METHOD",
        "statement_method_name must be a non-empty string.",
        issues,
    )
    if contract.statement_method_name != "run_statement":
        issues.append(
            PostgreSQLConnectionSessionContractIssue(
                code="POSTGRESQL_CONNECTION_SESSION_STATEMENT_METHOD_MISMATCH",
                message="statement_method_name must remain run_statement.",
                field_name="statement_method_name",
            )
        )

    _validate_true(
        contract.caller_provided,
        "caller_provided",
        "POSTGRESQL_CONNECTION_SESSION_CALLER_PROVIDED_REQUIRED",
        "caller_provided must remain True.",
        issues,
    )
    for field_name, value in (
        ("runtime_enabled", contract.runtime_enabled),
        ("opens_connection", contract.opens_connection),
        ("creates_cursor", contract.creates_cursor),
        ("runs_sql", contract.runs_sql),
        ("writes_records", contract.writes_records),
        ("starts_transaction", contract.starts_transaction),
        ("commits_transaction", contract.commits_transaction),
        ("rolls_back_transaction", contract.rolls_back_transaction),
        ("loads_environment", contract.loads_environment),
        ("loads_config_files", contract.loads_config_files),
        ("loads_credentials", contract.loads_credentials),
    ):
        _validate_false(
            value,
            field_name,
            "POSTGRESQL_CONNECTION_SESSION_RUNTIME_FLAG_NOT_ALLOWED",
            f"{field_name} must remain False for this contract boundary.",
            issues,
        )

    if (
        contract.transaction_boundary.ownership
        is not PostgreSQLTransactionOwnership.CALLER_OWNED
    ):
        issues.append(
            PostgreSQLConnectionSessionContractIssue(
                code="POSTGRESQL_CONNECTION_SESSION_TRANSACTION_OWNERSHIP_UNSAFE",
                message="transaction ownership must remain caller_owned.",
                field_name="transaction_boundary.ownership",
            )
        )
    if (
        contract.transaction_boundary.mode
        is not PostgreSQLTransactionMode.CALLER_MANAGED
    ):
        issues.append(
            PostgreSQLConnectionSessionContractIssue(
                code="POSTGRESQL_CONNECTION_SESSION_TRANSACTION_MODE_UNSAFE",
                message="transaction mode must remain caller_managed.",
                field_name="transaction_boundary.mode",
            )
        )
    _validate_true(
        contract.transaction_boundary.rollback_on_failure,
        "transaction_boundary.rollback_on_failure",
        "POSTGRESQL_CONNECTION_SESSION_ROLLBACK_MARKER_REQUIRED",
        "rollback_on_failure must remain True.",
        issues,
    )

    return PostgreSQLConnectionSessionContractValidationResult(
        status=(
            PostgreSQLConnectionSessionContractStatus.BLOCKED
            if issues
            else PostgreSQLConnectionSessionContractStatus.READY
        ),
        issues=tuple(issues),
    )


def validate_postgresql_statement_execution_contract(
    statement: PostgreSQLStatementExecutionContract,
) -> PostgreSQLConnectionSessionContractValidationResult:
    """Validate future statement handoff metadata without running it."""

    issues: list[PostgreSQLConnectionSessionContractIssue] = []
    _validate_required_text(
        statement.sql,
        "sql",
        "POSTGRESQL_CONNECTION_SESSION_STATEMENT_MISSING_SQL",
        "sql must be a non-empty string.",
        issues,
    )
    if statement.parameters is not None:
        if isinstance(statement.parameters, (str, bytes)) or not isinstance(
            statement.parameters,
            (Mapping, Sequence),
        ):
            issues.append(
                PostgreSQLConnectionSessionContractIssue(
                    code="POSTGRESQL_CONNECTION_SESSION_STATEMENT_PARAMETERS_UNSAFE",
                    message=(
                        "parameters must be a sequence, mapping, or None; "
                        "plain text parameters are not accepted."
                    ),
                    field_name="parameters",
                )
            )
    if statement.statement_metadata is not None and not isinstance(
        statement.statement_metadata,
        Mapping,
    ):
        issues.append(
            PostgreSQLConnectionSessionContractIssue(
                code="POSTGRESQL_CONNECTION_SESSION_STATEMENT_METADATA_UNSAFE",
                message="statement_metadata must be a mapping or None.",
                field_name="statement_metadata",
            )
        )

    return PostgreSQLConnectionSessionContractValidationResult(
        status=(
            PostgreSQLConnectionSessionContractStatus.BLOCKED
            if issues
            else PostgreSQLConnectionSessionContractStatus.READY
        ),
        issues=tuple(issues),
    )


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[PostgreSQLConnectionSessionContractIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            PostgreSQLConnectionSessionContractIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )


def _validate_true(
    value: bool,
    field_name: str,
    code: str,
    message: str,
    issues: list[PostgreSQLConnectionSessionContractIssue],
) -> None:
    if value is not True:
        issues.append(
            PostgreSQLConnectionSessionContractIssue(
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
    issues: list[PostgreSQLConnectionSessionContractIssue],
) -> None:
    if value is not False:
        issues.append(
            PostgreSQLConnectionSessionContractIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )
