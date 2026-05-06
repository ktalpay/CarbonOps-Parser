"""Parser adapter registry boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from carbonfactor_parser.parsers.adapter import ParserAdapter
from carbonfactor_parser.parsers.input_contract import ParserInputContract


@dataclass(frozen=True)
class ParserAdapterRegistry:
    """Deterministic registry of future parser adapters."""

    adapters: tuple[ParserAdapter, ...] = ()


def create_parser_adapter_registry(
    adapters: Iterable[ParserAdapter] = (),
) -> ParserAdapterRegistry:
    """Create a parser adapter registry without executing parsers."""

    normalized_adapters = tuple(adapters)
    _validate_parser_adapters(normalized_adapters)
    return ParserAdapterRegistry(adapters=normalized_adapters)


def register_parser_adapter(
    registry: ParserAdapterRegistry,
    adapter: ParserAdapter,
) -> ParserAdapterRegistry:
    """Return a new registry with one adapter appended."""

    return create_parser_adapter_registry((*registry.adapters, adapter))


def list_parser_adapters(
    registry: ParserAdapterRegistry,
) -> tuple[ParserAdapter, ...]:
    """Return adapters in deterministic registration order."""

    return registry.adapters


def resolve_parser_adapters(
    registry: ParserAdapterRegistry,
    parser_input: ParserInputContract,
) -> tuple[ParserAdapter, ...]:
    """Resolve adapters using metadata-only capability checks."""

    return tuple(
        adapter
        for adapter in registry.adapters
        if adapter.can_parse(parser_input)
    )


def _validate_parser_adapters(adapters: tuple[ParserAdapter, ...]) -> None:
    seen_source_families: set[str] = set()

    for index, adapter in enumerate(adapters):
        if not isinstance(adapter, ParserAdapter):
            raise TypeError(f"adapters[{index}] must be a ParserAdapter.")

        source_family = adapter.source_family
        if not isinstance(source_family, str) or not source_family.strip():
            raise ValueError(
                f"source_family must be a non-empty string for adapters[{index}].",
            )

        if source_family in seen_source_families:
            raise ValueError(
                f"Duplicate parser adapter source_family found: {source_family}",
            )
        seen_source_families.add(source_family)
