import carbonfactor_parser.parsers as parsers
from carbonfactor_parser.parsers import (
    ArtificialFixtureParser,
    DefraDesnzParser,
    ExampleInMemoryParser,
    ExampleSourceSpecificParser,
    ParserInputMapping,
    ParserInputMappingEntry,
    ParserIssue,
    ParserIssueSeverity,
    ParserResult,
    ParserResultSummary,
    build_fixture_parser_input_mapping,
)


EXPECTED_PUBLIC_SYMBOLS = (
    "ArtificialFixtureParser",
    "DefraDesnzParser",
    "ExampleInMemoryParser",
    "ExampleSourceSpecificParser",
    "ParserInputMapping",
    "ParserInputMappingEntry",
    "ParserIssue",
    "ParserIssueSeverity",
    "ParserResult",
    "ParserResultSummary",
    "build_fixture_parser_input_mapping",
)


def test_expected_parser_public_symbols_import_from_package() -> None:
    imported_symbols = {
        "ArtificialFixtureParser": ArtificialFixtureParser,
        "DefraDesnzParser": DefraDesnzParser,
        "ExampleInMemoryParser": ExampleInMemoryParser,
        "ExampleSourceSpecificParser": ExampleSourceSpecificParser,
        "ParserInputMapping": ParserInputMapping,
        "ParserInputMappingEntry": ParserInputMappingEntry,
        "ParserIssue": ParserIssue,
        "ParserIssueSeverity": ParserIssueSeverity,
        "ParserResult": ParserResult,
        "ParserResultSummary": ParserResultSummary,
        "build_fixture_parser_input_mapping": build_fixture_parser_input_mapping,
    }

    assert tuple(imported_symbols) == EXPECTED_PUBLIC_SYMBOLS
    assert imported_symbols == {
        name: getattr(parsers, name) for name in EXPECTED_PUBLIC_SYMBOLS
    }


def test_parser_all_lists_expected_public_symbols() -> None:
    assert parsers.__all__ == EXPECTED_PUBLIC_SYMBOLS


def test_parser_all_names_resolve_to_package_attributes() -> None:
    for name in parsers.__all__:
        assert hasattr(parsers, name)


def test_parser_all_excludes_internal_module_names() -> None:
    assert "contracts" not in parsers.__all__
    assert "defra_desnz_parser" not in parsers.__all__
    assert "example_parser" not in parsers.__all__
    assert "example_source_specific_parser" not in parsers.__all__
    assert "fixture_parser" not in parsers.__all__
    assert "input_mapping" not in parsers.__all__
    assert all(not name.startswith("_") for name in parsers.__all__)
