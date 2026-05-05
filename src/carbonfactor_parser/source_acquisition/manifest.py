"""Manifest helpers for local source acquisition outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Iterable

from carbonfactor_parser.source_acquisition.client import SourceAcquisitionResult


@dataclass(frozen=True)
class SourceAcquisitionManifestEntry:
    """Deterministic metadata entry for one acquisition result."""

    source_id: str
    source_family: str
    acquisition_url: str
    local_path: str | None
    checksum_sha256: str | None
    content_type: str | None
    content_length: int | None
    status: str
    message: str | None


def create_manifest_entry(result: SourceAcquisitionResult) -> SourceAcquisitionManifestEntry:
    """Create a manifest entry from an acquisition result."""

    normalized_local_path = _normalize_local_path(result.local_path)

    if normalized_local_path is not None and not normalized_local_path.strip():
        raise ValueError("local_path must be None or a non-empty string.")

    if normalized_local_path is not None and result.status not in {"success", "acquired"}:
        raise ValueError("local_path is only allowed when status is 'success' or 'acquired'.")

    if result.status in {"success", "acquired"} and normalized_local_path is not None and result.checksum_sha256 is None:
        raise ValueError("checksum_sha256 is required when a successful acquisition is persisted.")

    return SourceAcquisitionManifestEntry(
        source_id=result.source_id,
        source_family=result.source_family,
        acquisition_url=result.acquisition_url,
        local_path=normalized_local_path,
        checksum_sha256=result.checksum_sha256,
        content_type=result.content_type,
        content_length=result.content_length,
        status=result.status,
        message=result.message,
    )


def serialize_manifest_entries(entries: Iterable[SourceAcquisitionManifestEntry]) -> str:
    """Serialize manifest entries to deterministic JSON text."""

    payload = [asdict(entry) for entry in entries]
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_acquisition_manifest(
    entries: Iterable[SourceAcquisitionManifestEntry],
    manifest_path: Path | str,
) -> Path:
    """Write serialized manifest entries to a local JSON file."""

    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_manifest_entries(entries), encoding="utf-8")
    return path


def _normalize_local_path(local_path: object) -> str | None:
    if local_path is None:
        return None

    if isinstance(local_path, Path):
        return str(local_path)

    if isinstance(local_path, str):
        return local_path

    raise TypeError("local_path must be a string, Path, or None.")
