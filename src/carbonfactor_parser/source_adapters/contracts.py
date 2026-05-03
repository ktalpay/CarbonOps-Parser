"""Minimal contracts for source-family-specific adapter boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Mapping, Protocol, runtime_checkable


class SourceFamily(str, Enum):
    """Supported Phase 1 source families."""

    GHG_PROTOCOL = "ghg_protocol"
    DEFRA_DESNZ = "defra_desnz"
    IPCC_EFDB = "ipcc_efdb"


@dataclass(frozen=True)
class SourceDocument:
    """Traceability reference for a source document accepted by an adapter."""

    source_family: SourceFamily
    source_name: str
    source_url: str | None = None
    file_reference: str | None = None
    source_version: str | None = None
    publication_date: date | None = None
    retrieved_at: datetime | None = None
    content_hash: str | None = None


@dataclass(frozen=True)
class AdapterDiscoveryResult:
    """Source documents discovered by an adapter plus non-fatal warnings."""

    documents: list[SourceDocument] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AdapterParseResult:
    """Parsed records and explicit handoff notes from an adapter."""

    records: list[Mapping[str, Any]] = field(default_factory=list)
    rejected_records: list[Mapping[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    normalization_notes: list[str] = field(default_factory=list)


@runtime_checkable
class SourceAdapter(Protocol):
    """Protocol for source-family-specific discovery and parse boundaries."""

    @property
    def source_family(self) -> SourceFamily:
        """Return the source family handled by this adapter."""

    def discover(self) -> AdapterDiscoveryResult:
        """Return source document references without performing ingestion."""

    def parse(self, document: SourceDocument) -> AdapterParseResult:
        """Return parser records and explicit warnings for one document."""
