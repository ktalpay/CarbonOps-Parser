"""Runtime-passive parser input/source format contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.persistence.source_document_mapping import (
    create_source_document_persistence_mapping,
)
from carbonfactor_parser.source_acquisition.models import (
    SourceAcquisitionPlanMode,
    SourceDocumentPersistenceMappingResult,
)


PHASE1_SOURCE_FAMILIES = (
    "ghg_protocol",
    "defra_desnz",
    "ipcc_efdb",
)


class ParserSourceFormat(str, Enum):
    """Conservative source-format intent for parser input contracts."""

    DISCOVERY_REFERENCE = "discovery_reference"


@dataclass(frozen=True)
class ParserSourceFormatMapping:
    """Explicit source family to parser source-format mapping."""

    source_family: str
    parser_source_format: ParserSourceFormat
    format_hint: str


@dataclass(frozen=True)
class ParserInputDocument:
    """Runtime-passive parser input metadata for one source document."""

    source_family: str
    source_document_id: str
    source_document_uri: str
    source_checksum_sha256: str | None
    logical_document_name: str
    target_logical_path: str
    parser_source_format: ParserSourceFormat
    format_hint: str
    mode: SourceAcquisitionPlanMode = SourceAcquisitionPlanMode.DRY_RUN


@dataclass(frozen=True)
class ParserInputPlan:
    """Runtime-passive parser input plan for Phase 1 source documents."""

    mode: SourceAcquisitionPlanMode
    selected_source_families: tuple[str, ...]
    source_format_mappings: tuple[ParserSourceFormatMapping, ...]
    documents: tuple[ParserInputDocument, ...]


def get_phase1_parser_source_format_mappings() -> tuple[ParserSourceFormatMapping, ...]:
    """Return deterministic Phase 1 parser source-format mappings."""

    return tuple(
        ParserSourceFormatMapping(
            source_family=source_family,
            parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
            format_hint="discovery",
        )
        for source_family in PHASE1_SOURCE_FAMILIES
    )


def create_phase1_parser_input_plan(
    mapping: SourceDocumentPersistenceMappingResult | None = None,
) -> ParserInputPlan:
    """Derive parser input metadata without reading files or executing parsers."""

    active_mapping = (
        create_source_document_persistence_mapping() if mapping is None else mapping
    )
    if active_mapping.mode is not SourceAcquisitionPlanMode.DRY_RUN:
        raise ValueError("Only dry-run parser input plans are supported.")

    mappings_by_family = {
        item.source_family: item
        for item in get_phase1_parser_source_format_mappings()
    }
    documents = tuple(
        ParserInputDocument(
            source_family=record.source_family,
            source_document_id=record.source_document_id,
            source_document_uri=record.source_document_uri,
            source_checksum_sha256=record.source_checksum_sha256,
            logical_document_name=record.logical_document_name,
            target_logical_path=record.target_logical_path,
            parser_source_format=mappings_by_family[
                record.source_family
            ].parser_source_format,
            format_hint=mappings_by_family[record.source_family].format_hint,
            mode=SourceAcquisitionPlanMode.DRY_RUN,
        )
        for record in active_mapping.records
    )

    return ParserInputPlan(
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        selected_source_families=active_mapping.selected_source_families,
        source_format_mappings=get_phase1_parser_source_format_mappings(),
        documents=documents,
    )
