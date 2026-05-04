"""Intentional public exports for normalization contracts."""

from carbonfactor_parser.normalization.contracts import (
    NormalizationIssue,
    NormalizationIssueSeverity,
    NormalizationResult,
    NormalizedRecord,
)
from carbonfactor_parser.normalization.executor import ArtificialNormalizationExecutor
from carbonfactor_parser.normalization.handoff import (
    ParserNormalizationHandoff,
    ParserNormalizationHandoffEntry,
    build_parser_normalization_handoff,
)
from carbonfactor_parser.normalization.summary import NormalizationResultSummary

__all__ = (
    "NormalizationIssue",
    "NormalizationIssueSeverity",
    "NormalizationResult",
    "NormalizationResultSummary",
    "NormalizedRecord",
    "ArtificialNormalizationExecutor",
    "ParserNormalizationHandoff",
    "ParserNormalizationHandoffEntry",
    "build_parser_normalization_handoff",
)
