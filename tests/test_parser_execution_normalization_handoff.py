import builtins
import sqlite3
import urllib.request
from dataclasses import fields

from carbonfactor_parser.normalization import (
    ParserExecutionNormalizationHandoff,
    ParserExecutionNormalizationHandoffResult,
    ParserExecutionNormalizationHandoffStatus,
    build_parser_execution_normalization_handoff,
)
from carbonfactor_parser.parsers import (
    ParserExecutionResultStatus,
    create_parsed_raw_record,
    create_parsed_raw_record_payload,
    create_parser_execution_result,
    create_parser_input_contract,
)


def _parser_result(
    *,
    status: ParserExecutionResultStatus = ParserExecutionResultStatus.SUCCESS,
    parsed_record_count: int = 2,
    include_raw_payload: bool = False,
):
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="content_loaded",
        artifact_reference="memory://defra-desnz-content",
        content_type="text/csv",
    )
    return create_parser_execution_result(
        status=status,
        parser_input=parser_input,
        parsed_record_count=parsed_record_count,
        parser_metadata={"parser_kind": "minimal_defra_desnz_content_fixture"},
        raw_record_payload=(
            create_parsed_raw_record_payload(
                source_family="defra_desnz",
                source_id="defra_desnz",
                records=(
                    create_parsed_raw_record(
                        source_family="defra_desnz",
                        source_id="defra_desnz",
                        record_index=1,
                        raw_fields={"factor_id": "F1"},
                    ),
                ),
            )
            if include_raw_payload
            else None
        ),
    )


def test_successful_parser_execution_result_creates_ready_handoff() -> None:
    result = build_parser_execution_normalization_handoff(_parser_result())

    assert isinstance(result, ParserExecutionNormalizationHandoffResult)
    assert result.status == ParserExecutionNormalizationHandoffStatus.READY
    assert isinstance(result.handoff, ParserExecutionNormalizationHandoff)
    assert result.issues == ()


def test_failed_parser_execution_result_does_not_create_ready_handoff() -> None:
    result = build_parser_execution_normalization_handoff(
        _parser_result(status=ParserExecutionResultStatus.FAILED),
    )

    assert result.status == ParserExecutionNormalizationHandoffStatus.NOT_READY
    assert result.handoff is None
    assert result.issues[0].code == "PARSER_EXECUTION_HANDOFF_NOT_READY"
    assert result.issues[0].parser_status == ParserExecutionResultStatus.FAILED


def test_unsupported_parser_execution_result_does_not_create_ready_handoff() -> None:
    result = build_parser_execution_normalization_handoff(
        _parser_result(status=ParserExecutionResultStatus.UNSUPPORTED),
    )

    assert result.status == ParserExecutionNormalizationHandoffStatus.NOT_READY
    assert result.handoff is None
    assert result.issues[0].parser_status == ParserExecutionResultStatus.UNSUPPORTED


def test_no_records_parser_execution_result_does_not_create_ready_handoff() -> None:
    result = build_parser_execution_normalization_handoff(
        _parser_result(
            status=ParserExecutionResultStatus.NO_RECORDS,
            parsed_record_count=0,
        ),
    )

    assert result.status == ParserExecutionNormalizationHandoffStatus.NOT_READY
    assert result.handoff is None
    assert result.issues[0].parser_status == ParserExecutionResultStatus.NO_RECORDS


def test_parser_identity_metadata_is_preserved() -> None:
    result = build_parser_execution_normalization_handoff(_parser_result())

    assert result.handoff is not None
    assert result.handoff.source_family == "defra_desnz"
    assert result.handoff.source_id == "defra_desnz"
    assert result.handoff.parser_status == ParserExecutionResultStatus.SUCCESS
    assert result.handoff.parser_metadata == {
        "parser_kind": "minimal_defra_desnz_content_fixture",
    }


def test_parsed_record_count_is_preserved() -> None:
    result = build_parser_execution_normalization_handoff(
        _parser_result(parsed_record_count=5),
    )

    assert result.handoff is not None
    assert result.handoff.parsed_record_count == 5
    assert result.handoff.parsed_records_payload_status == "deferred"


def test_raw_record_payload_is_preserved_when_available() -> None:
    result = build_parser_execution_normalization_handoff(
        _parser_result(parsed_record_count=1, include_raw_payload=True),
    )

    assert result.handoff is not None
    assert result.handoff.parsed_records_payload_status == "available"
    assert result.handoff.raw_record_payload is not None
    assert result.handoff.raw_record_payload.records[0].raw_fields == {
        "factor_id": "F1",
    }


def test_handoff_has_no_normalized_output_or_persistence_fields() -> None:
    field_names = {field.name for field in fields(ParserExecutionNormalizationHandoff)}

    assert "normalized_records" not in field_names
    assert "normalization_result" not in field_names
    assert "database_table" not in field_names
    assert "database_record_id" not in field_names
    assert "persistence_status" not in field_names


def test_handoff_has_no_file_http_normalization_or_db_side_effects(
    monkeypatch,
    tmp_path,
) -> None:
    missing_artifact = tmp_path / "missing.csv"
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="content_loaded",
        artifact_reference=str(missing_artifact),
        content_type="text/csv",
    )
    parser_result = create_parser_execution_result(
        status=ParserExecutionResultStatus.SUCCESS,
        parser_input=parser_input,
        parsed_record_count=1,
    )

    def fail_side_effect(*args, **kwargs):
        raise AssertionError("handoff must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    result = build_parser_execution_normalization_handoff(parser_result)

    assert result.status == ParserExecutionNormalizationHandoffStatus.READY
    assert not missing_artifact.exists()
