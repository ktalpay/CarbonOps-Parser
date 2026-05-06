import builtins
import inspect
import sqlite3
import urllib.request

import carbonfactor_parser.persistence.postgresql_insert_builder as builder_module
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PersistenceInputRecord,
    PostgreSQLInsertBuildStatus,
    PostgreSQLInsertStatement,
    build_postgresql_insert_statement,
    get_normalized_record_postgresql_schema,
)


def _persistence_input(records=None) -> PersistenceInput:
    return PersistenceInput(
        source_family="defra_desnz",
        source_id="defra_desnz",
        records=records
        if records is not None
        else (
            PersistenceInputRecord(
                source_family="defra_desnz",
                source_id="defra_desnz",
                record_id="defra_desnz:defra_desnz:record-001",
                record_index=1,
                row_number=2,
                normalized_fields=(
                    ("source_family", "defra_desnz"),
                    ("source_id", "defra_desnz"),
                    ("record_index", 1),
                    ("row_number", 2),
                    ("factor_id", "F1"),
                    ("factor_name", "Electricity"),
                ),
                source_reference="memory://defra",
                parser_metadata={
                    "parser_kind": "minimal",
                    "source_artifact_reference": "artifact://fixture",
                    "source_checksum_sha256": "abc123",
                },
                normalization_metadata={"mapper_kind": "minimal_fixture"},
            ),
        ),
        parser_metadata={"parser_kind": "minimal"},
        normalization_metadata={"mapper_kind": "minimal_fixture"},
    )


def test_valid_persistence_input_produces_ready_statement_build_result() -> None:
    result = build_postgresql_insert_statement(_persistence_input())

    assert result.status == PostgreSQLInsertBuildStatus.READY
    assert isinstance(result.statement, PostgreSQLInsertStatement)
    assert result.issues == ()


def test_sql_text_is_deterministic_and_uses_placeholders() -> None:
    result_a = build_postgresql_insert_statement(_persistence_input())
    result_b = build_postgresql_insert_statement(_persistence_input())

    assert result_a.statement.sql == result_b.statement.sql
    assert result_a.statement.sql == (
        "INSERT INTO normalized_records "
        "(source_family, source_id, record_id, record_index, row_number, "
        "normalized_fields, source_reference, source_artifact_reference, "
        "source_checksum_sha256, parser_metadata, normalization_metadata, "
        "created_at, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )


def test_expected_table_name_and_columns_are_included() -> None:
    schema = get_normalized_record_postgresql_schema()
    result = build_postgresql_insert_statement(_persistence_input())

    assert result.statement.target_table_name == schema.table_name
    assert result.statement.column_names == tuple(
        column.name for column in schema.columns
    )
    assert result.statement.idempotency_key_fields == (
        schema.idempotency_key_fields
    )
    assert result.statement.conflict_target_fields == (
        schema.idempotency_key_fields
    )


def test_parameters_preserve_normalized_field_payload_and_metadata() -> None:
    result = build_postgresql_insert_statement(_persistence_input())
    statement = result.statement
    parameter_row = statement.parameters[0]
    values_by_column = dict(zip(statement.column_names, parameter_row))

    assert values_by_column["source_family"] == "defra_desnz"
    assert values_by_column["source_id"] == "defra_desnz"
    assert values_by_column["record_id"] == "defra_desnz:defra_desnz:record-001"
    assert values_by_column["record_index"] == 1
    assert values_by_column["row_number"] == 2
    assert values_by_column["normalized_fields"] == (
        ("source_family", "defra_desnz"),
        ("source_id", "defra_desnz"),
        ("record_index", 1),
        ("row_number", 2),
        ("factor_id", "F1"),
        ("factor_name", "Electricity"),
    )
    assert values_by_column["source_reference"] == "memory://defra"
    assert values_by_column["source_artifact_reference"] == "artifact://fixture"
    assert values_by_column["source_checksum_sha256"] == "abc123"
    assert values_by_column["parser_metadata"] == (
        ("parser_kind", "minimal"),
        ("source_artifact_reference", "artifact://fixture"),
        ("source_checksum_sha256", "abc123"),
    )
    assert values_by_column["normalization_metadata"] == (
        ("mapper_kind", "minimal_fixture"),
    )
    assert values_by_column["created_at"] is None
    assert values_by_column["updated_at"] is None


def test_record_count_is_preserved_for_multiple_records() -> None:
    result = build_postgresql_insert_statement(
        _persistence_input(
            records=(
                _persistence_input().records[0],
                PersistenceInputRecord(
                    source_family="defra_desnz",
                    source_id="defra_desnz",
                    record_id="defra_desnz:defra_desnz:record-002",
                    normalized_fields=(("factor_id", "F2"),),
                ),
            ),
        ),
    )

    assert result.status == PostgreSQLInsertBuildStatus.READY
    assert result.statement.record_count == 2
    assert len(result.statement.parameters) == 2


def test_no_records_input_returns_no_records_result() -> None:
    result = build_postgresql_insert_statement(_persistence_input(records=()))

    assert result.status == PostgreSQLInsertBuildStatus.NO_RECORDS
    assert result.statement is None
    assert result.issues[0].code == "POSTGRESQL_INSERT_NO_RECORDS"


def test_invalid_record_shape_returns_failed_result() -> None:
    result = build_postgresql_insert_statement(
        _persistence_input(
            records=(
                PersistenceInputRecord(
                    source_family="",
                    source_id="defra_desnz",
                    record_id="",
                    normalized_fields=(),
                ),
            ),
        ),
    )

    assert result.status == PostgreSQLInsertBuildStatus.FAILED
    assert result.statement is None
    assert [issue.code for issue in result.issues] == [
        "POSTGRESQL_INSERT_MISSING_SOURCE_FAMILY",
        "POSTGRESQL_INSERT_MISSING_RECORD_ID",
        "POSTGRESQL_INSERT_MISSING_NORMALIZED_FIELDS",
    ]


def test_builder_has_no_db_file_or_network_side_effects(monkeypatch) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("insert builder must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    result = build_postgresql_insert_statement(_persistence_input())

    assert result.status == PostgreSQLInsertBuildStatus.READY


def test_builder_module_has_no_db_dependency_or_sql_execution_behavior() -> None:
    module_source = inspect.getsource(builder_module)
    lower_source = module_source.lower()

    assert "psycopg" not in lower_source
    assert "asyncpg" not in lower_source
    assert "sqlalchemy" not in lower_source
    assert "connect(" not in module_source
    assert ".execute" not in module_source
    assert "cursor(" not in module_source
