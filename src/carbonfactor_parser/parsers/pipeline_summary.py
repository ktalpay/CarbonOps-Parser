"""Compact parser pipeline summaries from already-computed objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from carbonfactor_parser.parsers.contracts import ParserResult
from carbonfactor_parser.parsers.input_mapping import (
    ParserInputMapping,
    ParserInputMappingEntry,
)
from carbonfactor_parser.source_adapters import SourceDocument, SourceFamily


@dataclass(frozen=True)
class ParserPipelineSummary:
    """Small deterministic summary for fixture-only parser pipeline handoff."""

    discovered_document_count: int
    mapping_entry_count: int
    parser_record_count: int
    parser_warning_count: int
    parser_error_count: int
    has_discovered_documents: bool
    has_mapping_entries: bool
    has_parser_records: bool
    has_parser_warnings: bool
    has_parser_errors: bool
    is_clean: bool
    source_families: tuple[SourceFamily, ...] = ()
    source_names: tuple[str, ...] = ()


def summarize_parser_pipeline(
    discovered_documents: Sequence[SourceDocument],
    mapping: ParserInputMapping,
    parser_result: ParserResult,
) -> ParserPipelineSummary:
    """Summarize a fixture parser pipeline without running discovery or parsing."""

    documents = tuple(discovered_documents)
    entries = tuple(mapping.entries)
    parser_summary = parser_result.summary

    return ParserPipelineSummary(
        discovered_document_count=len(documents),
        mapping_entry_count=len(entries),
        parser_record_count=parser_summary.record_count,
        parser_warning_count=parser_summary.warning_count,
        parser_error_count=parser_summary.error_count,
        has_discovered_documents=bool(documents),
        has_mapping_entries=bool(entries),
        has_parser_records=parser_summary.has_records,
        has_parser_warnings=parser_summary.has_warnings,
        has_parser_errors=parser_summary.has_errors,
        is_clean=not parser_summary.has_warnings and not parser_summary.has_errors,
        source_families=_source_families(documents, entries),
        source_names=_source_names(documents, entries),
    )


def _source_families(
    documents: tuple[SourceDocument, ...],
    entries: tuple[ParserInputMappingEntry, ...],
) -> tuple[SourceFamily, ...]:
    return tuple(
        sorted(
            {
                *(document.source_family for document in documents),
                *(entry.source_family for entry in entries),
            },
            key=lambda family: family.value,
        )
    )


def _source_names(
    documents: tuple[SourceDocument, ...],
    entries: tuple[ParserInputMappingEntry, ...],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                *(document.source_name for document in documents),
                *(entry.source_name for entry in entries),
            }
        )
    )
