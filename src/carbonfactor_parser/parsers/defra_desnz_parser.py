"""Artificial DEFRA/DESNZ-labelled parser skeleton."""

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
class DefraDesnzParser:
    """DEFRA/DESNZ-labelled parser skeleton for artificial records."""

    source_name: str = "fixture:defra_desnz_artificial_parser"
    source_document: SourceDocument | None = None

    @property
    def source_family(self) -> SourceFamily:
        return SourceFamily.DEFRA_DESNZ

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
        code: str = "defra_desnz_artificial_warning",
        message: str = "Artificial DEFRA/DESNZ parser warning",
    ) -> ParserIssue:
        return ParserIssue(
            code=code,
            message=message,
            severity=ParserIssueSeverity.WARNING,
        )

    def error_issue(
        self,
        code: str = "defra_desnz_artificial_error",
        message: str = "Artificial DEFRA/DESNZ parser error",
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
