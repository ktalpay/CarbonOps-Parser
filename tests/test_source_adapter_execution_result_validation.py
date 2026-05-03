from dataclasses import replace
from datetime import datetime, timezone

import pytest

from carbonfactor_parser.source_adapters import (
    AdapterParseResult,
    IngestionRunStatus,
    IngestionRunSummary,
    SourceAdapterExecutionResult,
    SourceDocument,
    SourceFamily,
    validate_source_adapter_execution_result,
)


def valid_document() -> SourceDocument:
    return SourceDocument(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA local file",
        file_reference="data/raw/defra/source.xlsx",
        retrieved_at=datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc),
        content_hash="a" * 64,
    )


def valid_parse_result() -> AdapterParseResult:
    return AdapterParseResult(
        records=[{"row": 2}],
        rejected_records=[],
        warnings=[],
        normalization_notes=[],
    )


def valid_ingestion_summary() -> IngestionRunSummary:
    return IngestionRunSummary(
        ingestion_id="run-001",
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA local file",
        status=IngestionRunStatus.COMPLETED,
        records_discovered=1,
        records_parsed=1,
    )


def valid_execution_result() -> SourceAdapterExecutionResult:
    return SourceAdapterExecutionResult(
        document=valid_document(),
        parse_result=valid_parse_result(),
        ingestion_summary=valid_ingestion_summary(),
    )


def test_valid_execution_result_returns_no_issues() -> None:
    assert validate_source_adapter_execution_result(valid_execution_result()) == []


def test_non_execution_result_input_raises_type_error() -> None:
    with pytest.raises(
        TypeError,
        match="result must be a SourceAdapterExecutionResult.",
    ):
        validate_source_adapter_execution_result(object())  # type: ignore[arg-type]


def test_invalid_document_type_is_reported() -> None:
    result = replace(valid_execution_result(), document=object())

    assert validate_source_adapter_execution_result(result) == [
        "document must be a SourceDocument.",
    ]


def test_invalid_parse_result_type_is_reported() -> None:
    result = replace(valid_execution_result(), parse_result=object())

    assert validate_source_adapter_execution_result(result) == [
        "parse_result must be an AdapterParseResult.",
    ]


def test_invalid_ingestion_summary_type_is_reported() -> None:
    result = replace(valid_execution_result(), ingestion_summary=object())

    assert validate_source_adapter_execution_result(result) == [
        "ingestion_summary must be an IngestionRunSummary.",
    ]


def test_nested_document_validation_issues_are_prefixed() -> None:
    document = replace(
        valid_document(),
        source_name=" ",
        file_reference=None,
        content_hash="A" * 64,
    )
    result = replace(valid_execution_result(), document=document)

    assert validate_source_adapter_execution_result(result) == [
        "document: source_name must be a non-empty string.",
        "document: at least one of source_url or file_reference must be a non-empty string.",
        "document: content_hash must be a lowercase 64-character hexadecimal string.",
    ]


def test_nested_ingestion_summary_validation_issues_are_prefixed() -> None:
    ingestion_summary = replace(
        valid_ingestion_summary(),
        ingestion_id=" ",
        records_discovered=-1,
    )
    result = replace(valid_execution_result(), ingestion_summary=ingestion_summary)

    assert validate_source_adapter_execution_result(result) == [
        "ingestion_summary: ingestion_id must be a non-empty string.",
        "ingestion_summary: records_discovered must be a non-negative integer.",
    ]


def test_warnings_must_be_a_tuple() -> None:
    result = replace(valid_execution_result(), warnings=["warning"])

    assert validate_source_adapter_execution_result(result) == [
        "warnings must be a tuple of strings.",
    ]


def test_errors_must_be_a_tuple() -> None:
    result = replace(valid_execution_result(), errors=["error"])

    assert validate_source_adapter_execution_result(result) == [
        "errors must be a tuple of strings.",
    ]


def test_non_string_warning_is_reported() -> None:
    result = replace(valid_execution_result(), warnings=("warning", 123, None))

    assert validate_source_adapter_execution_result(result) == [
        "warnings[1] must be a string.",
        "warnings[2] must be a string.",
    ]


def test_non_string_error_is_reported() -> None:
    result = replace(valid_execution_result(), errors=("error", 123, None))

    assert validate_source_adapter_execution_result(result) == [
        "errors[1] must be a string.",
        "errors[2] must be a string.",
    ]


def test_issue_ordering_is_deterministic() -> None:
    document = replace(valid_document(), source_name=" ", file_reference=None)
    ingestion_summary = replace(
        valid_ingestion_summary(),
        ingestion_id=" ",
        records_discovered=-1,
    )
    result = SourceAdapterExecutionResult(
        document=document,
        parse_result=object(),  # type: ignore[arg-type]
        ingestion_summary=ingestion_summary,
        warnings=("warning", 123),  # type: ignore[arg-type]
        errors=("error", None),  # type: ignore[arg-type]
    )

    assert validate_source_adapter_execution_result(result) == [
        "document: source_name must be a non-empty string.",
        "document: at least one of source_url or file_reference must be a non-empty string.",
        "parse_result must be an AdapterParseResult.",
        "ingestion_summary: ingestion_id must be a non-empty string.",
        "ingestion_summary: records_discovered must be a non-negative integer.",
        "warnings[1] must be a string.",
        "errors[1] must be a string.",
    ]


def test_helper_does_not_require_count_consistency() -> None:
    parse_result = AdapterParseResult(records=[{"row": 1}, {"row": 2}])
    ingestion_summary = replace(
        valid_ingestion_summary(),
        records_discovered=1,
        records_parsed=99,
        records_rejected=99,
    )
    result = SourceAdapterExecutionResult(
        document=valid_document(),
        parse_result=parse_result,
        ingestion_summary=ingestion_summary,
    )

    assert validate_source_adapter_execution_result(result) == []
