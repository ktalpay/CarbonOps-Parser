"""DEFRA/DESNZ local fixture manifest model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from carbonfactor_parser.source_adapters.contracts import (
    SourceDocument,
    SourceFamily,
)


@dataclass(frozen=True)
class DefraDesnzFixtureManifestEntry:
    """Manifest entry for one already-discovered local fixture document."""

    source_family: SourceFamily
    source_name: str
    file_name: str
    file_extension: str
    path_reference: str
    is_artificial_fixture: bool = True


@dataclass(frozen=True)
class DefraDesnzFixtureManifest:
    """Manifest of already-discovered DEFRA/DESNZ fixture documents."""

    source_family: SourceFamily
    source_name: str
    document_count: int
    entries: tuple[DefraDesnzFixtureManifestEntry, ...]
    is_artificial_fixture: bool = True


def build_defra_desnz_fixture_manifest(
    documents: Sequence[SourceDocument],
) -> DefraDesnzFixtureManifest:
    entries = tuple(
        _entry_from_document(document)
        for document in sorted(
            documents,
            key=lambda document: (
                Path(document.file_reference or document.source_name).name,
                document.source_name,
            ),
        )
    )

    return DefraDesnzFixtureManifest(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="defra_desnz",
        document_count=len(entries),
        entries=entries,
    )


def _entry_from_document(
    document: SourceDocument,
) -> DefraDesnzFixtureManifestEntry:
    path_reference = document.file_reference or document.source_name
    path = Path(path_reference)

    return DefraDesnzFixtureManifestEntry(
        source_family=document.source_family,
        source_name=document.source_name,
        file_name=path.name,
        file_extension=path.suffix.lower(),
        path_reference=path_reference,
    )
