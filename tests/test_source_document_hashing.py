import re
from pathlib import Path

import pytest

from carbonfactor_parser.source_adapters import (
    sha256_hex_from_bytes,
    sha256_hex_from_file,
    sha256_hex_from_text,
)


def test_same_bytes_produce_same_hash() -> None:
    first = sha256_hex_from_bytes(b"source document")
    second = sha256_hex_from_bytes(b"source document")

    assert first == second


def test_different_bytes_produce_different_hashes() -> None:
    first = sha256_hex_from_bytes(b"source document")
    second = sha256_hex_from_bytes(b"other source document")

    assert first != second


def test_empty_bytes_hash_is_deterministic_and_64_hex_characters() -> None:
    digest = sha256_hex_from_bytes(b"")

    assert digest == sha256_hex_from_bytes(b"")
    assert len(digest) == 64
    assert re.fullmatch(r"[0-9a-f]{64}", digest)


def test_text_hash_uses_utf8_and_matches_equivalent_bytes_hash() -> None:
    text = "DEFRA / DESNZ source cafe"

    assert sha256_hex_from_text(text) == sha256_hex_from_bytes(text.encode("utf-8"))


def test_empty_text_hash_is_deterministic_and_64_hex_characters() -> None:
    digest = sha256_hex_from_text("")

    assert digest == sha256_hex_from_text("")
    assert len(digest) == 64
    assert re.fullmatch(r"[0-9a-f]{64}", digest)


@pytest.mark.parametrize("content", ["not bytes", 123, None])
def test_bytes_hash_rejects_non_bytes_input(content: object) -> None:
    with pytest.raises(TypeError, match="content must be bytes."):
        sha256_hex_from_bytes(content)  # type: ignore[arg-type]


@pytest.mark.parametrize("content", [b"not text", 123, None])
def test_text_hash_rejects_non_string_input(content: object) -> None:
    with pytest.raises(TypeError, match="content must be str."):
        sha256_hex_from_text(content)  # type: ignore[arg-type]


def test_hash_output_is_lowercase_hexadecimal() -> None:
    digest = sha256_hex_from_text("Source Document")

    assert digest == digest.lower()
    assert re.fullmatch(r"[0-9a-f]{64}", digest)


def test_file_hash_matches_bytes_hash_for_same_content(tmp_path: Path) -> None:
    content = b"source document bytes"
    file_path = tmp_path / "source.bin"
    file_path.write_bytes(content)

    assert sha256_hex_from_file(file_path) == sha256_hex_from_bytes(content)


def test_file_hash_accepts_str_and_path(tmp_path: Path) -> None:
    file_path = tmp_path / "source.txt"
    file_path.write_text("source document", encoding="utf-8")

    assert sha256_hex_from_file(file_path) == sha256_hex_from_file(str(file_path))


def test_empty_file_hash_is_deterministic_and_64_hex_characters(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "empty.txt"
    file_path.write_bytes(b"")

    digest = sha256_hex_from_file(file_path)

    assert digest == sha256_hex_from_file(file_path)
    assert len(digest) == 64
    assert re.fullmatch(r"[0-9a-f]{64}", digest)


def test_different_file_contents_produce_different_hashes(tmp_path: Path) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("first source document", encoding="utf-8")
    second.write_text("second source document", encoding="utf-8")

    assert sha256_hex_from_file(first) != sha256_hex_from_file(second)


def test_missing_file_raises_file_not_found_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        sha256_hex_from_file(tmp_path / "missing.txt")


def test_directory_path_raises_clear_exception(tmp_path: Path) -> None:
    with pytest.raises(IsADirectoryError, match="path is a directory:"):
        sha256_hex_from_file(tmp_path)


@pytest.mark.parametrize("path", [123, None, object()])
def test_file_hash_rejects_invalid_path_input(path: object) -> None:
    with pytest.raises(TypeError, match="path must be str or pathlib.Path."):
        sha256_hex_from_file(path)  # type: ignore[arg-type]


@pytest.mark.parametrize("chunk_size", [0, -1, "1024", None])
def test_file_hash_rejects_invalid_chunk_size(
    tmp_path: Path,
    chunk_size: object,
) -> None:
    file_path = tmp_path / "source.txt"
    file_path.write_text("source document", encoding="utf-8")

    with pytest.raises(ValueError, match="chunk_size must be a positive integer."):
        sha256_hex_from_file(file_path, chunk_size=chunk_size)  # type: ignore[arg-type]


def test_file_hash_output_is_lowercase_hexadecimal(tmp_path: Path) -> None:
    file_path = tmp_path / "source.txt"
    file_path.write_text("Source Document", encoding="utf-8")

    digest = sha256_hex_from_file(file_path, chunk_size=2)

    assert digest == digest.lower()
    assert re.fullmatch(r"[0-9a-f]{64}", digest)
