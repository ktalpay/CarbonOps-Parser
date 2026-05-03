"""Compact source adapter result summaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from carbonfactor_parser.source_adapters.contracts import (
    AdapterDiscoveryResult,
    SourceDocument,
    SourceFamily,
)
from carbonfactor_parser.source_adapters.execution_result import (
    SourceAdapterExecutionResult,
)


@dataclass(frozen=True)
class SourceAdapterResultSummary:
    """Small interpretation of discovery or execution handoff results."""

    document_count: int
    warning_count: int
    error_count: int
    has_documents: bool
    has_warnings: bool
    has_errors: bool
    is_clean: bool
    source_families: tuple[SourceFamily, ...] = ()
    source_names: tuple[str, ...] = ()
    file_extensions: tuple[str, ...] = ()


def summarize_source_adapter_result(
    result: AdapterDiscoveryResult | SourceAdapterExecutionResult,
) -> SourceAdapterResultSummary:
    if isinstance(result, AdapterDiscoveryResult):
        documents = tuple(result.documents)
        warnings = tuple(result.warnings)
        errors: tuple[str, ...] = ()
    elif isinstance(result, SourceAdapterExecutionResult):
        documents = (result.document,)
        warnings = tuple(result.warnings)
        errors = tuple(result.errors)
    else:
        raise TypeError(
            "result must be an AdapterDiscoveryResult or SourceAdapterExecutionResult."
        )

    return SourceAdapterResultSummary(
        document_count=len(documents),
        warning_count=len(warnings),
        error_count=len(errors),
        has_documents=bool(documents),
        has_warnings=bool(warnings),
        has_errors=bool(errors),
        is_clean=not warnings and not errors,
        source_families=_source_families(documents),
        source_names=_source_names(documents),
        file_extensions=_file_extensions(documents),
    )


def _source_families(documents: tuple[SourceDocument, ...]) -> tuple[SourceFamily, ...]:
    return tuple(
        sorted(
            {document.source_family for document in documents},
            key=lambda family: family.value,
        )
    )


def _source_names(documents: tuple[SourceDocument, ...]) -> tuple[str, ...]:
    return tuple(sorted({document.source_name for document in documents}))


def _file_extensions(documents: tuple[SourceDocument, ...]) -> tuple[str, ...]:
    extensions = {
        Path(document.file_reference or document.source_name).suffix.lower()
        for document in documents
    }
    return tuple(sorted(extension for extension in extensions if extension))
