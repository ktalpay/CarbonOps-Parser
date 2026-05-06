from datetime import date, datetime, timezone
from typing import Mapping, Any

from carbonfactor_parser.source_adapters import (
    AdapterDiscoveryResult,
    AdapterParseResult,
    IngestionRunStatus,
    IngestionRunSummary,
    SourceAdapterExecutionResult,
    SourceDocument,
    SourceFamily,
)


def make_source_document(
    *,
    source_family: SourceFamily = SourceFamily.DEFRA_DESNZ,
    source_name: str = "DEFRA local file",
    source_url: str | None = None,
    file_reference: str | None = "data/raw/defra/source.xlsx",
    source_version: str | None = "2026",
    publication_date: date | None = date(2026, 1, 1),
    retrieved_at: datetime | None = datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc),
    content_hash: str | None = "a" * 64,
) -> SourceDocument:
    return SourceDocument(
        source_family=source_family,
        source_name=source_name,
        source_url=source_url,
        file_reference=file_reference,
        source_version=source_version,
        publication_date=publication_date,
        retrieved_at=retrieved_at,
        content_hash=content_hash,
    )


def make_adapter_parse_result(
    *,
    records: list[Mapping[str, Any]] | None = None,
    rejected_records: list[Mapping[str, Any]] | None = None,
    warnings: list[str] | None = None,
    normalization_notes: list[str] | None = None,
) -> AdapterParseResult:
    return AdapterParseResult(
        records=records if records is not None else [{"row": 2}],
        rejected_records=rejected_records if rejected_records is not None else [],
        warnings=warnings if warnings is not None else [],
        normalization_notes=normalization_notes if normalization_notes is not None else [],
    )


def make_ingestion_run_summary(
    *,
    ingestion_id: str = "run-001",
    source_family: SourceFamily = SourceFamily.DEFRA_DESNZ,
    source_name: str = "DEFRA local file",
    status: IngestionRunStatus = IngestionRunStatus.PARSED,
    records_discovered: int = 1,
    records_parsed: int = 1,
    records_rejected: int = 0,
    validation_issue_count: int = 0,
    normalization_note_count: int = 0,
    warnings: tuple[str, ...] = (),
    failure_reason: str | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> IngestionRunSummary:
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
        warnings=warnings,
        failure_reason=failure_reason,
        created_at=created_at,
        updated_at=updated_at,
    )


def make_execution_result(
    *,
    document: SourceDocument | None = None,
    parse_result: AdapterParseResult | None = None,
    ingestion_summary: IngestionRunSummary | None = None,
    warnings: tuple[str, ...] = (),
    errors: tuple[str, ...] = (),
) -> SourceAdapterExecutionResult:
    return SourceAdapterExecutionResult(
        document=document or make_source_document(),
        parse_result=parse_result or make_adapter_parse_result(),
        ingestion_summary=ingestion_summary or make_ingestion_run_summary(),
        warnings=warnings,
        errors=errors,
    )


class FakeSourceAdapter:
    def __init__(
        self,
        *,
        source_family: SourceFamily = SourceFamily.DEFRA_DESNZ,
        discovery_result: AdapterDiscoveryResult | None = None,
        parse_result: AdapterParseResult | None = None,
    ) -> None:
        self._source_family = source_family
        self._discovery_result = discovery_result or AdapterDiscoveryResult(
            documents=[make_source_document(source_family=source_family)]
        )
        self._parse_result = parse_result or make_adapter_parse_result()
        self.discover_call_count = 0
        self._parsed_documents: list[SourceDocument] = []

    @property
    def source_family(self) -> SourceFamily:
        return self._source_family

    @property
    def parsed_documents(self) -> tuple[SourceDocument, ...]:
        return tuple(self._parsed_documents)

    def discover(self) -> AdapterDiscoveryResult:
        self.discover_call_count += 1
        return self._discovery_result

    def parse(self, document: SourceDocument) -> AdapterParseResult:
        self._parsed_documents.append(document)
        return self._parse_result
