from __future__ import annotations

import importlib
import sys

import pytest

from carbonfactor_parser.source_acquisition.document_manifest import (
    DRY_RUN_SOURCE_DOCUMENT_CHECKSUM,
    create_source_document_manifest,
)
from carbonfactor_parser.source_acquisition.download_planning import (
    create_source_download_batch_plan,
)
from carbonfactor_parser.source_acquisition.models import (
    SourceAcquisitionPlanMode,
    SourceDocumentChecksum,
    SourceDocumentChecksumStatus,
    SourceDocumentManifest,
    SourceDocumentManifestEntry,
)

EXPECTED_PHASE1_SOURCE_FAMILIES = (
    "ghg_protocol",
    "defra_desnz",
    "ipcc_efdb",
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


def test_default_source_document_manifest_is_exact() -> None:
    manifest = create_source_document_manifest()

    assert manifest == SourceDocumentManifest(
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        selected_source_families=EXPECTED_PHASE1_SOURCE_FAMILIES,
        entries=(
            SourceDocumentManifestEntry(
                source_family="ghg_protocol",
                logical_document_name="GHG Protocol",
                source_reference="discovery://ghg_protocol/adapter",
                target_logical_path="phase1/ghg_protocol/source",
                checksum=SourceDocumentChecksum(
                    algorithm="sha256",
                    value=None,
                    status=SourceDocumentChecksumStatus.DRY_RUN_UNAVAILABLE,
                ),
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
            SourceDocumentManifestEntry(
                source_family="defra_desnz",
                logical_document_name="DEFRA/DESNZ",
                source_reference="discovery://defra_desnz/adapter",
                target_logical_path="phase1/defra_desnz/source",
                checksum=SourceDocumentChecksum(
                    algorithm="sha256",
                    value=None,
                    status=SourceDocumentChecksumStatus.DRY_RUN_UNAVAILABLE,
                ),
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
            SourceDocumentManifestEntry(
                source_family="ipcc_efdb",
                logical_document_name="IPCC EFDB",
                source_reference="discovery://ipcc_efdb/adapter",
                target_logical_path="phase1/ipcc_efdb/source",
                checksum=SourceDocumentChecksum(
                    algorithm="sha256",
                    value=None,
                    status=SourceDocumentChecksumStatus.DRY_RUN_UNAVAILABLE,
                ),
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
        ),
    )


def test_source_document_manifest_is_deterministic_and_ordered() -> None:
    first = create_source_document_manifest()
    second = create_source_document_manifest()

    assert first == second
    assert first.mode is SourceAcquisitionPlanMode.DRY_RUN
    assert first.selected_source_families == EXPECTED_PHASE1_SOURCE_FAMILIES
    assert (
        tuple(entry.source_family for entry in first.entries)
        == EXPECTED_PHASE1_SOURCE_FAMILIES
    )


def test_source_document_manifest_count_matches_download_requests() -> None:
    download_plan = create_source_download_batch_plan()
    manifest = create_source_document_manifest(download_plan)

    assert len(manifest.entries) == len(download_plan.requests)
    assert tuple(entry.source_family for entry in manifest.entries) == tuple(
        request.source_family for request in download_plan.requests
    )


def test_source_document_manifest_checksum_metadata_is_dry_run_shape() -> None:
    manifest = create_source_document_manifest()

    assert DRY_RUN_SOURCE_DOCUMENT_CHECKSUM == SourceDocumentChecksum(
        algorithm="sha256",
        value=None,
        status=SourceDocumentChecksumStatus.DRY_RUN_UNAVAILABLE,
    )
    assert {entry.checksum for entry in manifest.entries} == {
        DRY_RUN_SOURCE_DOCUMENT_CHECKSUM
    }
    assert all(entry.checksum.value is None for entry in manifest.entries)
    assert all(
        entry.checksum.status is SourceDocumentChecksumStatus.DRY_RUN_UNAVAILABLE
        for entry in manifest.entries
    )


def test_source_document_manifest_has_no_duplicate_entries() -> None:
    manifest = create_source_document_manifest()
    manifest_keys = tuple(
        (
            entry.source_family,
            entry.source_reference,
            entry.target_logical_path,
        )
        for entry in manifest.entries
    )

    assert len(manifest_keys) == len(set(manifest_keys))
    assert len({entry.source_family for entry in manifest.entries}) == len(
        EXPECTED_PHASE1_SOURCE_FAMILIES
    )


def test_source_document_manifest_uses_safe_passive_references() -> None:
    manifest = create_source_document_manifest()

    for entry in manifest.entries:
        assert entry.source_reference.startswith("discovery://")
        assert not entry.source_reference.startswith(("http://", "https://"))
        assert "localhost" not in entry.source_reference
        assert "example" not in entry.source_reference
        assert "://" not in entry.target_logical_path
        assert not any(
            fragment in entry.source_family
            for fragment in FORBIDDEN_SOURCE_FAMILY_FRAGMENTS
        )


def test_source_document_manifest_module_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = "carbonfactor_parser.source_acquisition.document_manifest"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("source document manifest import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("source document manifest import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "create_source_document_manifest")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_modules_after - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )
