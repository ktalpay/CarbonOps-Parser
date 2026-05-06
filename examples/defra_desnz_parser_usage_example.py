"""Usage example for the artificial DEFRA/DESNZ parser skeleton."""

from __future__ import annotations

from carbonfactor_parser.parsers import DefraDesnzParser, ParserResult


def build_defra_desnz_parser_usage_example() -> dict[str, object]:
    records = (
        {
            "record_id": "record-1",
            "source_label": "defra-desnz-artificial",
            "value_label": "one",
        },
        {
            "record_id": "record-2",
            "source_label": "defra-desnz-artificial",
            "value_label": "two",
        },
    )

    parser = DefraDesnzParser()
    result = parser.parse_records(records)

    return _parser_result_to_dict(result)


def _parser_result_to_dict(result: ParserResult) -> dict[str, object]:
    summary = result.summary
    return {
        "source_family": result.source_document.source_family.value,
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
