from carbonfactor_parser.parsers import (
    ExampleSourceSpecificParser,
    ParserIssueSeverity,
    ParserResult,
)
from carbonfactor_parser.source_adapters import SourceDocument, SourceFamily


def _parser() -> ExampleSourceSpecificParser:
    return ExampleSourceSpecificParser(source_family=SourceFamily.GHG_PROTOCOL)


def _records() -> tuple[dict[str, str], ...]:
    return (
        {
            "record_id": "record-1",
            "source_label": "example-source",
            "value_label": "one",
        },
        {
            "record_id": "record-2",
            "source_label": "example-source",
            "value_label": "two",
        },
    )


def test_example_source_specific_parser_is_importable() -> None:
    parser = _parser()

    assert isinstance(parser, ExampleSourceSpecificParser)


def test_parse_records_returns_parser_result() -> None:
    result = _parser().parse_records(_records())

    assert isinstance(result, ParserResult)
    assert result.source_document.source_family == SourceFamily.GHG_PROTOCOL
    assert result.source_document.source_name == "fixture:example_source_specific"


def test_parse_records_returns_deterministic_records() -> None:
    parser = _parser()

    first = parser.parse_records(_records())
    second = parser.parse_records(_records())

    assert first.records == second.records
    assert first.records == _records()


def test_parse_empty_returns_empty_parser_result() -> None:
    result = _parser().parse_empty()

    assert result.records == ()
    assert result.issues == ()
    assert result.summary.record_count == 0
    assert result.summary.is_clean is True


def test_warning_issue_scenario_counts_warning() -> None:
    parser = _parser()
    result = parser.parse_empty(issues=(parser.warning_issue(),))

    assert result.issues[0].severity == ParserIssueSeverity.WARNING
    assert result.summary.warning_count == 1
    assert result.summary.error_count == 0
    assert result.summary.is_clean is False


def test_error_issue_scenario_counts_error() -> None:
    parser = _parser()
    result = parser.parse_empty(issues=(parser.error_issue(),))

    assert result.issues[0].severity == ParserIssueSeverity.ERROR
    assert result.summary.warning_count == 0
    assert result.summary.error_count == 1
    assert result.summary.has_errors is True


def test_parser_does_not_require_or_perform_file_io(tmp_path) -> None:
    missing_path = tmp_path / "source.csv"
    parser = ExampleSourceSpecificParser(
        source_family=SourceFamily.GHG_PROTOCOL,
        source_document=SourceDocument(
            source_family=SourceFamily.GHG_PROTOCOL,
            source_name="fixture:example-source",
            file_reference=str(missing_path),
        ),
    )

    result = parser.parse_records(_records())

    assert result.summary.record_count == 2
    assert not missing_path.exists()


def test_parser_uses_caller_provided_source_document() -> None:
    source_document = SourceDocument(
        source_family=SourceFamily.IPCC_EFDB,
        source_name="fixture:custom-example-source",
    )

    result = ExampleSourceSpecificParser(
        source_family=SourceFamily.GHG_PROTOCOL,
        source_document=source_document,
    ).parse_empty()

    assert result.source_document is source_document


def test_parser_uses_generic_artificial_record_fields() -> None:
    result = _parser().parse_records(_records())

    assert tuple(result.records[0]) == ("record_id", "source_label", "value_label")
    assert "factor" not in str(result.records).lower()
    assert "defra" not in str(result.records).lower()
    assert "desnz" not in str(result.records).lower()


def test_parser_does_not_use_real_source_names() -> None:
    result = _parser().parse_records(_records())

    assert "ghg" not in result.source_document.source_name.lower()
    assert "protocol" not in result.source_document.source_name.lower()
    assert "defra" not in result.source_document.source_name.lower()
    assert "desnz" not in result.source_document.source_name.lower()
