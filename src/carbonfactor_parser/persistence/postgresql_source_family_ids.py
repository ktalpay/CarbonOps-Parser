"""Stable UUID helpers for PostgreSQL source-family persistence."""

from __future__ import annotations

import json
import uuid

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    SourceFamily,
    source_family_postgresql_value,
)
from carbonfactor_parser.persistence.source_family_repository import (
    SourceFamilyMasterRecord,
)


def source_document_uuid(record: SourceFamilyMasterRecord) -> uuid.UUID:
    """Return the stable source document UUID for a master record."""

    return _stable_uuid(
        "source_document",
        source_family_postgresql_value(record.source_family),
        record.source_document_id,
    )


def ingestion_run_uuid(record: SourceFamilyMasterRecord) -> uuid.UUID | None:
    """Return the stable ingestion run UUID for a master record."""

    source = record.ingestion_run_id or record.run_id
    if source is None:
        source = (
            f"{source_family_postgresql_value(record.source_family)}:"
            f"{record.source_year}:"
            f"{record.source_version}"
        )
    return _stable_uuid(
        "ingestion_run",
        source_family_postgresql_value(record.source_family),
        source,
    )


def master_uuid(source_family: SourceFamily, master_id: str) -> uuid.UUID:
    """Return the stable source-family master UUID."""

    return _stable_uuid("master", source_family_postgresql_value(source_family), master_id)


def detail_uuid(source_family: SourceFamily, detail_id: str) -> uuid.UUID:
    """Return the stable source-family detail UUID."""

    return _stable_uuid("detail", source_family_postgresql_value(source_family), detail_id)


def _stable_uuid(*values: object) -> uuid.UUID:
    payload = json.dumps(tuple(str(value) for value in values), separators=(",", ":"))
    return uuid.uuid5(uuid.NAMESPACE_URL, payload)


__all__ = (
    "detail_uuid",
    "ingestion_run_uuid",
    "master_uuid",
    "source_document_uuid",
)
