import builtins
import sqlite3
import urllib.request

from carbonfactor_parser.parsers import (
    DEFRA_DESNZ_MINIMAL_CONTENT_HEADER,
    ParserExecutionResult,
    ParserExecutionResultStatus,
    create_parser_file_content_input,
    parse_defra_desnz_file_content,
)


def _content_input(
    *,
    content: str | bytes = "factor_id,factor_name,unit\nF1,Electricity,kWh\n",
    artifact_reference: str = "data/source-acquisition/defra_desnz/source.csv",
):
    return create_parser_file_content_input(
        source_family="defra_desnz",
        source_id="defra_desnz",
        content=content,
        content_type="text/csv",
        format_hint="csv",
        artifact_reference=artifact_reference,
        checksum_sha256="a" * 64,
    )


def test_defra_desnz_minimal_content_header_is_deterministic() -> None:
    assert DEFRA_DESNZ_MINIMAL_CONTENT_HEADER == (
        "factor_id",
        "factor_name",
        "unit",
    )


def test_valid_in_memory_defra_desnz_content_returns_success() -> None:
    content_input = _content_input(
        content=(
            "factor_id,factor_name,unit\n"
            "F1,Electricity,kWh\n"
            "F2,Natural gas,kWh\n"
        ),
    )

    result = parse_defra_desnz_file_content(content_input)

    assert isinstance(result, ParserExecutionResult)
    assert result.status == ParserExecutionResultStatus.SUCCESS
    assert result.parsed_record_count == 2
    assert result.issues == ()
    assert result.parser_metadata == {
        "parser_kind": "minimal_defra_desnz_content_fixture",
        "is_real_source_parser": False,
        "normalization_executed": False,
    }
    assert result.raw_record_payload is not None
    assert len(result.raw_record_payload.records) == 2
    assert result.raw_record_payload.records[0].raw_fields == {
        "factor_id": "F1",
        "factor_name": "Electricity",
        "unit": "kWh",
    }
    assert result.raw_record_payload.records[0].record_index == 1
    assert result.raw_record_payload.records[0].row_number == 2


def test_parsed_record_count_is_deterministic() -> None:
    content_input = _content_input(
        content=(
            "factor_id,factor_name,unit\n"
            "F1,Electricity,kWh\n"
            "F2,Natural gas,kWh\n"
            "F3,Diesel,litre\n"
        ),
    )

    first_result = parse_defra_desnz_file_content(content_input)
    second_result = parse_defra_desnz_file_content(content_input)

    assert first_result.parsed_record_count == 3
    assert second_result.parsed_record_count == 3
    assert first_result.raw_record_payload == second_result.raw_record_payload


def test_bytes_content_is_parsed_in_memory() -> None:
    result = parse_defra_desnz_file_content(
        _content_input(content=b"factor_id,factor_name,unit\nF1,Electricity,kWh\n"),
    )

    assert result.status == ParserExecutionResultStatus.SUCCESS
    assert result.parsed_record_count == 1
    assert result.raw_record_payload is not None
    assert result.raw_record_payload.records[0].raw_fields == {
        "factor_id": "F1",
        "factor_name": "Electricity",
        "unit": "kWh",
    }


def test_empty_content_returns_no_records_issue() -> None:
    result = parse_defra_desnz_file_content(_content_input(content=" "))

    assert result.status == ParserExecutionResultStatus.NO_RECORDS
    assert result.parsed_record_count == 0
    assert result.issues[0].code == "DEFRA_DESNZ_CONTENT_EMPTY"


def test_header_only_content_returns_no_records_issue() -> None:
    result = parse_defra_desnz_file_content(
        _content_input(content="factor_id,factor_name,unit\n"),
    )

    assert result.status == ParserExecutionResultStatus.NO_RECORDS
    assert result.parsed_record_count == 0
    assert result.issues[0].code == "DEFRA_DESNZ_CONTENT_NO_RECORDS"


def test_invalid_header_returns_failed_issue() -> None:
    result = parse_defra_desnz_file_content(
        _content_input(content="factor_id,wrong,unit\nF1,Electricity,kWh\n"),
    )

    assert result.status == ParserExecutionResultStatus.FAILED
    assert result.parsed_record_count == 0
    assert result.issues[0].code == "DEFRA_DESNZ_CONTENT_INVALID_HEADER"


def test_invalid_row_returns_failed_issue() -> None:
    result = parse_defra_desnz_file_content(
        _content_input(content="factor_id,factor_name,unit\nF1,Electricity,kWh,extra\n"),
    )

    assert result.status == ParserExecutionResultStatus.FAILED
    assert result.parsed_record_count == 0
    assert result.issues[0].code == "DEFRA_DESNZ_CONTENT_INVALID_ROW"


def test_invalid_content_identity_returns_failed_issue() -> None:
    content_input = create_parser_file_content_input(
        source_family=" ",
        source_id="defra_desnz",
        content="factor_id,factor_name,unit\nF1,Electricity,kWh\n",
        content_type="text/csv",
    )

    result = parse_defra_desnz_file_content(content_input)

    assert result.status == ParserExecutionResultStatus.FAILED
    assert result.issues[0].code == "PARSER_FILE_CONTENT_MISSING_SOURCE_FAMILY"


def test_non_defra_desnz_source_family_returns_failed_issue() -> None:
    content_input = create_parser_file_content_input(
        source_family="ghg_protocol",
        source_id="ghg_protocol",
        content="factor_id,factor_name,unit\nF1,Electricity,kWh\n",
        content_type="text/csv",
    )

    result = parse_defra_desnz_file_content(content_input)

    assert result.status == ParserExecutionResultStatus.FAILED
    assert result.issues[0].code == "DEFRA_DESNZ_CONTENT_SOURCE_FAMILY_MISMATCH"


def test_invalid_bytes_return_failed_issue() -> None:
    result = parse_defra_desnz_file_content(_content_input(content=b"\xff\xfe"))

    assert result.status == ParserExecutionResultStatus.FAILED
    assert result.issues[0].code == "DEFRA_DESNZ_CONTENT_BYTES_DECODE_FAILED"


def test_helper_preserves_metadata_without_reading_artifact_reference(tmp_path) -> None:
    missing_artifact = tmp_path / "missing.csv"

    result = parse_defra_desnz_file_content(
        _content_input(artifact_reference=str(missing_artifact)),
    )

    assert result.status == ParserExecutionResultStatus.SUCCESS
    assert result.parser_input.artifact_reference == str(missing_artifact)
    assert result.parser_input.checksum_sha256 == "a" * 64
    assert result.raw_record_payload is not None
    assert result.raw_record_payload.source_context == {
        "artifact_reference": str(missing_artifact),
    }
    assert not missing_artifact.exists()


def test_defra_desnz_content_parser_has_no_external_side_effects(
    monkeypatch,
    tmp_path,
) -> None:
    missing_artifact = tmp_path / "missing.csv"
    content_input = _content_input(artifact_reference=str(missing_artifact))

    def fail_side_effect(*args, **kwargs):
        raise AssertionError("content parser must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    result = parse_defra_desnz_file_content(content_input)

    assert result.status == ParserExecutionResultStatus.SUCCESS
    assert result.parsed_record_count == 1
    assert not missing_artifact.exists()
