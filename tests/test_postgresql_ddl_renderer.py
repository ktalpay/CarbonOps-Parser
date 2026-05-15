from __future__ import annotations

import importlib
from pathlib import Path
import re

import pytest

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    ColumnDefinition,
    ForeignKeyDefinition,
    IndexDefinition,
    PostgreSQLDataType,
    TableDefinition,
    UniqueConstraintDefinition,
)
from carbonfactor_parser.persistence.postgresql_ddl_renderer import (
    _render_identifier,
    render_create_index_statements,
    render_create_table_statement,
    render_postgresql_phase1_schema_ddl,
)

PHASE1_DDL_SNAPSHOT_PATH = Path(__file__).parent / "fixtures" / "postgresql_phase1_schema_ddl.sql"
KNOWN_SHORTENED_FOREIGN_KEY_NAME = "fk_defra_emission_factor_details_defra_emission_fa_98fe08fa20f4"
KNOWN_SHORTENED_INDEX_NAME = "idx_defra_emission_factor_details_defra_emission_f_532bf4e61faf"


def _rendered_phase1_sql_contract() -> str:
    return "\n\n".join(render_postgresql_phase1_schema_ddl().statements) + "\n"


def _phase1_sql_snapshot() -> str:
    return PHASE1_DDL_SNAPSHOT_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")


def _rendered_table_constraint_and_index_identifiers() -> tuple[str, ...]:
    rendered = render_postgresql_phase1_schema_ddl()
    identifiers: list[str] = [table.table_name for table in rendered.tables]

    for statement in rendered.statements:
        identifiers.extend(re.findall(r"\bCREATE TABLE ([a-z][a-z0-9_]*)", statement))
        identifiers.extend(re.findall(r"\bCONSTRAINT ([a-z][a-z0-9_]*)", statement))
        identifiers.extend(re.findall(r"\bCREATE (?:UNIQUE )?INDEX ([a-z][a-z0-9_]*)", statement))

    return tuple(identifiers)


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
        "source_family_year_states",
        "normalized_factor_records",
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


def test_rendered_phase1_sql_matches_contract_snapshot() -> None:
    assert _rendered_phase1_sql_contract() == _phase1_sql_snapshot()


def test_repeated_render_calls_match_contract_snapshot() -> None:
    snapshot = _phase1_sql_snapshot()
    assert _rendered_phase1_sql_contract() == snapshot
    assert _rendered_phase1_sql_contract() == snapshot


def test_contract_snapshot_includes_known_shortened_identifiers() -> None:
    snapshot = _phase1_sql_snapshot()
    assert KNOWN_SHORTENED_FOREIGN_KEY_NAME in snapshot
    assert KNOWN_SHORTENED_INDEX_NAME in snapshot


def test_rendered_table_constraint_and_index_identifiers_fit_postgresql_limit() -> None:
    identifiers = _rendered_table_constraint_and_index_identifiers()
    assert identifiers
    assert all(len(identifier.encode("utf-8")) <= 63 for identifier in identifiers)


def test_known_long_foreign_key_and_index_names_are_shortened_deterministically() -> None:
    statements = "\n".join(render_postgresql_phase1_schema_ddl().statements)

    long_fk_name = "fk_defra_emission_factor_details_defra_emission_factor_master_id"
    long_index_name = "idx_defra_emission_factor_details_defra_emission_factor_master_id"
    expected_fk_name = _render_identifier(long_fk_name, "constraint")
    expected_index_name = _render_identifier(long_index_name, "index")

    assert expected_fk_name == KNOWN_SHORTENED_FOREIGN_KEY_NAME
    assert expected_index_name == KNOWN_SHORTENED_INDEX_NAME
    assert expected_fk_name == _render_identifier(long_fk_name, "constraint")
    assert expected_index_name == _render_identifier(long_index_name, "index")
    assert expected_fk_name != long_fk_name
    assert expected_index_name != long_index_name
    assert f"CONSTRAINT {expected_fk_name} FOREIGN KEY" in statements
    assert f"CREATE INDEX {expected_index_name} ON defra_emission_factor_details" in statements
    assert long_fk_name not in statements
    assert long_index_name not in statements


def test_invalid_identifier_rejected() -> None:
    invalid = TableDefinition(
        name="bad-table",
        columns=(
            ColumnDefinition("column_id", PostgreSQLDataType.UUID, nullable=False, is_primary_key=True),
        ),
    )
    with pytest.raises(ValueError, match="Invalid table identifier"):
        render_create_table_statement(invalid)


def test_invalid_unsafe_index_identifier_rejected() -> None:
    invalid_table = TableDefinition(
        name="good_table",
        columns=(
            ColumnDefinition("id", PostgreSQLDataType.UUID, nullable=False, is_primary_key=True),
        ),
        indexes=(
            IndexDefinition(name="idx_Good_Table", column_names=("id",)),
        ),
    )
    with pytest.raises(ValueError, match="Invalid index identifier"):
        render_create_index_statements(invalid_table)


def test_forbidden_name_fragments_do_not_appear() -> None:
    forbidden = ("temp", "test", "fake", "sample", "manual", "json_input")
    statements = "\n".join(render_postgresql_phase1_schema_ddl().statements)
    lowered = statements.lower()
    assert not any(fragment in lowered for fragment in forbidden)


def test_identifiers_follow_lowercase_snake_case() -> None:
    snake_case = re.compile(r"^[a-z][a-z0-9_]*$")
    for identifier in _rendered_table_constraint_and_index_identifiers():
        assert snake_case.match(identifier)


def test_different_long_identifiers_with_same_visible_prefix_do_not_collapse() -> None:
    base_name = "idx_shared_visible_prefix_for_length_hardening_collision_case"
    first_name = f"{base_name}_left"
    second_name = f"{base_name}_right"
    table = TableDefinition(
        name="good_table",
        columns=(
            ColumnDefinition("id", PostgreSQLDataType.UUID, nullable=False, is_primary_key=True),
        ),
        indexes=(
            IndexDefinition(name=first_name, column_names=("id",)),
            IndexDefinition(name=second_name, column_names=("id",)),
        ),
    )
    statements = render_create_index_statements(table)

    first_rendered = _render_identifier(first_name, "index")
    second_rendered = _render_identifier(second_name, "index")
    assert first_rendered != second_rendered
    assert f"CREATE INDEX {first_rendered} ON good_table (id);" in statements
    assert f"CREATE INDEX {second_rendered} ON good_table (id);" in statements


def test_structured_renderer_rejects_unknown_unique_and_foreign_key_columns() -> None:
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
        foreign_keys=(
            ForeignKeyDefinition(
                "missing_fk_id",
                "referenced_table",
                "referenced_id",
            ),
        ),
        unique_constraints=(
            UniqueConstraintDefinition(
                name="uq_good_table_missing_unique_column",
                column_names=("missing_unique_id",),
            ),
        ),
    )

    with pytest.raises(ValueError, match="unknown columns"):
        render_create_table_statement(invalid_table)


def test_structured_renderer_rejects_unknown_index_columns() -> None:
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
        render_create_index_statements(invalid_table)
