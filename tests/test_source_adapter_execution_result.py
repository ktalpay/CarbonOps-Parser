from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from carbonfactor_parser.source_adapters import (
    AdapterParseResult,
    IngestionRunStatus,
    IngestionRunSummary,
    SourceAdapterExecutionResult,
    SourceDocument,
    SourceFamily,
    has_errors,
    has_warnings,
)


def sample_document() -> SourceDocument:
    return SourceDocument(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA local file",
        file_reference="data/raw/defra/source.xlsx",
        retrieved_at=datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc),
        content_hash="a" * 64,
    )


def sample_parse_result() -> AdapterParseResult:
    return AdapterParseResult(
        records=[{"row": 2}],
        rejected_records=[{"row": 3, "reason": "missing value"}],
        warnings=["sample parse warning"],
        normalization_notes=["trimmed whitespace"],
    )


def sample_ingestion_summary() -> IngestionRunSummary:
    return IngestionRunSummary(
        ingestion_id="run-001",
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA local file",
        status=IngestionRunStatus.PARSED,
        records_discovered=2,
        records_parsed=1,
        records_rejected=1,
        validation_issue_count=1,
        normalization_note_count=1,
    )


def test_execution_result_can_be_created_with_required_objects() -> None:
    document = sample_document()
    parse_result = sample_parse_result()
    ingestion_summary = sample_ingestion_summary()

    result = SourceAdapterExecutionResult(
        document=document,
        parse_result=parse_result,
        ingestion_summary=ingestion_summary,
    )

    assert result.document is document
    assert result.parse_result is parse_result
    assert result.ingestion_summary is ingestion_summary


def test_warnings_and_errors_default_to_empty_tuples() -> None:
    result = SourceAdapterExecutionResult(
        document=sample_document(),
        parse_result=sample_parse_result(),
        ingestion_summary=sample_ingestion_summary(),
    )

    assert result.warnings == ()
    assert result.errors == ()


def test_warning_and_error_tuples_are_preserved() -> None:
    warnings = ("adapter warning",)
    errors = ("adapter error",)

    result = SourceAdapterExecutionResult(
        document=sample_document(),
        parse_result=sample_parse_result(),
        ingestion_summary=sample_ingestion_summary(),
        warnings=warnings,
        errors=errors,
    )

    assert result.warnings is warnings
    assert result.errors is errors


def test_execution_result_is_frozen() -> None:
    result = SourceAdapterExecutionResult(
        document=sample_document(),
        parse_result=sample_parse_result(),
        ingestion_summary=sample_ingestion_summary(),
    )

    with pytest.raises(FrozenInstanceError):
        result.errors = ("new error",)


def test_contract_does_not_modify_parse_result_or_ingestion_summary() -> None:
    parse_result = sample_parse_result()
    ingestion_summary = sample_ingestion_summary()

    result = SourceAdapterExecutionResult(
        document=sample_document(),
        parse_result=parse_result,
        ingestion_summary=ingestion_summary,
        warnings=("adapter warning",),
        errors=("adapter error",),
    )

    assert result.parse_result.records == [{"row": 2}]
    assert result.parse_result.rejected_records == [
        {"row": 3, "reason": "missing value"}
    ]
    assert result.ingestion_summary.records_discovered == 2
    assert result.ingestion_summary.records_parsed == 1
    assert result.ingestion_summary.records_rejected == 1


def test_has_errors_returns_false_for_empty_errors() -> None:
    result = SourceAdapterExecutionResult(
        document=sample_document(),
        parse_result=sample_parse_result(),
        ingestion_summary=sample_ingestion_summary(),
    )

    assert has_errors(result) is False


def test_has_errors_returns_true_for_non_empty_errors() -> None:
    result = SourceAdapterExecutionResult(
        document=sample_document(),
        parse_result=sample_parse_result(),
        ingestion_summary=sample_ingestion_summary(),
        errors=("adapter error",),
    )

    assert has_errors(result) is True


def test_has_warnings_returns_false_for_empty_warnings() -> None:
    result = SourceAdapterExecutionResult(
        document=sample_document(),
        parse_result=sample_parse_result(),
        ingestion_summary=sample_ingestion_summary(),
    )

    assert has_warnings(result) is False


def test_has_warnings_returns_true_for_non_empty_warnings() -> None:
    result = SourceAdapterExecutionResult(
        document=sample_document(),
        parse_result=sample_parse_result(),
        ingestion_summary=sample_ingestion_summary(),
        warnings=("adapter warning",),
    )

    assert has_warnings(result) is True
