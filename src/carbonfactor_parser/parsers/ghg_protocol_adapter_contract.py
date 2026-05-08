"""Runtime-passive GHG Protocol parser adapter skeleton contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.parsers.selection_registry_contract import (
    PHASE1_PARSER_KEYS_BY_SOURCE_FAMILY,
)
from carbonfactor_parser.parsers.source_format_contract import ParserSourceFormat
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionPlanMode


GHG_PROTOCOL_SOURCE_FAMILY = "ghg_protocol"
GHG_PROTOCOL_PARSER_KEY = PHASE1_PARSER_KEYS_BY_SOURCE_FAMILY[
    GHG_PROTOCOL_SOURCE_FAMILY
]


class ParserAdapterSkeletonReadiness(str, Enum):
    """Runtime-passive parser adapter skeleton readiness values."""

    CONTRACT_ONLY = "contract_only"


@dataclass(frozen=True)
class ParserAdapterCapability:
    """Contract-level parser adapter capability metadata."""

    source_family: str
    parser_key: str
    parser_source_format: ParserSourceFormat
    format_hint: str
    supports_parser_execution: bool
    supports_file_reads: bool
    supports_content_inspection: bool


@dataclass(frozen=True)
class GHGProtocolParserAdapterDescriptor:
    """Runtime-passive GHG Protocol parser adapter skeleton descriptor."""

    source_family: str
    parser_key: str
    readiness: ParserAdapterSkeletonReadiness
    capability: ParserAdapterCapability
    mode: SourceAcquisitionPlanMode = SourceAcquisitionPlanMode.DRY_RUN


def describe_ghg_protocol_parser_adapter() -> GHGProtocolParserAdapterDescriptor:
    """Return deterministic GHG parser adapter skeleton metadata only."""

    capability = ParserAdapterCapability(
        source_family=GHG_PROTOCOL_SOURCE_FAMILY,
        parser_key=GHG_PROTOCOL_PARSER_KEY,
        parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
        format_hint="discovery",
        supports_parser_execution=False,
        supports_file_reads=False,
        supports_content_inspection=False,
    )

    return GHGProtocolParserAdapterDescriptor(
        source_family=GHG_PROTOCOL_SOURCE_FAMILY,
        parser_key=GHG_PROTOCOL_PARSER_KEY,
        readiness=ParserAdapterSkeletonReadiness.CONTRACT_ONLY,
        capability=capability,
        mode=SourceAcquisitionPlanMode.DRY_RUN,
    )
