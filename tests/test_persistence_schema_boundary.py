import builtins
import inspect
import sqlite3
import urllib.request

from carbonfactor_parser.persistence import (
    PostgreSQLPersistenceColumn,
    PostgreSQLPersistenceSchema,
    get_normalized_record_postgresql_schema,
)
from carbonfactor_parser.persistence import schema as schema_module


def test_schema_descriptor_exposes_deterministic_table_name() -> None:
    schema = get_normalized_record_postgresql_schema()

    assert isinstance(schema, PostgreSQLPersistenceSchema)
    assert schema.table_name == "normalized_records"


def test_schema_descriptor_exposes_deterministic_columns() -> None:
    schema = get_normalized_record_postgresql_schema()

    assert all(isinstance(column, PostgreSQLPersistenceColumn) for column in schema.columns)
    assert tuple(column.name for column in schema.columns) == (
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
    assert {column.name: column.logical_type for column in schema.columns} == {
        "source_family": "text",
        "source_id": "text",
        "record_id": "text",
        "record_index": "text",
        "row_number": "text",
        "normalized_fields": "jsonb",
        "source_reference": "text",
        "source_artifact_reference": "text",
        "source_checksum_sha256": "text",
        "parser_metadata": "jsonb",
        "normalization_metadata": "jsonb",
        "created_at": "timestamptz",
        "updated_at": "timestamptz",
    }


def test_schema_descriptor_exposes_idempotency_key_fields() -> None:
    schema = get_normalized_record_postgresql_schema()

    assert schema.idempotency_key_fields == (
        "source_family",
        "source_id",
        "record_id",
        "source_artifact_reference",
        "source_checksum_sha256",
    )


def test_schema_descriptor_does_not_generate_executable_sql() -> None:
    schema = get_normalized_record_postgresql_schema()
    field_names = set(schema.__dataclass_fields__)

    assert "sql" not in field_names
    assert "statement" not in field_names
    assert "migration" not in field_names

    module_source = inspect.getsource(schema_module)
    assert "execute(" not in module_source
    assert "connect(" not in module_source
    assert "CREATE TABLE" not in module_source
    assert "INSERT INTO" not in module_source


def test_schema_descriptor_has_no_db_file_or_network_side_effects(
    monkeypatch,
) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("schema boundary must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    schema = get_normalized_record_postgresql_schema()

    assert schema.table_name == "normalized_records"
