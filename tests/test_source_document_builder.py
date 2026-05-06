from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from carbonfactor_parser.source_adapters import (
    SourceFamily,
    build_source_document_from_file,
    sha256_hex_from_file,
)


def test_source_document_is_built_with_file_traceability(tmp_path: Path) -> None:
    file_path = tmp_path / "source.txt"
    file_path.write_text("source document", encoding="utf-8")

    document = build_source_document_from_file(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA local file",
        file_path=file_path,
    )

    assert document.source_family is SourceFamily.DEFRA_DESNZ
    assert document.source_name == "DEFRA local file"
    assert document.file_reference == str(file_path)
    assert document.content_hash == sha256_hex_from_file(file_path)


def test_source_document_preserves_provided_metadata(tmp_path: Path) -> None:
    file_path = tmp_path / "source.txt"
    file_path.write_text("source document", encoding="utf-8")
    retrieved_at = datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc)

    document = build_source_document_from_file(
        source_family=SourceFamily.GHG_PROTOCOL,
        source_name="GHG Protocol local file",
        file_path=file_path,
        source_url="https://example.invalid/source.xlsx",
        source_version="2026.1",
        publication_date=date(2026, 1, 1),
        retrieved_at=retrieved_at,
    )

    assert document.source_url == "https://example.invalid/source.xlsx"
    assert document.source_version == "2026.1"
    assert document.publication_date == date(2026, 1, 1)
    assert document.retrieved_at is retrieved_at


def test_omitted_retrieved_at_defaults_to_timezone_aware_utc(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "source.txt"
    file_path.write_text("source document", encoding="utf-8")
    before = datetime.now(timezone.utc)

    document = build_source_document_from_file(
        source_family=SourceFamily.IPCC_EFDB,
        source_name="IPCC EFDB local file",
        file_path=file_path,
    )

    after = datetime.now(timezone.utc)

    assert document.retrieved_at is not None
    assert document.retrieved_at.tzinfo is timezone.utc
    assert before <= document.retrieved_at <= after


def test_omitted_source_url_uses_contract_neutral_value(tmp_path: Path) -> None:
    file_path = tmp_path / "source.txt"
    file_path.write_text("source document", encoding="utf-8")

    document = build_source_document_from_file(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="DEFRA local file",
        file_path=file_path,
    )

    assert document.source_url is None


def test_missing_file_raises_file_not_found_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        build_source_document_from_file(
            source_family=SourceFamily.GHG_PROTOCOL,
            source_name="missing source",
            file_path=tmp_path / "missing.xlsx",
        )


def test_invalid_file_path_input_raises_type_error() -> None:
    with pytest.raises(TypeError, match="path must be str or pathlib.Path."):
        build_source_document_from_file(
            source_family=SourceFamily.IPCC_EFDB,
            source_name="invalid source",
            file_path=123,  # type: ignore[arg-type]
        )


def test_helper_does_not_parse_or_transform_file_content(tmp_path: Path) -> None:
    file_path = tmp_path / "source.txt"
    content = "  source document with spacing  \n"
    file_path.write_text(content, encoding="utf-8")

    document = build_source_document_from_file(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="spaced source",
        file_path=file_path,
        chunk_size=2,
    )

    assert file_path.read_text(encoding="utf-8") == content
    assert document.content_hash == sha256_hex_from_file(file_path, chunk_size=2)


def test_returned_content_hash_matches_file_hash(tmp_path: Path) -> None:
    file_path = tmp_path / "source.bin"
    file_path.write_bytes(b"\x00source bytes\xff")

    document = build_source_document_from_file(
        source_family=SourceFamily.IPCC_EFDB,
        source_name="binary source",
        file_path=str(file_path),
    )

    assert document.file_reference == str(file_path)
    assert document.content_hash == sha256_hex_from_file(file_path)
