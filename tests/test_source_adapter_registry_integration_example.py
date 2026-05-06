import pytest

from examples.source_adapter_registry_example import (
    create_example_registry,
    discover_for_source,
    resolve_adapter,
)
from carbonfactor_parser.source_adapters import (
    LocalFileSourceAdapter,
    NoOpSourceAdapter,
    SourceFamily,
)


def test_example_registers_and_resolves_noop_adapter(tmp_path) -> None:
    registry = create_example_registry(tmp_path)

    adapter = resolve_adapter(registry, SourceFamily.GHG_PROTOCOL)

    assert isinstance(adapter, NoOpSourceAdapter)
    assert adapter.discover().documents == ()


def test_example_registers_and_resolves_local_file_adapter(tmp_path) -> None:
    registry = create_example_registry(tmp_path)

    adapter = resolve_adapter(registry, SourceFamily.DEFRA_DESNZ)

    assert isinstance(adapter, LocalFileSourceAdapter)


def test_resolved_local_file_adapter_discovers_local_files(tmp_path) -> None:
    (tmp_path / "source-b.xlsx").write_text("source b", encoding="utf-8")
    (tmp_path / "source-a.csv").write_text("source a", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("notes", encoding="utf-8")

    registry = create_example_registry(tmp_path)
    result = discover_for_source(registry, SourceFamily.DEFRA_DESNZ)

    assert result.warnings == ()
    assert [document.source_name for document in result.documents] == [
        "source-a.csv",
        "source-b.xlsx",
    ]
    assert {document.source_family for document in result.documents} == {
        SourceFamily.DEFRA_DESNZ
    }


def test_unknown_adapter_lookup_uses_registry_key_error(tmp_path) -> None:
    registry = create_example_registry(tmp_path)

    with pytest.raises(
        KeyError,
        match="No source adapter registered for ipcc_efdb.",
    ):
        resolve_adapter(registry, SourceFamily.IPCC_EFDB)
