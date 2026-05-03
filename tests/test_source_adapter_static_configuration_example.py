from pathlib import Path

from examples.source_adapter_static_configuration_example import (
    FIXTURE_DIRECTORY,
    STATIC_LOCAL_FILE_CONFIG,
    StaticSourceAdapterConfig,
    build_local_file_adapter_from_static_config,
    build_static_configuration_example,
    create_static_configuration_registry,
)
from carbonfactor_parser.source_adapters import (
    LocalFileSourceAdapter,
    SourceFamily,
)


def test_static_configuration_example_is_importable_and_callable() -> None:
    result = build_static_configuration_example()

    assert isinstance(result, dict)


def test_static_configuration_builds_local_file_adapter() -> None:
    adapter = build_local_file_adapter_from_static_config()

    assert isinstance(adapter, LocalFileSourceAdapter)
    assert adapter.directory_path == FIXTURE_DIRECTORY
    assert adapter.source_family == SourceFamily.GHG_PROTOCOL
    assert adapter.allowed_extensions == (".csv", ".json")


def test_static_configuration_example_discovers_expected_fixture_files() -> None:
    result = build_static_configuration_example()

    assert result["document_count"] == 2
    assert result["source_names"] == (
        "sample_factors.csv",
        "sample_metadata.json",
    )


def test_static_configuration_example_respects_allowed_extensions() -> None:
    config = StaticSourceAdapterConfig(
        source_family=SourceFamily.GHG_PROTOCOL,
        local_directory=FIXTURE_DIRECTORY,
        allowed_extensions=(".txt",),
        source_key="local_fixture_notes",
    )

    result = build_static_configuration_example(config)

    assert result["document_count"] == 1
    assert result["source_names"] == ("notes.txt",)
    assert result["file_extensions"] == (".txt",)


def test_static_configuration_example_returns_deterministic_data() -> None:
    first = build_static_configuration_example()
    second = build_static_configuration_example()

    assert first == second
    assert tuple(first) == (
        "source_key",
        "source_family",
        "allowed_extensions",
        "registered_source_families",
        "document_count",
        "source_names",
        "file_extensions",
        "warning_count",
        "error_count",
        "is_clean",
    )


def test_static_configuration_example_does_not_parse_fixture_contents() -> None:
    result = build_static_configuration_example()

    assert "factor_id" not in str(result)
    assert "Example fixture metadata" not in str(result)
    assert result["warning_count"] == 0
    assert result["error_count"] == 0


def test_static_configuration_registry_resolution_is_explicit() -> None:
    registry = create_static_configuration_registry()

    assert registry.source_families() == (SourceFamily.GHG_PROTOCOL,)
    assert registry.get(SourceFamily.GHG_PROTOCOL) is not None


def test_static_configuration_uses_repository_relative_fixture_path() -> None:
    assert FIXTURE_DIRECTORY.is_dir()
    assert STATIC_LOCAL_FILE_CONFIG.local_directory == (
        Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "source_documents"
    )
