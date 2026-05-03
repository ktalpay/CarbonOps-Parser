"""Fixture-only DEFRA/DESNZ manifest example."""

from __future__ import annotations

from pathlib import Path

from carbonfactor_parser.source_adapters import (
    DefraDesnzSourceAdapter,
    build_defra_desnz_fixture_manifest,
)


FIXTURE_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "source_documents"
    / "defra_desnz"
)


def build_defra_desnz_fixture_manifest_example(
    *,
    fixture_directory: str | Path = FIXTURE_DIRECTORY,
) -> dict[str, object]:
    discovery_result = DefraDesnzSourceAdapter(
        directory_path=fixture_directory,
    ).discover()
    manifest = build_defra_desnz_fixture_manifest(discovery_result.documents)

    return {
        "source_family": manifest.source_family.value,
        "source_name": manifest.source_name,
        "document_count": manifest.document_count,
        "is_artificial_fixture": manifest.is_artificial_fixture,
        "warnings": tuple(discovery_result.warnings),
        "entries": tuple(
            {
                "source_family": entry.source_family.value,
                "source_name": entry.source_name,
                "file_name": entry.file_name,
                "file_extension": entry.file_extension,
                "path_reference": entry.path_reference,
                "is_artificial_fixture": entry.is_artificial_fixture,
            }
            for entry in manifest.entries
        ),
    }
