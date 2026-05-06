import builtins
import sqlite3
import urllib.request

from carbonfactor_parser.normalization import (
    NormalizationIssue,
    NormalizationIssueSeverity,
    NormalizationResult,
    NormalizedRecord,
)
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PersistenceInputBuildStatus,
    PersistenceInputRecord,
    build_persistence_input_from_normalization_result,
)


def _successful_normalization_result() -> NormalizationResult:
    return NormalizationResult(
        records=(
            NormalizedRecord(
                record_id="defra_desnz:defra_desnz:record-001",
                fields=(
                    ("source_family", "defra_desnz"),
                    ("source_id", "defra_desnz"),
                    ("record_index", 1),
                    ("row_number", 2),
                    ("factor_id", "F1"),
                    ("factor_name", "Electricity"),
                    ("unit", "kWh"),
                ),
                source_reference="memory://defra",
            ),
        ),
    )


def test_successful_normalization_result_produces_ready_persistence_input() -> None:
    result = build_persistence_input_from_normalization_result(
        _successful_normalization_result(),
    )

    assert result.status == PersistenceInputBuildStatus.READY
    assert isinstance(result.persistence_input, PersistenceInput)
    assert result.issues == ()


def test_source_identity_is_preserved() -> None:
    result = build_persistence_input_from_normalization_result(
        _successful_normalization_result(),
    )

    assert result.persistence_input is not None
    assert result.persistence_input.source_family == "defra_desnz"
    assert result.persistence_input.source_id == "defra_desnz"
    assert result.persistence_input.records[0].source_family == "defra_desnz"
    assert result.persistence_input.records[0].source_id == "defra_desnz"


def test_record_identity_is_preserved() -> None:
    result = build_persistence_input_from_normalization_result(
        _successful_normalization_result(),
    )

    record = result.persistence_input.records[0]

    assert isinstance(record, PersistenceInputRecord)
    assert record.record_id == "defra_desnz:defra_desnz:record-001"
    assert record.record_index == 1
    assert record.row_number == 2
    assert record.source_reference == "memory://defra"


def test_normalized_fields_are_preserved_exactly() -> None:
    normalization_result = _successful_normalization_result()

    result = build_persistence_input_from_normalization_result(
        normalization_result,
    )

    assert result.persistence_input is not None
    assert result.persistence_input.records[0].normalized_fields == (
        normalization_result.records[0].fields
    )


def test_parser_and_normalization_metadata_are_preserved_when_provided() -> None:
    result = build_persistence_input_from_normalization_result(
        _successful_normalization_result(),
        parser_metadata={"parser_kind": "minimal"},
        normalization_metadata={"mapper_kind": "minimal_fixture"},
    )

    assert result.persistence_input is not None
    assert result.persistence_input.parser_metadata == {"parser_kind": "minimal"}
    assert result.persistence_input.normalization_metadata == {
        "mapper_kind": "minimal_fixture",
    }
    assert result.persistence_input.records[0].parser_metadata == {
        "parser_kind": "minimal",
    }
    assert result.persistence_input.records[0].normalization_metadata == {
        "mapper_kind": "minimal_fixture",
    }


def test_failed_normalization_result_does_not_produce_ready_input() -> None:
    normalization_result = NormalizationResult(
        issues=(
            NormalizationIssue(
                code="NORMALIZATION_FAILED",
                message="Normalization failed.",
                severity=NormalizationIssueSeverity.ERROR,
                location="records[1]",
            ),
        ),
    )

    result = build_persistence_input_from_normalization_result(
        normalization_result,
    )

    assert result.status == PersistenceInputBuildStatus.FAILED
    assert result.persistence_input is None
    assert result.issues[0].code == "NORMALIZATION_FAILED"
    assert result.issues[0].field_name == "records[1]"


def test_no_records_normalization_result_does_not_produce_ready_input() -> None:
    result = build_persistence_input_from_normalization_result(
        NormalizationResult(),
    )

    assert result.status == PersistenceInputBuildStatus.NO_RECORDS
    assert result.persistence_input is None
    assert result.issues[0].code == "PERSISTENCE_INPUT_NO_NORMALIZED_RECORDS"


def test_missing_source_identity_returns_failed_result() -> None:
    normalization_result = NormalizationResult(
        records=(
            NormalizedRecord(
                record_id="record-001",
                fields=(
                    ("record_index", 1),
                    ("factor_id", "F1"),
                ),
            ),
        ),
    )

    result = build_persistence_input_from_normalization_result(
        normalization_result,
    )

    assert result.status == PersistenceInputBuildStatus.FAILED
    assert result.persistence_input is None
    assert [issue.field_name for issue in result.issues] == [
        "records[1].fields.source_family",
        "records[1].fields.source_id",
    ]


def test_mixed_source_identity_returns_failed_result() -> None:
    normalization_result = NormalizationResult(
        records=(
            NormalizedRecord(
                record_id="record-001",
                fields=(
                    ("source_family", "defra_desnz"),
                    ("source_id", "defra_desnz"),
                ),
            ),
            NormalizedRecord(
                record_id="record-002",
                fields=(
                    ("source_family", "ghg_protocol"),
                    ("source_id", "ghg_protocol"),
                ),
            ),
        ),
    )

    result = build_persistence_input_from_normalization_result(
        normalization_result,
    )

    assert result.status == PersistenceInputBuildStatus.FAILED
    assert result.issues[0].code == "PERSISTENCE_INPUT_MIXED_SOURCE_IDENTITY"


def test_persistence_input_has_no_database_runtime_fields() -> None:
    result = build_persistence_input_from_normalization_result(
        _successful_normalization_result(),
    )

    input_fields = set(result.persistence_input.__dataclass_fields__)
    record_fields = set(result.persistence_input.records[0].__dataclass_fields__)

    assert "connection_string" not in input_fields
    assert "database_url" not in input_fields
    assert "credentials" not in input_fields
    assert "sql" not in record_fields
    assert "table_name" not in record_fields
    assert "migration_name" not in record_fields


def test_persistence_input_has_no_db_file_or_network_side_effects(
    monkeypatch,
    tmp_path,
) -> None:
    missing_artifact = tmp_path / "missing.csv"

    def fail_side_effect(*args, **kwargs):
        raise AssertionError("persistence input boundary must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    normalization_result = NormalizationResult(
        records=(
            NormalizedRecord(
                record_id="record-001",
                fields=(
                    ("source_family", "defra_desnz"),
                    ("source_id", "defra_desnz"),
                    ("record_index", 1),
                    ("artifact_reference", str(missing_artifact)),
                ),
            ),
        ),
    )

    result = build_persistence_input_from_normalization_result(
        normalization_result,
    )

    assert result.status == PersistenceInputBuildStatus.READY
    assert not missing_artifact.exists()
