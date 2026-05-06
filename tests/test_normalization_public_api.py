import carbonfactor_parser.normalization as normalization
from carbonfactor_parser.normalization import (
    contracts,
    executor,
    handoff,
    input,
    summary_builder,
)
from carbonfactor_parser.normalization import (
    ArtificialNormalizationExecutor,
    ArtificialNormalizationSummaryBuilder,
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
    create_normalization_input_from_raw_payload,
    create_normalization_input_record_from_raw_record,
    validate_normalization_input,
    validate_normalization_input_record,
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

EXPECTED_PUBLIC_EXPORTS = {
    "NormalizationIssue": contracts.NormalizationIssue,
    "NormalizationIssueSeverity": contracts.NormalizationIssueSeverity,
    "NormalizationResult": contracts.NormalizationResult,
    "NormalizationResultSummary": SummaryModuleNormalizationResultSummary,
    "NormalizedRecord": contracts.NormalizedRecord,
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
    "create_normalization_input_from_raw_payload": (
        input.create_normalization_input_from_raw_payload
    ),
    "create_normalization_input_record_from_raw_record": (
        input.create_normalization_input_record_from_raw_record
    ),
    "validate_normalization_input": input.validate_normalization_input,
    "validate_normalization_input_record": (
        input.validate_normalization_input_record
    ),
}


def test_expected_normalization_public_symbols_import_from_package() -> None:
    imported_symbols = {
        "NormalizationIssue": NormalizationIssue,
        "NormalizationIssueSeverity": NormalizationIssueSeverity,
        "NormalizationResult": NormalizationResult,
        "NormalizationResultSummary": NormalizationResultSummary,
        "NormalizedRecord": NormalizedRecord,
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
        "create_normalization_input_from_raw_payload": (
            create_normalization_input_from_raw_payload
        ),
        "create_normalization_input_record_from_raw_record": (
            create_normalization_input_record_from_raw_record
        ),
        "validate_normalization_input": validate_normalization_input,
        "validate_normalization_input_record": validate_normalization_input_record,
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
    assert "executor" not in normalization.__all__
    assert "handoff" not in normalization.__all__
    assert "input" not in normalization.__all__
    assert "summary" not in normalization.__all__
    assert "summary_builder" not in normalization.__all__
    assert all(not name.startswith("_") for name in normalization.__all__)
