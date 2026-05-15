import carbonfactor_parser.normalization as normalization
from carbonfactor_parser.normalization import (
    contracts,
    defra_desnz_mapper,
    executor,
    handoff,
    input,
    summary_builder,
)
from carbonfactor_parser.normalization import (
    ArtificialNormalizationExecutor,
    ArtificialNormalizationSummaryBuilder,
    DEFRA_DESNZ_MINIMAL_NORMALIZATION_FIELDS,
    DEFRA_DESNZ_NORMALIZED_MAPPING_FIELDS,
    DEFAULT_SUPPORTED_FACTOR_UNITS,
    REDACTED_DIAGNOSTIC_VALUE,
    DataQualityDiagnostic,
    DataQualityProvenanceContext,
    DataQualityValidationCheck,
    DataQualityValidationResult,
    DataQualityValidationSeverity,
    DefraDesnzNormalizationMappingResult,
    DefraDesnzNormalizationMappingStatus,
    NormalizationInput,
    NormalizationInputBuildResult,
    NormalizationInputBuildStatus,
    NormalizationInputIssue,
    NormalizationInputRecord,
    NormalizationInputValidationResult,
    NormalizationIssue,
    NormalizationIssueSeverity,
    NormalizationResult,
    NormalizationResultSummary,
    NormalizedRecord,
    ParserExecutionNormalizationHandoff,
    ParserExecutionNormalizationHandoffIssue,
    ParserExecutionNormalizationHandoffResult,
    ParserExecutionNormalizationHandoffStatus,
    ParserNormalizationHandoff,
    ParserNormalizationHandoffEntry,
    build_normalization_input_from_parser_execution_handoff,
    build_normalization_input_from_raw_payload,
    build_parser_execution_normalization_handoff,
    build_parser_normalization_handoff,
    create_data_quality_diagnostic,
    create_normalization_input_from_raw_payload,
    create_normalization_input_record_from_raw_record,
    map_defra_desnz_normalization_input,
    map_defra_desnz_normalization_input_record,
    validate_normalization_input,
    validate_normalization_input_record,
    validate_normalized_factor_output,
)
from carbonfactor_parser.normalization.summary import (
    NormalizationResultSummary as SummaryModuleNormalizationResultSummary,
)


EXPECTED_PUBLIC_SYMBOLS = (
    "NormalizationIssue",
    "NormalizationIssueSeverity",
    "NormalizationResult",
    "NormalizationResultSummary",
    "NormalizedRecord",
    "DEFAULT_SUPPORTED_FACTOR_UNITS",
    "REDACTED_DIAGNOSTIC_VALUE",
    "DataQualityDiagnostic",
    "DataQualityProvenanceContext",
    "DataQualityValidationCheck",
    "DataQualityValidationResult",
    "DataQualityValidationSeverity",
    "DEFRA_DESNZ_MINIMAL_NORMALIZATION_FIELDS",
    "DEFRA_DESNZ_NORMALIZED_MAPPING_FIELDS",
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
    "create_data_quality_diagnostic",
    "create_normalization_input_from_raw_payload",
    "create_normalization_input_record_from_raw_record",
    "map_defra_desnz_normalization_input",
    "map_defra_desnz_normalization_input_record",
    "validate_normalization_input",
    "validate_normalization_input_record",
    "validate_normalized_factor_output",
)

EXPECTED_PUBLIC_EXPORTS = {
    "NormalizationIssue": contracts.NormalizationIssue,
    "NormalizationIssueSeverity": contracts.NormalizationIssueSeverity,
    "NormalizationResult": contracts.NormalizationResult,
    "NormalizationResultSummary": SummaryModuleNormalizationResultSummary,
    "NormalizedRecord": contracts.NormalizedRecord,
    "DEFAULT_SUPPORTED_FACTOR_UNITS": normalization.DEFAULT_SUPPORTED_FACTOR_UNITS,
    "REDACTED_DIAGNOSTIC_VALUE": normalization.REDACTED_DIAGNOSTIC_VALUE,
    "DataQualityDiagnostic": normalization.DataQualityDiagnostic,
    "DataQualityProvenanceContext": normalization.DataQualityProvenanceContext,
    "DataQualityValidationCheck": normalization.DataQualityValidationCheck,
    "DataQualityValidationResult": normalization.DataQualityValidationResult,
    "DataQualityValidationSeverity": normalization.DataQualityValidationSeverity,
    "DEFRA_DESNZ_MINIMAL_NORMALIZATION_FIELDS": (
        defra_desnz_mapper.DEFRA_DESNZ_MINIMAL_NORMALIZATION_FIELDS
    ),
    "DEFRA_DESNZ_NORMALIZED_MAPPING_FIELDS": (
        defra_desnz_mapper.DEFRA_DESNZ_NORMALIZED_MAPPING_FIELDS
    ),
    "DefraDesnzNormalizationMappingResult": (
        defra_desnz_mapper.DefraDesnzNormalizationMappingResult
    ),
    "DefraDesnzNormalizationMappingStatus": (
        defra_desnz_mapper.DefraDesnzNormalizationMappingStatus
    ),
    "ArtificialNormalizationExecutor": executor.ArtificialNormalizationExecutor,
    "ArtificialNormalizationSummaryBuilder": (
        summary_builder.ArtificialNormalizationSummaryBuilder
    ),
    "NormalizationInput": input.NormalizationInput,
    "NormalizationInputBuildResult": input.NormalizationInputBuildResult,
    "NormalizationInputBuildStatus": input.NormalizationInputBuildStatus,
    "NormalizationInputIssue": input.NormalizationInputIssue,
    "NormalizationInputRecord": input.NormalizationInputRecord,
    "NormalizationInputValidationResult": input.NormalizationInputValidationResult,
    "ParserExecutionNormalizationHandoff": (
        handoff.ParserExecutionNormalizationHandoff
    ),
    "ParserExecutionNormalizationHandoffIssue": (
        handoff.ParserExecutionNormalizationHandoffIssue
    ),
    "ParserExecutionNormalizationHandoffResult": (
        handoff.ParserExecutionNormalizationHandoffResult
    ),
    "ParserExecutionNormalizationHandoffStatus": (
        handoff.ParserExecutionNormalizationHandoffStatus
    ),
    "ParserNormalizationHandoff": handoff.ParserNormalizationHandoff,
    "ParserNormalizationHandoffEntry": handoff.ParserNormalizationHandoffEntry,
    "build_normalization_input_from_parser_execution_handoff": (
        input.build_normalization_input_from_parser_execution_handoff
    ),
    "build_normalization_input_from_raw_payload": (
        input.build_normalization_input_from_raw_payload
    ),
    "build_parser_execution_normalization_handoff": (
        handoff.build_parser_execution_normalization_handoff
    ),
    "build_parser_normalization_handoff": handoff.build_parser_normalization_handoff,
    "create_data_quality_diagnostic": normalization.create_data_quality_diagnostic,
    "create_normalization_input_from_raw_payload": (
        input.create_normalization_input_from_raw_payload
    ),
    "create_normalization_input_record_from_raw_record": (
        input.create_normalization_input_record_from_raw_record
    ),
    "map_defra_desnz_normalization_input": (
        defra_desnz_mapper.map_defra_desnz_normalization_input
    ),
    "map_defra_desnz_normalization_input_record": (
        defra_desnz_mapper.map_defra_desnz_normalization_input_record
    ),
    "validate_normalization_input": input.validate_normalization_input,
    "validate_normalization_input_record": (
        input.validate_normalization_input_record
    ),
    "validate_normalized_factor_output": (
        normalization.validate_normalized_factor_output
    ),
}


def test_expected_normalization_public_symbols_import_from_package() -> None:
    imported_symbols = {
        "NormalizationIssue": NormalizationIssue,
        "NormalizationIssueSeverity": NormalizationIssueSeverity,
        "NormalizationResult": NormalizationResult,
        "NormalizationResultSummary": NormalizationResultSummary,
        "NormalizedRecord": NormalizedRecord,
        "DEFAULT_SUPPORTED_FACTOR_UNITS": DEFAULT_SUPPORTED_FACTOR_UNITS,
        "REDACTED_DIAGNOSTIC_VALUE": REDACTED_DIAGNOSTIC_VALUE,
        "DataQualityDiagnostic": DataQualityDiagnostic,
        "DataQualityProvenanceContext": DataQualityProvenanceContext,
        "DataQualityValidationCheck": DataQualityValidationCheck,
        "DataQualityValidationResult": DataQualityValidationResult,
        "DataQualityValidationSeverity": DataQualityValidationSeverity,
        "DEFRA_DESNZ_MINIMAL_NORMALIZATION_FIELDS": (
            DEFRA_DESNZ_MINIMAL_NORMALIZATION_FIELDS
        ),
        "DEFRA_DESNZ_NORMALIZED_MAPPING_FIELDS": (
            DEFRA_DESNZ_NORMALIZED_MAPPING_FIELDS
        ),
        "DefraDesnzNormalizationMappingResult": (
            DefraDesnzNormalizationMappingResult
        ),
        "DefraDesnzNormalizationMappingStatus": (
            DefraDesnzNormalizationMappingStatus
        ),
        "ArtificialNormalizationExecutor": ArtificialNormalizationExecutor,
        "ArtificialNormalizationSummaryBuilder": ArtificialNormalizationSummaryBuilder,
        "NormalizationInput": NormalizationInput,
        "NormalizationInputBuildResult": NormalizationInputBuildResult,
        "NormalizationInputBuildStatus": NormalizationInputBuildStatus,
        "NormalizationInputIssue": NormalizationInputIssue,
        "NormalizationInputRecord": NormalizationInputRecord,
        "NormalizationInputValidationResult": NormalizationInputValidationResult,
        "ParserExecutionNormalizationHandoff": ParserExecutionNormalizationHandoff,
        "ParserExecutionNormalizationHandoffIssue": (
            ParserExecutionNormalizationHandoffIssue
        ),
        "ParserExecutionNormalizationHandoffResult": (
            ParserExecutionNormalizationHandoffResult
        ),
        "ParserExecutionNormalizationHandoffStatus": (
            ParserExecutionNormalizationHandoffStatus
        ),
        "ParserNormalizationHandoff": ParserNormalizationHandoff,
        "ParserNormalizationHandoffEntry": ParserNormalizationHandoffEntry,
        "build_normalization_input_from_parser_execution_handoff": (
            build_normalization_input_from_parser_execution_handoff
        ),
        "build_normalization_input_from_raw_payload": (
            build_normalization_input_from_raw_payload
        ),
        "build_parser_execution_normalization_handoff": (
            build_parser_execution_normalization_handoff
        ),
        "build_parser_normalization_handoff": build_parser_normalization_handoff,
        "create_data_quality_diagnostic": create_data_quality_diagnostic,
        "create_normalization_input_from_raw_payload": (
            create_normalization_input_from_raw_payload
        ),
        "create_normalization_input_record_from_raw_record": (
            create_normalization_input_record_from_raw_record
        ),
        "map_defra_desnz_normalization_input": map_defra_desnz_normalization_input,
        "map_defra_desnz_normalization_input_record": (
            map_defra_desnz_normalization_input_record
        ),
        "validate_normalization_input": validate_normalization_input,
        "validate_normalization_input_record": validate_normalization_input_record,
        "validate_normalized_factor_output": validate_normalized_factor_output,
    }

    assert tuple(imported_symbols) == EXPECTED_PUBLIC_SYMBOLS
    assert imported_symbols == {
        name: getattr(normalization, name) for name in EXPECTED_PUBLIC_SYMBOLS
    }
    assert NormalizationResultSummary is SummaryModuleNormalizationResultSummary


def test_normalization_all_lists_expected_public_symbols() -> None:
    assert normalization.__all__ == EXPECTED_PUBLIC_SYMBOLS


def test_normalization_public_exports_match_origin_modules() -> None:
    assert {
        name: getattr(normalization, name) for name in EXPECTED_PUBLIC_SYMBOLS
    } == EXPECTED_PUBLIC_EXPORTS


def test_normalization_all_names_resolve_to_package_attributes() -> None:
    for name in normalization.__all__:
        assert hasattr(normalization, name)


def test_normalization_all_excludes_internal_module_names() -> None:
    assert "contracts" not in normalization.__all__
    assert "defra_desnz_mapper" not in normalization.__all__
    assert "executor" not in normalization.__all__
    assert "handoff" not in normalization.__all__
    assert "input" not in normalization.__all__
    assert "summary" not in normalization.__all__
    assert "summary_builder" not in normalization.__all__
    assert all(not name.startswith("_") for name in normalization.__all__)
