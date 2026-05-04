"""Artificial normalization result summary usage example."""

from __future__ import annotations

from carbonfactor_parser.normalization import NormalizationResultSummary


def run_example() -> dict[str, object]:
    summary = NormalizationResultSummary(
        record_count=2,
        issue_count=1,
        source_family="artificial",
        source_id="artificial-summary-source",
        metadata={
            "example_kind": "direct_summary_model",
            "input_kind": "artificial_values",
        },
        warning_count=1,
        error_count=0,
    )

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
