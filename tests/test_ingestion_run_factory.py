from datetime import datetime, timezone

from carbonfactor_parser.source_adapters import (
    IngestionRunStatus,
    IngestionRunSummary,
    SourceFamily,
    create_ingestion_run_summary,
    validate_ingestion_run_summary,
)


def test_factory_returns_ingestion_run_summary() -> None:
    summary = create_ingestion_run_summary(
        ingestion_id="run-001",
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA local file",
    )

    assert isinstance(summary, IngestionRunSummary)


def test_default_status_is_discovered() -> None:
    summary = create_ingestion_run_summary(
        ingestion_id="run-001",
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA local file",
    )

    assert summary.status is IngestionRunStatus.DISCOVERED


def test_default_created_at_and_updated_at_are_timezone_aware_utc() -> None:
    summary = create_ingestion_run_summary(
        ingestion_id="run-001",
        source_family=SourceFamily.GHG_PROTOCOL,
        source_name="GHG Protocol local file",
    )

    assert summary.created_at is not None
    assert summary.updated_at is not None
    assert summary.created_at.tzinfo is timezone.utc
    assert summary.updated_at.tzinfo is timezone.utc


def test_default_created_at_and_updated_at_are_equal_for_same_summary() -> None:
    summary = create_ingestion_run_summary(
        ingestion_id="run-001",
        source_family=SourceFamily.IPCC_EFDB,
        source_name="IPCC EFDB local file",
    )

    assert summary.created_at == summary.updated_at


def test_provided_status_is_preserved() -> None:
    summary = create_ingestion_run_summary(
        ingestion_id="run-001",
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA local file",
        status=IngestionRunStatus.PARSED,
    )

    assert summary.status is IngestionRunStatus.PARSED


def test_provided_created_at_and_updated_at_are_preserved() -> None:
    created_at = datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc)
    updated_at = datetime(2026, 5, 3, 12, 1, tzinfo=timezone.utc)

    summary = create_ingestion_run_summary(
        ingestion_id="run-001",
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA local file",
        created_at=created_at,
        updated_at=updated_at,
    )

    assert summary.created_at is created_at
    assert summary.updated_at is updated_at


def test_list_warnings_are_converted_to_tuple() -> None:
    summary = create_ingestion_run_summary(
        ingestion_id="run-001",
        source_family=SourceFamily.GHG_PROTOCOL,
        source_name="GHG Protocol local file",
        warnings=["first warning", "second warning"],
    )

    assert summary.warnings == ("first warning", "second warning")


def test_tuple_warnings_are_preserved() -> None:
    warnings = ("first warning", "second warning")

    summary = create_ingestion_run_summary(
        ingestion_id="run-001",
        source_family=SourceFamily.GHG_PROTOCOL,
        source_name="GHG Protocol local file",
        warnings=warnings,
    )

    assert summary.warnings is warnings


def test_warning_list_mutation_after_creation_does_not_mutate_summary() -> None:
    warnings = ["first warning"]

    summary = create_ingestion_run_summary(
        ingestion_id="run-001",
        source_family=SourceFamily.IPCC_EFDB,
        source_name="IPCC EFDB local file",
        warnings=warnings,
    )
    warnings.append("second warning")

    assert summary.warnings == ("first warning",)


def test_count_fields_are_passed_through_unchanged() -> None:
    summary = create_ingestion_run_summary(
        ingestion_id="run-001",
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA local file",
        records_discovered=10,
        records_parsed=9,
        records_rejected=1,
        validation_issue_count=2,
        normalization_note_count=3,
    )

    assert summary.records_discovered == 10
    assert summary.records_parsed == 9
    assert summary.records_rejected == 1
    assert summary.validation_issue_count == 2
    assert summary.normalization_note_count == 3


def test_failure_reason_is_passed_through_unchanged() -> None:
    summary = create_ingestion_run_summary(
        ingestion_id="run-001",
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA local file",
        status=IngestionRunStatus.FAILED,
        failure_reason="source metadata validation failed",
    )

    assert summary.failure_reason == "source metadata validation failed"


def test_returned_summary_passes_validation_for_valid_input() -> None:
    summary = create_ingestion_run_summary(
        ingestion_id="run-001",
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA local file",
        warnings=("sample warning",),
    )

    assert validate_ingestion_run_summary(summary) == []
