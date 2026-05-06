"""Usage example for the artificial fixture parser skeleton."""

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


def build_artificial_fixture_parser_usage_example(
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
    result = ArtificialFixtureParser().parse_mapping(mapping)
    summary = result.summary

    return {
        "source_family": result.source_document.source_family.value,
        "source_name": result.source_document.source_name,
        "input_document_count": mapping.document_count,
        "record_count": summary.record_count,
        "warning_count": summary.warning_count,
        "error_count": summary.error_count,
        "has_records": summary.has_records,
        "has_warnings": summary.has_warnings,
        "has_errors": summary.has_errors,
        "is_clean": summary.is_clean,
        "warnings": tuple(discovery_result.warnings),
        "records": tuple(dict(record) for record in result.records),
    }
