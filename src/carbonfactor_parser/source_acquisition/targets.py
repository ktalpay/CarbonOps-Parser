"""Deterministic source acquisition target planning helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor


_FORMAT_TO_EXTENSION = {
    "csv": ".csv",
    "json": ".json",
    "xlsx": ".xlsx",
    "zip": ".zip",
    "pdf": ".pdf",
}
_FILENAME_SAFE_PATTERN = re.compile(r"[^a-z0-9._-]+")


@dataclass(frozen=True)
class SourceAcquisitionTarget:
    """Immutable file target plan for a source acquisition descriptor."""

    source_id: str
    source_family: str
    expected_format: str
    target_directory: Path
    target_filename: str
    local_path: Path


def plan_source_acquisition_target(
    descriptor: SourceAcquisitionDescriptor,
    base_directory: Path | str,
) -> SourceAcquisitionTarget:
    """Plan a deterministic local target path without writing files."""

    if not isinstance(descriptor, SourceAcquisitionDescriptor):
        raise TypeError("descriptor must be a SourceAcquisitionDescriptor.")

    _validate_required_string(descriptor.source_id, "source_id")
    _validate_required_string(descriptor.source_family, "source_family")
    _validate_required_string(descriptor.expected_format, "expected_format")

    target_directory = _normalize_base_directory(base_directory)

    sanitized_source_id = _sanitize_filename_token(descriptor.source_id)
    extension = _map_expected_format_to_extension(descriptor.expected_format)
    target_filename = f"{sanitized_source_id}{extension}"
    local_path = target_directory / target_filename

    return SourceAcquisitionTarget(
        source_id=descriptor.source_id,
        source_family=descriptor.source_family,
        expected_format=descriptor.expected_format,
        target_directory=target_directory,
        target_filename=target_filename,
        local_path=local_path,
    )


def plan_source_acquisition_targets(
    descriptors: Iterable[SourceAcquisitionDescriptor],
    base_directory: Path | str,
) -> tuple[SourceAcquisitionTarget, ...]:
    """Plan deterministic targets in input order without writing files."""

    return tuple(
        plan_source_acquisition_target(descriptor=descriptor, base_directory=base_directory)
        for descriptor in descriptors
    )


def _normalize_base_directory(base_directory: Path | str) -> Path:
    if isinstance(base_directory, Path):
        directory = base_directory
    elif isinstance(base_directory, str):
        if not base_directory.strip():
            raise ValueError("base_directory must be a non-empty path.")
        directory = Path(base_directory)
    else:
        raise TypeError("base_directory must be a Path or str.")

    if not str(directory).strip():
        raise ValueError("base_directory must be a non-empty path.")

    return directory


def _validate_required_string(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")


def _sanitize_filename_token(value: str) -> str:
    sanitized = _FILENAME_SAFE_PATTERN.sub("_", value.strip().lower()).strip("._-")
    return sanitized or "source"


def _map_expected_format_to_extension(expected_format: str) -> str:
    normalized = expected_format.strip().lower()
    return _FORMAT_TO_EXTENSION.get(normalized, ".dat")
