"""Fixture-only parser input mapping model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from carbonfactor_parser.source_adapters import SourceDocument, SourceFamily


@dataclass(frozen=True)
class ParserInputMappingEntry:
    """Parser input reference for one already-known fixture document."""

    source_family: SourceFamily
    source_name: str
    document_id: str
    document_path: str | None
    file_name: str
    file_extension: str
    parser_hint: str | None = None
    is_artificial_fixture: bool = True


@dataclass(frozen=True)
class ParserInputMapping:
    """Fixture-only parser input mapping for already-known documents."""

    source_family: SourceFamily | None
    source_name: str
    document_count: int
    entries: tuple[ParserInputMappingEntry, ...]
    parser_hint: str | None = None
    is_artificial_fixture: bool = True


def build_fixture_parser_input_mapping(
    documents: Sequence[SourceDocument],
    *,
    parser_hint: str | None = None,
) -> ParserInputMapping:
    entries = tuple(
        _entry_from_document(document, parser_hint=parser_hint)
        for document in sorted(
            documents,
            key=lambda document: (
                Path(document.file_reference or document.source_name).name,
                document.source_family.value,
                document.source_name,
            ),
        )
    )

    return ParserInputMapping(
        source_family=_shared_source_family(entries),
        source_name="fixture_parser_input_mapping",
        document_count=len(entries),
        entries=entries,
        parser_hint=parser_hint,
    )


def _entry_from_document(
    document: SourceDocument,
    *,
    parser_hint: str | None,
) -> ParserInputMappingEntry:
    path_reference = document.file_reference
    path = Path(path_reference or document.source_name)

    return ParserInputMappingEntry(
        source_family=document.source_family,
        source_name=document.source_name,
        document_id=document.source_name,
        document_path=path_reference,
        file_name=path.name,
        file_extension=path.suffix.lower(),
        parser_hint=parser_hint,
    )


def _shared_source_family(
    entries: tuple[ParserInputMappingEntry, ...],
) -> SourceFamily | None:
    source_families = {entry.source_family for entry in entries}
    if len(source_families) == 1:
        return next(iter(source_families))
    return None
