from dataclasses import replace
from datetime import datetime, timezone

import pytest

from carbonfactor_parser.source_adapters import (
    IngestionRunStatus,
    IngestionRunSummary,
    SourceFamily,
    validate_ingestion_run_summary,
)


def valid_summary() -> IngestionRunSummary:
    return IngestionRunSummary(
        ingestion_id="run-001",
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA local file",
        status=IngestionRunStatus.COMPLETED,
        records_discovered=3,
        records_parsed=2,
        records_rejected=1,
        validation_issue_count=1,
        normalization_note_count=1,
        warnings=("sample warning",),
        created_at=datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 3, 12, 1, tzinfo=timezone.utc),
    )


def test_valid_summary_returns_no_issues() -> None:
    assert validate_ingestion_run_summary(valid_summary()) == []


def test_non_ingestion_run_summary_input_raises_type_error() -> None:
    with pytest.raises(TypeError, match="summary must be an IngestionRunSummary."):
        validate_ingestion_run_summary(object())  # type: ignore[arg-type]


def test_blank_ingestion_id_is_reported() -> None:
    summary = replace(valid_summary(), ingestion_id=" ")

    assert validate_ingestion_run_summary(summary) == [
        "ingestion_id must be a non-empty string.",
    ]


def test_blank_source_name_is_reported() -> None:
    summary = replace(valid_summary(), source_name="")

    assert validate_ingestion_run_summary(summary) == [
        "source_name must be a non-empty string.",
    ]


def test_invalid_source_family_is_reported() -> None:
    summary = replace(valid_summary(), source_family=None)  # type: ignore[arg-type]

    assert validate_ingestion_run_summary(summary) == [
        "source_family must be a SourceFamily.",
    ]


def test_invalid_status_is_reported() -> None:
    summary = replace(valid_summary(), status="completed")  # type: ignore[arg-type]

    assert validate_ingestion_run_summary(summary) == [
        "status must be an IngestionRunStatus.",
    ]


def test_negative_counts_are_reported() -> None:
    summary = replace(
        valid_summary(),
        records_discovered=-1,
        records_parsed=-1,
        records_rejected=-1,
        validation_issue_count=-1,
        normalization_note_count=-1,
    )

    assert validate_ingestion_run_summary(summary) == [
        "records_discovered must be a non-negative integer.",
        "records_parsed must be a non-negative integer.",
        "records_rejected must be a non-negative integer.",
        "validation_issue_count must be a non-negative integer.",
        "normalization_note_count must be a non-negative integer.",
    ]


def test_non_integer_counts_are_reported() -> None:
    summary = replace(
        valid_summary(),
        records_discovered="3",  # type: ignore[arg-type]
        records_parsed=2.5,  # type: ignore[arg-type]
        records_rejected=None,  # type: ignore[arg-type]
        validation_issue_count=object(),  # type: ignore[arg-type]
        normalization_note_count="1",  # type: ignore[arg-type]
    )

    assert validate_ingestion_run_summary(summary) == [
        "records_discovered must be a non-negative integer.",
        "records_parsed must be a non-negative integer.",
        "records_rejected must be a non-negative integer.",
        "validation_issue_count must be a non-negative integer.",
        "normalization_note_count must be a non-negative integer.",
    ]


def test_warnings_must_be_a_tuple() -> None:
    summary = replace(valid_summary(), warnings=["warning"])  # type: ignore[arg-type]

    assert validate_ingestion_run_summary(summary) == [
        "warnings must be a tuple of strings.",
    ]


def test_non_string_warnings_are_reported() -> None:
    summary = replace(
        valid_summary(),
        warnings=("valid warning", 123, None),  # type: ignore[arg-type]
    )

    assert validate_ingestion_run_summary(summary) == [
        "warnings[1] must be a string.",
        "warnings[2] must be a string.",
    ]


@pytest.mark.parametrize("failure_reason", [None, "", "  "])
def test_failed_status_requires_non_empty_failure_reason(
    failure_reason: str | None,
) -> None:
    summary = replace(
        valid_summary(),
        status=IngestionRunStatus.FAILED,
        failure_reason=failure_reason,
    )

    assert validate_ingestion_run_summary(summary) == [
        "failure_reason must be a non-empty string when status is failed.",
    ]


def test_non_failed_status_accepts_none_failure_reason() -> None:
    summary = replace(
        valid_summary(),
        status=IngestionRunStatus.COMPLETED,
        failure_reason=None,
    )

    assert validate_ingestion_run_summary(summary) == []


def test_non_string_failure_reason_is_reported_for_non_failed_status() -> None:
    summary = replace(
        valid_summary(),
        status=IngestionRunStatus.COMPLETED,
        failure_reason=123,  # type: ignore[arg-type]
    )

    assert validate_ingestion_run_summary(summary) == [
        "failure_reason must be None or a string.",
    ]


def test_naive_created_at_and_updated_at_are_reported() -> None:
    summary = replace(
        valid_summary(),
        created_at=datetime(2026, 5, 3, 12, 0),
        updated_at=datetime(2026, 5, 3, 12, 1),
    )

    assert validate_ingestion_run_summary(summary) == [
        "created_at must be timezone-aware when present.",
        "updated_at must be timezone-aware when present.",
    ]


def test_non_datetime_created_at_and_updated_at_are_reported() -> None:
    summary = replace(
        valid_summary(),
        created_at="2026-05-03T12:00:00Z",  # type: ignore[arg-type]
        updated_at=123,  # type: ignore[arg-type]
    )

    assert validate_ingestion_run_summary(summary) == [
        "created_at must be a datetime when present.",
        "updated_at must be a datetime when present.",
    ]


def test_issue_ordering_is_deterministic() -> None:
    summary = IngestionRunSummary(
        ingestion_id="",
        source_family=None,  # type: ignore[arg-type]
        source_name=" ",
        status="failed",  # type: ignore[arg-type]
        records_discovered=-1,
        records_parsed="2",  # type: ignore[arg-type]
        records_rejected=-1,
        validation_issue_count="1",  # type: ignore[arg-type]
        normalization_note_count=-1,
        warnings=("valid warning", 123),  # type: ignore[arg-type]
        failure_reason=123,  # type: ignore[arg-type]
        created_at=datetime(2026, 5, 3, 12, 0),
        updated_at="2026-05-03T12:01:00Z",  # type: ignore[arg-type]
    )

    assert validate_ingestion_run_summary(summary) == [
        "ingestion_id must be a non-empty string.",
        "source_family must be a SourceFamily.",
        "source_name must be a non-empty string.",
        "status must be an IngestionRunStatus.",
        "records_discovered must be a non-negative integer.",
        "records_parsed must be a non-negative integer.",
        "records_rejected must be a non-negative integer.",
        "validation_issue_count must be a non-negative integer.",
        "normalization_note_count must be a non-negative integer.",
        "warnings[1] must be a string.",
        "failure_reason must be None or a string.",
        "created_at must be timezone-aware when present.",
        "updated_at must be a datetime when present.",
    ]
