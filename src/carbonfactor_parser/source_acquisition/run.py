"""Synchronous orchestration helper for source acquisition runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from carbonfactor_parser.source_acquisition.client import (
    SourceAcquisitionClient,
    SourceAcquisitionResult,
    acquire_all_sources,
)
from carbonfactor_parser.source_acquisition.manifest import (
    SourceAcquisitionManifestEntry,
    create_manifest_entry,
    write_acquisition_manifest,
)
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor


@dataclass(frozen=True)
class SourceAcquisitionRunResult:
    """Deterministic result metadata for one source acquisition run."""

    results: tuple[SourceAcquisitionResult, ...]
    manifest_entries: tuple[SourceAcquisitionManifestEntry, ...]
    manifest_path: Path | None
    acquired_count: int
    failed_count: int
    skipped_count: int


def run_source_acquisition(
    descriptors: Iterable[SourceAcquisitionDescriptor],
    client: SourceAcquisitionClient,
    manifest_path: Path | str | None = None,
) -> SourceAcquisitionRunResult:
    """Run deterministic acquisition orchestration for descriptors."""

    ordered_descriptors = tuple(descriptors)
    results = acquire_all_sources(ordered_descriptors, client)
    manifest_entries = tuple(create_manifest_entry(result) for result in results)

    written_manifest_path: Path | None = None
    if manifest_path is not None:
        written_manifest_path = write_acquisition_manifest(manifest_entries, manifest_path)

    acquired_count = sum(result.status == "acquired" for result in results)
    failed_count = sum(result.status == "failed" for result in results)
    skipped_count = sum(
        result.status in {"skipped", "not_implemented"}
        for result in results
    )

    return SourceAcquisitionRunResult(
        results=results,
        manifest_entries=manifest_entries,
        manifest_path=written_manifest_path,
        acquired_count=acquired_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
    )
