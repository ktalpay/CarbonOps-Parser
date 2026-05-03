"""Small source adapter registry integration example."""

from __future__ import annotations

from pathlib import Path

from carbonfactor_parser.source_adapters import (
    AdapterDiscoveryResult,
    LocalFileSourceAdapter,
    NoOpSourceAdapter,
    SourceAdapter,
    SourceAdapterRegistry,
    SourceFamily,
)


def create_example_registry(local_directory: str | Path) -> SourceAdapterRegistry:
    registry = SourceAdapterRegistry()
    registry.register(NoOpSourceAdapter(source_family=SourceFamily.GHG_PROTOCOL))
    registry.register(
        LocalFileSourceAdapter(
            directory_path=local_directory,
            source_family=SourceFamily.DEFRA_DESNZ,
            allowed_extensions=(".csv", ".xlsx"),
        )
    )
    return registry


def resolve_adapter(
    registry: SourceAdapterRegistry,
    source_family: SourceFamily,
) -> SourceAdapter:
    return registry.get(source_family)


def discover_for_source(
    registry: SourceAdapterRegistry,
    source_family: SourceFamily,
) -> AdapterDiscoveryResult:
    return resolve_adapter(registry, source_family).discover()
