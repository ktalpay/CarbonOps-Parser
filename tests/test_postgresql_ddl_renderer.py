from __future__ import annotations

import importlib
import re

import pytest

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    ColumnDefinition,
    PostgreSQLDataType,
    TableDefinition,
)
from carbonfactor_parser.persistence.postgresql_ddl_renderer import (
    render_create_index_statements,
    render_create_table_statement,
    render_postgresql_phase1_schema_ddl,
)


def test_renderer_import_is_runtime_passive() -> None:
    importlib.import_module("carbonfactor_parser.persistence.postgresql_ddl_renderer")


@pytest.mark.parametrize("module_name", ("requests", "psycopg", "sqlalchemy", "dotenv"))
def test_renderer_import_does_not_import_banned_runtime_modules(module_name: str) -> None:
    import sys

    sys.modules.pop(module_name, None)
    importlib.import_module("carbonfactor_parser.persistence.postgresql_ddl_renderer")
    assert module_name not in sys.modules


def test_renderer_returns_sql_strings_without_execution_side_effects() -> None:
    rendered = render_postgresql_phase1_schema_ddl()
    assert rendered.tables
    assert all(isinstance(statement, str) for statement in rendered.statements)


def test_required_create_table_statements_are_rendered() -> None:
    rendered = render_postgresql_phase1_schema_ddl()
    statements = "\n".join(rendered.statements)

    required_tables = (
        "ingestion_runs",
        "source_documents",
        "parser_runs",
        "schema_bootstrap_states",
        "ghg_emission_factor_masters",
        "ghg_emission_factor_details",
        "defra_emission_factor_masters",
        "defra_emission_factor_details",
        "ipcc_emission_factor_masters",
        "ipcc_emission_factor_details",
    )
    for table_name in required_tables:
        assert f"CREATE TABLE {table_name}" in statements


def test_primary_key_foreign_key_unique_and_index_statements_are_rendered() -> None:
    rendered = render_postgresql_phase1_schema_ddl()
    statements = "\n".join(rendered.statements)

    assert "PRIMARY KEY" in statements
    assert "REFERENCES ghg_emission_factor_masters (ghg_emission_factor_master_id)" in statements
    assert "CONSTRAINT uq_source_documents_family_uri_checksum UNIQUE" in statements
    assert "CREATE INDEX idx_ingestion_runs_run_status ON ingestion_runs (run_status);" in statements


def test_renderer_output_is_deterministic() -> None:
    first = render_postgresql_phase1_schema_ddl()
    second = render_postgresql_phase1_schema_ddl()
    assert first.statements == second.statements


def test_invalid_identifier_rejected() -> None:
    invalid = TableDefinition(
        name="bad-table",
        columns=(
            ColumnDefinition("column_id", PostgreSQLDataType.UUID, nullable=False, is_primary_key=True),
        ),
    )
    with pytest.raises(ValueError, match="Invalid table identifier"):
        render_create_table_statement(invalid)


def test_forbidden_name_fragments_do_not_appear() -> None:
    forbidden = ("temp", "test", "fake", "sample", "manual", "json_input")
    statements = "\n".join(render_postgresql_phase1_schema_ddl().statements)
    lowered = statements.lower()
    assert not any(fragment in lowered for fragment in forbidden)


def test_identifiers_follow_lowercase_snake_case() -> None:
    snake_case = re.compile(r"^[a-z][a-z0-9_]*$")
    rendered = render_postgresql_phase1_schema_ddl()
    for table in rendered.tables:
        assert snake_case.match(table.table_name)


def test_render_create_index_statements_rejects_invalid_index_name() -> None:
    invalid_table = TableDefinition(
        name="good_table",
        columns=(
            ColumnDefinition("id", PostgreSQLDataType.UUID, nullable=False, is_primary_key=True),
        ),
        indexes=(),
    )
    assert render_create_index_statements(invalid_table) == ()
