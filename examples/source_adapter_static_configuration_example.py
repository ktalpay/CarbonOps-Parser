"""Static in-code source adapter configuration example."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from carbonfactor_parser.source_adapters import (
    LocalFileSourceAdapter,
    SourceAdapterRegistry,
    SourceFamily,
    summarize_source_adapter_result,
)


FIXTURE_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "source_documents"
)


@dataclass(frozen=True)
class StaticSourceAdapterConfig:
    """Discovery-level values used to construct one adapter explicitly."""

    source_family: SourceFamily
    local_directory: Path
    allowed_extensions: tuple[str, ...]
    source_key: str


STATIC_LOCAL_FILE_CONFIG = StaticSourceAdapterConfig(
    source_family=SourceFamily.GHG_PROTOCOL,
    local_directory=FIXTURE_DIRECTORY,
    allowed_extensions=(".csv", ".json"),
    source_key="local_fixture_sources",
)


def build_local_file_adapter_from_static_config(
    config: StaticSourceAdapterConfig = STATIC_LOCAL_FILE_CONFIG,
) -> LocalFileSourceAdapter:
    return LocalFileSourceAdapter(
        directory_path=config.local_directory,
        source_family=config.source_family,
        allowed_extensions=config.allowed_extensions,
    )


def create_static_configuration_registry(
    config: StaticSourceAdapterConfig = STATIC_LOCAL_FILE_CONFIG,
) -> SourceAdapterRegistry:
    registry = SourceAdapterRegistry()
    registry.register(build_local_file_adapter_from_static_config(config))
    return registry


def build_static_configuration_example(
    config: StaticSourceAdapterConfig = STATIC_LOCAL_FILE_CONFIG,
) -> dict[str, object]:
    registry = create_static_configuration_registry(config)
    adapter = registry.get(config.source_family)
    discovery_result = adapter.discover()
    summary = summarize_source_adapter_result(discovery_result)

    return {
        "source_key": config.source_key,
        "source_family": config.source_family.value,
        "allowed_extensions": config.allowed_extensions,
        "registered_source_families": tuple(
            source_family.value for source_family in registry.source_families()
        ),
        "document_count": summary.document_count,
        "source_names": summary.source_names,
        "file_extensions": summary.file_extensions,
        "warning_count": summary.warning_count,
        "error_count": summary.error_count,
        "is_clean": summary.is_clean,
    }
