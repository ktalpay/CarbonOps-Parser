"""Runtime-passive source document persistence mapping contracts."""

from __future__ import annotations

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    get_postgresql_phase1_schema_catalog,
)
from carbonfactor_parser.source_acquisition.document_manifest import (
    create_source_document_manifest,
)
from carbonfactor_parser.source_acquisition.models import (
    SourceAcquisitionPlanMode,
    SourceDocumentManifest,
    SourceDocumentPersistenceMappingResult,
    SourceDocumentPersistenceMappingStatus,
    SourceDocumentPersistenceRecord,
)


SOURCE_DOCUMENTS_TABLE_NAME = "source_documents"
DRY_RUN_INGESTION_RUN_ID = "dry_run_ingestion_run_phase1"
DRY_RUN_TIMESTAMP_LABEL = "dry_run_timestamp_unavailable"


def create_source_document_persistence_mapping(
    manifest: SourceDocumentManifest | None = None,
) -> SourceDocumentPersistenceMappingResult:
    """Map source document manifest entries to persistence records without I/O."""

    active_manifest = create_source_document_manifest() if manifest is None else manifest
    if active_manifest.mode is not SourceAcquisitionPlanMode.DRY_RUN:
        raise ValueError("Only dry-run source document persistence mappings are supported.")

    column_names = _source_documents_column_names()
    records = tuple(
        SourceDocumentPersistenceRecord(
            source_document_id=(
                f"dry_run_source_document_{index:03d}_{entry.source_family}"
            ),
            ingestion_run_id=DRY_RUN_INGESTION_RUN_ID,
            source_family=entry.source_family,
            source_document_uri=entry.source_reference,
            source_checksum_sha256=entry.checksum.value,
            checksum_status=entry.checksum.status,
            acquisition_status=SourceDocumentPersistenceMappingStatus.DRY_RUN_MAPPED,
            acquired_at=None,
            created_at=DRY_RUN_TIMESTAMP_LABEL,
            updated_at=DRY_RUN_TIMESTAMP_LABEL,
            logical_document_name=entry.logical_document_name,
            target_logical_path=entry.target_logical_path,
            mode=SourceAcquisitionPlanMode.DRY_RUN,
        )
        for index, entry in enumerate(active_manifest.entries, start=1)
    )

    return SourceDocumentPersistenceMappingResult(
        status=SourceDocumentPersistenceMappingStatus.DRY_RUN_MAPPED,
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        table_name=SOURCE_DOCUMENTS_TABLE_NAME,
        column_names=column_names,
        selected_source_families=active_manifest.selected_source_families,
        records=records,
    )


def _source_documents_column_names() -> tuple[str, ...]:
    catalog = get_postgresql_phase1_schema_catalog()
    return tuple(
        column.name
        for column in catalog.get_table(SOURCE_DOCUMENTS_TABLE_NAME).columns
    )
