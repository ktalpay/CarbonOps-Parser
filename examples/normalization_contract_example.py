"""In-memory normalization contract example."""

from __future__ import annotations

from carbonfactor_parser.normalization import (
    NormalizationIssue,
    NormalizationIssueSeverity,
    NormalizationResult,
    NormalizedRecord,
)


def build_normalization_contract_example() -> dict[str, object]:
    result = NormalizationResult(
        records=(
            NormalizedRecord(
                record_id="record-001",
                fields=(
                    ("field_name", "alpha"),
                    ("value_label", "one"),
                ),
                source_reference="fixture:artificial_record_001",
            ),
            NormalizedRecord(
                record_id="record-002",
                fields=(
                    ("field_name", "beta"),
                    ("value_label", "two"),
                ),
                source_reference="fixture:artificial_record_002",
            ),
        ),
        issues=(
            NormalizationIssue(
                code="example_warning",
                message="Artificial normalization warning",
                severity=NormalizationIssueSeverity.WARNING,
                location="record 2",
            ),
        ),
    )
    return _normalization_result_to_dict(result)


def build_normalization_error_example() -> dict[str, object]:
    result = NormalizationResult(
        records=(),
        issues=(
            NormalizationIssue(
                code="example_error",
                message="Artificial normalization error",
                severity=NormalizationIssueSeverity.ERROR,
                location="record 1",
            ),
        ),
    )
    return _normalization_result_to_dict(result)


def _normalization_result_to_dict(
    result: NormalizationResult,
) -> dict[str, object]:
    summary = result.summary
    return {
        "normalized_record_count": summary.normalized_record_count,
        "warning_count": summary.warning_count,
        "error_count": summary.error_count,
        "has_normalized_records": summary.has_normalized_records,
        "has_warnings": summary.has_warnings,
        "has_errors": summary.has_errors,
        "is_clean": summary.is_clean,
        "records": tuple(
            {
                "record_id": record.record_id,
                "fields": record.fields,
                "source_reference": record.source_reference,
                "is_artificial": record.is_artificial,
            }
            for record in result.records
        ),
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
