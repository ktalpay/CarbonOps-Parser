from __future__ import annotations

import importlib
import re
import sys

import pytest

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    ColumnDefinition,
    IndexDefinition,
    PostgreSQLDataType,
    TableDefinition,
    get_postgresql_phase1_schema_catalog,
    get_required_table_names,
)
from carbonfactor_parser.persistence.postgresql_schema_ddl import (
    render_postgresql_phase1_create_table_ddl,
    render_postgresql_phase1_index_ddl,
    render_postgresql_phase1_schema_ddl,
    render_postgresql_table_create_table_ddl,
    render_postgresql_table_index_ddl,
)

BANNED_RUNTIME_MODULE_PREFIXES = (
    "requests",
    "psycopg",
    "sqlalchemy",
    "asyncpg",
    "dotenv",
    "boto3",
    "httpx",
    "urllib3",
)

FORBIDDEN_NAME_FRAGMENTS = (
    "temp",
    "test",
    "fake",
    "sample",
    "manual",
    "json_input",
)


def _create_table_names(sql_statements: tuple[str, ...]) -> tuple[str, ...]:
    names: list[str] = []
    for statement in sql_statements:
        match = re.match(r"CREATE TABLE (?:IF NOT EXISTS )?([a-z][a-z0-9_]*) \(", statement)
        if match is not None:
            names.append(match.group(1))
    return tuple(names)


def _sql_for_table(table_name: str) -> str:
    for statement in render_postgresql_phase1_create_table_ddl():
        if statement.startswith(f"CREATE TABLE IF NOT EXISTS {table_name} ") or statement.startswith(f"CREATE TABLE {table_name} "):
            return statement
    raise AssertionError(f"CREATE TABLE statement not rendered for {table_name}")


def test_all_phase1_required_tables_render_create_table_sql_text() -> None:
    statements = render_postgresql_phase1_create_table_ddl()
    required_table_names = get_required_table_names()
    rendered_table_names = _create_table_names(statements)

    assert statements
    assert all(isinstance(statement, str) for statement in statements)
    assert set(rendered_table_names) == set(required_table_names)
    assert len(rendered_table_names) == len(required_table_names)


def test_rendered_sql_includes_table_names_and_representative_columns() -> None:
    assert "ingestion_run_id uuid NOT NULL" in _sql_for_table("ingestion_runs")
    assert "run_status text NOT NULL" in _sql_for_table("ingestion_runs")
    assert "source_document_id uuid NOT NULL" in _sql_for_table("source_documents")
    assert "source_document_uri text NOT NULL" in _sql_for_table("source_documents")
    assert "source_family text NOT NULL" in _sql_for_table(
        "ghg_emission_factor_masters"
    )
    assert "source_year integer NOT NULL" in _sql_for_table(
        "ghg_emission_factor_masters"
    )
    assert "source_version text NOT NULL" in _sql_for_table(
        "ghg_emission_factor_masters"
    )
    assert "artifact_checksum_sha256 text" in _sql_for_table(
        "ghg_emission_factor_masters"
    )
    assert "archive_reference text" in _sql_for_table(
        "ghg_emission_factor_masters"
    )
    assert "run_id text" in _sql_for_table("ghg_emission_factor_masters")
    assert "status text NOT NULL" in _sql_for_table("ghg_emission_factor_masters")
    assert "master_external_key text NOT NULL" in _sql_for_table(
        "ghg_emission_factor_masters"
    )
    assert "raw_fields jsonb NOT NULL" in _sql_for_table(
        "defra_emission_factor_details"
    )
    assert "factor_value numeric NOT NULL" in _sql_for_table(
        "defra_emission_factor_details"
    )


def test_unique_foreign_key_and_index_fragments_follow_catalog_metadata() -> None:
    statements = "\n".join(render_postgresql_phase1_schema_ddl())
    index_statements = render_postgresql_phase1_index_ddl()
    catalog = get_postgresql_phase1_schema_catalog()
    expected_index_count = sum(len(table.indexes) for table in catalog.tables)

    assert (
        "CONSTRAINT uq_source_documents_family_uri_checksum "
        "UNIQUE (source_family, source_document_uri, source_checksum_sha256)"
    ) in statements
    assert (
        "FOREIGN KEY (source_document_id) "
        "REFERENCES source_documents (source_document_id)"
    ) in statements
    assert (
        "CONSTRAINT uq_ghg_emission_factor_masters_family_year_version_key "
        "UNIQUE (source_family, source_year, source_version, master_external_key)"
    ) in statements
    assert len(index_statements) == expected_index_count
    assert (
        "ON defra_emission_factor_details (defra_emission_factor_master_id);"
    ) in "\n".join(index_statements)
    assert (
        "ON ipcc_emission_factor_masters "
        "(source_family, source_year, source_version);"
    ) in "\n".join(index_statements)


def test_output_ordering_is_deterministic_across_repeated_calls() -> None:
    first = render_postgresql_phase1_schema_ddl()
    second = render_postgresql_phase1_schema_ddl()
    third = render_postgresql_phase1_schema_ddl()

    assert first == second == third


def test_output_excludes_forbidden_non_contract_name_fragments() -> None:
    rendered_sql = "\n".join(render_postgresql_phase1_schema_ddl()).lower()
    identifiers = re.findall(r"[a-z][a-z0-9_]*", rendered_sql)

    assert not any(
        identifier == fragment or identifier.startswith(f"{fragment}_")
        for identifier in identifiers
        for fragment in FORBIDDEN_NAME_FRAGMENTS
    )


def test_schema_bootstrap_ddl_is_additive_only() -> None:
    rendered_sql = "\n".join(render_postgresql_phase1_schema_ddl()).upper()

    assert "DROP " not in rendered_sql
    assert "TRUNCATE " not in rendered_sql
    assert "DELETE " not in rendered_sql
    assert "ALTER TABLE" not in rendered_sql


def test_importing_schema_ddl_does_not_import_runtime_heavy_libraries() -> None:
    module_name = "carbonfactor_parser.persistence.postgresql_schema_ddl"
    sys.modules.pop(module_name, None)
    for banned_module_prefix in BANNED_RUNTIME_MODULE_PREFIXES:
        sys.modules.pop(banned_module_prefix, None)

    module = importlib.import_module(module_name)

    assert hasattr(module, "render_postgresql_phase1_schema_ddl")
    for banned_module_prefix in BANNED_RUNTIME_MODULE_PREFIXES:
        assert banned_module_prefix not in sys.modules


def test_invalid_identifier_is_rejected() -> None:
    invalid_table = TableDefinition(
        name="BadTable",
        columns=(
            ColumnDefinition(
                "id",
                PostgreSQLDataType.UUID,
                nullable=False,
                is_primary_key=True,
            ),
        ),
    )

    with pytest.raises(ValueError, match="Invalid table identifier"):
        render_postgresql_table_create_table_ddl(invalid_table)


def test_index_columns_must_exist_in_table_catalog_metadata() -> None:
    invalid_table = TableDefinition(
        name="good_table",
        columns=(
            ColumnDefinition(
                "id",
                PostgreSQLDataType.UUID,
                nullable=False,
                is_primary_key=True,
            ),
        ),
        indexes=(
            IndexDefinition(
                name="idx_good_table_missing_column",
                column_names=("missing_id",),
            ),
        ),
    )

    with pytest.raises(ValueError, match="unknown columns"):
        render_postgresql_table_index_ddl(invalid_table)
