from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from carbonfactor_parser.persistence.postgresql_ddl_renderer import (
    render_postgresql_phase1_schema_ddl,
)
from carbonfactor_parser.persistence.postgresql_schema_bootstrap_planner import (
    POSTGRESQL_PHASE1_SCHEMA_MARKER,
    POSTGRESQL_SCHEMA_BOOTSTRAP_EXECUTION_SCOPE,
    POSTGRESQL_SCHEMA_BOOTSTRAP_TARGET_ENGINE,
    build_postgresql_phase1_schema_bootstrap_plan,
    verify_postgresql_phase1_schema_bootstrap_idempotency,
)
from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    ColumnDefinition,
    IndexDefinition,
    PostgreSQLDataType,
    SchemaCatalog,
    TableDefinition,
    UniqueConstraintDefinition,
    get_required_table_names,
)

PHASE1_DDL_SNAPSHOT_PATH = (
    Path(__file__).parent / "fixtures" / "postgresql_phase1_schema_ddl.sql"
)


def _snapshot_statements() -> tuple[str, ...]:
    snapshot_text = PHASE1_DDL_SNAPSHOT_PATH.read_text(encoding="utf-8").replace(
        "\r\n",
        "\n",
    )
    return tuple(snapshot_text.strip().split("\n\n"))


def test_schema_bootstrap_planner_import_is_runtime_passive() -> None:
    importlib.import_module("carbonfactor_parser.persistence.postgresql_schema_bootstrap_planner")


@pytest.mark.parametrize(
    "module_name",
    ("requests", "psycopg", "sqlalchemy", "asyncpg", "dotenv"),
)
def test_schema_bootstrap_planner_import_does_not_import_banned_runtime_modules(
    module_name: str,
) -> None:
    import sys

    sys.modules.pop(module_name, None)
    importlib.import_module("carbonfactor_parser.persistence.postgresql_schema_bootstrap_planner")
    assert module_name not in sys.modules


def test_schema_bootstrap_plan_contains_required_phase1_metadata() -> None:
    plan = build_postgresql_phase1_schema_bootstrap_plan()

    assert plan.target_database_engine == POSTGRESQL_SCHEMA_BOOTSTRAP_TARGET_ENGINE
    assert plan.target_database_engine == "postgresql"
    assert plan.schema_phase == POSTGRESQL_PHASE1_SCHEMA_MARKER
    assert plan.schema_phase == "phase1"
    assert plan.execution_scope == POSTGRESQL_SCHEMA_BOOTSTRAP_EXECUTION_SCOPE
    assert plan.required_table_names == (
        "ingestion_runs",
        "source_documents",
        "parser_runs",
        "schema_bootstrap_states",
        "parser_ingestion_runs",
        "parser_ingestion_source_results",
        "parser_ingestion_issues",
        "source_family_year_states",
        "normalized_factor_records",
        "ghg_emission_factor_masters",
        "ghg_emission_factor_details",
        "defra_emission_factor_masters",
        "defra_emission_factor_details",
        "ipcc_emission_factor_masters",
        "ipcc_emission_factor_details",
    )
    assert set(plan.required_table_names) == set(get_required_table_names())


def test_schema_bootstrap_plan_contains_renderer_and_snapshot_sql() -> None:
    plan = build_postgresql_phase1_schema_bootstrap_plan()
    rendered = render_postgresql_phase1_schema_ddl()

    rendered_create_tables = tuple(table.create_table_statement for table in rendered.tables)
    rendered_create_indexes = tuple(
        statement
        for table in rendered.tables
        for statement in table.create_index_statements
    )
    rendered_snapshot_order = tuple(rendered.statements)

    assert (
        tuple(statement.sql for statement in plan.create_table_statements)
        == rendered_create_tables
    )
    assert (
        tuple(statement.sql for statement in plan.create_index_statements)
        == rendered_create_indexes
    )
    assert rendered_snapshot_order == _snapshot_statements()
    assert tuple(sorted(plan.ordered_sql_statements)) == tuple(
        sorted(_snapshot_statements())
    )


def test_schema_bootstrap_plan_orders_tables_before_indexes() -> None:
    plan = build_postgresql_phase1_schema_bootstrap_plan()
    ordered_kinds = tuple(statement.statement_kind for statement in plan.ordered_statements)
    create_table_count = len(plan.create_table_statements)

    assert ordered_kinds[:create_table_count] == ("create_table",) * create_table_count
    assert ordered_kinds[create_table_count:] == ("create_index",) * len(
        plan.create_index_statements
    )
    assert tuple(statement.ordinal for statement in plan.ordered_statements) == tuple(
        range(1, len(plan.ordered_statements) + 1)
    )
    assert all(
        index_statement.ordinal > plan.create_table_statements[-1].ordinal
        for index_statement in plan.create_index_statements
    )


def test_schema_bootstrap_plan_orders_tables_deterministically() -> None:
    plan = build_postgresql_phase1_schema_bootstrap_plan()

    assert (
        tuple(statement.table_name for statement in plan.create_table_statements)
        == plan.required_table_names
    )
    assert tuple(statement.table_name for statement in plan.create_index_statements) == (
        "ingestion_runs",
        "source_documents",
        "parser_runs",
        "parser_ingestion_issues",
        "parser_ingestion_issues",
        "parser_ingestion_issues",
        "source_family_year_states",
        "normalized_factor_records",
        "ghg_emission_factor_masters",
        "ghg_emission_factor_masters",
        "ghg_emission_factor_details",
        "defra_emission_factor_masters",
        "defra_emission_factor_masters",
        "defra_emission_factor_details",
        "ipcc_emission_factor_masters",
        "ipcc_emission_factor_masters",
        "ipcc_emission_factor_details",
    )


def test_schema_bootstrap_plan_repeated_calls_are_equal() -> None:
    first = build_postgresql_phase1_schema_bootstrap_plan()
    second = build_postgresql_phase1_schema_bootstrap_plan()
    assert first == second


def test_schema_bootstrap_idempotency_verification_passes_for_phase1_catalog() -> None:
    verification = verify_postgresql_phase1_schema_bootstrap_idempotency(
        repeat_count=3,
    )

    assert verification.passed is True
    assert verification.repeated_plan_count == 3
    assert verification.plans_equivalent is True
    assert verification.ordered_sql_stable is True
    assert verification.metadata_stable is True
    assert verification.duplicate_table_names == ()
    assert verification.duplicate_index_names == ()
    assert verification.duplicate_constraint_names == ()
    assert verification.duplicate_sql_statements == ()
    assert verification.no_execution is True
    assert verification.opens_connection is False
    assert verification.runs_sql is False


def test_schema_bootstrap_idempotency_verification_detects_duplicate_definitions() -> None:
    duplicate_table = TableDefinition(
        name="duplicate_table",
        columns=(
            ColumnDefinition(
                "duplicate_table_id",
                PostgreSQLDataType.UUID,
                nullable=False,
                is_primary_key=True,
            ),
            ColumnDefinition("business_key", PostgreSQLDataType.TEXT, nullable=False),
        ),
        unique_constraints=(
            UniqueConstraintDefinition(
                name="uq_duplicate_business_key",
                column_names=("business_key",),
            ),
        ),
        indexes=(
            IndexDefinition(
                name="idx_duplicate_business_key",
                column_names=("business_key",),
            ),
        ),
    )
    catalog = SchemaCatalog(
        tables=(duplicate_table, duplicate_table),
        source_family_tables={},
    )

    verification = verify_postgresql_phase1_schema_bootstrap_idempotency(
        catalog,
        repeat_count=2,
    )

    assert verification.passed is False
    assert verification.plans_equivalent is True
    assert verification.ordered_sql_stable is True
    assert verification.metadata_stable is True
    assert verification.duplicate_table_names == ("duplicate_table",)
    assert verification.duplicate_index_names == ("idx_duplicate_business_key",)
    assert verification.duplicate_constraint_names == (
        "pk_duplicate_table",
        "uq_duplicate_business_key",
    )
    assert verification.duplicate_sql_statements == tuple(
        sorted(
            (
                duplicate_table_sql(duplicate_table),
                "CREATE INDEX IF NOT EXISTS idx_duplicate_business_key ON duplicate_table (business_key);",
            )
        )
    )
    assert verification.no_execution is True
    assert verification.opens_connection is False
    assert verification.runs_sql is False


def test_schema_bootstrap_plan_is_immutable() -> None:
    plan = build_postgresql_phase1_schema_bootstrap_plan()
    with pytest.raises(FrozenInstanceError):
        plan.target_database_engine = "sqlite"  # type: ignore[misc]


def test_schema_bootstrap_plan_declares_no_execution_or_connection_behavior() -> None:
    plan = build_postgresql_phase1_schema_bootstrap_plan()

    assert plan.execution_out_of_scope is True
    assert plan.opens_connection is False
    assert plan.runs_sql is False
    assert plan.creates_tables_now is False
    assert plan.runs_migrations is False
    assert plan.loads_environment is False
    assert plan.loads_config_files is False
    assert plan.performs_network_calls is False


def duplicate_table_sql(table: TableDefinition) -> str:
    plan = build_postgresql_phase1_schema_bootstrap_plan(
        SchemaCatalog(tables=(table,), source_family_tables={})
    )
    return plan.create_table_statements[0].sql
