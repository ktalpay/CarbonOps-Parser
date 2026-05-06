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
from carbonfactor_parser.normalization.input import (
    NormalizationInput,
    NormalizationInputBuildResult,
    NormalizationInputBuildStatus,
    NormalizationInputIssue,
    NormalizationInputRecord,
    NormalizationInputValidationResult,
    build_normalization_input_from_parser_execution_handoff,
    build_normalization_input_from_raw_payload,
    create_normalization_input_from_raw_payload,
    create_normalization_input_record_from_raw_record,
    validate_normalization_input,
    validate_normalization_input_record,
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
    "NormalizationInput",
    "NormalizationInputBuildResult",
    "NormalizationInputBuildStatus",
    "NormalizationInputIssue",
    "NormalizationInputRecord",
    "NormalizationInputValidationResult",
    "ParserExecutionNormalizationHandoff",
    "ParserExecutionNormalizationHandoffIssue",
    "ParserExecutionNormalizationHandoffResult",
    "ParserExecutionNormalizationHandoffStatus",
    "ParserNormalizationHandoff",
    "ParserNormalizationHandoffEntry",
    "build_normalization_input_from_parser_execution_handoff",
    "build_normalization_input_from_raw_payload",
    "build_parser_execution_normalization_handoff",
    "build_parser_normalization_handoff",
    "create_normalization_input_from_raw_payload",
    "create_normalization_input_record_from_raw_record",
    "validate_normalization_input",
    "validate_normalization_input_record",
)
