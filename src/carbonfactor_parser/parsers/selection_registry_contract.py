"""Runtime-passive parser selection registry contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.parsers.source_format_contract import (
    ParserInputPlan,
    ParserSourceFormat,
    create_phase1_parser_input_plan,
)
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionPlanMode


PHASE1_PARSER_KEYS_BY_SOURCE_FAMILY = {
    "ghg_protocol": "ghg_protocol_phase1_parser",
    "defra_desnz": "defra_desnz_phase1_parser",
    "ipcc_efdb": "ipcc_efdb_phase1_parser",
}


class ParserSelectionStatus(str, Enum):
    """Runtime-passive parser selection status values."""

    PLANNED = "planned"


@dataclass(frozen=True)
class ParserIdentity:
    """Stable parser identity metadata for one source family."""

    source_family: str
    parser_key: str
    parser_source_format: ParserSourceFormat
    format_hint: str


@dataclass(frozen=True)
class ParserSelectionRegistry:
    """Deterministic registry of Phase 1 parser identities."""

    identities: tuple[ParserIdentity, ...]


@dataclass(frozen=True)
class ParserSelection:
    """Runtime-passive parser selection for one parser input document."""

    source_family: str
    source_document_id: str
    source_document_uri: str
    parser_key: str
    parser_source_format: ParserSourceFormat
    status: ParserSelectionStatus
    mode: SourceAcquisitionPlanMode = SourceAcquisitionPlanMode.DRY_RUN


@dataclass(frozen=True)
class ParserSelectionResult:
    """Deterministic parser selections for a parser input plan."""

    status: ParserSelectionStatus
    mode: SourceAcquisitionPlanMode
    selected_source_families: tuple[str, ...]
    registry: ParserSelectionRegistry
    selections: tuple[ParserSelection, ...]


def create_phase1_parser_selection_registry() -> ParserSelectionRegistry:
    """Return stable Phase 1 parser identity metadata."""

    identities = tuple(
        ParserIdentity(
            source_family=source_family,
            parser_key=parser_key,
            parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
            format_hint="discovery",
        )
        for source_family, parser_key in PHASE1_PARSER_KEYS_BY_SOURCE_FAMILY.items()
    )
    return ParserSelectionRegistry(identities=identities)


def select_phase1_parsers(
    parser_input_plan: ParserInputPlan | None = None,
) -> ParserSelectionResult:
    """Select parser identities for parser inputs without executing parsers."""

    active_plan = (
        create_phase1_parser_input_plan()
        if parser_input_plan is None
        else parser_input_plan
    )
    if active_plan.mode is not SourceAcquisitionPlanMode.DRY_RUN:
        raise ValueError("Only dry-run parser selections are supported.")

    registry = create_phase1_parser_selection_registry()
    identities_by_family = {
        identity.source_family: identity
        for identity in registry.identities
    }
    selections = tuple(
        ParserSelection(
            source_family=document.source_family,
            source_document_id=document.source_document_id,
            source_document_uri=document.source_document_uri,
            parser_key=identities_by_family[document.source_family].parser_key,
            parser_source_format=(
                identities_by_family[document.source_family].parser_source_format
            ),
            status=ParserSelectionStatus.PLANNED,
            mode=SourceAcquisitionPlanMode.DRY_RUN,
        )
        for document in active_plan.documents
    )

    return ParserSelectionResult(
        status=ParserSelectionStatus.PLANNED,
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        selected_source_families=active_plan.selected_source_families,
        registry=registry,
        selections=selections,
    )
