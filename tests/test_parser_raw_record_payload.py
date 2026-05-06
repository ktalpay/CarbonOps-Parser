import builtins
import sqlite3
import urllib.request
from dataclasses import fields

from carbonfactor_parser.parsers import (
    ParsedRawRecord,
    ParsedRawRecordPayload,
    ParsedRawRecordValidationIssue,
    ParsedRawRecordValidationResult,
    create_parsed_raw_record,
    create_parsed_raw_record_payload,
    validate_parsed_raw_record,
    validate_parsed_raw_record_payload,
)


def test_raw_parsed_record_can_be_created_in_memory() -> None:
    record = create_parsed_raw_record(
        source_family="defra_desnz",
        source_id="defra_desnz",
        record_index=1,
        row_number=2,
        raw_fields={"factor_id": "F1", "unit": "kWh"},
    )

    assert isinstance(record, ParsedRawRecord)
    assert record.source_family == "defra_desnz"
    assert record.record_index == 1
    assert record.row_number == 2


def test_raw_fields_are_preserved_exactly() -> None:
    raw_fields = {"factor_id": " F1 ", "unit": "kWh", "value": "001.20"}

    record = create_parsed_raw_record(
        source_family="defra_desnz",
        source_id="defra_desnz",
        record_index=1,
        raw_fields=raw_fields,
    )

    assert record.raw_fields == raw_fields


def test_record_index_and_row_number_are_deterministic() -> None:
    first = create_parsed_raw_record(
        source_family="defra_desnz",
        source_id="defra_desnz",
        record_index=3,
        row_number=4,
        raw_fields={"factor_id": "F3"},
    )
    second = create_parsed_raw_record(
        source_family="defra_desnz",
        source_id="defra_desnz",
        record_index=3,
        row_number=4,
        raw_fields={"factor_id": "F3"},
    )

    assert first == second


def test_raw_payload_collection_preserves_records_and_metadata() -> None:
    record = create_parsed_raw_record(
        source_family="defra_desnz",
        source_id="defra_desnz",
        record_index=1,
        raw_fields={"factor_id": "F1"},
        parser_metadata={"parser_kind": "minimal"},
        source_context={"artifact_reference": "memory://content"},
    )

    payload = create_parsed_raw_record_payload(
        source_family="defra_desnz",
        source_id="defra_desnz",
        records=(record,),
        parser_metadata={"parser_kind": "minimal"},
        source_context={"artifact_reference": "memory://content"},
    )

    assert isinstance(payload, ParsedRawRecordPayload)
    assert payload.records == (record,)
    assert payload.parser_metadata == {"parser_kind": "minimal"}
    assert payload.source_context == {"artifact_reference": "memory://content"}


def test_raw_payload_is_not_normalized_or_persistence_output() -> None:
    record_fields = {field.name for field in fields(ParsedRawRecord)}
    payload_fields = {field.name for field in fields(ParsedRawRecordPayload)}

    assert "normalized_fields" not in record_fields
    assert "normalized_records" not in payload_fields
    assert "database_table" not in record_fields
    assert "database_record_id" not in payload_fields
    assert "persistence_status" not in payload_fields


def test_raw_record_validation_accepts_valid_record() -> None:
    record = create_parsed_raw_record(
        source_family="defra_desnz",
        source_id="defra_desnz",
        record_index=1,
        raw_fields={"factor_id": "F1"},
    )

    result = validate_parsed_raw_record(record)

    assert isinstance(result, ParsedRawRecordValidationResult)
    assert result.is_valid is True
    assert result.issues == ()


def test_raw_record_validation_catches_blank_identity_and_missing_fields() -> None:
    record = create_parsed_raw_record(
        source_family=" ",
        source_id="",
        record_index=0,
        raw_fields={},
    )

    result = validate_parsed_raw_record(record)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "PARSED_RAW_RECORD_MISSING_SOURCE_FAMILY",
        "PARSED_RAW_RECORD_MISSING_SOURCE_ID",
        "PARSED_RAW_RECORD_INVALID_RECORD_INDEX",
        "PARSED_RAW_RECORD_MISSING_RAW_FIELDS",
    )


def test_payload_validation_reports_record_issues_with_paths() -> None:
    record = create_parsed_raw_record(
        source_family="defra_desnz",
        source_id="defra_desnz",
        record_index=0,
        raw_fields={},
    )
    payload = create_parsed_raw_record_payload(
        source_family="defra_desnz",
        source_id="defra_desnz",
        records=(record,),
    )

    result = validate_parsed_raw_record_payload(payload)

    assert result.is_valid is False
    assert [issue.field_name for issue in result.issues] == [
        "records[1].record_index",
        "records[1].raw_fields",
    ]


def test_validation_issue_shape_is_structured() -> None:
    record = create_parsed_raw_record(
        source_family="",
        source_id="defra_desnz",
        record_index=1,
        raw_fields={"factor_id": "F1"},
    )

    issue = validate_parsed_raw_record(record).issues[0]

    assert isinstance(issue, ParsedRawRecordValidationIssue)
    assert issue.code == "PARSED_RAW_RECORD_MISSING_SOURCE_FAMILY"
    assert issue.field_name == "source_family"
    assert issue.severity == "error"


def test_raw_record_payload_has_no_external_side_effects(monkeypatch, tmp_path) -> None:
    missing_artifact = tmp_path / "missing.csv"

    def fail_side_effect(*args, **kwargs):
        raise AssertionError("raw record payload must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    record = create_parsed_raw_record(
        source_family="defra_desnz",
        source_id="defra_desnz",
        record_index=1,
        raw_fields={"artifact_reference": str(missing_artifact)},
    )
    payload = create_parsed_raw_record_payload(
        source_family="defra_desnz",
        source_id="defra_desnz",
        records=(record,),
    )

    assert validate_parsed_raw_record_payload(payload).is_valid is True
    assert not missing_artifact.exists()


def _issue_codes(result: ParsedRawRecordValidationResult) -> tuple[str, ...]:
    return tuple(issue.code for issue in result.issues)
