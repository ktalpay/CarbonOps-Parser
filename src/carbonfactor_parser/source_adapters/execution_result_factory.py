"""Factory helpers for source adapter execution result contracts."""

from __future__ import annotations

from carbonfactor_parser.source_adapters.contracts import (
    AdapterParseResult,
    SourceDocument,
)
from carbonfactor_parser.source_adapters.execution_result import (
    SourceAdapterExecutionResult,
)
from carbonfactor_parser.source_adapters.ingestion_run import IngestionRunSummary


def create_source_adapter_execution_result(
    *,
    document: SourceDocument,
    parse_result: AdapterParseResult,
    ingestion_summary: IngestionRunSummary,
    warnings: tuple[str, ...] | list[str] = (),
    errors: tuple[str, ...] | list[str] = (),
) -> SourceAdapterExecutionResult:
    return SourceAdapterExecutionResult(
        document=document,
        parse_result=parse_result,
        ingestion_summary=ingestion_summary,
        warnings=tuple(warnings),
        errors=tuple(errors),
    )
