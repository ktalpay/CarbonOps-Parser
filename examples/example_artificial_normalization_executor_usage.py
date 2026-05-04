"""Artificial normalization executor usage example."""

from __future__ import annotations

from carbonfactor_parser.normalization import (
    ArtificialNormalizationExecutor,
    NormalizationResult,
    ParserNormalizationHandoff,
    ParserNormalizationHandoffEntry,
)


def build_artificial_normalization_executor_usage() -> dict[str, object]:
    handoff = ParserNormalizationHandoff(
        parser_record_count=2,
        issue_count=0,
        source_reference="fixture:artificial_parser_source",
        entries=(
            ParserNormalizationHandoffEntry(
                record_id="record-001",
                parser_record=(
                    ("field_name", "alpha"),
                    ("value_label", "one"),
                ),
                source_reference="fixture:artificial_parser_source",
            ),
            ParserNormalizationHandoffEntry(
                record_id="record-002",
                parser_record=(
                    ("field_name", "beta"),
                    ("value_label", "two"),
                ),
                source_reference="fixture:artificial_parser_source",
            ),
        ),
    )
    result = ArtificialNormalizationExecutor().execute(handoff)
    return _normalization_result_to_dict(result)


def _normalization_result_to_dict(result: NormalizationResult) -> dict[str, object]:
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
    }
