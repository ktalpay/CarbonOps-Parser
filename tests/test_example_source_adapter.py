from pathlib import Path

from carbonfactor_parser.source_adapters import (
    ExampleSourceAdapter,
    SourceAdapterRegistry,
    SourceFamily,
    summarize_source_adapter_result,
)


FIXTURE_DIRECTORY = (
    Path(__file__).resolve().parents[0] / "fixtures" / "source_documents"
)


def _source_family() -> SourceFamily:
    return tuple(SourceFamily)[0]


def test_example_source_adapter_is_importable() -> None:
    adapter = ExampleSourceAdapter(
        directory_path=FIXTURE_DIRECTORY,
        source_family=_source_family(),
    )

    assert isinstance(adapter, ExampleSourceAdapter)


def test_example_source_adapter_discovers_deterministic_fixture_documents() -> None:
    adapter = ExampleSourceAdapter(
        directory_path=FIXTURE_DIRECTORY,
        source_family=_source_family(),
        source_key="artificial",
        allowed_extensions=(".csv", ".json"),
    )

    result = adapter.discover()

    assert result.warnings == ()
    assert [document.source_name for document in result.documents] == [
        "artificial:sample_factors.csv",
        "artificial:sample_metadata.json",
    ]
    assert [Path(document.file_reference or "").name for document in result.documents] == [
        "sample_factors.csv",
        "sample_metadata.json",
    ]


def test_example_source_adapter_ignores_directories(tmp_path) -> None:
    (tmp_path / "nested.csv").mkdir()
    (tmp_path / "source.csv").write_text("source", encoding="utf-8")

    adapter = ExampleSourceAdapter(
        directory_path=tmp_path,
        source_family=_source_family(),
    )

    result = adapter.discover()

    assert [document.source_name for document in result.documents] == [
        "example_source:source.csv"
    ]


def test_example_source_adapter_respects_extension_filtering() -> None:
    adapter = ExampleSourceAdapter(
        directory_path=FIXTURE_DIRECTORY,
        source_family=_source_family(),
        allowed_extensions="txt",
    )

    result = adapter.discover()

    assert [document.source_name for document in result.documents] == [
        "example_source:notes.txt"
    ]


def test_example_source_adapter_respects_name_filtering() -> None:
    adapter = ExampleSourceAdapter(
        directory_path=FIXTURE_DIRECTORY,
        source_family=_source_family(),
        allowed_name_prefixes="sample_meta",
    )

    result = adapter.discover()

    assert [document.source_name for document in result.documents] == [
        "example_source:sample_metadata.json"
    ]


def test_example_source_adapter_handles_missing_directory_with_warning(tmp_path) -> None:
    missing_directory = tmp_path / "missing"
    adapter = ExampleSourceAdapter(
        directory_path=missing_directory,
        source_family=_source_family(),
    )

    result = adapter.discover()

    assert result.documents == ()
    assert result.warnings == (
        f"Example source directory not found: {missing_directory}",
    )


def test_example_source_adapter_handles_empty_directory(tmp_path) -> None:
    adapter = ExampleSourceAdapter(
        directory_path=tmp_path,
        source_family=_source_family(),
    )

    result = adapter.discover()

    assert result.documents == ()
    assert result.warnings == ()


def test_example_source_adapter_metadata_is_consistent() -> None:
    adapter = ExampleSourceAdapter(
        directory_path=FIXTURE_DIRECTORY,
        source_family=_source_family(),
        source_key="artificial",
        allowed_extensions=(".csv",),
    )

    document = adapter.discover().documents[0]

    assert document.source_family == _source_family()
    assert document.source_name == "artificial:sample_factors.csv"
    assert document.source_url is None
    assert document.file_reference == str(FIXTURE_DIRECTORY / "sample_factors.csv")


def test_example_source_adapter_integrates_with_registry() -> None:
    adapter = ExampleSourceAdapter(
        directory_path=FIXTURE_DIRECTORY,
        source_family=_source_family(),
    )
    registry = SourceAdapterRegistry()

    registry.register(adapter)

    assert registry.get(_source_family()) is adapter


def test_example_source_adapter_works_with_summary_helper() -> None:
    adapter = ExampleSourceAdapter(
        directory_path=FIXTURE_DIRECTORY,
        source_family=_source_family(),
        allowed_extensions=(".csv", ".json"),
    )

    summary = summarize_source_adapter_result(adapter.discover())

    assert summary.document_count == 2
    assert summary.file_extensions == (".csv", ".json")
    assert summary.has_documents is True
    assert summary.is_clean is True


def test_example_source_adapter_does_not_parse_fixture_contents() -> None:
    adapter = ExampleSourceAdapter(
        directory_path=FIXTURE_DIRECTORY,
        source_family=_source_family(),
        allowed_extensions=(".csv", ".json", ".txt"),
    )

    result = adapter.discover()
    parse_result = adapter.parse(result.documents[0])

    assert "factor_id" not in str(result)
    assert "Example fixture metadata" not in str(result)
    assert parse_result.records == ()
    assert parse_result.rejected_records == ()
    assert parse_result.warnings == ()
    assert parse_result.normalization_notes == ()
