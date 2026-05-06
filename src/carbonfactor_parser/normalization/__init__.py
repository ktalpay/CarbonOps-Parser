"""Intentional public exports for normalization contracts."""

from carbonfactor_parser.normalization.contracts import (
    NormalizationIssue,
    NormalizationIssueSeverity,
    NormalizationResult,
    NormalizedRecord,
)
from carbonfactor_parser.normalization.defra_desnz_mapper import (
    DEFRA_DESNZ_MINIMAL_NORMALIZATION_FIELDS,
    DefraDesnzNormalizationMappingResult,
    DefraDesnzNormalizationMappingStatus,
    map_defra_desnz_normalization_input,
    map_defra_desnz_normalization_input_record,
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
    "DEFRA_DESNZ_MINIMAL_NORMALIZATION_FIELDS",
    "DefraDesnzNormalizationMappingResult",
    "DefraDesnzNormalizationMappingStatus",
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
    "map_defra_desnz_normalization_input",
    "map_defra_desnz_normalization_input_record",
    "validate_normalization_input",
    "validate_normalization_input_record",
)
