import builtins
import inspect
import sqlite3
import urllib.request

import carbonfactor_parser.persistence.postgresql_persistence_preview as preview_module
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PersistenceInputRecord,
    PersistenceResultStatus,
    PostgreSQLInsertBuildStatus,
    PostgreSQLPersistencePreview,
    PostgreSQLPersistencePreviewStatus,
    PostgreSQLPersistenceRepository,
    build_postgresql_insert_statement,
    build_postgresql_persistence_preview,
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
    )


def test_valid_persistence_input_produces_ready_preview_result() -> None:
    result = build_postgresql_persistence_preview(_persistence_input())

    assert result.status == PostgreSQLPersistencePreviewStatus.READY
    assert result.insert_build_status == PostgreSQLInsertBuildStatus.READY
    assert isinstance(result.preview, PostgreSQLPersistencePreview)
    assert result.issues == ()


def test_preview_matches_insert_builder_output() -> None:
    persistence_input = _persistence_input()
    insert_result = build_postgresql_insert_statement(persistence_input)
    preview_result = build_postgresql_persistence_preview(persistence_input)

    assert preview_result.preview.sql == insert_result.statement.sql
    assert preview_result.preview.parameters == insert_result.statement.parameters
    assert (
        preview_result.preview.target_table_name
        == insert_result.statement.target_table_name
    )
    assert preview_result.preview.column_names == insert_result.statement.column_names
    assert preview_result.preview.record_count == insert_result.statement.record_count
    assert (
        preview_result.preview.idempotency_key_fields
        == insert_result.statement.idempotency_key_fields
    )
    assert (
        preview_result.preview.conflict_target_fields
        == insert_result.statement.conflict_target_fields
    )


def test_preview_delegates_to_insert_builder(monkeypatch) -> None:
    calls = []
    insert_result = build_postgresql_insert_statement(_persistence_input())

    def fake_builder(persistence_input, *, schema=None):
        calls.append((persistence_input, schema))
        return insert_result

    monkeypatch.setattr(
        preview_module,
        "build_postgresql_insert_statement",
        fake_builder,
    )

    result = build_postgresql_persistence_preview(_persistence_input())

    assert result.status == PostgreSQLPersistencePreviewStatus.READY
    assert len(calls) == 1


def test_preview_exposes_sql_table_columns_parameters_and_record_count() -> None:
    result = build_postgresql_persistence_preview(_persistence_input())
    preview = result.preview
    values_by_column = dict(zip(preview.column_names, preview.parameters[0]))

    assert preview.sql == (
        "INSERT INTO normalized_records "
        "(source_family, source_id, record_id, record_index, row_number, "
        "normalized_fields, source_reference, source_artifact_reference, "
        "source_checksum_sha256, parser_metadata, normalization_metadata, "
        "created_at, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    assert preview.target_table_name == "normalized_records"
    assert preview.column_names == (
        "source_family",
        "source_id",
        "record_id",
        "record_index",
        "row_number",
        "normalized_fields",
        "source_reference",
        "source_artifact_reference",
        "source_checksum_sha256",
        "parser_metadata",
        "normalization_metadata",
        "created_at",
        "updated_at",
    )
    assert values_by_column["normalized_fields"] == (
        ("source_family", "defra_desnz"),
        ("source_id", "defra_desnz"),
        ("record_index", 1),
        ("row_number", 2),
        ("factor_id", "F1"),
        ("factor_name", "Electricity"),
    )
    assert preview.record_count == 1


def test_preview_surfaces_idempotency_and_conflict_metadata() -> None:
    result = build_postgresql_persistence_preview(_persistence_input())

    assert result.preview.idempotency_key_fields == (
        "source_family",
        "source_id",
        "record_id",
        "source_artifact_reference",
        "source_checksum_sha256",
    )
    assert result.preview.conflict_target_fields == (
        result.preview.idempotency_key_fields
    )


def test_no_records_input_returns_no_records_without_ready_preview() -> None:
    result = build_postgresql_persistence_preview(_persistence_input(records=()))

    assert result.status == PostgreSQLPersistencePreviewStatus.NO_RECORDS
    assert result.insert_build_status == PostgreSQLInsertBuildStatus.NO_RECORDS
    assert result.preview is None
    assert result.issues[0].code == "POSTGRESQL_INSERT_NO_RECORDS"


def test_failed_input_does_not_produce_ready_preview() -> None:
    result = build_postgresql_persistence_preview(
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

    assert result.status == PostgreSQLPersistencePreviewStatus.FAILED
    assert result.insert_build_status == PostgreSQLInsertBuildStatus.FAILED
    assert result.preview is None
    assert [issue.code for issue in result.issues] == [
        "POSTGRESQL_INSERT_MISSING_SOURCE_FAMILY",
        "POSTGRESQL_INSERT_MISSING_RECORD_ID",
        "POSTGRESQL_INSERT_MISSING_NORMALIZED_FIELDS",
    ]


def test_repository_remains_unsupported_no_execution() -> None:
    repository = PostgreSQLPersistenceRepository()

    result = repository.persist(_persistence_input())

    assert result.status == PersistenceResultStatus.UNSUPPORTED
    assert result.persisted_record_count == 0
    assert result.issues[0].code == "POSTGRESQL_REPOSITORY_NOT_IMPLEMENTED"


def test_preview_has_no_db_file_or_network_side_effects(monkeypatch) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("preview must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    result = build_postgresql_persistence_preview(_persistence_input())

    assert result.status == PostgreSQLPersistencePreviewStatus.READY


def test_preview_module_has_no_db_dependency_or_execution_behavior() -> None:
    module_source = inspect.getsource(preview_module)
    lower_source = module_source.lower()

    assert "psycopg" not in lower_source
    assert "asyncpg" not in lower_source
    assert "sqlalchemy" not in lower_source
    assert "connect(" not in module_source
    assert ".execute" not in module_source
    assert "cursor(" not in module_source
