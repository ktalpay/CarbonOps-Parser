from __future__ import annotations

import builtins
import json
from decimal import Decimal
import sqlite3
import urllib.request

from carbonfactor_parser.parsers import (
    GHG_PROTOCOL_NORMALIZED_CONTENT_HEADER,
    ParserExecutionResult,
    ParserExecutionResultStatus,
    create_parser_file_content_input,
    parse_ghg_protocol_file_content,
)


FIXTURE_DIR = "tests/fixtures/source_documents/ghg_protocol"
PARITY_EXPECTATIONS = (
    "tests/fixtures/parity/ghg_protocol_normalized_output_expectations.json"
)


def _content_input(
    *,
    content: str | bytes,
    artifact_reference: str = f"{FIXTURE_DIR}/ghg_protocol_sample_factors.csv",
):
    return create_parser_file_content_input(
        source_family="ghg_protocol",
        source_id="ghg_protocol",
        content=content,
        content_type="text/csv",
        format_hint="csv",
        artifact_reference=artifact_reference,
        checksum_sha256="b" * 64,
    )


def _fixture_content(name: str) -> str:
    with open(f"{FIXTURE_DIR}/{name}", encoding="utf-8") as fixture:
        return fixture.read()


def _parity_expectations() -> dict[str, object]:
    with open(PARITY_EXPECTATIONS, encoding="utf-8") as fixture:
        return json.load(fixture)


def _canonical_fields(raw_fields: dict[str, object]) -> list[list[str | None]]:
    expected_keys = [
        key for key, _ in _parity_expectations()["sample_rows"][0]["fields"]
    ]
    return [
        [key, None if raw_fields[key] is None else str(raw_fields[key])]
        for key in expected_keys
    ]


def test_ghg_protocol_normalized_content_header_is_deterministic() -> None:
    assert list(GHG_PROTOCOL_NORMALIZED_CONTENT_HEADER) == _parity_expectations()["header"]


def test_valid_ghg_protocol_content_returns_normalized_records() -> None:
    result = parse_ghg_protocol_file_content(
        _content_input(content=_fixture_content("ghg_protocol_sample_factors.csv")),
    )

    assert isinstance(result, ParserExecutionResult)
    assert result.status == ParserExecutionResultStatus.SUCCESS
    assert result.parsed_record_count == 2
    assert result.parser_metadata == {
        "parser_kind": "ghg_protocol_normalized_content",
        "is_real_source_parser": True,
        "normalization_executed": True,
        "skipped_record_count": 1,
    }
    assert tuple(issue.code for issue in result.issues) == (
        "GHG_PROTOCOL_CONTENT_UNSUPPORTED_ROW_SKIPPED",
    )
    assert result.raw_record_payload is not None
    first = result.raw_record_payload.records[0]
    assert first.record_index == 1
    assert first.row_number == 2
    assert first.raw_fields == {
        "source_family": "ghg_protocol",
        "source_id": "ghg_protocol",
        "source_year": 2024,
        "source_version": "v1",
        "factor_id": "GHG-ELEC-001",
        "factor_name": "Grid electricity",
        "factor_value": Decimal("0.233"),
        "unit": "kg CO2e/kWh",
        "category": "Stationary combustion",
        "subcategory": "Electricity",
        "scope": "Scope 2",
        "gas": "CO2e",
        "provenance_note": "fixture row 1",
        "provenance_artifact_reference": (
            "tests/fixtures/source_documents/ghg_protocol/"
            "ghg_protocol_sample_factors.csv"
        ),
        "provenance_checksum_algorithm": "sha256",
        "provenance_checksum_value": "b" * 64,
        "provenance_row_number": 2,
        "source_family_master_id": "ghg_master_2024_v1_GHG-ELEC-001",
        "source_family_detail_id": "ghg_detail_2024_v1_GHG-ELEC-001",
        "master_external_key": "2024:v1:GHG-ELEC-001",
        "detail_external_key": "GHG-ELEC-001:kg CO2e/kWh",
    }


def test_valid_ghg_protocol_content_matches_shared_parity_expectations() -> None:
    expectations = _parity_expectations()

    result = parse_ghg_protocol_file_content(
        _content_input(content=_fixture_content("ghg_protocol_sample_factors.csv")),
    )

    assert result.status.value == expectations["sample_status"]["python"]
    assert tuple(issue.code for issue in result.issues) == tuple(
        expectations["sample_issue_codes"],
    )
    assert result.raw_record_payload is not None
    assert result.parsed_record_count == len(expectations["sample_rows"])

    for record, expected_row in zip(
        result.raw_record_payload.records,
        expectations["sample_rows"],
        strict=True,
    ):
        assert record.row_number == expected_row["source_row_number"]
        assert _canonical_fields(record.raw_fields) == expected_row["fields"]


def test_ghg_protocol_content_parser_is_deterministic_for_fixture_input() -> None:
    content_input = _content_input(
        content=_fixture_content("ghg_protocol_sample_factors.csv"),
    )

    first_result = parse_ghg_protocol_file_content(content_input)
    second_result = parse_ghg_protocol_file_content(content_input)

    assert first_result == second_result
    assert first_result.parsed_record_count == 2


def test_malformed_ghg_protocol_rows_return_structured_errors() -> None:
    expectations = _parity_expectations()
    result = parse_ghg_protocol_file_content(
        _content_input(content=_fixture_content("ghg_protocol_malformed_factors.csv")),
    )

    assert result.status.value == expectations["malformed_status"]["python"]
    assert result.parsed_record_count == 0
    assert result.raw_record_payload is None
    assert tuple(issue.code for issue in result.issues) == tuple(
        issue["code"] for issue in expectations["malformed_issues"]
    )
    assert tuple(issue.location for issue in result.issues) == tuple(
        issue["python_location"] for issue in expectations["malformed_issues"]
    )
    assert result.issues[0].context == {"row_number": 2}


def test_unsupported_ghg_protocol_rows_are_skipped_with_warning() -> None:
    expectations = _parity_expectations()
    content = (
        "record_type,source_year,source_version,factor_id,factor_name,"
        "factor_value,unit,category,subcategory,scope,gas,provenance_note\n"
        "metadata,2024,v1,NOTE-001,Workbook note,0,none,Notes,,,,skip\n"
    )

    result = parse_ghg_protocol_file_content(_content_input(content=content))

    assert result.status.value == expectations["unsupported_only_status"]["python"]
    assert result.parsed_record_count == 0
    assert tuple(issue.code for issue in result.issues) == tuple(
        expectations["unsupported_only_issue_codes"],
    )
    assert result.issues[0].context == {
        "row_number": 2,
        "record_type": "metadata",
    }


def test_invalid_ghg_protocol_header_returns_failed_issue() -> None:
    result = parse_ghg_protocol_file_content(
        _content_input(content="record_type,source_year\nemission_factor,2024\n"),
    )

    assert result.status == ParserExecutionResultStatus.FAILED
    assert result.issues[0].code == "GHG_PROTOCOL_CONTENT_INVALID_HEADER"


def test_non_ghg_source_family_returns_failed_issue() -> None:
    content_input = create_parser_file_content_input(
        source_family="defra_desnz",
        source_id="defra_desnz",
        content=_fixture_content("ghg_protocol_sample_factors.csv"),
        content_type="text/csv",
    )

    result = parse_ghg_protocol_file_content(content_input)

    assert result.status == ParserExecutionResultStatus.FAILED
    assert result.issues[0].code == "GHG_PROTOCOL_CONTENT_SOURCE_FAMILY_MISMATCH"


def test_invalid_bytes_return_failed_issue() -> None:
    result = parse_ghg_protocol_file_content(_content_input(content=b"\xff\xfe"))

    assert result.status == ParserExecutionResultStatus.FAILED
    assert result.issues[0].code == "GHG_PROTOCOL_CONTENT_BYTES_DECODE_FAILED"


def test_ghg_protocol_content_parser_does_not_read_artifact_reference(
    monkeypatch,
    tmp_path,
) -> None:
    missing_artifact = tmp_path / "missing-ghg.csv"
    content = _fixture_content("ghg_protocol_sample_factors.csv")

    real_open = builtins.open

    def fail_unexpected_open(path, *args, **kwargs):
        if path == str(missing_artifact):
            raise AssertionError("parser must not read artifact_reference")
        return real_open(path, *args, **kwargs)

    def fail_side_effect(*args, **kwargs):
        raise AssertionError("content parser must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_unexpected_open)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    result = parse_ghg_protocol_file_content(
        _content_input(content=content, artifact_reference=str(missing_artifact)),
    )

    assert result.status == ParserExecutionResultStatus.SUCCESS
    assert not missing_artifact.exists()
