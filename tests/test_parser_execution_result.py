import builtins
import sqlite3
import urllib.request
from dataclasses import fields

from carbonfactor_parser.parsers import (
    ParserExecutionIssue,
    ParserExecutionIssueSeverity,
    ParserExecutionResult,
    ParserExecutionResultStatus,
    create_parsed_raw_record,
    create_parsed_raw_record_payload,
    create_parser_execution_result,
    create_parser_input_contract,
)


def _parser_input():
    return create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference="data/source-acquisition/defra_desnz/source.csv",
        content_type="text/csv",
    )


def test_success_result_can_be_created_with_parsed_record_count() -> None:
    result = create_parser_execution_result(
        status=ParserExecutionResultStatus.SUCCESS,
        parser_input=_parser_input(),
        parsed_record_count=3,
        parser_metadata={"parser_name": "future-parser"},
    )

    assert isinstance(result, ParserExecutionResult)
    assert result.status == ParserExecutionResultStatus.SUCCESS
    assert result.source_family == "defra_desnz"
    assert result.source_id == "defra_desnz"
    assert result.parsed_record_count == 3
    assert result.issues == ()
    assert result.parser_metadata == {"parser_name": "future-parser"}


def test_success_result_can_include_raw_record_payload() -> None:
    record = create_parsed_raw_record(
        source_family="defra_desnz",
        source_id="defra_desnz",
        record_index=1,
        raw_fields={"factor_id": "F1", "unit": "kWh"},
    )
    payload = create_parsed_raw_record_payload(
        source_family="defra_desnz",
        source_id="defra_desnz",
        records=(record,),
    )

    result = create_parser_execution_result(
        status=ParserExecutionResultStatus.SUCCESS,
        parser_input=_parser_input(),
        parsed_record_count=1,
        raw_record_payload=payload,
    )

    assert result.raw_record_payload == payload
    assert result.raw_record_payload.records[0].raw_fields == {
        "factor_id": "F1",
        "unit": "kWh",
    }


def test_failed_result_can_include_issues() -> None:
    issue = ParserExecutionIssue(
        code="PARSER_EXECUTION_FAILED",
        message="Future parser failed before producing records.",
        severity=ParserExecutionIssueSeverity.ERROR,
        location="worksheet:summary",
        context={"phase": "parse"},
    )

    result = create_parser_execution_result(
        status=ParserExecutionResultStatus.FAILED,
        parser_input=_parser_input(),
        issues=(issue,),
    )

    assert result.status == ParserExecutionResultStatus.FAILED
    assert result.parsed_record_count == 0
    assert result.issues == (issue,)
    assert result.issues[0].severity == ParserExecutionIssueSeverity.ERROR


def test_unsupported_result_can_include_reason_issue() -> None:
    issue = ParserExecutionIssue(
        code="PARSER_INPUT_UNSUPPORTED_FORMAT",
        message="No parser supports this format hint.",
        severity=ParserExecutionIssueSeverity.WARNING,
        location="format_hint",
    )

    result = create_parser_execution_result(
        status=ParserExecutionResultStatus.UNSUPPORTED,
        parser_input=_parser_input(),
        issues=[issue],
    )

    assert result.status == ParserExecutionResultStatus.UNSUPPORTED
    assert result.issues == (issue,)
    assert result.issues[0].code == "PARSER_INPUT_UNSUPPORTED_FORMAT"


def test_no_records_result_is_represented_explicitly() -> None:
    result = create_parser_execution_result(
        status=ParserExecutionResultStatus.NO_RECORDS,
        parser_input=_parser_input(),
        parsed_record_count=0,
    )

    assert result.status == ParserExecutionResultStatus.NO_RECORDS
    assert result.parsed_record_count == 0


def test_execution_result_is_not_normalization_or_persistence_output() -> None:
    field_names = {field.name for field in fields(ParserExecutionResult)}

    assert "normalized_records" not in field_names
    assert "normalization_result" not in field_names
    assert "database_table" not in field_names
    assert "database_record_id" not in field_names
    assert "persistence_status" not in field_names


def test_execution_result_creation_has_no_external_side_effects(
    monkeypatch,
    tmp_path,
) -> None:
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference=str(tmp_path / "missing.csv"),
        content_type="text/csv",
    )

    def fail_side_effect(*args, **kwargs):
        raise AssertionError("result contract creation must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    result = create_parser_execution_result(
        status=ParserExecutionResultStatus.SUCCESS,
        parser_input=parser_input,
        parsed_record_count=1,
    )

    assert result.parsed_record_count == 1
    assert not (tmp_path / "missing.csv").exists()
