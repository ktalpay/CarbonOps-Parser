import builtins
import inspect
import sqlite3
import urllib.request

import pytest

import carbonfactor_parser.persistence.ddl_preview as ddl_preview_module
from carbonfactor_parser.persistence import (
    get_normalized_record_postgresql_schema,
    render_postgresql_ddl_preview,
)


def test_postgresql_ddl_preview_is_deterministic() -> None:
    first_preview = render_postgresql_ddl_preview()
    second_preview = render_postgresql_ddl_preview()

    assert first_preview == second_preview


def test_postgresql_ddl_preview_includes_schema_table_name() -> None:
    schema = get_normalized_record_postgresql_schema()
    preview = render_postgresql_ddl_preview(schema)

    assert f"CREATE TABLE {schema.table_name} (" in preview


def test_postgresql_ddl_preview_includes_expected_logical_columns() -> None:
    preview = render_postgresql_ddl_preview()

    assert "    source_family text NOT NULL," in preview
    assert "    source_id text NOT NULL," in preview
    assert "    record_id text NOT NULL," in preview
    assert "    record_index text," in preview
    assert "    row_number text," in preview
    assert "    normalized_fields jsonb NOT NULL," in preview
    assert "    source_reference text," in preview
    assert "    source_artifact_reference text," in preview
    assert "    source_checksum_sha256 text," in preview
    assert "    parser_metadata jsonb," in preview
    assert "    normalization_metadata jsonb," in preview
    assert "    created_at timestamptz," in preview
    assert "    updated_at timestamptz," in preview


def test_postgresql_ddl_preview_includes_idempotency_unique_constraint() -> None:
    preview = render_postgresql_ddl_preview()

    assert "    CONSTRAINT normalized_records_idempotency_key UNIQUE (" in preview
    assert "        source_family," in preview
    assert "        source_id," in preview
    assert "        record_id," in preview
    assert "        source_artifact_reference," in preview
    assert "        source_checksum_sha256" in preview


def test_postgresql_ddl_preview_has_no_database_or_io_behavior(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_open(*args: object, **kwargs: object) -> None:
        raise AssertionError("DDL preview must not read or write files")

    def fail_connect(*args: object, **kwargs: object) -> None:
        raise AssertionError("DDL preview must not connect to a database")

    def fail_urlopen(*args: object, **kwargs: object) -> None:
        raise AssertionError("DDL preview must not perform network calls")

    monkeypatch.setattr(builtins, "open", fail_open)
    monkeypatch.setattr(sqlite3, "connect", fail_connect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)

    preview = render_postgresql_ddl_preview()

    assert "CREATE TABLE normalized_records" in preview


def test_postgresql_ddl_preview_module_avoids_database_runtime_imports() -> None:
    module_source = inspect.getsource(ddl_preview_module).lower()

    assert "psycopg" not in module_source
    assert "sqlalchemy" not in module_source
    assert "connect(" not in module_source
    assert "cursor(" not in module_source
    assert ".execute" not in module_source
