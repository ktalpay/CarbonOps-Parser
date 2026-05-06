"""Artificial source-specific parser skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from carbonfactor_parser.parsers.contracts import (
    ParserIssue,
    ParserIssueSeverity,
    ParserResult,
)
from carbonfactor_parser.source_adapters import SourceDocument, SourceFamily


@dataclass(frozen=True)
class ExampleSourceSpecificParser:
    """Source-family-labelled parser skeleton for artificial records."""

    source_family: SourceFamily
    source_name: str = "fixture:example_source_specific"
    source_document: SourceDocument | None = None

    def parse_records(
        self,
        records: Sequence[Mapping[str, Any]],
        *,
        issues: Sequence[ParserIssue] = (),
    ) -> ParserResult:
        return ParserResult(
            source_document=self._source_document(),
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
        code: str = "example_source_specific_warning",
        message: str = "Artificial source-specific parser warning",
    ) -> ParserIssue:
        return ParserIssue(
            code=code,
            message=message,
            severity=ParserIssueSeverity.WARNING,
        )

    def error_issue(
        self,
        code: str = "example_source_specific_error",
        message: str = "Artificial source-specific parser error",
    ) -> ParserIssue:
        return ParserIssue(
            code=code,
            message=message,
            severity=ParserIssueSeverity.ERROR,
        )

    def _source_document(self) -> SourceDocument:
        if self.source_document is not None:
            return self.source_document
        return SourceDocument(
            source_family=self.source_family,
            source_name=self.source_name,
        )
