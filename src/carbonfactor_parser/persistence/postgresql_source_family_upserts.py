"""PostgreSQL source-family source-document and ingestion-run upserts."""

from __future__ import annotations

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    source_family_postgresql_value,
)
from carbonfactor_parser.persistence.postgresql_source_family_ids import (
    ingestion_run_uuid,
    source_document_uuid,
)
from carbonfactor_parser.persistence.source_family_repository import (
    SourceFamilyMasterRecord,
)


def ensure_ingestion_run(connection: object, master: SourceFamilyMasterRecord) -> None:
    """Ensure the source-family ingestion run row exists."""

    ingestion_run_id = ingestion_run_uuid(master)
    if ingestion_run_id is None:
        return
    _execute(
        connection,
        """
        INSERT INTO ingestion_runs (
            ingestion_run_id,
            run_status,
            created_at,
            updated_at
        )
        VALUES (%s, %s, NOW(), NOW())
        ON CONFLICT (ingestion_run_id) DO NOTHING
        """,
        (str(ingestion_run_id), "completed"),
    )


def ensure_source_document(connection: object, master: SourceFamilyMasterRecord) -> None:
    """Ensure the source-family source document row exists."""

    _execute(
        connection,
        """
        INSERT INTO source_documents (
            source_document_id,
            ingestion_run_id,
            source_family,
            source_document_uri,
            source_checksum_sha256,
            acquisition_status,
            acquired_at,
            created_at,
            updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW())
        ON CONFLICT (source_family, source_document_uri, source_checksum_sha256)
        DO NOTHING
        """,
        (
            str(source_document_uuid(master)),
            str(ingestion_run_uuid(master)),
            source_family_postgresql_value(master.source_family),
            master.artifact_reference or master.source_document_id,
            master.artifact_checksum_sha256 or "checksum-unavailable",
            "downloaded",
        ),
    )


def _execute(
    connection: object,
    statement: str,
    parameters: object | None = None,
) -> object:
    execute = getattr(connection, "execute")
    if parameters is None:
        return execute(statement)
    return execute(statement, parameters)


__all__ = (
    "ensure_ingestion_run",
    "ensure_source_document",
)
