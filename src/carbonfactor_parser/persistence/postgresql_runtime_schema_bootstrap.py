"""PostgreSQL runtime schema bootstrap for Phase 1 tables."""

from __future__ import annotations

from dataclasses import dataclass

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    get_required_table_names,
)
from carbonfactor_parser.persistence.postgresql_schema_ddl import (
    render_postgresql_phase1_create_table_ddl,
    render_postgresql_phase1_index_ddl,
)


@dataclass(frozen=True)
class PostgreSQLRuntimeSchemaBootstrapResult:
    """Result of runtime Phase 1 schema bootstrap."""

    required_table_names: tuple[str, ...]
    present_table_names: tuple[str, ...]
    missing_table_names: tuple[str, ...]
    created_table_names: tuple[str, ...]
    statement_count: int


def bootstrap_postgresql_phase1_schema(
    connection: object,
) -> PostgreSQLRuntimeSchemaBootstrapResult:
    """Create missing Phase 1 PostgreSQL tables with idempotent DDL."""

    required_table_names = get_required_table_names()
    present_before = _fetch_present_table_names(connection, required_table_names)

    statements = _idempotent_schema_statements()
    for statement in statements:
        _execute(connection, statement)
    _commit(connection)

    present_after = _fetch_present_table_names(connection, required_table_names)
    created = tuple(
        table_name
        for table_name in required_table_names
        if table_name in present_after and table_name not in present_before
    )
    missing_after = tuple(
        table_name
        for table_name in required_table_names
        if table_name not in present_after
    )
    return PostgreSQLRuntimeSchemaBootstrapResult(
        required_table_names=required_table_names,
        present_table_names=present_after,
        missing_table_names=missing_after,
        created_table_names=created,
        statement_count=len(statements),
    )


def _fetch_present_table_names(
    connection: object,
    required_table_names: tuple[str, ...],
) -> tuple[str, ...]:
    cursor = _execute(
        connection,
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = current_schema()
          AND table_name = ANY(%s)
        ORDER BY table_name
        """,
        (list(required_table_names),),
    )
    rows = _fetchall(cursor)
    found = {str(row[0]) for row in rows}
    return tuple(
        table_name for table_name in required_table_names if table_name in found
    )


def _idempotent_schema_statements() -> tuple[str, ...]:
    statements: list[str] = []
    for statement in render_postgresql_phase1_create_table_ddl():
        statements.append(
            statement.replace("CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ", 1),
        )
    for statement in render_postgresql_phase1_index_ddl():
        statements.append(
            statement.replace("CREATE INDEX ", "CREATE INDEX IF NOT EXISTS ", 1),
        )
    return tuple(statements)


def _execute(
    connection: object,
    statement: str,
    parameters: object | None = None,
) -> object:
    execute = getattr(connection, "execute")
    if parameters is None:
        return execute(statement)
    return execute(statement, parameters)


def _fetchall(cursor: object) -> list[object]:
    fetchall = getattr(cursor, "fetchall")
    rows = fetchall()
    return list(rows)


def _commit(connection: object) -> None:
    commit = getattr(connection, "commit", None)
    if commit is not None:
        commit()
