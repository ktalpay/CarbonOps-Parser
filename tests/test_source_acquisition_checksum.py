from carbonfactor_parser import source_acquisition
from carbonfactor_parser.source_acquisition.checksum import compute_sha256_hex


def test_compute_sha256_hex_returns_known_digest_for_non_empty_bytes() -> None:
    assert (
        compute_sha256_hex(b"abc")
        == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_compute_sha256_hex_returns_known_digest_for_empty_bytes() -> None:
    assert (
        compute_sha256_hex(b"")
        == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )


def test_compute_sha256_hex_is_deterministic() -> None:
    content = b"a,b\\n1,2\\n"
    assert compute_sha256_hex(content) == compute_sha256_hex(content)


def test_compute_sha256_hex_rejects_non_bytes_content() -> None:
    try:
        compute_sha256_hex("not-bytes")  # type: ignore[arg-type]
    except TypeError as error:
        assert str(error) == "content must be bytes."
    else:
        raise AssertionError("Expected TypeError for non-bytes input.")


def test_compute_sha256_hex_is_exported_in_public_api() -> None:
    assert source_acquisition.compute_sha256_hex is compute_sha256_hex
