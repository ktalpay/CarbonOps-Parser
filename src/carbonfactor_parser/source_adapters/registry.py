"""In-memory registry for explicitly provided source adapters."""

from __future__ import annotations

from carbonfactor_parser.source_adapters.contracts import SourceAdapter, SourceFamily


class SourceAdapterRegistry:
    """Small registry for source adapters without auto-discovery."""

    def __init__(self) -> None:
        self._adapters: dict[SourceFamily, SourceAdapter] = {}

    def register(self, adapter: SourceAdapter) -> None:
        source_family = adapter.source_family

        if source_family in self._adapters:
            raise ValueError(
                f"Source adapter already registered for {source_family.value}."
            )

        self._adapters[source_family] = adapter

    def get(self, source_family: SourceFamily) -> SourceAdapter:
        try:
            return self._adapters[source_family]
        except KeyError as error:
            raise KeyError(
                f"No source adapter registered for {source_family.value}."
            ) from error

    def contains(self, source_family: SourceFamily) -> bool:
        return source_family in self._adapters

    def source_families(self) -> tuple[SourceFamily, ...]:
        return tuple(self._adapters)
