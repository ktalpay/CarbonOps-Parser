"""Fixture-only parser pipeline summary example."""

from __future__ import annotations

from pathlib import Path

from carbonfactor_parser.parsers import (
    ArtificialFixtureParser,
    build_fixture_parser_input_mapping,
    summarize_parser_pipeline,
)
from carbonfactor_parser.source_adapters import DefraDesnzSourceAdapter


FIXTURE_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "source_documents"
    / "defra_desnz"
)


def build_parser_pipeline_summary_example(
    *,
    fixture_directory: str | Path = FIXTURE_DIRECTORY,
) -> dict[str, object]:
    discovery_result = DefraDesnzSourceAdapter(
        directory_path=fixture_directory,
    ).discover()
    mapping = build_fixture_parser_input_mapping(
        discovery_result.documents,
        parser_hint="artificial-fixture",
    )
    parser_result = ArtificialFixtureParser().parse_mapping(mapping)
    summary = summarize_parser_pipeline(
        discovery_result.documents,
        mapping,
        parser_result,
    )

    return {
        "discovered_document_count": summary.discovered_document_count,
        "mapping_entry_count": summary.mapping_entry_count,
        "parser_record_count": summary.parser_record_count,
        "parser_warning_count": summary.parser_warning_count,
        "parser_error_count": summary.parser_error_count,
        "has_discovered_documents": summary.has_discovered_documents,
        "has_mapping_entries": summary.has_mapping_entries,
        "has_parser_records": summary.has_parser_records,
        "has_parser_warnings": summary.has_parser_warnings,
        "has_parser_errors": summary.has_parser_errors,
        "is_clean": summary.is_clean,
        "source_families": tuple(
            source_family.value for source_family in summary.source_families
        ),
        "source_names": summary.source_names,
    }
