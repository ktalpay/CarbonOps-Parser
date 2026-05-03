"""In-memory parser result contract example."""

from __future__ import annotations

from carbonfactor_parser.parsers import (
    ParserIssue,
    ParserIssueSeverity,
    ParserResult,
)
from carbonfactor_parser.source_adapters import SourceDocument, SourceFamily


def build_parser_result_contract_example() -> dict[str, object]:
    result = ParserResult(
        source_document=_example_source_document(),
        records=(
            {"field_name": "alpha", "raw_value": "one"},
            {"field_name": "beta", "raw_value": "two"},
        ),
        issues=(
            ParserIssue(
                code="example_warning",
                message="Artificial parser warning",
                severity=ParserIssueSeverity.WARNING,
                location="record 2",
            ),
        ),
    )
    return _parser_result_to_dict(result)


def build_parser_result_error_example() -> dict[str, object]:
    result = ParserResult(
        source_document=_example_source_document(),
        records=(),
        issues=(
            ParserIssue(
                code="example_error",
                message="Artificial parser error",
                severity=ParserIssueSeverity.ERROR,
                location="record 1",
            ),
        ),
    )
    return _parser_result_to_dict(result)


def _example_source_document() -> SourceDocument:
    return SourceDocument(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="fixture:artificial_source",
        file_reference="fixtures/artificial_source.txt",
    )


def _parser_result_to_dict(result: ParserResult) -> dict[str, object]:
    summary = result.summary
    return {
        "source_family": result.source_document.source_family.value,
        "source_name": result.source_document.source_name,
        "file_reference": result.source_document.file_reference,
        "record_count": summary.record_count,
        "warning_count": summary.warning_count,
        "error_count": summary.error_count,
        "has_records": summary.has_records,
        "has_warnings": summary.has_warnings,
        "has_errors": summary.has_errors,
        "is_clean": summary.is_clean,
        "records": tuple(dict(record) for record in result.records),
        "issues": tuple(
            {
                "code": issue.code,
                "message": issue.message,
                "severity": issue.severity.value,
                "location": issue.location,
            }
            for issue in result.issues
        ),
    }
