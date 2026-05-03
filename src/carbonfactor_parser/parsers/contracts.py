"""Source-agnostic parser result contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from carbonfactor_parser.source_adapters import SourceDocument


class ParserIssueSeverity(str, Enum):
    """Parser issue severity levels."""

    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ParserIssue:
    """Parser-level warning or error without source-specific interpretation."""

    code: str
    message: str
    severity: ParserIssueSeverity
    location: str | None = None
    context: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class ParserResultSummary:
    """Small summary of source-agnostic parser result counts."""

    record_count: int
    warning_count: int
    error_count: int
    has_records: bool
    has_warnings: bool
    has_errors: bool
    is_clean: bool


@dataclass(frozen=True)
class ParserResult:
    """Source-agnostic parser result contract."""

    source_document: SourceDocument
    records: tuple[Mapping[str, Any], ...] = ()
    issues: tuple[ParserIssue, ...] = ()

    @property
    def summary(self) -> ParserResultSummary:
        warning_count = sum(
            issue.severity == ParserIssueSeverity.WARNING for issue in self.issues
        )
        error_count = sum(
            issue.severity == ParserIssueSeverity.ERROR for issue in self.issues
        )

        return ParserResultSummary(
            record_count=len(self.records),
            warning_count=warning_count,
            error_count=error_count,
            has_records=bool(self.records),
            has_warnings=bool(warning_count),
            has_errors=bool(error_count),
            is_clean=not warning_count and not error_count,
        )
