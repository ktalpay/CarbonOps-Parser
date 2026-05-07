"""Shared runtime-passive ingestion contract boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Mapping


class SourceType(str, Enum):
    """Stable source type identifiers for ingestion contracts."""

    GHG_PROTOCOL = "ghg_protocol"
    DEFRA_DESNZ = "defra_desnz"
    IPCC_EFDB = "ipcc_efdb"


class IngestionStatus(str, Enum):
    """Stable ingestion lifecycle states for metadata snapshots."""

    PREPARED = "prepared"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class SourceDocument:
    """Metadata-only description of an acquired source document."""

    source_type: SourceType
    source_name: str
    document_id: str
    source_uri: str | None = None
    local_path: str | None = None
    source_version: str | None = None
    publication_date: date | None = None
    acquired_at: datetime | None = None
    content_hash: str | None = None


@dataclass(frozen=True)
class SourceAcquisitionResult:
    """Acquisition metadata snapshot and its acquired source documents."""

    status: IngestionStatus
    source_type: SourceType
    run_id: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    documents: tuple[SourceDocument, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ParsedFactorRecord:
    """Contract-level normalized parsed emission factor record."""

    record_id: str
    source_type: SourceType
    factor_value: float | None = None
    factor_unit: str | None = None
    activity_unit: str | None = None
    gas: str | None = None
    geography: str | None = None
    context: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class IngestionRun:
    """Ingestion run metadata snapshot without execution behavior."""

    run_id: str
    source_type: SourceType
    status: IngestionStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    acquired_document_count: int = 0
    parsed_record_count: int = 0
    warning_count: int = 0
    error_count: int = 0


@dataclass(frozen=True)
class PersistenceBootstrapResult:
    """Persistence bootstrap readiness metadata without DB connections."""

    status: IngestionStatus
    backend_name: str
    ready: bool
    schema_version: str | None = None
    details: Mapping[str, Any] | None = None
