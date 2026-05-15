from pathlib import Path

from carbonfactor_parser.source_adapters import (
    DefraDesnzSourceAdapter,
    SourceAdapterRegistry,
    SourceFamily,
    summarize_source_adapter_result,
)


FIXTURE_DIRECTORY = (
    Path(__file__).resolve().parents[0] / "fixtures" / "source_documents" / "defra_desnz"
)

EXPECTED_FIXTURE_FILE_NAMES = [
    "defra_desnz_malformed_factors.csv",
    "defra_desnz_metadata.json",
    "defra_desnz_normalized_factors.csv",
    "defra_desnz_sample_factors.csv",
]

EXPECTED_FIXTURE_SOURCE_NAMES = [
    f"defra_desnz:{file_name}" for file_name in EXPECTED_FIXTURE_FILE_NAMES
]


def test_defra_desnz_source_adapter_is_importable() -> None:
    adapter = DefraDesnzSourceAdapter(directory_path=FIXTURE_DIRECTORY)

    assert isinstance(adapter, DefraDesnzSourceAdapter)


def test_defra_desnz_source_adapter_discovers_deterministic_fixture_documents() -> None:
    adapter = DefraDesnzSourceAdapter(directory_path=FIXTURE_DIRECTORY)

    result = adapter.discover()

    assert result.warnings == ()
    assert [document.source_name for document in result.documents] == (
        EXPECTED_FIXTURE_SOURCE_NAMES
    )
    assert [Path(document.file_reference or "").name for document in result.documents] == [
        *EXPECTED_FIXTURE_FILE_NAMES
    ]


def test_defra_desnz_source_adapter_excludes_unrelated_fixture_files() -> None:
    adapter = DefraDesnzSourceAdapter(directory_path=FIXTURE_DIRECTORY)

    result = adapter.discover()

    assert "notes.txt" not in {
        Path(document.file_reference or "").name for document in result.documents
    }


def test_defra_desnz_source_adapter_ignores_directories(tmp_path) -> None:
    (tmp_path / "defra_desnz_nested.csv").mkdir()
    (tmp_path / "defra_desnz_source.csv").write_text("source", encoding="utf-8")

    adapter = DefraDesnzSourceAdapter(directory_path=tmp_path)

    result = adapter.discover()

    assert [document.source_name for document in result.documents] == [
        "defra_desnz:defra_desnz_source.csv"
    ]


def test_defra_desnz_source_adapter_respects_extension_filtering() -> None:
    adapter = DefraDesnzSourceAdapter(
        directory_path=FIXTURE_DIRECTORY,
        allowed_extensions="json",
    )

    result = adapter.discover()

    assert [document.source_name for document in result.documents] == [
        "defra_desnz:defra_desnz_metadata.json"
    ]


def test_defra_desnz_source_adapter_can_relax_name_filtering() -> None:
    adapter = DefraDesnzSourceAdapter(
        directory_path=FIXTURE_DIRECTORY,
        allowed_extensions=".txt",
        allowed_name_prefixes=None,
    )

    result = adapter.discover()

    assert [document.source_name for document in result.documents] == [
        "defra_desnz:notes.txt"
    ]


def test_defra_desnz_source_adapter_handles_missing_directory_with_warning(
    tmp_path,
) -> None:
    missing_directory = tmp_path / "missing"
    adapter = DefraDesnzSourceAdapter(directory_path=missing_directory)

    result = adapter.discover()

    assert result.documents == ()
    assert result.warnings == (
        f"DEFRA/DESNZ source directory not found: {missing_directory}",
    )


def test_defra_desnz_source_adapter_handles_empty_directory(tmp_path) -> None:
    adapter = DefraDesnzSourceAdapter(directory_path=tmp_path)

    result = adapter.discover()

    assert result.documents == ()
    assert result.warnings == ()


def test_defra_desnz_source_adapter_metadata_is_consistent() -> None:
    adapter = DefraDesnzSourceAdapter(
        directory_path=FIXTURE_DIRECTORY,
        allowed_extensions=(".csv",),
    )

    document = adapter.discover().documents[0]

    assert document.source_family == SourceFamily.DEFRA_DESNZ
    assert document.source_name == "defra_desnz:defra_desnz_malformed_factors.csv"
    assert document.source_url is None
    assert document.file_reference == (
        str(FIXTURE_DIRECTORY / "defra_desnz_malformed_factors.csv")
    )


def test_defra_desnz_source_adapter_integrates_with_registry() -> None:
    adapter = DefraDesnzSourceAdapter(directory_path=FIXTURE_DIRECTORY)
    registry = SourceAdapterRegistry()

    registry.register(adapter)

    assert registry.get(SourceFamily.DEFRA_DESNZ) is adapter


def test_defra_desnz_source_adapter_works_with_summary_helper() -> None:
    adapter = DefraDesnzSourceAdapter(directory_path=FIXTURE_DIRECTORY)

    summary = summarize_source_adapter_result(adapter.discover())

    assert summary.document_count == 4
    assert summary.file_extensions == (".csv", ".json")
    assert summary.source_families == (SourceFamily.DEFRA_DESNZ,)
    assert summary.has_documents is True
    assert summary.is_clean is True


def test_defra_desnz_source_adapter_does_not_parse_fixture_contents() -> None:
    adapter = DefraDesnzSourceAdapter(directory_path=FIXTURE_DIRECTORY)

    result = adapter.discover()
    parse_result = adapter.parse(result.documents[0])

    assert "Artificial local fixture" not in str(result)
    assert "adapter skeleton discovery" not in str(result)
    assert parse_result.records == ()
    assert parse_result.rejected_records == ()
    assert parse_result.warnings == ()
    assert parse_result.normalization_notes == ()
