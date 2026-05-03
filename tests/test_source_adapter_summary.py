import pytest

from carbonfactor_parser.source_adapters import (
    AdapterDiscoveryResult,
    AdapterParseResult,
    IngestionRunStatus,
    IngestionRunSummary,
    LocalFileSourceAdapter,
    SourceAdapterExecutionResult,
    SourceAdapterResultSummary,
    SourceDocument,
    SourceFamily,
    summarize_source_adapter_result,
)


def make_document(
    *,
    source_family: SourceFamily = SourceFamily.GHG_PROTOCOL,
    source_name: str = "sample.csv",
    file_reference: str | None = "data/raw/sample.csv",
) -> SourceDocument:
    return SourceDocument(
        source_family=source_family,
        source_name=source_name,
        file_reference=file_reference,
    )


def make_execution_result(
    *,
    document: SourceDocument | None = None,
    warnings: tuple[str, ...] = (),
    errors: tuple[str, ...] = (),
) -> SourceAdapterExecutionResult:
    return SourceAdapterExecutionResult(
        document=document or make_document(),
        parse_result=AdapterParseResult(),
        ingestion_summary=IngestionRunSummary(
            ingestion_id="run-001",
            source_family=SourceFamily.GHG_PROTOCOL,
            source_name="Example source",
            status=IngestionRunStatus.PARSED,
        ),
        warnings=warnings,
        errors=errors,
    )


def test_empty_discovery_result_produces_zero_counts() -> None:
    summary = summarize_source_adapter_result(AdapterDiscoveryResult())

    assert summary == SourceAdapterResultSummary(
        document_count=0,
        warning_count=0,
        error_count=0,
        has_documents=False,
        has_warnings=False,
        has_errors=False,
        is_clean=True,
    )


def test_discovery_result_with_documents_counts_documents() -> None:
    result = AdapterDiscoveryResult(
        documents=[
            make_document(
                source_family=SourceFamily.DEFRA_DESNZ,
                source_name="beta.xlsx",
                file_reference="data/raw/beta.xlsx",
            ),
            make_document(
                source_family=SourceFamily.GHG_PROTOCOL,
                source_name="alpha.csv",
                file_reference="data/raw/alpha.csv",
            ),
        ]
    )

    summary = summarize_source_adapter_result(result)

    assert summary.document_count == 2
    assert summary.has_documents is True
    assert summary.source_families == (
        SourceFamily.DEFRA_DESNZ,
        SourceFamily.GHG_PROTOCOL,
    )
    assert summary.source_names == ("alpha.csv", "beta.xlsx")
    assert summary.file_extensions == (".csv", ".xlsx")


def test_discovery_result_with_warnings_counts_warnings() -> None:
    result = AdapterDiscoveryResult(warnings=["first warning", "second warning"])

    summary = summarize_source_adapter_result(result)

    assert summary.warning_count == 2
    assert summary.error_count == 0
    assert summary.has_warnings is True
    assert summary.has_errors is False
    assert summary.is_clean is False


def test_execution_result_with_errors_counts_errors() -> None:
    result = make_execution_result(errors=("first error", "second error"))

    summary = summarize_source_adapter_result(result)

    assert summary.document_count == 1
    assert summary.warning_count == 0
    assert summary.error_count == 2
    assert summary.has_documents is True
    assert summary.has_errors is True
    assert summary.is_clean is False


def test_execution_result_with_warnings_and_errors_sets_booleans() -> None:
    result = make_execution_result(
        warnings=("sample warning",),
        errors=("sample error",),
    )

    summary = summarize_source_adapter_result(result)

    assert summary.warning_count == 1
    assert summary.error_count == 1
    assert summary.has_warnings is True
    assert summary.has_errors is True
    assert summary.is_clean is False


def test_summary_handles_local_file_source_adapter_discovery(tmp_path) -> None:
    (tmp_path / "source-b.json").write_text("{}", encoding="utf-8")
    (tmp_path / "source-a.csv").write_text("id,value\n1,2", encoding="utf-8")

    discovery_result = LocalFileSourceAdapter(
        directory_path=tmp_path,
        source_family=SourceFamily.DEFRA_DESNZ,
        allowed_extensions=(".csv", ".json"),
    ).discover()

    summary = summarize_source_adapter_result(discovery_result)

    assert summary.document_count == 2
    assert summary.source_families == (SourceFamily.DEFRA_DESNZ,)
    assert summary.source_names == ("source-a.csv", "source-b.json")
    assert summary.file_extensions == (".csv", ".json")


def test_summary_rejects_unsupported_result_type() -> None:
    with pytest.raises(
        TypeError,
        match="result must be an AdapterDiscoveryResult or SourceAdapterExecutionResult.",
    ):
        summarize_source_adapter_result(object())
