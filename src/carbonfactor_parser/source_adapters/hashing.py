"""Hashing helpers for source document content."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_hex_from_bytes(content: bytes) -> str:
    if not isinstance(content, bytes):
        raise TypeError("content must be bytes.")

    return hashlib.sha256(content).hexdigest()


def sha256_hex_from_text(content: str) -> str:
    if not isinstance(content, str):
        raise TypeError("content must be str.")

    return sha256_hex_from_bytes(content.encode("utf-8"))


def sha256_hex_from_file(path: str | Path, *, chunk_size: int = 1024 * 1024) -> str:
    if not isinstance(path, (str, Path)):
        raise TypeError("path must be str or pathlib.Path.")
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer.")

    file_path = Path(path)
    if file_path.is_dir():
        raise IsADirectoryError(f"path is a directory: {file_path}")

    digest = hashlib.sha256()
    with file_path.open("rb") as source:
        for chunk in iter(lambda: source.read(chunk_size), b""):
            digest.update(chunk)

    return digest.hexdigest()
