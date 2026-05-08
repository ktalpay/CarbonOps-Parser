"""Runtime-passive IPCC EFDB parser adapter skeleton contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.parsers.selection_registry_contract import (
    PHASE1_PARSER_KEYS_BY_SOURCE_FAMILY,
)
from carbonfactor_parser.parsers.source_format_contract import ParserSourceFormat
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionPlanMode


IPCC_EFDB_SOURCE_FAMILY = "ipcc_efdb"
IPCC_EFDB_PARSER_KEY = PHASE1_PARSER_KEYS_BY_SOURCE_FAMILY[
    IPCC_EFDB_SOURCE_FAMILY
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
class IpccEfdbParserAdapterDescriptor:
    """Runtime-passive IPCC EFDB parser adapter skeleton descriptor."""

    source_family: str
    parser_key: str
    readiness: ParserAdapterSkeletonReadiness
    capability: ParserAdapterCapability
    mode: SourceAcquisitionPlanMode = SourceAcquisitionPlanMode.DRY_RUN


def describe_ipcc_efdb_parser_adapter() -> IpccEfdbParserAdapterDescriptor:
    """Return deterministic IPCC EFDB parser adapter skeleton metadata only."""

    capability = ParserAdapterCapability(
        source_family=IPCC_EFDB_SOURCE_FAMILY,
        parser_key=IPCC_EFDB_PARSER_KEY,
        parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
        format_hint="discovery",
        supports_parser_execution=False,
        supports_file_reads=False,
        supports_content_inspection=False,
    )

    return IpccEfdbParserAdapterDescriptor(
        source_family=IPCC_EFDB_SOURCE_FAMILY,
        parser_key=IPCC_EFDB_PARSER_KEY,
        readiness=ParserAdapterSkeletonReadiness.CONTRACT_ONLY,
        capability=capability,
        mode=SourceAcquisitionPlanMode.DRY_RUN,
    )
