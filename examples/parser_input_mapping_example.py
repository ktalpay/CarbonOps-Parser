"""Fixture-only parser input mapping example."""

from __future__ import annotations

from pathlib import Path

from carbonfactor_parser.parsers import build_fixture_parser_input_mapping
from carbonfactor_parser.source_adapters import DefraDesnzSourceAdapter


FIXTURE_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "source_documents"
    / "defra_desnz"
)


def build_parser_input_mapping_example(
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

    return {
        "source_family": (
            mapping.source_family.value if mapping.source_family is not None else None
        ),
        "source_name": mapping.source_name,
        "document_count": mapping.document_count,
        "parser_hint": mapping.parser_hint,
        "is_artificial_fixture": mapping.is_artificial_fixture,
        "warnings": tuple(discovery_result.warnings),
        "entries": tuple(
            {
                "source_family": entry.source_family.value,
                "source_name": entry.source_name,
                "document_id": entry.document_id,
                "document_path": entry.document_path,
                "file_name": entry.file_name,
                "file_extension": entry.file_extension,
                "parser_hint": entry.parser_hint,
                "is_artificial_fixture": entry.is_artificial_fixture,
            }
            for entry in mapping.entries
        ),
    }
