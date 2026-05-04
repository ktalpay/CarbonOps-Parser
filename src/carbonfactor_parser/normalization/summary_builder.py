"""Artificial normalization summary builder skeleton."""

from __future__ import annotations

from dataclasses import dataclass

from carbonfactor_parser.normalization.contracts import (
    NormalizationIssueSeverity,
    NormalizationResult,
)
from carbonfactor_parser.normalization.summary import NormalizationResultSummary


@dataclass(frozen=True)
class ArtificialNormalizationSummaryBuilder:
    """Build an artificial output-shape summary from normalization output."""

    def build(self, result: NormalizationResult) -> NormalizationResultSummary:
        warning_count = sum(
            issue.severity == NormalizationIssueSeverity.WARNING
            for issue in result.issues
        )
        error_count = sum(
            issue.severity == NormalizationIssueSeverity.ERROR for issue in result.issues
        )
        source_reference = _common_source_reference(result)
        metadata = (
            {"source_reference": source_reference} if source_reference is not None else {}
        )

        return NormalizationResultSummary(
            record_count=len(result.records),
            issue_count=len(result.issues),
            source_id=source_reference,
            is_artificial=True,
            metadata=metadata,
            warning_count=warning_count,
            error_count=error_count,
        )


def _common_source_reference(result: NormalizationResult) -> str | None:
    references = {
        record.source_reference for record in result.records if record.source_reference
    }
    if len(references) == 1:
        return next(iter(references))
    return None
