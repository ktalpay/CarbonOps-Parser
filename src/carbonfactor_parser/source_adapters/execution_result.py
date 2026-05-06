"""Contracts for source adapter execution results."""

from __future__ import annotations

from dataclasses import dataclass

from carbonfactor_parser.source_adapters.contracts import (
    AdapterParseResult,
    SourceDocument,
)
from carbonfactor_parser.source_adapters.ingestion_run import IngestionRunSummary


@dataclass(frozen=True)
class SourceAdapterExecutionResult:
    """Contract tying adapter output to source and ingestion metadata."""

    document: SourceDocument
    parse_result: AdapterParseResult
    ingestion_summary: IngestionRunSummary
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


def has_errors(result: SourceAdapterExecutionResult) -> bool:
    return bool(result.errors)


def has_warnings(result: SourceAdapterExecutionResult) -> bool:
    return bool(result.warnings)
