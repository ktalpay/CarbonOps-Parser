from __future__ import annotations

import json

from carbonfactor_parser import source_acquisition
from carbonfactor_parser.source_acquisition.client import SourceAcquisitionResult
from carbonfactor_parser.source_acquisition.manifest import (
    SourceAcquisitionManifestEntry,
    create_manifest_entry,
    serialize_manifest_entries,
    write_acquisition_manifest,
)


def test_create_manifest_entry_from_successful_persisted_result() -> None:
    result = SourceAcquisitionResult(
        source_id="epa_ghg_emission_factors_hub",
        source_family="government_publications",
        status="success",
        acquisition_url="https://example.invalid/file.csv",
        content_type="text/csv",
        content_length=42,
        checksum_sha256="a" * 64,
        local_path="/tmp/acquired/file.csv",
        message=None,
    )

    entry = create_manifest_entry(result)

    assert entry == SourceAcquisitionManifestEntry(
        source_id=result.source_id,
        source_family=result.source_family,
        acquisition_url=result.acquisition_url,
        local_path=result.local_path,
        checksum_sha256=result.checksum_sha256,
        content_type=result.content_type,
        content_length=result.content_length,
        status=result.status,
        message=result.message,
    )


def test_create_manifest_entry_allows_failed_non_persisted_result() -> None:
    result = SourceAcquisitionResult(
        source_id="defra_ghg_conversion_factors",
        source_family="government_publications",
        status="failed",
        acquisition_url="https://example.invalid/failure.csv",
        local_path=None,
        checksum_sha256=None,
        content_type=None,
        content_length=None,
        message="offline transport failure",
    )

    entry = create_manifest_entry(result)

    assert entry.local_path is None
    assert entry.status == "failed"


def test_serialize_manifest_entries_is_deterministic_and_ordered() -> None:
    entries = (
        SourceAcquisitionManifestEntry(
            source_id="first",
            source_family="family",
            acquisition_url="https://example.invalid/1",
            local_path="/tmp/1",
            checksum_sha256="1" * 64,
            content_type="text/plain",
            content_length=1,
            status="success",
            message=None,
        ),
        SourceAcquisitionManifestEntry(
            source_id="second",
            source_family="family",
            acquisition_url="https://example.invalid/2",
            local_path=None,
            checksum_sha256=None,
            content_type=None,
            content_length=None,
            status="failed",
            message="failure",
        ),
    )

    first = serialize_manifest_entries(entries)
    second = serialize_manifest_entries(entries)

    assert first == second

    payload = json.loads(first)
    assert [item["source_id"] for item in payload] == ["first", "second"]
    assert list(payload[0].keys()) == sorted(payload[0].keys())


def test_write_acquisition_manifest_creates_parent_and_overwrites(tmp_path) -> None:
    source_file = tmp_path / "acquired" / "source.bin"
    source_file.parent.mkdir(parents=True)
    source_file.write_bytes(b"payload")

    manifest_path = tmp_path / "manifests" / "acquisition.json"
    first_entries = (
        SourceAcquisitionManifestEntry(
            source_id="first",
            source_family="family",
            acquisition_url="https://example.invalid/1",
            local_path=str(source_file),
            checksum_sha256="1" * 64,
            content_type="application/octet-stream",
            content_length=7,
            status="success",
            message=None,
        ),
    )
    second_entries = (
        SourceAcquisitionManifestEntry(
            source_id="second",
            source_family="family",
            acquisition_url="https://example.invalid/2",
            local_path=None,
            checksum_sha256=None,
            content_type=None,
            content_length=None,
            status="failed",
            message="failure",
        ),
    )

    written = write_acquisition_manifest(first_entries, manifest_path)
    initial = written.read_text(encoding="utf-8")

    overwritten = write_acquisition_manifest(second_entries, manifest_path)
    updated = overwritten.read_text(encoding="utf-8")

    assert written == manifest_path
    assert overwritten == manifest_path
    assert initial != updated
    assert json.loads(updated)[0]["source_id"] == "second"
    assert source_file.read_bytes() == b"payload"


def test_manifest_public_exports_are_importable() -> None:
    assert source_acquisition.SourceAcquisitionManifestEntry is SourceAcquisitionManifestEntry
    assert source_acquisition.create_manifest_entry is create_manifest_entry
    assert source_acquisition.serialize_manifest_entries is serialize_manifest_entries
    assert source_acquisition.write_acquisition_manifest is write_acquisition_manifest
