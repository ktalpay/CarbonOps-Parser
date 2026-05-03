"""Contracts for ingestion run metadata."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from carbonfactor_parser.source_adapters.contracts import SourceFamily


class IngestionRunStatus(str, Enum):
    """Conceptual ingestion run states from the metadata model."""

    DISCOVERED = "discovered"
    RETRIEVED = "retrieved"
    PARSED = "parsed"
    VALIDATED = "validated"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class IngestionRunSummary:
    """Summary metadata for one ingestion run or attempt."""

    ingestion_id: str
    source_family: SourceFamily
    source_name: str
    status: IngestionRunStatus
    records_discovered: int = 0
    records_parsed: int = 0
    records_rejected: int = 0
    validation_issue_count: int = 0
    normalization_note_count: int = 0
    warnings: tuple[str, ...] = ()
    failure_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
