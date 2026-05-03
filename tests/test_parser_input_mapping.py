from pathlib import Path

from carbonfactor_parser.parsers import (
    ParserInputMapping,
    ParserInputMappingEntry,
    build_fixture_parser_input_mapping,
)
from carbonfactor_parser.source_adapters import (
    DefraDesnzSourceAdapter,
    SourceDocument,
    SourceFamily,
)


FIXTURE_DIRECTORY = (
    Path(__file__).resolve().parents[0] / "fixtures" / "source_documents" / "defra_desnz"
)


def test_mapping_can_be_created_from_no_documents() -> None:
    mapping = build_fixture_parser_input_mapping(())

    assert isinstance(mapping, ParserInputMapping)
    assert mapping.source_family is None
    assert mapping.source_name == "fixture_parser_input_mapping"
    assert mapping.document_count == 0
    assert mapping.entries == ()
    assert mapping.parser_hint is None
    assert mapping.is_artificial_fixture is True


def test_mapping_can_be_created_from_discovered_fixture_documents() -> None:
    documents = DefraDesnzSourceAdapter(directory_path=FIXTURE_DIRECTORY).discover().documents

    mapping = build_fixture_parser_input_mapping(documents)

    assert mapping.document_count == 2
    assert mapping.source_family == SourceFamily.DEFRA_DESNZ
    assert [entry.file_name for entry in mapping.entries] == [
        "defra_desnz_metadata.json",
        "defra_desnz_sample_factors.csv",
    ]


def test_mapping_entry_ordering_is_deterministic() -> None:
    documents = (
        SourceDocument(
            source_family=SourceFamily.IPCC_EFDB,
            source_name="fixture:z.csv",
            file_reference=str(FIXTURE_DIRECTORY / "z.csv"),
        ),
        SourceDocument(
            source_family=SourceFamily.DEFRA_DESNZ,
            source_name="fixture:a.json",
            file_reference=str(FIXTURE_DIRECTORY / "a.json"),
        ),
    )

    first = build_fixture_parser_input_mapping(documents)
    second = build_fixture_parser_input_mapping(reversed(documents))

    assert first.entries == second.entries
    assert [entry.file_name for entry in first.entries] == [
        "a.json",
        "z.csv",
    ]
    assert first.source_family is None


def test_mapping_derives_file_names_and_extensions() -> None:
    document = SourceDocument(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="fixture:source.CSV",
        file_reference=str(FIXTURE_DIRECTORY / "source.CSV"),
    )

    mapping = build_fixture_parser_input_mapping((document,))
    entry = mapping.entries[0]

    assert isinstance(entry, ParserInputMappingEntry)
    assert entry.document_id == "fixture:source.CSV"
    assert entry.document_path == str(FIXTURE_DIRECTORY / "source.CSV")
    assert entry.file_name == "source.CSV"
    assert entry.file_extension == ".csv"


def test_mapping_uses_source_name_when_file_reference_is_missing() -> None:
    document = SourceDocument(
        source_family=SourceFamily.GHG_PROTOCOL,
        source_name="fixture:source.txt",
    )

    mapping = build_fixture_parser_input_mapping((document,))
    entry = mapping.entries[0]

    assert entry.document_path is None
    assert entry.file_name == "fixture:source.txt"
    assert entry.file_extension == ".txt"


def test_mapping_marks_entries_as_artificial_fixtures() -> None:
    document = SourceDocument(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="fixture:source.csv",
        file_reference=str(FIXTURE_DIRECTORY / "source.csv"),
    )

    mapping = build_fixture_parser_input_mapping((document,))

    assert mapping.is_artificial_fixture is True
    assert mapping.entries[0].is_artificial_fixture is True


def test_mapping_preserves_parser_hint_without_interpreting_it() -> None:
    document = SourceDocument(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="fixture:source.csv",
        file_reference=str(FIXTURE_DIRECTORY / "source.csv"),
    )

    mapping = build_fixture_parser_input_mapping(
        (document,),
        parser_hint="artificial-table",
    )

    assert mapping.parser_hint == "artificial-table"
    assert mapping.entries[0].parser_hint == "artificial-table"


def test_mapping_does_not_read_fixture_contents(monkeypatch, tmp_path) -> None:
    missing_path = tmp_path / "missing.csv"
    document = SourceDocument(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="fixture:missing.csv",
        file_reference=str(missing_path),
    )

    def fail_open(*args, **kwargs):
        raise AssertionError("mapping helper should not open files")

    monkeypatch.setattr("builtins.open", fail_open)

    mapping = build_fixture_parser_input_mapping((document,))

    assert mapping.document_count == 1
    assert not missing_path.exists()


def test_mapping_works_with_defra_desnz_fixture_documents_without_schema_assumptions() -> None:
    documents = DefraDesnzSourceAdapter(directory_path=FIXTURE_DIRECTORY).discover().documents

    mapping = build_fixture_parser_input_mapping(documents)

    mapping_text = str(mapping).lower()
    assert "activity" not in mapping_text
    assert "unit" not in mapping_text
    assert "scope" not in mapping_text
    assert "kgco2e" not in mapping_text
