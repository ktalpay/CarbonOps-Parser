import carbonfactor_parser.normalization as normalization
from carbonfactor_parser.normalization import contracts, executor, handoff, summary_builder
from carbonfactor_parser.normalization import (
    ArtificialNormalizationExecutor,
    ArtificialNormalizationSummaryBuilder,
    NormalizationIssue,
    NormalizationIssueSeverity,
    NormalizationResult,
    NormalizationResultSummary,
    NormalizedRecord,
    ParserNormalizationHandoff,
    ParserNormalizationHandoffEntry,
    build_parser_normalization_handoff,
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
    "ParserNormalizationHandoff",
    "ParserNormalizationHandoffEntry",
    "build_parser_normalization_handoff",
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
    "ParserNormalizationHandoff": handoff.ParserNormalizationHandoff,
    "ParserNormalizationHandoffEntry": handoff.ParserNormalizationHandoffEntry,
    "build_parser_normalization_handoff": handoff.build_parser_normalization_handoff,
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
        "ParserNormalizationHandoff": ParserNormalizationHandoff,
        "ParserNormalizationHandoffEntry": ParserNormalizationHandoffEntry,
        "build_parser_normalization_handoff": build_parser_normalization_handoff,
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
    assert "summary" not in normalization.__all__
    assert "summary_builder" not in normalization.__all__
    assert all(not name.startswith("_") for name in normalization.__all__)
