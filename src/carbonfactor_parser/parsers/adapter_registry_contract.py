"""Runtime-passive Phase 1 parser adapter registry contract."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from carbonfactor_parser.parsers.defra_desnz_adapter_contract import (
    DefraDesnzParserAdapterDescriptor,
    describe_defra_desnz_parser_adapter,
)
from carbonfactor_parser.parsers.ghg_protocol_adapter_contract import (
    GHGProtocolParserAdapterDescriptor,
    describe_ghg_protocol_parser_adapter,
)
from carbonfactor_parser.parsers.ipcc_efdb_adapter_contract import (
    IpccEfdbParserAdapterDescriptor,
    describe_ipcc_efdb_parser_adapter,
)


Phase1ParserAdapterDescriptor = (
    GHGProtocolParserAdapterDescriptor
    | DefraDesnzParserAdapterDescriptor
    | IpccEfdbParserAdapterDescriptor
)

_PHASE1_ADAPTER_DESCRIPTOR_FACTORIES: tuple[
    Callable[[], Phase1ParserAdapterDescriptor],
    ...,
] = (
    describe_ghg_protocol_parser_adapter,
    describe_defra_desnz_parser_adapter,
    describe_ipcc_efdb_parser_adapter,
)


@dataclass(frozen=True)
class Phase1ParserAdapterRegistry:
    """Deterministic registry of Phase 1 parser adapter skeleton descriptors."""

    descriptors: tuple[Phase1ParserAdapterDescriptor, ...]


def create_phase1_parser_adapter_registry() -> Phase1ParserAdapterRegistry:
    """Return all Phase 1 parser adapter skeleton descriptors in stable order."""

    descriptors = tuple(
        describe_adapter()
        for describe_adapter in _PHASE1_ADAPTER_DESCRIPTOR_FACTORIES
    )
    return Phase1ParserAdapterRegistry(descriptors=descriptors)


def list_phase1_parser_adapter_descriptors(
    registry: Phase1ParserAdapterRegistry | None = None,
) -> tuple[Phase1ParserAdapterDescriptor, ...]:
    """List Phase 1 parser adapter skeleton descriptors without execution."""

    active_registry = (
        create_phase1_parser_adapter_registry()
        if registry is None
        else registry
    )
    return active_registry.descriptors


def get_phase1_parser_adapter_by_source_family(
    source_family: str,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> Phase1ParserAdapterDescriptor | None:
    """Find a Phase 1 parser adapter skeleton descriptor by source family."""

    for descriptor in list_phase1_parser_adapter_descriptors(registry):
        if descriptor.source_family == source_family:
            return descriptor
    return None


def get_phase1_parser_adapter_by_parser_key(
    parser_key: str,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> Phase1ParserAdapterDescriptor | None:
    """Find a Phase 1 parser adapter skeleton descriptor by parser key."""

    for descriptor in list_phase1_parser_adapter_descriptors(registry):
        if descriptor.parser_key == parser_key:
            return descriptor
    return None
