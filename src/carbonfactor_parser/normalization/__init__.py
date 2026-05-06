"""Intentional public exports for normalization contracts."""

from carbonfactor_parser.normalization.contracts import (
    NormalizationIssue,
    NormalizationIssueSeverity,
    NormalizationResult,
    NormalizedRecord,
)
from carbonfactor_parser.normalization.executor import ArtificialNormalizationExecutor
from carbonfactor_parser.normalization.handoff import (
    ParserExecutionNormalizationHandoff,
    ParserExecutionNormalizationHandoffIssue,
    ParserExecutionNormalizationHandoffResult,
    ParserExecutionNormalizationHandoffStatus,
    ParserNormalizationHandoff,
    ParserNormalizationHandoffEntry,
    build_parser_execution_normalization_handoff,
    build_parser_normalization_handoff,
)
from carbonfactor_parser.normalization.summary import NormalizationResultSummary
from carbonfactor_parser.normalization.summary_builder import (
    ArtificialNormalizationSummaryBuilder,
)

__all__ = (
    "NormalizationIssue",
    "NormalizationIssueSeverity",
    "NormalizationResult",
    "NormalizationResultSummary",
    "NormalizedRecord",
    "ArtificialNormalizationExecutor",
    "ArtificialNormalizationSummaryBuilder",
    "ParserExecutionNormalizationHandoff",
    "ParserExecutionNormalizationHandoffIssue",
    "ParserExecutionNormalizationHandoffResult",
    "ParserExecutionNormalizationHandoffStatus",
    "ParserNormalizationHandoff",
    "ParserNormalizationHandoffEntry",
    "build_parser_execution_normalization_handoff",
    "build_parser_normalization_handoff",
)
