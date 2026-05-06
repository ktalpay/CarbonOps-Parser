"""Persistence repository protocol and result boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Protocol, runtime_checkable

from carbonfactor_parser.persistence.input import PersistenceInput


class PersistenceResultStatus(str, Enum):
    """Persistence repository result status values."""

    SUCCESS = "success"
    FAILED = "failed"
    NO_RECORDS = "no_records"
    UNSUPPORTED = "unsupported"


class PersistenceIssueSeverity(str, Enum):
    """Persistence repository issue severity values."""

    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class PersistenceIssue:
    """Structured issue from a persistence repository boundary."""

    code: str
    message: str
    severity: PersistenceIssueSeverity
    field_name: str | None = None
    context: Mapping[str, object] | None = None


@dataclass(frozen=True)
class PersistenceResult:
    """Structured result from a persistence repository boundary."""

    status: PersistenceResultStatus
    attempted_record_count: int = 0
    persisted_record_count: int = 0
    issues: tuple[PersistenceIssue, ...] = ()
    repository_metadata: Mapping[str, object] | None = None


@runtime_checkable
class PersistenceRepository(Protocol):
    """Protocol for future persistence repositories."""

    provider_name: str

    def persist(self, persistence_input: PersistenceInput) -> PersistenceResult:
        """Persist normalized records behind a future repository boundary."""
        ...


def create_persistence_result(
    *,
    status: PersistenceResultStatus,
    attempted_record_count: int = 0,
    persisted_record_count: int = 0,
    issues: tuple[PersistenceIssue, ...] | list[PersistenceIssue] = (),
    repository_metadata: Mapping[str, object] | None = None,
) -> PersistenceResult:
    """Create a persistence result without performing persistence."""

    return PersistenceResult(
        status=status,
        attempted_record_count=attempted_record_count,
        persisted_record_count=persisted_record_count,
        issues=tuple(issues),
        repository_metadata=(
            dict(repository_metadata)
            if repository_metadata is not None
            else None
        ),
    )
