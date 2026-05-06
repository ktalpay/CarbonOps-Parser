import builtins
import sqlite3
import urllib.request
from dataclasses import fields

import pytest

from carbonfactor_parser.normalization import (
    NormalizationInput,
    NormalizationInputBuildStatus,
    NormalizationInputRecord,
    build_normalization_input_from_parser_execution_handoff,
    build_normalization_input_from_raw_payload,
    build_parser_execution_normalization_handoff,
    create_normalization_input_from_raw_payload,
    create_normalization_input_record_from_raw_record,
    validate_normalization_input,
    validate_normalization_input_record,
)
from carbonfactor_parser.parsers import (
    ParserExecutionResultStatus,
    create_parsed_raw_record,
    create_parsed_raw_record_payload,
    create_parser_execution_result,
    create_parser_input_contract,
)


def _raw_payload():
    return create_parsed_raw_record_payload(
        source_family="defra_desnz",
        source_id="defra_desnz",
        records=(
            create_parsed_raw_record(
                source_family="defra_desnz",
                source_id="defra_desnz",
                record_index=1,
                row_number=2,
                raw_fields={
                    " Factor ID ": " F1 ",
                    "Unit": "kWh",
                    "Value": "001.20",
                },
                parser_metadata={"parser_kind": "minimal"},
                source_context={"artifact_reference": "memory://defra"},
            ),
            create_parsed_raw_record(
                source_family="defra_desnz",
                source_id="defra_desnz",
                record_index=2,
                row_number=3,
                raw_fields={
                    " Factor ID ": " F2 ",
                    "Unit": "kg",
                    "Value": "000.50",
                },
            ),
        ),
        parser_metadata={"parser_kind": "minimal"},
        source_context={"artifact_reference": "memory://defra"},
    )


def _parser_result_with_raw_payload(
    status: ParserExecutionResultStatus = ParserExecutionResultStatus.SUCCESS,
):
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="content_loaded",
        artifact_reference="memory://defra",
        content_type="text/csv",
    )
    return create_parser_execution_result(
        status=status,
        parser_input=parser_input,
        parsed_record_count=2 if status == ParserExecutionResultStatus.SUCCESS else 0,
        raw_record_payload=_raw_payload(),
    )


def test_normalization_input_can_be_created_from_raw_parser_payload() -> None:
    normalization_input = create_normalization_input_from_raw_payload(_raw_payload())

    assert isinstance(normalization_input, NormalizationInput)
    assert normalization_input.source_family == "defra_desnz"
    assert normalization_input.source_id == "defra_desnz"
    assert len(normalization_input.records) == 2


def test_raw_record_identity_and_order_are_preserved() -> None:
    result = build_normalization_input_from_raw_payload(_raw_payload())

    assert result.status == NormalizationInputBuildStatus.READY
    assert result.normalization_input is not None
    assert [
        (record.record_index, record.row_number)
        for record in result.normalization_input.records
    ] == [(1, 2), (2, 3)]


def test_raw_fields_are_preserved_exactly_without_canonicalization() -> None:
    record = create_normalization_input_record_from_raw_record(
        _raw_payload().records[0],
    )

    assert isinstance(record, NormalizationInputRecord)
    assert record.raw_fields == {
        " Factor ID ": " F1 ",
        "Unit": "kWh",
        "Value": "001.20",
    }
    assert "factor_id" not in record.raw_fields
    assert record.raw_fields["Value"] == "001.20"


def test_parser_and_source_metadata_are_preserved() -> None:
    normalization_input = create_normalization_input_from_raw_payload(_raw_payload())

    assert normalization_input.parser_metadata == {"parser_kind": "minimal"}
    assert normalization_input.source_context == {
        "artifact_reference": "memory://defra",
    }
    assert normalization_input.records[0].parser_metadata == {
        "parser_kind": "minimal",
    }
    assert normalization_input.records[0].source_context == {
        "artifact_reference": "memory://defra",
    }


def test_ready_handoff_with_raw_payload_builds_normalization_input() -> None:
    handoff_result = build_parser_execution_normalization_handoff(
        _parser_result_with_raw_payload(),
    )

    result = build_normalization_input_from_parser_execution_handoff(handoff_result)

    assert result.status == NormalizationInputBuildStatus.READY
    assert result.normalization_input is not None
    assert result.normalization_input.records[0].raw_fields[" Factor ID "] == " F1 "


@pytest.mark.parametrize(
    "status",
    (
        ParserExecutionResultStatus.FAILED,
        ParserExecutionResultStatus.UNSUPPORTED,
        ParserExecutionResultStatus.NO_RECORDS,
    ),
)
def test_non_success_parser_results_do_not_produce_ready_normalization_input(
    status,
) -> None:
    handoff_result = build_parser_execution_normalization_handoff(
        _parser_result_with_raw_payload(status=status),
    )

    result = build_normalization_input_from_parser_execution_handoff(handoff_result)

    assert result.status == NormalizationInputBuildStatus.NOT_READY
    assert result.normalization_input is None
    assert result.issues[0].code == "NORMALIZATION_INPUT_HANDOFF_NOT_READY"


def test_ready_handoff_without_raw_payload_does_not_build_normalization_input() -> None:
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="content_loaded",
        artifact_reference="memory://defra",
    )
    parser_result = create_parser_execution_result(
        status=ParserExecutionResultStatus.SUCCESS,
        parser_input=parser_input,
        parsed_record_count=1,
    )
    handoff_result = build_parser_execution_normalization_handoff(parser_result)

    result = build_normalization_input_from_parser_execution_handoff(handoff_result)

    assert result.status == NormalizationInputBuildStatus.NOT_READY
    assert result.normalization_input is None
    assert result.issues[0].code == "NORMALIZATION_INPUT_RAW_PAYLOAD_MISSING"


def test_normalization_input_has_no_normalized_output_or_persistence_fields() -> None:
    input_fields = {field.name for field in fields(NormalizationInput)}
    record_fields = {field.name for field in fields(NormalizationInputRecord)}

    assert "normalized_records" not in input_fields
    assert "normalized_fields" not in record_fields
    assert "canonical_fields" not in record_fields
    assert "emission_category" not in record_fields
    assert "database_table" not in input_fields
    assert "database_record_id" not in record_fields


def test_validation_catches_blank_identity_and_missing_raw_fields() -> None:
    record = NormalizationInputRecord(
        source_family=" ",
        source_id="",
        record_index=0,
        raw_fields={},
    )

    result = validate_normalization_input_record(record)

    assert result.is_valid is False
    assert tuple(issue.code for issue in result.issues) == (
        "NORMALIZATION_INPUT_MISSING_SOURCE_FAMILY",
        "NORMALIZATION_INPUT_MISSING_SOURCE_ID",
        "NORMALIZATION_INPUT_INVALID_RECORD_INDEX",
        "NORMALIZATION_INPUT_MISSING_RAW_FIELDS",
    )


def test_payload_validation_reports_record_paths_and_empty_records() -> None:
    normalization_input = NormalizationInput(
        source_family="defra_desnz",
        source_id="defra_desnz",
        records=(),
    )

    empty_result = validate_normalization_input(normalization_input)

    assert empty_result.is_valid is False
    assert empty_result.issues[0].field_name == "records"

    invalid_record_input = NormalizationInput(
        source_family="defra_desnz",
        source_id="defra_desnz",
        records=(
            NormalizationInputRecord(
                source_family="defra_desnz",
                source_id="defra_desnz",
                record_index=0,
                raw_fields={},
            ),
        ),
    )
    invalid_result = validate_normalization_input(invalid_record_input)

    assert [issue.field_name for issue in invalid_result.issues] == [
        "records[1].record_index",
        "records[1].raw_fields",
    ]


def test_normalization_input_build_has_no_external_side_effects(
    monkeypatch,
    tmp_path,
) -> None:
    missing_artifact = tmp_path / "missing.csv"

    def fail_side_effect(*args, **kwargs):
        raise AssertionError("normalization input must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    raw_payload = create_parsed_raw_record_payload(
        source_family="defra_desnz",
        source_id="defra_desnz",
        records=(
            create_parsed_raw_record(
                source_family="defra_desnz",
                source_id="defra_desnz",
                record_index=1,
                raw_fields={"artifact_reference": str(missing_artifact)},
            ),
        ),
    )

    result = build_normalization_input_from_raw_payload(raw_payload)

    assert result.status == NormalizationInputBuildStatus.READY
    assert not missing_artifact.exists()
