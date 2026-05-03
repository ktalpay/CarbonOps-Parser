"""Hashing helpers for source document content."""

from __future__ import annotations

import hashlib


def sha256_hex_from_bytes(content: bytes) -> str:
    if not isinstance(content, bytes):
        raise TypeError("content must be bytes.")

    return hashlib.sha256(content).hexdigest()


def sha256_hex_from_text(content: str) -> str:
    if not isinstance(content, str):
        raise TypeError("content must be str.")

    return sha256_hex_from_bytes(content.encode("utf-8"))
