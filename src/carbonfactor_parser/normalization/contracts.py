"""Source-agnostic normalization result contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class NormalizationIssueSeverity(str, Enum):
    """Normalization issue severity levels."""

    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class NormalizationIssue:
    """Normalization-level warning or error without source-specific interpretation."""

    code: str
    message: str
    severity: NormalizationIssueSeverity
    location: str | None = None


@dataclass(frozen=True)
class NormalizedRecord:
    """Source-agnostic normalized record contract."""

    record_id: str
    fields: tuple[tuple[str, Any], ...] = ()
    source_reference: str | None = None
    is_artificial: bool = True


@dataclass(frozen=True)
class NormalizationResultSummary:
    """Small summary of source-agnostic normalization result counts."""

    normalized_record_count: int
    warning_count: int
    error_count: int
    has_normalized_records: bool
    has_warnings: bool
    has_errors: bool
    is_clean: bool


@dataclass(frozen=True)
class NormalizationResult:
    """Source-agnostic normalization result contract."""

    records: tuple[NormalizedRecord, ...] = ()
    issues: tuple[NormalizationIssue, ...] = ()

    @property
    def summary(self) -> NormalizationResultSummary:
        warning_count = sum(
            issue.severity == NormalizationIssueSeverity.WARNING
            for issue in self.issues
        )
        error_count = sum(
            issue.severity == NormalizationIssueSeverity.ERROR for issue in self.issues
        )

        return NormalizationResultSummary(
            normalized_record_count=len(self.records),
            warning_count=warning_count,
            error_count=error_count,
            has_normalized_records=bool(self.records),
            has_warnings=bool(warning_count),
            has_errors=bool(error_count),
            is_clean=not warning_count and not error_count,
        )
