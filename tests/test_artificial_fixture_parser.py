from carbonfactor_parser.parsers import (
    ArtificialFixtureParser,
    ParserInputMapping,
    ParserInputMappingEntry,
    ParserResult,
)
from carbonfactor_parser.source_adapters import SourceFamily


def _mapping() -> ParserInputMapping:
    return ParserInputMapping(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="fixture_parser_input_mapping",
        document_count=2,
        parser_hint="artificial-fixture",
        entries=(
            ParserInputMappingEntry(
                source_family=SourceFamily.DEFRA_DESNZ,
                source_name="defra_desnz:metadata.json",
                document_id="defra_desnz:metadata.json",
                document_path="/tmp/metadata.json",
                file_name="metadata.json",
                file_extension=".json",
                parser_hint="artificial-fixture",
            ),
            ParserInputMappingEntry(
                source_family=SourceFamily.DEFRA_DESNZ,
                source_name="defra_desnz:sample.csv",
                document_id="defra_desnz:sample.csv",
                document_path="/tmp/sample.csv",
                file_name="sample.csv",
                file_extension=".csv",
                parser_hint="artificial-fixture",
            ),
        ),
    )


def test_artificial_fixture_parser_is_importable() -> None:
    parser = ArtificialFixtureParser()

    assert isinstance(parser, ArtificialFixtureParser)


def test_parser_accepts_input_mapping_and_returns_parser_result() -> None:
    result = ArtificialFixtureParser().parse_mapping(_mapping())

    assert isinstance(result, ParserResult)
    assert result.source_document.source_family == SourceFamily.DEFRA_DESNZ
    assert result.source_document.source_name == "fixture_parser_input_mapping"


def test_parser_creates_one_artificial_record_per_mapping_entry() -> None:
    result = ArtificialFixtureParser().parse_mapping(_mapping())

    assert result.summary.record_count == 2
    assert result.records == (
        {
            "record_id": "defra_desnz:metadata.json",
            "file_name": "metadata.json",
            "file_extension": ".json",
            "source_label": "defra_desnz:metadata.json",
            "value_label": "artificial-fixture",
        },
        {
            "record_id": "defra_desnz:sample.csv",
            "file_name": "sample.csv",
            "file_extension": ".csv",
            "source_label": "defra_desnz:sample.csv",
            "value_label": "artificial-fixture",
        },
    )


def test_parser_returns_deterministic_records() -> None:
    parser = ArtificialFixtureParser()

    first = parser.parse_mapping(_mapping())
    second = parser.parse_mapping(_mapping())

    assert first.records == second.records


def test_empty_mapping_returns_empty_parser_result() -> None:
    mapping = ParserInputMapping(
        source_family=None,
        source_name="fixture_parser_input_mapping",
        document_count=0,
        entries=(),
    )

    result = ArtificialFixtureParser().parse_mapping(mapping)

    assert result.records == ()
    assert result.issues == ()
    assert result.summary.record_count == 0
    assert result.summary.is_clean is True
    assert result.source_document.source_family == SourceFamily.DEFRA_DESNZ


def test_parser_does_not_require_or_perform_file_io(monkeypatch, tmp_path) -> None:
    missing_path = tmp_path / "metadata.json"
    mapping = ParserInputMapping(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="fixture_parser_input_mapping",
        document_count=1,
        entries=(
            ParserInputMappingEntry(
                source_family=SourceFamily.DEFRA_DESNZ,
                source_name="defra_desnz:metadata.json",
                document_id="defra_desnz:metadata.json",
                document_path=str(missing_path),
                file_name="metadata.json",
                file_extension=".json",
            ),
        ),
    )

    def fail_open(*args, **kwargs):
        raise AssertionError("parser should not open files")

    monkeypatch.setattr("builtins.open", fail_open)

    result = ArtificialFixtureParser().parse_mapping(mapping)

    assert result.summary.record_count == 1
    assert not missing_path.exists()


def test_parser_records_do_not_use_defra_desnz_schema_fields() -> None:
    result = ArtificialFixtureParser().parse_mapping(_mapping())
    records_text = str(result.records).lower()

    assert "activity" not in records_text
    assert "unit" not in records_text
    assert "scope" not in records_text
    assert "kgco2e" not in records_text
