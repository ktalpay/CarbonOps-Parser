"""File persistence helpers for source acquisition content."""

from __future__ import annotations

from pathlib import Path

from carbonfactor_parser.source_acquisition.targets import SourceAcquisitionTarget


def write_acquired_content(target: SourceAcquisitionTarget, content: bytes) -> Path:
    """Write acquired bytes to the planned local target path and return it.

    Existing files are overwritten.
    """

    if not isinstance(target, SourceAcquisitionTarget):
        raise TypeError("target must be a SourceAcquisitionTarget.")
    if not isinstance(content, bytes):
        raise TypeError("content must be bytes.")

    target.local_path.parent.mkdir(parents=True, exist_ok=True)
    target.local_path.write_bytes(content)
    return target.local_path
