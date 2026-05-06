"""Driver-neutral PostgreSQL connection/session contract boundary."""

from __future__ import annotations

from dataclasses import dataclass
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


def describe_postgresql_connection_session_contract(
    *,
    transaction_boundary: PostgreSQLTransactionBoundary | None = None,
) -> PostgreSQLConnectionSessionContractDescription:
    """Describe the future session contract without creating a connection."""

    return PostgreSQLConnectionSessionContractDescription(
        driver_neutral=True,
        caller_provided=True,
        opens_connection=False,
        runs_sql=False,
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
        statement_method_name="run_statement",
        transaction_boundary=(
            transaction_boundary
            if transaction_boundary is not None
            else PostgreSQLTransactionBoundary()
        ),
        notes=(
            "Protocol shape only.",
            "Future runtime adapters must stay behind the safety gate.",
            "Pure preview modules must remain driver-free.",
        ),
    )
