"""Runtime-passive PostgreSQL Phase 1 schema bootstrap planner."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Sequence

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
_CREATE_INDEX_IDENTIFIER_PATTERN = re.compile(
    r"\bCREATE (?:UNIQUE )?INDEX ([a-z][a-z0-9_]*)"
)
_CONSTRAINT_IDENTIFIER_PATTERN = re.compile(r"\bCONSTRAINT ([a-z][a-z0-9_]*)")


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


@dataclass(frozen=True)
class PostgreSQLSchemaBootstrapIdempotencyVerification:
    """Offline verification result for repeated bootstrap plan rendering."""

    repeated_plan_count: int
    plans_equivalent: bool
    ordered_sql_stable: bool
    metadata_stable: bool
    duplicate_table_names: tuple[str, ...]
    duplicate_index_names: tuple[str, ...]
    duplicate_constraint_names: tuple[str, ...]
    duplicate_sql_statements: tuple[str, ...]
    no_execution: bool
    opens_connection: bool
    runs_sql: bool

    @property
    def passed(self) -> bool:
        return (
            self.plans_equivalent
            and self.ordered_sql_stable
            and self.metadata_stable
            and not self.duplicate_table_names
            and not self.duplicate_index_names
            and not self.duplicate_constraint_names
            and not self.duplicate_sql_statements
            and self.no_execution
            and not self.opens_connection
            and not self.runs_sql
        )


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


def verify_postgresql_phase1_schema_bootstrap_idempotency(
    catalog: SchemaCatalog | None = None,
    *,
    repeat_count: int = 2,
) -> PostgreSQLSchemaBootstrapIdempotencyVerification:
    """Verify Phase 1 schema bootstrap planning is deterministic and duplicate-free.

    The verification is runtime-passive: it only rebuilds in-memory planning metadata
    and rendered SQL text, and it does not open a database connection or execute SQL.
    """

    if repeat_count < 2:
        raise ValueError("repeat_count must be at least 2.")

    plans = tuple(
        build_postgresql_phase1_schema_bootstrap_plan(catalog)
        for _ in range(repeat_count)
    )
    first_plan = plans[0]
    ordered_sql_sequences = tuple(plan.ordered_sql_statements for plan in plans)
    metadata_sequences = tuple(_bootstrap_metadata_signature(plan) for plan in plans)
    sql_statements = first_plan.ordered_sql_statements

    return PostgreSQLSchemaBootstrapIdempotencyVerification(
        repeated_plan_count=repeat_count,
        plans_equivalent=all(plan == first_plan for plan in plans),
        ordered_sql_stable=all(
            sql_sequence == ordered_sql_sequences[0]
            for sql_sequence in ordered_sql_sequences
        ),
        metadata_stable=all(
            metadata_sequence == metadata_sequences[0]
            for metadata_sequence in metadata_sequences
        ),
        duplicate_table_names=_duplicates(
            statement.table_name for statement in first_plan.create_table_statements
        ),
        duplicate_index_names=_duplicates(_index_names(sql_statements)),
        duplicate_constraint_names=_duplicates(_constraint_names(sql_statements)),
        duplicate_sql_statements=_duplicates(sql_statements),
        no_execution=all(plan.execution_out_of_scope for plan in plans),
        opens_connection=any(plan.opens_connection for plan in plans),
        runs_sql=any(plan.runs_sql for plan in plans),
    )


def _bootstrap_metadata_signature(
    plan: PostgreSQLSchemaBootstrapPlan,
) -> tuple[object, ...]:
    return (
        plan.target_database_engine,
        plan.schema_phase,
        plan.required_table_names,
        tuple(
            (statement.ordinal, statement.statement_kind, statement.table_name)
            for statement in plan.ordered_statements
        ),
        plan.execution_scope,
        plan.execution_out_of_scope,
        plan.opens_connection,
        plan.runs_sql,
        plan.creates_tables_now,
        plan.runs_migrations,
        plan.loads_environment,
        plan.loads_config_files,
        plan.performs_network_calls,
        plan.notes,
    )


def _index_names(sql_statements: Sequence[str]) -> tuple[str, ...]:
    return tuple(
        match.group(1)
        for statement in sql_statements
        for match in _CREATE_INDEX_IDENTIFIER_PATTERN.finditer(statement)
    )


def _constraint_names(sql_statements: Sequence[str]) -> tuple[str, ...]:
    return tuple(
        match.group(1)
        for statement in sql_statements
        for match in _CONSTRAINT_IDENTIFIER_PATTERN.finditer(statement)
    )


def _duplicates(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
            continue
        seen.add(value)
    return tuple(sorted(duplicates))
