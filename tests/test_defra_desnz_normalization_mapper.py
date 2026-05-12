import builtins
import sqlite3
import urllib.request

from carbonfactor_parser.normalization import (
    DEFRA_DESNZ_MINIMAL_NORMALIZATION_FIELDS,
    DEFRA_DESNZ_NORMALIZED_MAPPING_FIELDS,
    DefraDesnzNormalizationMappingResult,
    DefraDesnzNormalizationMappingStatus,
    NormalizationInput,
    NormalizationInputRecord,
    NormalizationResult,
    build_normalization_input_from_parser_execution_handoff,
    build_parser_execution_normalization_handoff,
    map_defra_desnz_normalization_input,
    map_defra_desnz_normalization_input_record,
)
from carbonfactor_parser.parsers import (
    DEFRA_DESNZ_NORMALIZED_CONTENT_HEADER,
    ParserExecutionResultStatus,
    create_parser_file_content_input,
    parse_defra_desnz_file_content,
)


def _normalization_input(records=None) -> NormalizationInput:
    return NormalizationInput(
        source_family="defra_desnz",
        source_id="defra_desnz",
        records=records
        if records is not None
        else (
            NormalizationInputRecord(
                source_family="defra_desnz",
                source_id="defra_desnz",
                record_index=1,
                row_number=2,
                raw_fields={
                    "factor_id": " F1 ",
                    "factor_name": " Electricity ",
                    "unit": "kWh",
                    "unused_raw_field": "not-mapped",
                },
                source_context={"artifact_reference": "memory://defra"},
            ),
        ),
        parser_metadata={"parser_kind": "minimal_defra_desnz_content_fixture"},
        source_context={"artifact_reference": "memory://defra"},
    )


def test_valid_defra_desnz_fixture_input_maps_to_success_result() -> None:
    result = map_defra_desnz_normalization_input(_normalization_input())

    assert isinstance(result, DefraDesnzNormalizationMappingResult)
    assert result.status == DefraDesnzNormalizationMappingStatus.SUCCESS
    assert isinstance(result.normalization_result, NormalizationResult)
    assert result.normalization_result.summary.normalized_record_count == 1
    assert result.normalization_result.issues == ()


def test_normalized_record_preserves_source_and_record_identity() -> None:
    result = map_defra_desnz_normalization_input(_normalization_input())

    record = result.normalization_result.records[0]

    assert record.record_id == "defra_desnz:defra_desnz:record-001"
    assert dict(record.fields)["source_family"] == "defra_desnz"
    assert dict(record.fields)["source_id"] == "defra_desnz"
    assert dict(record.fields)["record_index"] == 1
    assert dict(record.fields)["row_number"] == 2
    assert record.source_reference == "memory://defra"


def test_expected_raw_fields_are_copied_deterministically() -> None:
    result = map_defra_desnz_normalization_input(_normalization_input())

    record_fields = result.normalization_result.records[0].fields

    assert DEFRA_DESNZ_MINIMAL_NORMALIZATION_FIELDS == (
        "factor_id",
        "factor_name",
        "unit",
    )
    assert record_fields == (
        ("source_family", "defra_desnz"),
        ("source_id", "defra_desnz"),
        ("record_index", 1),
        ("row_number", 2),
        ("factor_id", " F1 "),
        ("factor_name", " Electricity "),
        ("unit", "kWh"),
    )
    assert "unused_raw_field" not in dict(record_fields)


def test_normalized_defra_desnz_record_maps_to_persistence_ready_fields() -> None:
    normalized_input = _normalization_input(
        (
            NormalizationInputRecord(
                source_family="defra_desnz",
                source_id="defra_desnz",
                record_index=1,
                row_number=2,
                raw_fields={
                    "source_year": "2024",
                    "source_version": "conversion-factors-2024",
                    "category": "Energy",
                    "subcategory": "Electricity",
                    "activity": "Generated",
                    "factor_id": "DEFRA-2024-ELEC",
                    "factor_name": "Electricity generated",
                    "factor_value": "0.20705",
                    "unit": "kWh",
                    "greenhouse_gas": "CO2e",
                    "provenance": "worksheet:UK electricity row 10",
                },
                source_context={"artifact_reference": "memory://defra"},
            ),
        ),
    )

    result = map_defra_desnz_normalization_input(normalized_input)

    assert result.status == DefraDesnzNormalizationMappingStatus.SUCCESS
    record = result.normalization_result.records[0]
    assert record.record_id == (
        "defra_desnz:defra_desnz:2024:"
        "conversion-factors-2024:DEFRA-2024-ELEC"
    )
    assert record.is_artificial is False
    assert record.source_reference == "memory://defra"
    assert DEFRA_DESNZ_NORMALIZED_MAPPING_FIELDS == tuple(
        field_name for field_name, _ in record.fields
    )
    assert record.fields == (
        ("source_family", "defra_desnz"),
        ("source_id", "defra_desnz"),
        ("source_year", "2024"),
        ("source_version", "conversion-factors-2024"),
        ("record_index", 1),
        ("row_number", 2),
        ("factor_id", "DEFRA-2024-ELEC"),
        ("factor_name", "Electricity generated"),
        ("factor_value", 0.20705),
        ("unit", "kWh"),
        ("category", "Energy"),
        ("subcategory", "Electricity"),
        ("activity", "Generated"),
        ("greenhouse_gas", "CO2e"),
        ("provenance", "worksheet:UK electricity row 10"),
    )


def test_single_record_mapping_helper_returns_success_result() -> None:
    result = map_defra_desnz_normalization_input_record(
        _normalization_input().records[0],
    )

    assert result.status == DefraDesnzNormalizationMappingStatus.SUCCESS
    assert result.normalization_result.summary.normalized_record_count == 1


def test_missing_required_raw_field_returns_failed_result_with_issue() -> None:
    bad_record = NormalizationInputRecord(
        source_family="defra_desnz",
        source_id="defra_desnz",
        record_index=1,
        row_number=2,
        raw_fields={
            "factor_id": "F1",
            "unit": "kWh",
        },
    )

    result = map_defra_desnz_normalization_input(_normalization_input((bad_record,)))

    assert result.status == DefraDesnzNormalizationMappingStatus.FAILED
    assert result.normalization_result.records == ()
    assert result.normalization_result.issues[0].code == (
        "DEFRA_DESNZ_NORMALIZATION_MISSING_RAW_FIELD"
    )
    assert result.normalization_result.issues[0].location == (
        "records[1].raw_fields.factor_name"
    )


def test_invalid_normalized_factor_value_returns_failed_result_with_issue() -> None:
    bad_record = NormalizationInputRecord(
        source_family="defra_desnz",
        source_id="defra_desnz",
        record_index=1,
        row_number=2,
        raw_fields={
            "source_year": "2024",
            "source_version": "conversion-factors-2024",
            "category": "Energy",
            "factor_id": "DEFRA-2024-ELEC",
            "factor_name": "Electricity generated",
            "factor_value": "not-a-number",
            "unit": "kWh",
            "provenance": "worksheet:UK electricity row 10",
        },
    )

    result = map_defra_desnz_normalization_input(_normalization_input((bad_record,)))

    assert result.status == DefraDesnzNormalizationMappingStatus.FAILED
    assert result.normalization_result.records == ()
    assert result.normalization_result.issues[0].code == (
        "DEFRA_DESNZ_NORMALIZATION_INVALID_FACTOR_VALUE"
    )
    assert result.normalization_result.issues[0].location == (
        "records[1].raw_fields.factor_value"
    )


def test_empty_input_returns_no_records_result_with_issue() -> None:
    result = map_defra_desnz_normalization_input(_normalization_input(records=()))

    assert result.status == DefraDesnzNormalizationMappingStatus.NO_RECORDS
    assert result.normalization_result.records == ()
    assert result.normalization_result.issues[0].code == (
        "DEFRA_DESNZ_NORMALIZATION_NO_RECORDS"
    )


def test_non_defra_source_family_returns_failed_result() -> None:
    bad_record = NormalizationInputRecord(
        source_family="ghg_protocol",
        source_id="ghg_protocol",
        record_index=1,
        raw_fields={
            "factor_id": "F1",
            "factor_name": "Electricity",
            "unit": "kWh",
        },
    )

    result = map_defra_desnz_normalization_input(_normalization_input((bad_record,)))

    assert result.status == DefraDesnzNormalizationMappingStatus.FAILED
    assert result.normalization_result.issues[0].code == (
        "DEFRA_DESNZ_NORMALIZATION_SOURCE_FAMILY_MISMATCH"
    )


def test_no_unit_conversion_or_category_inference_occurs() -> None:
    result = map_defra_desnz_normalization_input(_normalization_input())

    record_fields = dict(result.normalization_result.records[0].fields)

    assert record_fields["unit"] == "kWh"
    assert "converted_unit" not in record_fields
    assert "emission_category" not in record_fields
    assert "category" not in record_fields


def test_mapper_has_no_file_http_db_scheduler_or_auth_side_effects(
    monkeypatch,
    tmp_path,
) -> None:
    missing_artifact = tmp_path / "missing.csv"

    def fail_side_effect(*args, **kwargs):
        raise AssertionError("mapper must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    result = map_defra_desnz_normalization_input(
        _normalization_input(
            (
                NormalizationInputRecord(
                    source_family="defra_desnz",
                    source_id="defra_desnz",
                    record_index=1,
                    raw_fields={
                        "factor_id": str(missing_artifact),
                        "factor_name": "Electricity",
                        "unit": "kWh",
                        "scheduler": "not-used",
                        "auth_note": "not-used",
                    },
                ),
            ),
        ),
    )

    assert result.status == DefraDesnzNormalizationMappingStatus.SUCCESS
    assert not missing_artifact.exists()


def test_in_memory_parser_to_minimal_normalization_mapping_path() -> None:
    parser_input = create_parser_file_content_input(
        source_family="defra_desnz",
        source_id="defra_desnz",
        content=(
            "factor_id,factor_name,unit\n"
            "F1,Electricity,kWh\n"
            "F2,Natural gas,m3\n"
        ),
        content_type="text/csv",
        artifact_reference="memory://defra-desnz-content",
    )

    parser_result = parse_defra_desnz_file_content(parser_input)
    handoff_result = build_parser_execution_normalization_handoff(parser_result)
    input_result = build_normalization_input_from_parser_execution_handoff(
        handoff_result,
    )

    assert parser_result.status == ParserExecutionResultStatus.SUCCESS
    assert input_result.normalization_input is not None

    mapping_result = map_defra_desnz_normalization_input(
        input_result.normalization_input,
    )

    assert mapping_result.status == DefraDesnzNormalizationMappingStatus.SUCCESS
    assert mapping_result.normalization_result.summary.normalized_record_count == 2
    assert mapping_result.normalization_result.records[1].fields == (
        ("source_family", "defra_desnz"),
        ("source_id", "defra_desnz"),
        ("record_index", 2),
        ("row_number", 3),
        ("factor_id", "F2"),
        ("factor_name", "Natural gas"),
        ("unit", "m3"),
    )


def test_in_memory_parser_to_normalized_defra_desnz_mapping_path() -> None:
    parser_input = create_parser_file_content_input(
        source_family="defra_desnz",
        source_id="defra_desnz",
        content=(
            ",".join(DEFRA_DESNZ_NORMALIZED_CONTENT_HEADER)
            + "\n"
            + "2024,conversion-factors-2024,Energy,Electricity,Generated,"
            + "DEFRA-2024-ELEC,Electricity generated,0.20705,kWh,CO2e,"
            + "worksheet:UK electricity row 10\n"
        ),
        content_type="text/csv",
        artifact_reference="memory://defra-desnz-content",
    )

    parser_result = parse_defra_desnz_file_content(parser_input)
    handoff_result = build_parser_execution_normalization_handoff(parser_result)
    input_result = build_normalization_input_from_parser_execution_handoff(
        handoff_result,
    )

    assert parser_result.status == ParserExecutionResultStatus.SUCCESS
    assert input_result.normalization_input is not None

    mapping_result = map_defra_desnz_normalization_input(
        input_result.normalization_input,
    )

    assert mapping_result.status == DefraDesnzNormalizationMappingStatus.SUCCESS
    assert mapping_result.normalization_result.records[0].fields == (
        ("source_family", "defra_desnz"),
        ("source_id", "defra_desnz"),
        ("source_year", "2024"),
        ("source_version", "conversion-factors-2024"),
        ("record_index", 1),
        ("row_number", 2),
        ("factor_id", "DEFRA-2024-ELEC"),
        ("factor_name", "Electricity generated"),
        ("factor_value", 0.20705),
        ("unit", "kWh"),
        ("category", "Energy"),
        ("subcategory", "Electricity"),
        ("activity", "Generated"),
        ("greenhouse_gas", "CO2e"),
        ("provenance", "worksheet:UK electricity row 10"),
    )
