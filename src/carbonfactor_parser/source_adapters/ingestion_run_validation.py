"""Validation helpers for ingestion run summary metadata."""

from __future__ import annotations

from datetime import datetime

from carbonfactor_parser.source_adapters.contracts import SourceFamily
from carbonfactor_parser.source_adapters.ingestion_run import (
    IngestionRunStatus,
    IngestionRunSummary,
)


_COUNT_FIELDS = (
    "records_discovered",
    "records_parsed",
    "records_rejected",
    "validation_issue_count",
    "normalization_note_count",
)


def validate_ingestion_run_summary(summary: IngestionRunSummary) -> list[str]:
    if not isinstance(summary, IngestionRunSummary):
        raise TypeError("summary must be an IngestionRunSummary.")

    issues: list[str] = []

    if not isinstance(summary.ingestion_id, str) or not summary.ingestion_id.strip():
        issues.append("ingestion_id must be a non-empty string.")

    if not isinstance(summary.source_family, SourceFamily):
        issues.append("source_family must be a SourceFamily.")

    if not isinstance(summary.source_name, str) or not summary.source_name.strip():
        issues.append("source_name must be a non-empty string.")

    if not isinstance(summary.status, IngestionRunStatus):
        issues.append("status must be an IngestionRunStatus.")

    for field_name in _COUNT_FIELDS:
        value = getattr(summary, field_name)
        if not isinstance(value, int):
            issues.append(f"{field_name} must be a non-negative integer.")
        elif value < 0:
            issues.append(f"{field_name} must be a non-negative integer.")

    if not isinstance(summary.warnings, tuple):
        issues.append("warnings must be a tuple of strings.")
    else:
        for index, warning in enumerate(summary.warnings):
            if not isinstance(warning, str):
                issues.append(f"warnings[{index}] must be a string.")

    if summary.status is IngestionRunStatus.FAILED:
        if not isinstance(summary.failure_reason, str) or not summary.failure_reason.strip():
            issues.append(
                "failure_reason must be a non-empty string when status is failed."
            )
    elif summary.failure_reason is not None and not isinstance(
        summary.failure_reason,
        str,
    ):
        issues.append("failure_reason must be None or a string.")

    _validate_optional_datetime(summary.created_at, "created_at", issues)
    _validate_optional_datetime(summary.updated_at, "updated_at", issues)

    return issues


def _validate_optional_datetime(
    value: object,
    field_name: str,
    issues: list[str],
) -> None:
    if value is None:
        return

    if not isinstance(value, datetime):
        issues.append(f"{field_name} must be a datetime when present.")
    elif value.tzinfo is None:
        issues.append(f"{field_name} must be timezone-aware when present.")
