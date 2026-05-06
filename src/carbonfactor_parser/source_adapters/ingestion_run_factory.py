"""Factory helpers for ingestion run summary contracts."""

from __future__ import annotations

from datetime import datetime, timezone

from carbonfactor_parser.source_adapters.contracts import SourceFamily
from carbonfactor_parser.source_adapters.ingestion_run import (
    IngestionRunStatus,
    IngestionRunSummary,
)


def create_ingestion_run_summary(
    *,
    ingestion_id: str,
    source_family: SourceFamily,
    source_name: str,
    status: IngestionRunStatus = IngestionRunStatus.DISCOVERED,
    records_discovered: int = 0,
    records_parsed: int = 0,
    records_rejected: int = 0,
    validation_issue_count: int = 0,
    normalization_note_count: int = 0,
    warnings: tuple[str, ...] | list[str] = (),
    failure_reason: str | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> IngestionRunSummary:
    timestamp = datetime.now(timezone.utc)
    resolved_created_at = created_at or timestamp
    resolved_updated_at = updated_at or timestamp

    return IngestionRunSummary(
        ingestion_id=ingestion_id,
        source_family=source_family,
        source_name=source_name,
        status=status,
        records_discovered=records_discovered,
        records_parsed=records_parsed,
        records_rejected=records_rejected,
        validation_issue_count=validation_issue_count,
        normalization_note_count=normalization_note_count,
        warnings=tuple(warnings),
        failure_reason=failure_reason,
        created_at=resolved_created_at,
        updated_at=resolved_updated_at,
    )
