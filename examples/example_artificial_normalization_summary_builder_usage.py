"""Artificial normalization summary builder usage example."""

from __future__ import annotations

from carbonfactor_parser.normalization import (
    ArtificialNormalizationSummaryBuilder,
    NormalizationIssue,
    NormalizationIssueSeverity,
    NormalizationResult,
    NormalizedRecord,
)


def run_example() -> dict[str, object]:
    result = NormalizationResult(
        records=(
            NormalizedRecord(
                record_id="record-001",
                fields=(
                    ("field_name", "alpha"),
                    ("value_label", "one"),
                ),
                source_reference="fixture:artificial-normalization-summary",
            ),
            NormalizedRecord(
                record_id="record-002",
                fields=(
                    ("field_name", "beta"),
                    ("value_label", "two"),
                ),
                source_reference="fixture:artificial-normalization-summary",
            ),
        ),
        issues=(
            NormalizationIssue(
                code="artificial_warning",
                message="Artificial warning",
                severity=NormalizationIssueSeverity.WARNING,
                location="record-002",
            ),
        ),
    )

    summary = ArtificialNormalizationSummaryBuilder().build(result)

    return {
        "record_count": summary.record_count,
        "issue_count": summary.issue_count,
        "source_family": summary.source_family,
        "source_id": summary.source_id,
        "is_artificial": summary.is_artificial,
        "metadata": tuple(sorted(summary.metadata.items())),
        "warning_count": summary.warning_count,
        "error_count": summary.error_count,
        "has_normalized_records": summary.has_normalized_records,
        "has_warnings": summary.has_warnings,
        "has_errors": summary.has_errors,
        "is_clean": summary.is_clean,
    }
