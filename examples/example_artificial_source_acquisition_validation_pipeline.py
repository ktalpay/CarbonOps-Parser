"""Artificial source acquisition validation pipeline usage example."""

from __future__ import annotations

from carbonfactor_parser import (
    create_artificial_source_acquisition_metadata,
    validate_and_summarize_artificial_source_acquisition_metadata,
)


ARTIFICIAL_CHECKSUM_SHA256 = "e" * 64


def run_example() -> dict[str, object]:
    metadata = create_artificial_source_acquisition_metadata(
        source_family="artificial_source_acquisition",
        logical_source_name="artificial-in-memory-source",
        declared_content_type="text/csv",
        checksum_sha256=ARTIFICIAL_CHECKSUM_SHA256,
        acquired_at_label="static-artificial-acquisition-label",
        parser_hint="artificial-parser-hint",
        adapter_hint="artificial-adapter-hint",
    )

    pipeline_result = validate_and_summarize_artificial_source_acquisition_metadata(
        metadata,
    )
    summary = pipeline_result.summary

    return {
        "source_family": metadata.source_family,
        "logical_source_name": metadata.logical_source_name,
        "declared_content_type": metadata.declared_content_type,
        "acquired_at_label": metadata.acquired_at_label,
        "parser_hint": metadata.parser_hint,
        "adapter_hint": metadata.adapter_hint,
        "validation_is_valid": pipeline_result.validation_result.is_valid,
        "summary_is_valid": summary.is_valid,
        "total_issue_count": summary.total_issue_count,
        "severity_counts": tuple(
            (count.name, count.count) for count in summary.severity_counts
        ),
        "category_counts": tuple(
            (count.name, count.count) for count in summary.category_counts
        ),
    }
