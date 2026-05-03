"""Usage example for the artificial in-memory parser skeleton."""

from __future__ import annotations

from carbonfactor_parser.parsers import ExampleInMemoryParser, ParserResult
from carbonfactor_parser.source_adapters import SourceDocument, SourceFamily


def build_example_in_memory_parser_usage() -> dict[str, object]:
    source_document = SourceDocument(
        source_family=SourceFamily.GHG_PROTOCOL,
        source_name="fixture:artificial_in_memory_source",
    )
    records = (
        {"record_id": "record-1", "category": "alpha", "value_label": "one"},
        {"record_id": "record-2", "category": "beta", "value_label": "two"},
    )

    parser = ExampleInMemoryParser(source_document=source_document)
    result = parser.parse_records(records)

    return _parser_result_to_dict(result)


def _parser_result_to_dict(result: ParserResult) -> dict[str, object]:
    summary = result.summary
    return {
        "source_name": result.source_document.source_name,
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
