from carbonfactor_parser.parsers import (
    ExampleInMemoryParser,
    ParserIssueSeverity,
    ParserResult,
)
from carbonfactor_parser.source_adapters import SourceDocument, SourceFamily


def _source_document() -> SourceDocument:
    return SourceDocument(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="fixture:in_memory_source",
    )


def test_example_in_memory_parser_is_importable() -> None:
    parser = ExampleInMemoryParser(source_document=_source_document())

    assert isinstance(parser, ExampleInMemoryParser)


def test_parse_records_returns_parser_result() -> None:
    result = ExampleInMemoryParser(source_document=_source_document()).parse_records(
        (
            {"record_id": "1", "category": "alpha", "value_label": "one"},
        )
    )

    assert isinstance(result, ParserResult)


def test_parse_records_returns_deterministic_records() -> None:
    records = (
        {"record_id": "2", "category": "beta", "value_label": "two"},
        {"record_id": "1", "category": "alpha", "value_label": "one"},
    )

    parser = ExampleInMemoryParser(source_document=_source_document())
    first = parser.parse_records(records)
    second = parser.parse_records(records)

    assert first.records == second.records
    assert first.records == records


def test_parse_empty_returns_empty_parser_result() -> None:
    result = ExampleInMemoryParser(source_document=_source_document()).parse_empty()

    assert result.records == ()
    assert result.issues == ()
    assert result.summary.record_count == 0
    assert result.summary.is_clean is True


def test_warning_issue_scenario_counts_warning() -> None:
    parser = ExampleInMemoryParser(source_document=_source_document())
    result = parser.parse_empty(issues=(parser.warning_issue(),))

    assert result.issues[0].severity == ParserIssueSeverity.WARNING
    assert result.summary.warning_count == 1
    assert result.summary.error_count == 0
    assert result.summary.is_clean is False


def test_error_issue_scenario_counts_error() -> None:
    parser = ExampleInMemoryParser(source_document=_source_document())
    result = parser.parse_empty(issues=(parser.error_issue(),))

    assert result.issues[0].severity == ParserIssueSeverity.ERROR
    assert result.summary.warning_count == 0
    assert result.summary.error_count == 1
    assert result.summary.has_errors is True


def test_parser_does_not_require_or_perform_file_io(tmp_path) -> None:
    missing_path = tmp_path / "source.csv"
    parser = ExampleInMemoryParser(
        source_document=SourceDocument(
            source_family=SourceFamily.DEFRA_DESNZ,
            source_name="fixture:source",
            file_reference=str(missing_path),
        )
    )

    result = parser.parse_records(
        ({"record_id": "1", "category": "alpha", "value_label": "one"},)
    )

    assert result.summary.record_count == 1
    assert not missing_path.exists()


def test_parser_uses_caller_provided_source_document() -> None:
    source_document = SourceDocument(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="fixture:custom",
    )

    result = ExampleInMemoryParser(source_document=source_document).parse_empty()

    assert result.source_document is source_document


def test_parser_uses_generic_artificial_record_fields() -> None:
    result = ExampleInMemoryParser(source_document=_source_document()).parse_records(
        (
            {"record_id": "1", "category": "alpha", "value_label": "one"},
        )
    )

    assert tuple(result.records[0]) == ("record_id", "category", "value_label")
    assert "defra" not in str(result.records).lower()
    assert "desnz" not in str(result.records).lower()
