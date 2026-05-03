"""Helpers for constructing source document references from explicit metadata."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from carbonfactor_parser.source_adapters.contracts import SourceDocument, SourceFamily
from carbonfactor_parser.source_adapters.hashing import sha256_hex_from_file


def build_source_document_from_file(
    *,
    source_family: SourceFamily,
    source_name: str,
    file_path: str | Path,
    source_url: str | None = None,
    source_version: str | None = None,
    publication_date: date | None = None,
    retrieved_at: datetime | None = None,
    chunk_size: int = 1024 * 1024,
) -> SourceDocument:
    """Build a traceable source document reference without parsing content."""

    content_hash = sha256_hex_from_file(file_path, chunk_size=chunk_size)

    return SourceDocument(
        source_family=source_family,
        source_name=source_name,
        source_url=source_url,
        file_reference=str(file_path),
        source_version=source_version,
        publication_date=publication_date,
        retrieved_at=retrieved_at or datetime.now(timezone.utc),
        content_hash=content_hash,
    )
