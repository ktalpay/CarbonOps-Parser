import re

import pytest

from carbonfactor_parser.source_adapters import (
    sha256_hex_from_bytes,
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
