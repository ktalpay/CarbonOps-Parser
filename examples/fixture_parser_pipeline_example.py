"""Fixture-only parser pipeline example."""

from __future__ import annotations

from pathlib import Path

from carbonfactor_parser.parsers import (
    ArtificialFixtureParser,
    build_fixture_parser_input_mapping,
)
from carbonfactor_parser.source_adapters import DefraDesnzSourceAdapter


FIXTURE_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "source_documents"
    / "defra_desnz"
)


def build_fixture_parser_pipeline_example(
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
    summary = parser_result.summary

    return {
        "discovered_document_count": len(discovery_result.documents),
        "mapping_document_count": mapping.document_count,
        "parser_record_count": summary.record_count,
        "parser_warning_count": summary.warning_count,
        "parser_error_count": summary.error_count,
        "parser_has_records": summary.has_records,
        "parser_has_warnings": summary.has_warnings,
        "parser_has_errors": summary.has_errors,
        "parser_is_clean": summary.is_clean,
        "discovery_warnings": tuple(discovery_result.warnings),
        "mapping_entries": tuple(
            {
                "document_id": entry.document_id,
                "file_name": entry.file_name,
                "file_extension": entry.file_extension,
                "is_artificial_fixture": entry.is_artificial_fixture,
            }
            for entry in mapping.entries
        ),
        "records": tuple(dict(record) for record in parser_result.records),
    }
