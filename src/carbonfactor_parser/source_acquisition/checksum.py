"""Checksum helpers for in-memory source acquisition content."""

from __future__ import annotations

from hashlib import sha256


def compute_sha256_hex(content: bytes) -> str:
    """Compute a deterministic lowercase SHA-256 hex digest for bytes content."""

    if not isinstance(content, bytes):
        raise TypeError("content must be bytes.")

    return sha256(content).hexdigest()
