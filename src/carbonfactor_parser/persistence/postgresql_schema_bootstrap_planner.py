"""Runtime-passive PostgreSQL Phase 1 schema bootstrap planner."""

from __future__ import annotations

from dataclasses import dataclass

from carbonfactor_parser.persistence.postgresql_ddl_renderer import (
    render_postgresql_phase1_schema_ddl,
)
from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    SchemaCatalog,
    get_postgresql_phase1_schema_catalog,
)

POSTGRESQL_SCHEMA_BOOTSTRAP_TARGET_ENGINE = "postgresql"
POSTGRESQL_PHASE1_SCHEMA_MARKER = "phase1"
POSTGRESQL_SCHEMA_BOOTSTRAP_EXECUTION_SCOPE = "planning_only_no_execution"


@dataclass(frozen=True)
class PostgreSQLSchemaBootstrapPlanStatement:
    """A deterministic SQL statement entry for schema bootstrap planning."""

    ordinal: int
    statement_kind: str
    table_name: str
    sql: str


@dataclass(frozen=True)
class PostgreSQLSchemaBootstrapPlan:
    """Runtime-passive Phase 1 schema bootstrap plan."""

    target_database_engine: str
    schema_phase: str
    required_table_names: tuple[str, ...]
    create_table_statements: tuple[PostgreSQLSchemaBootstrapPlanStatement, ...]
    create_index_statements: tuple[PostgreSQLSchemaBootstrapPlanStatement, ...]
    execution_scope: str
    execution_out_of_scope: bool
    opens_connection: bool
    runs_sql: bool
    creates_tables_now: bool
    runs_migrations: bool
    loads_environment: bool
    loads_config_files: bool
    performs_network_calls: bool
    notes: tuple[str, ...]

    @property
    def ordered_statements(self) -> tuple[PostgreSQLSchemaBootstrapPlanStatement, ...]:
        return self.create_table_statements + self.create_index_statements

    @property
    def ordered_sql_statements(self) -> tuple[str, ...]:
        return tuple(statement.sql for statement in self.ordered_statements)


def build_postgresql_phase1_schema_bootstrap_plan(
    catalog: SchemaCatalog | None = None,
) -> PostgreSQLSchemaBootstrapPlan:
    """Build a deterministic no-execution PostgreSQL Phase 1 bootstrap plan."""

    active_catalog = catalog if catalog is not None else get_postgresql_phase1_schema_catalog()
    rendered_schema = render_postgresql_phase1_schema_ddl(active_catalog)

    create_table_statements: list[PostgreSQLSchemaBootstrapPlanStatement] = []
    create_index_statements: list[PostgreSQLSchemaBootstrapPlanStatement] = []

    for rendered_table in rendered_schema.tables:
        create_table_statements.append(
            PostgreSQLSchemaBootstrapPlanStatement(
                ordinal=len(create_table_statements) + 1,
                statement_kind="create_table",
                table_name=rendered_table.table_name,
                sql=rendered_table.create_table_statement,
            )
        )

    for rendered_table in rendered_schema.tables:
        for create_index_statement in rendered_table.create_index_statements:
            create_index_statements.append(
                PostgreSQLSchemaBootstrapPlanStatement(
                    ordinal=(
                        len(create_table_statements)
                        + len(create_index_statements)
                        + 1
                    ),
                    statement_kind="create_index",
                    table_name=rendered_table.table_name,
                    sql=create_index_statement,
                )
            )

    return PostgreSQLSchemaBootstrapPlan(
        target_database_engine=POSTGRESQL_SCHEMA_BOOTSTRAP_TARGET_ENGINE,
        schema_phase=POSTGRESQL_PHASE1_SCHEMA_MARKER,
        required_table_names=tuple(table.name for table in active_catalog.tables),
        create_table_statements=tuple(create_table_statements),
        create_index_statements=tuple(create_index_statements),
        execution_scope=POSTGRESQL_SCHEMA_BOOTSTRAP_EXECUTION_SCOPE,
        execution_out_of_scope=True,
        opens_connection=False,
        runs_sql=False,
        creates_tables_now=False,
        runs_migrations=False,
        loads_environment=False,
        loads_config_files=False,
        performs_network_calls=False,
        notes=(
            "Schema bootstrap planner metadata only.",
            "DDL is rendered for future startup inspection.",
            "No PostgreSQL connection is opened.",
            "No SQL is executed and no migration is created.",
        ),
    )
