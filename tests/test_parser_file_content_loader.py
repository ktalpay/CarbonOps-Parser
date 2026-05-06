import inspect
import sqlite3
import urllib.request
from pathlib import Path

import pytest

import carbonfactor_parser.parsers.file_content_loader as loader_module
from carbonfactor_parser.parsers import (
    ParserFileContentInput,
    ParserFileContentLoadStatus,
    load_parser_file_content_from_local_path,
)


def test_valid_utf8_file_loads_into_parser_file_content_input(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "defra_fixture.csv"
    file_path.write_text("factor_id,factor_name,unit\n1,Electricity,kWh\n", encoding="utf-8")

    result = load_parser_file_content_from_local_path(
        source_family="defra_desnz",
        source_id="defra_desnz_2024",
        local_path=file_path,
        content_type="text/csv",
        format_hint="csv",
        checksum_sha256="abc123",
    )

    assert result.status == ParserFileContentLoadStatus.SUCCESS
    assert result.is_success is True
    assert isinstance(result.content_input, ParserFileContentInput)
    assert result.content_input.content == (
        "factor_id,factor_name,unit\n1,Electricity,kWh\n"
    )


def test_local_file_loader_preserves_source_identity_and_metadata(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "source.csv"
    file_path.write_text("a,b\n1,2\n", encoding="utf-8")

    result = load_parser_file_content_from_local_path(
        source_family="defra_desnz",
        source_id="source-001",
        local_path=file_path,
        content_type="text/csv",
        format_hint="csv",
        artifact_reference="artifact://source/source.csv",
        checksum_sha256="f" * 64,
    )

    assert result.status == ParserFileContentLoadStatus.SUCCESS
    assert result.local_path == str(file_path)
    assert result.content_input is not None
    assert result.content_input.source_family == "defra_desnz"
    assert result.content_input.source_id == "source-001"
    assert result.content_input.content_type == "text/csv"
    assert result.content_input.format_hint == "csv"
    assert result.content_input.artifact_reference == "artifact://source/source.csv"
    assert result.content_input.checksum_sha256 == "f" * 64


def test_local_file_loader_defaults_artifact_reference_to_local_path(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "source.txt"
    file_path.write_text("hello\n", encoding="utf-8")

    result = load_parser_file_content_from_local_path(
        source_family="artificial",
        source_id="source-001",
        local_path=file_path,
        content_type="text/plain",
    )

    assert result.status == ParserFileContentLoadStatus.SUCCESS
    assert result.content_input is not None
    assert result.content_input.artifact_reference == str(file_path)


def test_missing_local_path_returns_failed_result() -> None:
    result = load_parser_file_content_from_local_path(
        source_family="defra_desnz",
        source_id="source-001",
        local_path="",
    )

    assert result.status == ParserFileContentLoadStatus.FAILED
    assert result.content_input is None
    assert result.issues[0].field_name == "local_path"


def test_nonexistent_file_returns_not_found_result(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.csv"

    result = load_parser_file_content_from_local_path(
        source_family="defra_desnz",
        source_id="source-001",
        local_path=missing_path,
    )

    assert result.status == ParserFileContentLoadStatus.NOT_FOUND
    assert result.content_input is None
    assert result.local_path == str(missing_path)
    assert result.issues[0].code == "PARSER_FILE_CONTENT_LOAD_NOT_FOUND"


def test_directory_path_returns_failed_result(tmp_path: Path) -> None:
    result = load_parser_file_content_from_local_path(
        source_family="defra_desnz",
        source_id="source-001",
        local_path=tmp_path,
    )

    assert result.status == ParserFileContentLoadStatus.FAILED
    assert result.content_input is None
    assert result.issues[0].code == "PARSER_FILE_CONTENT_LOAD_DIRECTORY"


def test_invalid_utf8_file_returns_unsupported_result(tmp_path: Path) -> None:
    file_path = tmp_path / "binary.dat"
    file_path.write_bytes(b"\xff\xfe\x00")

    result = load_parser_file_content_from_local_path(
        source_family="defra_desnz",
        source_id="source-001",
        local_path=file_path,
    )

    assert result.status == ParserFileContentLoadStatus.UNSUPPORTED
    assert result.content_input is None
    assert (
        result.issues[0].code
        == "PARSER_FILE_CONTENT_LOAD_UNSUPPORTED_ENCODING"
    )


def test_binary_like_utf8_file_returns_unsupported_result(tmp_path: Path) -> None:
    file_path = tmp_path / "binary-like.txt"
    file_path.write_bytes(b"valid utf-8\x00but binary-like")

    result = load_parser_file_content_from_local_path(
        source_family="defra_desnz",
        source_id="source-001",
        local_path=file_path,
    )

    assert result.status == ParserFileContentLoadStatus.UNSUPPORTED
    assert result.content_input is None
    assert result.issues[0].code == "PARSER_FILE_CONTENT_LOAD_BINARY_CONTENT"


def test_file_above_max_bytes_returns_unsupported_result(tmp_path: Path) -> None:
    file_path = tmp_path / "large.csv"
    file_path.write_text("abcdef", encoding="utf-8")

    result = load_parser_file_content_from_local_path(
        source_family="defra_desnz",
        source_id="source-001",
        local_path=file_path,
        max_bytes=3,
    )

    assert result.status == ParserFileContentLoadStatus.UNSUPPORTED
    assert result.content_input is None
    assert result.issues[0].code == "PARSER_FILE_CONTENT_LOAD_TOO_LARGE"


def test_loader_does_not_trigger_parser_normalization_db_or_network_behavior(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_path = tmp_path / "source.csv"
    file_path.write_text("a,b\n1,2\n", encoding="utf-8")

    def fail_connect(*args: object, **kwargs: object) -> None:
        raise AssertionError("loader must not connect to a database")

    def fail_urlopen(*args: object, **kwargs: object) -> None:
        raise AssertionError("loader must not perform network calls")

    monkeypatch.setattr(sqlite3, "connect", fail_connect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)

    result = load_parser_file_content_from_local_path(
        source_family="defra_desnz",
        source_id="source-001",
        local_path=file_path,
    )

    assert result.status == ParserFileContentLoadStatus.SUCCESS


def test_loader_module_avoids_downstream_runtime_imports() -> None:
    module_source = inspect.getsource(loader_module).lower()

    assert "parse_defra" not in module_source
    assert "normalization" not in module_source
    assert "persistence" not in module_source
    assert "psycopg" not in module_source
    assert "sqlalchemy" not in module_source
    assert "urllib" not in module_source
    assert ".execute" not in module_source
