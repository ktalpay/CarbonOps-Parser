from carbonfactor_parser.source_adapters import (
    AdapterDiscoveryResult,
    AdapterParseResult,
    LocalFileSourceAdapter,
    SourceAdapter,
    SourceAdapterRegistry,
    SourceDocument,
    SourceFamily,
)


def test_local_file_source_adapter_satisfies_source_adapter_protocol(tmp_path) -> None:
    adapter = LocalFileSourceAdapter(directory_path=tmp_path)

    assert isinstance(adapter, SourceAdapter)


def test_local_adapter_returns_files_from_directory(tmp_path) -> None:
    first = tmp_path / "first.csv"
    second = tmp_path / "second.xlsx"
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")

    adapter = LocalFileSourceAdapter(
        directory_path=tmp_path,
        source_family=SourceFamily.DEFRA_DESNZ,
    )

    result = adapter.discover()

    assert isinstance(result, AdapterDiscoveryResult)
    assert result.warnings == ()
    assert [document.source_name for document in result.documents] == [
        "first.csv",
        "second.xlsx",
    ]
    assert [document.file_reference for document in result.documents] == [
        str(first),
        str(second),
    ]
    assert {document.source_family for document in result.documents} == {
        SourceFamily.DEFRA_DESNZ
    }


def test_local_adapter_returns_files_in_deterministic_order(tmp_path) -> None:
    for filename in ("zeta.csv", "alpha.csv", "middle.csv"):
        (tmp_path / filename).write_text(filename, encoding="utf-8")

    result = LocalFileSourceAdapter(directory_path=tmp_path).discover()

    assert [document.source_name for document in result.documents] == [
        "alpha.csv",
        "middle.csv",
        "zeta.csv",
    ]


def test_local_adapter_ignores_directories(tmp_path) -> None:
    nested_path = tmp_path / "nested"
    nested_path.mkdir()
    (nested_path / "nested.csv").write_text("nested", encoding="utf-8")
    (tmp_path / "source.csv").write_text("source", encoding="utf-8")

    result = LocalFileSourceAdapter(directory_path=tmp_path).discover()

    assert [document.source_name for document in result.documents] == ["source.csv"]


def test_local_adapter_filters_extensions(tmp_path) -> None:
    (tmp_path / "source.csv").write_text("source", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("notes", encoding="utf-8")
    (tmp_path / "workbook.XLSX").write_text("workbook", encoding="utf-8")

    adapter = LocalFileSourceAdapter(
        directory_path=tmp_path,
        allowed_extensions=("csv", ".xlsx"),
    )

    result = adapter.discover()

    assert [document.source_name for document in result.documents] == [
        "source.csv",
        "workbook.XLSX",
    ]


def test_local_adapter_accepts_single_extension_string(tmp_path) -> None:
    (tmp_path / "source.csv").write_text("source", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("notes", encoding="utf-8")

    adapter = LocalFileSourceAdapter(
        directory_path=tmp_path,
        allowed_extensions=".csv",
    )

    result = adapter.discover()

    assert [document.source_name for document in result.documents] == ["source.csv"]


def test_missing_directory_returns_empty_result_with_warning(tmp_path) -> None:
    missing_path = tmp_path / "missing"

    result = LocalFileSourceAdapter(directory_path=missing_path).discover()

    assert result.documents == ()
    assert result.warnings == (f"Local source directory not found: {missing_path}",)


def test_parse_returns_empty_parse_result_without_mutating_document(tmp_path) -> None:
    adapter = LocalFileSourceAdapter(directory_path=tmp_path)
    document = SourceDocument(
        source_family=SourceFamily.IPCC_EFDB,
        source_name="local.csv",
        file_reference="data/raw/example/local.csv",
    )

    result = adapter.parse(document)

    assert isinstance(result, AdapterParseResult)
    assert result.records == ()
    assert result.rejected_records == ()
    assert result.warnings == ()
    assert result.normalization_notes == ()
    assert document == SourceDocument(
        source_family=SourceFamily.IPCC_EFDB,
        source_name="local.csv",
        file_reference="data/raw/example/local.csv",
    )


def test_local_adapter_can_be_registered_and_retrieved(tmp_path) -> None:
    registry = SourceAdapterRegistry()
    adapter = LocalFileSourceAdapter(
        directory_path=tmp_path,
        source_family=SourceFamily.DEFRA_DESNZ,
    )

    registry.register(adapter)

    assert registry.get(SourceFamily.DEFRA_DESNZ) is adapter
