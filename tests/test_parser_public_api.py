import carbonfactor_parser.parsers as parsers
from carbonfactor_parser.parsers import (
    ParserIssue,
    ParserIssueSeverity,
    ParserResult,
    ParserResultSummary,
)


EXPECTED_PUBLIC_SYMBOLS = (
    "ParserIssue",
    "ParserIssueSeverity",
    "ParserResult",
    "ParserResultSummary",
)


def test_expected_parser_public_symbols_import_from_package() -> None:
    imported_symbols = {
        "ParserIssue": ParserIssue,
        "ParserIssueSeverity": ParserIssueSeverity,
        "ParserResult": ParserResult,
        "ParserResultSummary": ParserResultSummary,
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
    assert all(not name.startswith("_") for name in parsers.__all__)
