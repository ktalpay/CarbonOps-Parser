from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from carbonfactor_parser.source_adapters import (
    IngestionRunStatus,
    IngestionRunSummary,
    SourceFamily,
)


def test_ingestion_run_status_contains_documented_states() -> None:
    assert {status.value for status in IngestionRunStatus} == {
        "discovered",
        "retrieved",
        "parsed",
        "validated",
        "completed",
        "completed_with_warnings",
        "failed",
        "cancelled",
    }


def test_ingestion_run_summary_can_be_created_with_required_fields() -> None:
    summary = IngestionRunSummary(
        ingestion_id="run-001",
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA local file",
        status=IngestionRunStatus.DISCOVERED,
    )

    assert summary.ingestion_id == "run-001"
    assert summary.source_family is SourceFamily.DEFRA_DESNZ
    assert summary.source_name == "DEFRA local file"
    assert summary.status is IngestionRunStatus.DISCOVERED


def test_default_count_fields_are_zero() -> None:
    summary = IngestionRunSummary(
        ingestion_id="run-001",
        source_family=SourceFamily.GHG_PROTOCOL,
        source_name="GHG Protocol local file",
        status=IngestionRunStatus.RETRIEVED,
    )

    assert summary.records_discovered == 0
    assert summary.records_parsed == 0
    assert summary.records_rejected == 0
    assert summary.validation_issue_count == 0
    assert summary.normalization_note_count == 0


def test_default_warnings_are_immutable_and_do_not_leak_across_instances() -> None:
    first = IngestionRunSummary(
        ingestion_id="run-001",
        source_family=SourceFamily.IPCC_EFDB,
        source_name="IPCC EFDB local file",
        status=IngestionRunStatus.PARSED,
    )
    second = IngestionRunSummary(
        ingestion_id="run-002",
        source_family=SourceFamily.IPCC_EFDB,
        source_name="IPCC EFDB local file",
        status=IngestionRunStatus.PARSED,
    )

    assert first.warnings == ()
    assert second.warnings == ()
    assert not hasattr(first.warnings, "append")

    with pytest.raises(FrozenInstanceError):
        first.warnings = ("sample warning",)

    assert second.warnings == ()


def test_failure_summary_can_include_failure_reason() -> None:
    summary = IngestionRunSummary(
        ingestion_id="run-003",
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA local file",
        status=IngestionRunStatus.FAILED,
        failure_reason="source metadata validation failed",
    )

    assert summary.status is IngestionRunStatus.FAILED
    assert summary.failure_reason == "source metadata validation failed"


def test_summary_can_include_counts_warnings_and_timestamps() -> None:
    created_at = datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc)
    updated_at = datetime(2026, 5, 3, 12, 1, tzinfo=timezone.utc)

    summary = IngestionRunSummary(
        ingestion_id="run-004",
        source_family=SourceFamily.GHG_PROTOCOL,
        source_name="GHG Protocol local file",
        status=IngestionRunStatus.COMPLETED_WITH_WARNINGS,
        records_discovered=10,
        records_parsed=9,
        records_rejected=1,
        validation_issue_count=2,
        normalization_note_count=3,
        warnings=("unsupported optional column",),
        created_at=created_at,
        updated_at=updated_at,
    )

    assert summary.records_discovered == 10
    assert summary.records_parsed == 9
    assert summary.records_rejected == 1
    assert summary.validation_issue_count == 2
    assert summary.normalization_note_count == 3
    assert summary.warnings == ("unsupported optional column",)
    assert summary.created_at is created_at
    assert summary.updated_at is updated_at
