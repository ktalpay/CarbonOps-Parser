from __future__ import annotations

import builtins
import json
import sqlite3
import urllib.request
from decimal import Decimal

from carbonfactor_parser.parsers import (
    IPCC_EFDB_NORMALIZED_CONTENT_HEADER,
    IpccEfdbParserAdapter,
    ParserExecutionResult,
    ParserExecutionResultStatus,
    create_parser_file_content_input,
    create_parser_input_contract,
    parse_ipcc_efdb_file_content,
)


FIXTURE_DIR = "tests/fixtures/source_documents/ipcc_efdb"
PARITY_EXPECTATIONS = (
    "tests/fixtures/parity/ipcc_efdb_normalized_output_expectations.json"
)


def _content_input(
    *,
    content: str | bytes,
    artifact_reference: str = f"{FIXTURE_DIR}/ipcc_efdb_sample_factors.csv",
):
    return create_parser_file_content_input(
        source_family="ipcc_efdb",
        source_id="ipcc_efdb",
        content=content,
        content_type="text/csv",
        format_hint="csv",
        artifact_reference=artifact_reference,
        checksum_sha256="d" * 64,
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


def test_ipcc_efdb_normalized_content_header_is_deterministic() -> None:
    assert list(IPCC_EFDB_NORMALIZED_CONTENT_HEADER) == _parity_expectations()["header"]


def test_valid_ipcc_efdb_content_returns_normalized_records() -> None:
    result = parse_ipcc_efdb_file_content(
        _content_input(content=_fixture_content("ipcc_efdb_sample_factors.csv")),
    )

    assert isinstance(result, ParserExecutionResult)
    assert result.status == ParserExecutionResultStatus.SUCCESS
    assert result.parsed_record_count == 2
    assert result.parser_metadata == {
        "parser_kind": "ipcc_efdb_normalized_content",
        "is_real_source_parser": True,
        "normalization_executed": True,
        "skipped_record_count": 1,
    }
    assert tuple(issue.code for issue in result.issues) == (
        "IPCC_EFDB_CONTENT_UNSUPPORTED_ROW_SKIPPED",
    )
    assert result.raw_record_payload is not None
    record = result.raw_record_payload.records[0]
    assert record.record_index == 1
    assert record.row_number == 2
    assert record.raw_fields == {
        "source_family": "ipcc_efdb",
        "source_id": "ipcc_efdb",
        "source_year": 2006,
        "source_version": "efdb-v2024",
        "factor_id": "IPCC-ENERGY-CO2",
        "factor_name": "Stationary combustion CO2",
        "factor_value": Decimal("56.1"),
        "unit": "t CO2/TJ",
        "category": "Energy",
        "subcategory": "Stationary combustion",
        "ipcc_sector": "1A",
        "gas": "CO2",
        "region": "Global",
        "technology": "Default",
        "provenance_artifact_reference": (
            "tests/fixtures/source_documents/ipcc_efdb/"
            "ipcc_efdb_sample_factors.csv"
        ),
        "provenance_checksum_algorithm": "sha256",
        "provenance_checksum_value": "d" * 64,
        "provenance_row_number": 2,
        "provenance": "worksheet:EFDB row 12",
        "source_family_master_id": (
            "ipcc_master_2006_efdb-v2024_IPCC-ENERGY-CO2"
        ),
        "source_family_detail_id": (
            "ipcc_detail_2006_efdb-v2024_IPCC-ENERGY-CO2"
        ),
        "master_external_key": "2006:efdb-v2024:IPCC-ENERGY-CO2",
        "detail_external_key": "IPCC-ENERGY-CO2:t CO2/TJ:CO2:1A",
    }
    assert record.source_context == {
        "artifact_reference": (
            "tests/fixtures/source_documents/ipcc_efdb/"
            "ipcc_efdb_sample_factors.csv"
        ),
        "checksum_sha256": "d" * 64,
        "row_number": 2,
        "source_year": "2006",
        "source_version": "efdb-v2024",
        "provenance": "worksheet:EFDB row 12",
    }


def test_valid_ipcc_efdb_content_matches_shared_parity_expectations() -> None:
    expectations = _parity_expectations()

    result = parse_ipcc_efdb_file_content(
        _content_input(content=_fixture_content("ipcc_efdb_sample_factors.csv")),
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


def test_ipcc_efdb_content_parser_is_deterministic_for_fixture_input() -> None:
    content_input = _content_input(
        content=_fixture_content("ipcc_efdb_sample_factors.csv"),
    )

    first_result = parse_ipcc_efdb_file_content(content_input)
    second_result = parse_ipcc_efdb_file_content(content_input)

    assert first_result == second_result
    assert first_result.parsed_record_count == 2


def test_malformed_ipcc_efdb_rows_return_structured_errors() -> None:
    expectations = _parity_expectations()
    result = parse_ipcc_efdb_file_content(
        _content_input(content=_fixture_content("ipcc_efdb_malformed_factors.csv")),
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
    assert result.issues[0].context == {
        "row_number": 2,
        "field_name": "source_year",
        "raw_value": "year",
    }


def test_unsupported_ipcc_efdb_rows_are_skipped_with_warning() -> None:
    expectations = _parity_expectations()
    content = (
        "record_type,source_year,source_version,factor_id,factor_name,"
        "factor_value,unit,category,subcategory,ipcc_sector,gas,region,"
        "technology,provenance\n"
        "metadata,2006,efdb-v2024,IPCC-NOTE-001,Workbook note,0,none,"
        "Notes,,metadata,CO2,,,skip\n"
    )

    result = parse_ipcc_efdb_file_content(_content_input(content=content))

    assert result.status.value == expectations["unsupported_only_status"]["python"]
    assert result.parsed_record_count == 0
    assert tuple(issue.code for issue in result.issues) == tuple(
        expectations["unsupported_only_issue_codes"],
    )
    assert result.issues[0].context == {
        "row_number": 2,
        "record_type": "metadata",
    }


def test_invalid_ipcc_efdb_header_returns_failed_issue() -> None:
    result = parse_ipcc_efdb_file_content(
        _content_input(content="record_type,source_year\nemission_factor,2006\n"),
    )

    assert result.status == ParserExecutionResultStatus.FAILED
    assert result.issues[0].code == "IPCC_EFDB_CONTENT_INVALID_HEADER"


def test_non_ipcc_source_family_returns_failed_issue() -> None:
    content_input = create_parser_file_content_input(
        source_family="ghg_protocol",
        source_id="ghg_protocol",
        content=_fixture_content("ipcc_efdb_sample_factors.csv"),
        content_type="text/csv",
    )

    result = parse_ipcc_efdb_file_content(content_input)

    assert result.status == ParserExecutionResultStatus.FAILED
    assert result.issues[0].code == "IPCC_EFDB_CONTENT_SOURCE_FAMILY_MISMATCH"


def test_invalid_bytes_return_failed_issue() -> None:
    result = parse_ipcc_efdb_file_content(_content_input(content=b"\xff\xfe"))

    assert result.status == ParserExecutionResultStatus.FAILED
    assert result.issues[0].code == "IPCC_EFDB_CONTENT_BYTES_DECODE_FAILED"


def test_ipcc_efdb_adapter_delegates_already_loaded_content() -> None:
    adapter = IpccEfdbParserAdapter()

    result = adapter.parse_content(
        _content_input(content=_fixture_content("ipcc_efdb_sample_factors.csv")),
    )

    assert result.status == ParserExecutionResultStatus.SUCCESS
    assert result.parsed_record_count == 2


def test_ipcc_efdb_adapter_matches_csv_metadata_only() -> None:
    adapter = IpccEfdbParserAdapter()
    parser_input = create_parser_input_contract(
        source_family="ipcc_efdb",
        source_id="ipcc_efdb",
        acquisition_status="acquired",
        artifact_reference="tests/fixtures/source_documents/ipcc_efdb/source.csv",
        content_type="text/csv",
        format_hint="csv",
    )
    xlsx_input = create_parser_input_contract(
        source_family="ipcc_efdb",
        source_id="ipcc_efdb",
        acquisition_status="acquired",
        artifact_reference="tests/fixtures/source_documents/ipcc_efdb/source.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        format_hint="xlsx",
    )

    assert adapter.can_parse(parser_input) is True
    assert adapter.can_parse(xlsx_input) is False


def test_ipcc_efdb_content_parser_does_not_read_artifact_reference(
    monkeypatch,
    tmp_path,
) -> None:
    missing_artifact = tmp_path / "missing-ipcc.csv"
    content = _fixture_content("ipcc_efdb_sample_factors.csv")

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

    result = parse_ipcc_efdb_file_content(
        _content_input(content=content, artifact_reference=str(missing_artifact)),
    )

    assert result.status == ParserExecutionResultStatus.SUCCESS
    assert not missing_artifact.exists()
