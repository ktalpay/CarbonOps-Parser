from __future__ import annotations

import importlib
import sys

import pytest

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    get_postgresql_phase1_schema_catalog,
)
from carbonfactor_parser.persistence.source_document_mapping import (
    DRY_RUN_INGESTION_RUN_ID,
    DRY_RUN_TIMESTAMP_LABEL,
    SOURCE_DOCUMENTS_TABLE_NAME,
    create_source_document_persistence_mapping,
)
from carbonfactor_parser.source_acquisition.document_manifest import (
    create_source_document_manifest,
)
from carbonfactor_parser.source_acquisition.models import (
    SourceAcquisitionPlanMode,
    SourceDocumentChecksumStatus,
    SourceDocumentPersistenceMappingResult,
    SourceDocumentPersistenceMappingStatus,
    SourceDocumentPersistenceRecord,
)

EXPECTED_PHASE1_SOURCE_FAMILIES = (
    "ghg_protocol",
    "defra_desnz",
    "ipcc_efdb",
)

EXPECTED_SOURCE_DOCUMENTS_COLUMNS = (
    "source_document_id",
    "ingestion_run_id",
    "source_family",
    "source_document_uri",
    "source_checksum_sha256",
    "acquisition_status",
    "acquired_at",
    "created_at",
    "updated_at",
)

FORBIDDEN_SOURCE_FAMILY_FRAGMENTS = (
    "temp",
    "test",
    "fake",
    "sample",
    "manual",
    "json_input",
)

BANNED_RUNTIME_MODULE_PREFIXES = (
    "requests",
    "psycopg",
    "sqlalchemy",
    "asyncpg",
    "dotenv",
    "boto3",
    "httpx",
    "urllib3",
)


def test_default_source_document_persistence_mapping_is_exact() -> None:
    result = create_source_document_persistence_mapping()

    assert result == SourceDocumentPersistenceMappingResult(
        status=SourceDocumentPersistenceMappingStatus.DRY_RUN_MAPPED,
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        table_name="source_documents",
        column_names=EXPECTED_SOURCE_DOCUMENTS_COLUMNS,
        selected_source_families=EXPECTED_PHASE1_SOURCE_FAMILIES,
        records=(
            SourceDocumentPersistenceRecord(
                source_document_id="dry_run_source_document_001_ghg_protocol",
                ingestion_run_id=DRY_RUN_INGESTION_RUN_ID,
                source_family="ghg_protocol",
                source_document_uri="discovery://ghg_protocol/adapter",
                source_checksum_sha256=None,
                checksum_status=SourceDocumentChecksumStatus.DRY_RUN_UNAVAILABLE,
                acquisition_status=(
                    SourceDocumentPersistenceMappingStatus.DRY_RUN_MAPPED
                ),
                acquired_at=None,
                created_at=DRY_RUN_TIMESTAMP_LABEL,
                updated_at=DRY_RUN_TIMESTAMP_LABEL,
                logical_document_name="GHG Protocol",
                target_logical_path="phase1/ghg_protocol/source",
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
            SourceDocumentPersistenceRecord(
                source_document_id="dry_run_source_document_002_defra_desnz",
                ingestion_run_id=DRY_RUN_INGESTION_RUN_ID,
                source_family="defra_desnz",
                source_document_uri="discovery://defra_desnz/adapter",
                source_checksum_sha256=None,
                checksum_status=SourceDocumentChecksumStatus.DRY_RUN_UNAVAILABLE,
                acquisition_status=(
                    SourceDocumentPersistenceMappingStatus.DRY_RUN_MAPPED
                ),
                acquired_at=None,
                created_at=DRY_RUN_TIMESTAMP_LABEL,
                updated_at=DRY_RUN_TIMESTAMP_LABEL,
                logical_document_name="DEFRA/DESNZ",
                target_logical_path="phase1/defra_desnz/source",
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
            SourceDocumentPersistenceRecord(
                source_document_id="dry_run_source_document_003_ipcc_efdb",
                ingestion_run_id=DRY_RUN_INGESTION_RUN_ID,
                source_family="ipcc_efdb",
                source_document_uri="discovery://ipcc_efdb/adapter",
                source_checksum_sha256=None,
                checksum_status=SourceDocumentChecksumStatus.DRY_RUN_UNAVAILABLE,
                acquisition_status=(
                    SourceDocumentPersistenceMappingStatus.DRY_RUN_MAPPED
                ),
                acquired_at=None,
                created_at=DRY_RUN_TIMESTAMP_LABEL,
                updated_at=DRY_RUN_TIMESTAMP_LABEL,
                logical_document_name="IPCC EFDB",
                target_logical_path="phase1/ipcc_efdb/source",
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
        ),
    )


def test_source_document_persistence_mapping_is_deterministic_and_ordered() -> None:
    first = create_source_document_persistence_mapping()
    second = create_source_document_persistence_mapping()

    assert first == second
    assert first.mode is SourceAcquisitionPlanMode.DRY_RUN
    assert first.selected_source_families == EXPECTED_PHASE1_SOURCE_FAMILIES
    assert (
        tuple(record.source_family for record in first.records)
        == EXPECTED_PHASE1_SOURCE_FAMILIES
    )


def test_source_document_persistence_record_count_matches_manifest_entries() -> None:
    manifest = create_source_document_manifest()
    result = create_source_document_persistence_mapping(manifest)

    assert len(result.records) == len(manifest.entries)
    assert tuple(record.source_document_uri for record in result.records) == tuple(
        entry.source_reference for entry in manifest.entries
    )


def test_source_document_persistence_mapping_aligns_with_schema_catalog() -> None:
    result = create_source_document_persistence_mapping()
    catalog = get_postgresql_phase1_schema_catalog()
    source_documents_table = catalog.get_table(SOURCE_DOCUMENTS_TABLE_NAME)

    assert result.table_name == source_documents_table.name
    assert result.column_names == tuple(
        column.name for column in source_documents_table.columns
    )
    for column_name in result.column_names:
        assert hasattr(result.records[0], column_name)


def test_source_document_persistence_mapping_carries_checksum_metadata() -> None:
    manifest = create_source_document_manifest()
    result = create_source_document_persistence_mapping(manifest)

    for entry, record in zip(manifest.entries, result.records, strict=True):
        assert record.source_checksum_sha256 == entry.checksum.value
        assert record.checksum_status is entry.checksum.status
        assert record.checksum_status is (
            SourceDocumentChecksumStatus.DRY_RUN_UNAVAILABLE
        )


def test_source_document_persistence_mapping_has_no_duplicate_records() -> None:
    result = create_source_document_persistence_mapping()
    record_keys = tuple(
        (
            record.source_family,
            record.source_document_uri,
            record.source_checksum_sha256,
        )
        for record in result.records
    )

    assert len(record_keys) == len(set(record_keys))
    assert len({record.source_document_id for record in result.records}) == len(
        result.records
    )


def test_source_document_persistence_mapping_uses_safe_passive_references() -> None:
    result = create_source_document_persistence_mapping()

    for record in result.records:
        assert record.source_document_uri.startswith("discovery://")
        assert not record.source_document_uri.startswith(("http://", "https://"))
        assert "localhost" not in record.source_document_uri
        assert "example" not in record.source_document_uri
        assert "://" not in record.target_logical_path
        assert record.source_document_id.startswith("dry_run_source_document_")
        assert record.ingestion_run_id == DRY_RUN_INGESTION_RUN_ID
        assert not any(
            fragment in record.source_family
            for fragment in FORBIDDEN_SOURCE_FAMILY_FRAGMENTS
        )


def test_source_document_persistence_mapping_module_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = "carbonfactor_parser.persistence.source_document_mapping"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("source document mapping import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("source document mapping import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "create_source_document_persistence_mapping")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_modules_after - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )
