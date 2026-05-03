"""Artificial in-memory parser skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from carbonfactor_parser.parsers.contracts import (
    ParserIssue,
    ParserIssueSeverity,
    ParserResult,
)
from carbonfactor_parser.source_adapters import SourceDocument


@dataclass(frozen=True)
class ExampleInMemoryParser:
    """Parser-shaped skeleton for caller-supplied artificial records."""

    source_document: SourceDocument

    def parse_records(
        self,
        records: Sequence[Mapping[str, Any]],
        *,
        issues: Sequence[ParserIssue] = (),
    ) -> ParserResult:
        return ParserResult(
            source_document=self.source_document,
            records=tuple(dict(record) for record in records),
            issues=tuple(issues),
        )

    def parse_empty(
        self,
        *,
        issues: Sequence[ParserIssue] = (),
    ) -> ParserResult:
        return self.parse_records((), issues=issues)

    def warning_issue(
        self,
        code: str = "example_warning",
        message: str = "Artificial parser warning",
    ) -> ParserIssue:
        return ParserIssue(
            code=code,
            message=message,
            severity=ParserIssueSeverity.WARNING,
        )

    def error_issue(
        self,
        code: str = "example_error",
        message: str = "Artificial parser error",
    ) -> ParserIssue:
        return ParserIssue(
            code=code,
            message=message,
            severity=ParserIssueSeverity.ERROR,
        )
