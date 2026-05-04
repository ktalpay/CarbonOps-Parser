import carbonfactor_parser.normalization as normalization
from carbonfactor_parser.normalization import (
    ArtificialNormalizationExecutor,
    NormalizationIssue,
    NormalizationIssueSeverity,
    NormalizationResult,
    NormalizationResultSummary,
    NormalizedRecord,
    ParserNormalizationHandoff,
    ParserNormalizationHandoffEntry,
    build_parser_normalization_handoff,
)


EXPECTED_PUBLIC_SYMBOLS = (
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


def test_expected_normalization_public_symbols_import_from_package() -> None:
    imported_symbols = {
        "NormalizationIssue": NormalizationIssue,
        "NormalizationIssueSeverity": NormalizationIssueSeverity,
        "NormalizationResult": NormalizationResult,
        "NormalizationResultSummary": NormalizationResultSummary,
        "NormalizedRecord": NormalizedRecord,
        "ArtificialNormalizationExecutor": ArtificialNormalizationExecutor,
        "ParserNormalizationHandoff": ParserNormalizationHandoff,
        "ParserNormalizationHandoffEntry": ParserNormalizationHandoffEntry,
        "build_parser_normalization_handoff": build_parser_normalization_handoff,
    }

    assert tuple(imported_symbols) == EXPECTED_PUBLIC_SYMBOLS
    assert imported_symbols == {
        name: getattr(normalization, name) for name in EXPECTED_PUBLIC_SYMBOLS
    }


def test_normalization_all_lists_expected_public_symbols() -> None:
    assert normalization.__all__ == EXPECTED_PUBLIC_SYMBOLS


def test_normalization_all_names_resolve_to_package_attributes() -> None:
    for name in normalization.__all__:
        assert hasattr(normalization, name)


def test_normalization_all_excludes_internal_module_names() -> None:
    assert "contracts" not in normalization.__all__
    assert "executor" not in normalization.__all__
    assert "handoff" not in normalization.__all__
    assert all(not name.startswith("_") for name in normalization.__all__)
