import builtins
import sqlite3
import urllib.request
from dataclasses import fields

from carbonfactor_parser.parsers import (
    ParserFileContentInput,
    ParserFileContentValidationIssue,
    ParserFileContentValidationResult,
    create_parser_file_content_input,
    validate_parser_file_content_input,
)


def test_parser_file_content_input_can_be_created_in_memory() -> None:
    content_input = create_parser_file_content_input(
        source_family="defra_desnz",
        source_id="defra_desnz",
        content="already loaded csv text",
        content_type="text/csv",
    )

    assert isinstance(content_input, ParserFileContentInput)
    assert content_input.content == "already loaded csv text"
    assert content_input.content_type == "text/csv"


def test_parser_file_content_input_preserves_required_fields() -> None:
    content_input = create_parser_file_content_input(
        source_family="defra_desnz",
        source_id="defra_desnz",
        content=b"already loaded bytes",
    )

    assert content_input.source_family == "defra_desnz"
    assert content_input.source_id == "defra_desnz"
    assert content_input.content == b"already loaded bytes"


def test_parser_file_content_input_preserves_optional_metadata() -> None:
    content_input = create_parser_file_content_input(
        source_family="defra_desnz",
        source_id="defra_desnz",
        content="header,value\nscope,1\n",
        content_type="text/csv",
        format_hint="csv",
        artifact_reference="data/source-acquisition/defra_desnz/source.csv",
        checksum_sha256="a" * 64,
    )

    assert content_input.content_type == "text/csv"
    assert content_input.format_hint == "csv"
    assert (
        content_input.artifact_reference
        == "data/source-acquisition/defra_desnz/source.csv"
    )
    assert content_input.checksum_sha256 == "a" * 64


def test_parser_file_content_input_allows_optional_metadata_to_be_omitted() -> None:
    content_input = create_parser_file_content_input(
        source_family="defra_desnz",
        source_id="defra_desnz",
        content="already loaded content",
    )

    assert content_input.content_type is None
    assert content_input.format_hint is None
    assert content_input.artifact_reference is None
    assert content_input.checksum_sha256 is None


def test_parser_file_content_validation_accepts_valid_input() -> None:
    content_input = create_parser_file_content_input(
        source_family="defra_desnz",
        source_id="defra_desnz",
        content="already loaded content",
        content_type="text/csv",
    )

    result = validate_parser_file_content_input(content_input)

    assert isinstance(result, ParserFileContentValidationResult)
    assert result.is_valid is True
    assert result.issues == ()


def test_parser_file_content_validation_reports_blank_required_fields() -> None:
    content_input = create_parser_file_content_input(
        source_family=" ",
        source_id="",
        content=" ",
    )

    result = validate_parser_file_content_input(content_input)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "PARSER_FILE_CONTENT_MISSING_SOURCE_FAMILY",
        "PARSER_FILE_CONTENT_MISSING_SOURCE_ID",
        "PARSER_FILE_CONTENT_MISSING_CONTENT",
    )


def test_parser_file_content_validation_reports_empty_bytes_content() -> None:
    content_input = create_parser_file_content_input(
        source_family="defra_desnz",
        source_id="defra_desnz",
        content=b"",
    )

    result = validate_parser_file_content_input(content_input)

    assert result.is_valid is False
    assert _issue_codes(result) == ("PARSER_FILE_CONTENT_MISSING_CONTENT",)


def test_parser_file_content_validation_reports_blank_optional_metadata() -> None:
    content_input = create_parser_file_content_input(
        source_family="defra_desnz",
        source_id="defra_desnz",
        content="already loaded content",
        content_type=" ",
        format_hint="",
        artifact_reference=" ",
        checksum_sha256="",
    )

    result = validate_parser_file_content_input(content_input)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "PARSER_FILE_CONTENT_BLANK_CONTENT_TYPE",
        "PARSER_FILE_CONTENT_BLANK_FORMAT_HINT",
        "PARSER_FILE_CONTENT_BLANK_ARTIFACT_REFERENCE",
        "PARSER_FILE_CONTENT_BLANK_CHECKSUM_SHA256",
    )


def test_parser_file_content_validation_issue_shape_is_structured() -> None:
    content_input = create_parser_file_content_input(
        source_family="",
        source_id="defra_desnz",
        content="already loaded content",
    )

    issue = validate_parser_file_content_input(content_input).issues[0]

    assert isinstance(issue, ParserFileContentValidationIssue)
    assert issue.code == "PARSER_FILE_CONTENT_MISSING_SOURCE_FAMILY"
    assert issue.field_name == "source_family"
    assert issue.severity == "error"
    assert issue.message == "source_family must be a non-empty string."


def test_parser_file_content_contract_is_not_acquisition_or_output_shape() -> None:
    field_names = {field.name for field in fields(ParserFileContentInput)}

    assert "acquisition_status" not in field_names
    assert "acquisition_run_id" not in field_names
    assert "parser_output" not in field_names
    assert "normalization_output" not in field_names
    assert "database_record_id" not in field_names


def test_parser_file_content_creation_has_no_external_side_effects(
    monkeypatch,
    tmp_path,
) -> None:
    missing_artifact = tmp_path / "missing.csv"

    def fail_side_effect(*args, **kwargs):
        raise AssertionError("file content input must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    content_input = create_parser_file_content_input(
        source_family="defra_desnz",
        source_id="defra_desnz",
        content="already loaded content",
        artifact_reference=str(missing_artifact),
    )
    result = validate_parser_file_content_input(content_input)

    assert result.is_valid is True
    assert content_input.artifact_reference == str(missing_artifact)
    assert not missing_artifact.exists()


def _issue_codes(
    result: ParserFileContentValidationResult,
) -> tuple[str, ...]:
    return tuple(issue.code for issue in result.issues)
