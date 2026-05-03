"""Validation helpers for source adapter execution result contracts."""

from __future__ import annotations

from carbonfactor_parser.source_adapters.contracts import (
    AdapterParseResult,
    SourceDocument,
)
from carbonfactor_parser.source_adapters.document_validation import (
    validate_source_document_metadata,
)
from carbonfactor_parser.source_adapters.execution_result import (
    SourceAdapterExecutionResult,
)
from carbonfactor_parser.source_adapters.ingestion_run import IngestionRunSummary
from carbonfactor_parser.source_adapters.ingestion_run_validation import (
    validate_ingestion_run_summary,
)


def validate_source_adapter_execution_result(
    result: SourceAdapterExecutionResult,
) -> list[str]:
    if not isinstance(result, SourceAdapterExecutionResult):
        raise TypeError("result must be a SourceAdapterExecutionResult.")

    issues: list[str] = []

    if not isinstance(result.document, SourceDocument):
        issues.append("document must be a SourceDocument.")
    else:
        issues.extend(
            f"document: {issue}"
            for issue in validate_source_document_metadata(result.document)
        )

    if not isinstance(result.parse_result, AdapterParseResult):
        issues.append("parse_result must be an AdapterParseResult.")

    if not isinstance(result.ingestion_summary, IngestionRunSummary):
        issues.append("ingestion_summary must be an IngestionRunSummary.")
    else:
        issues.extend(
            f"ingestion_summary: {issue}"
            for issue in validate_ingestion_run_summary(result.ingestion_summary)
        )

    if not isinstance(result.warnings, tuple):
        issues.append("warnings must be a tuple of strings.")
    else:
        for index, warning in enumerate(result.warnings):
            if not isinstance(warning, str):
                issues.append(f"warnings[{index}] must be a string.")

    if not isinstance(result.errors, tuple):
        issues.append("errors must be a tuple of strings.")
    else:
        for index, error in enumerate(result.errors):
            if not isinstance(error, str):
                issues.append(f"errors[{index}] must be a string.")

    return issues
