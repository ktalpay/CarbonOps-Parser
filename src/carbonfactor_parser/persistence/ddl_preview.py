"""Preview-only PostgreSQL DDL rendering from logical schema metadata."""

from __future__ import annotations

from carbonfactor_parser.persistence.schema import (
    PostgreSQLPersistenceColumn,
    PostgreSQLPersistenceSchema,
    get_normalized_record_postgresql_schema,
)


def render_postgresql_ddl_preview(
    schema: PostgreSQLPersistenceSchema | None = None,
) -> str:
    """Return deterministic PostgreSQL DDL preview text for review."""

    active_schema = schema or get_normalized_record_postgresql_schema()
    entries = [(_render_column(column),) for column in active_schema.columns]

    unique_constraint = _render_idempotency_constraint(active_schema)
    if unique_constraint:
        entries.append(unique_constraint)

    lines = (
        "-- PostgreSQL DDL preview only. Review before use in a separate migration.",
        f"CREATE TABLE {active_schema.table_name} (",
    )

    body_lines: list[str] = []
    for index, entry_lines in enumerate(entries):
        is_last_entry = index == len(entries) - 1
        for line_index, line in enumerate(entry_lines):
            is_last_entry_line = line_index == len(entry_lines) - 1
            suffix = "" if is_last_entry and is_last_entry_line else ","
            body_lines.append(f"{line}{suffix if is_last_entry_line else ''}")

    return "\n".join((*lines, *body_lines, ");", ""))


def _render_column(column: PostgreSQLPersistenceColumn) -> str:
    nullability = "" if column.nullable else " NOT NULL"
    return f"    {column.name} {column.logical_type}{nullability}"


def _render_idempotency_constraint(
    schema: PostgreSQLPersistenceSchema,
) -> tuple[str, ...] | None:
    if not schema.idempotency_key_fields:
        return None

    field_lines = []
    for index, field_name in enumerate(schema.idempotency_key_fields):
        suffix = "," if index < len(schema.idempotency_key_fields) - 1 else ""
        field_lines.append(f"        {field_name}{suffix}")

    constraint_name = f"{schema.table_name}_idempotency_key"
    return (
        f"    CONSTRAINT {constraint_name} UNIQUE (",
        *field_lines,
        "    )",
    )
