"""Runtime-passive PostgreSQL DDL renderer for Phase 1 schema catalog."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    PostgreSQLDataType,
    SchemaCatalog,
    TableDefinition,
    get_postgresql_phase1_schema_catalog,
)

_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_POSTGRESQL_IDENTIFIER_LIMIT_BYTES = 63
_SHORT_IDENTIFIER_HASH_HEX_LENGTH = 12
_SHORT_IDENTIFIER_SEPARATOR = "_"
_DATA_TYPE_SQL: dict[PostgreSQLDataType, str] = {
    PostgreSQLDataType.UUID: "uuid",
    PostgreSQLDataType.TEXT: "text",
    PostgreSQLDataType.INTEGER: "integer",
    PostgreSQLDataType.NUMERIC: "numeric",
    PostgreSQLDataType.BOOLEAN: "boolean",
    PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE: "timestamp with time zone",
    PostgreSQLDataType.JSONB: "jsonb",
}


@dataclass(frozen=True)
class RenderedTableDDL:
    table_name: str
    create_table_statement: str
    create_index_statements: tuple[str, ...]


@dataclass(frozen=True)
class RenderedSchemaDDL:
    tables: tuple[RenderedTableDDL, ...]

    @property
    def statements(self) -> tuple[str, ...]:
        rendered: list[str] = []
        for table in self.tables:
            rendered.append(table.create_table_statement)
            rendered.extend(table.create_index_statements)
        return tuple(rendered)


def _validate_identifier(identifier: str, kind: str) -> None:
    if not _IDENTIFIER_PATTERN.match(identifier):
        raise ValueError(f"Invalid {kind} identifier: {identifier!r}")


def _render_identifier(identifier: str, kind: str) -> str:
    _validate_identifier(identifier, kind)
    if len(identifier.encode("utf-8")) <= _POSTGRESQL_IDENTIFIER_LIMIT_BYTES:
        return identifier

    suffix = hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:_SHORT_IDENTIFIER_HASH_HEX_LENGTH]
    prefix_limit = (
        _POSTGRESQL_IDENTIFIER_LIMIT_BYTES
        - len(_SHORT_IDENTIFIER_SEPARATOR)
        - _SHORT_IDENTIFIER_HASH_HEX_LENGTH
    )
    prefix = identifier[:prefix_limit].rstrip(_SHORT_IDENTIFIER_SEPARATOR)
    shortened_identifier = f"{prefix}{_SHORT_IDENTIFIER_SEPARATOR}{suffix}"
    _validate_identifier(shortened_identifier, kind)
    if len(shortened_identifier.encode("utf-8")) > _POSTGRESQL_IDENTIFIER_LIMIT_BYTES:
        raise ValueError(f"Invalid {kind} identifier length after shortening: {identifier!r}")
    return shortened_identifier


def render_create_table_statement(table_definition: TableDefinition) -> str:
    table_name = _render_identifier(table_definition.name, "table")

    primary_key_columns: list[str] = []
    lines: list[str] = []

    for column in table_definition.columns:
        column_name = _render_identifier(column.name, "column")
        column_sql = f"{column_name} {_DATA_TYPE_SQL[column.data_type]}"
        if not column.nullable:
            column_sql += " NOT NULL"
        lines.append(column_sql)
        if column.is_primary_key:
            primary_key_columns.append(column_name)

    if primary_key_columns:
        pk_name = _render_identifier(f"pk_{table_name}", "constraint")
        lines.append(f"CONSTRAINT {pk_name} PRIMARY KEY ({', '.join(primary_key_columns)})")

    for unique_constraint in table_definition.unique_constraints:
        unique_constraint_name = _render_identifier(unique_constraint.name, "constraint")
        unique_column_names: list[str] = []
        for column_name in unique_constraint.column_names:
            unique_column_names.append(_render_identifier(column_name, "column"))
        column_list = ", ".join(unique_column_names)
        lines.append(f"CONSTRAINT {unique_constraint_name} UNIQUE ({column_list})")

    for foreign_key in table_definition.foreign_keys:
        column_name = _render_identifier(foreign_key.column_name, "column")
        referenced_table_name = _render_identifier(foreign_key.referenced_table_name, "table")
        referenced_column_name = _render_identifier(foreign_key.referenced_column_name, "column")
        fk_name = _render_identifier(f"fk_{table_name}_{column_name}", "constraint")
        lines.append(
            "CONSTRAINT "
            f"{fk_name} FOREIGN KEY ({column_name}) "
            f"REFERENCES {referenced_table_name} ({referenced_column_name})"
        )

    inner = ",\n    ".join(lines)
    return f"CREATE TABLE {table_name} (\n    {inner}\n);"


def render_create_index_statements(table_definition: TableDefinition) -> tuple[str, ...]:
    table_name = _render_identifier(table_definition.name, "table")

    statements: list[str] = []
    for index in table_definition.indexes:
        index_name = _render_identifier(index.name, "index")
        columns: list[str] = []
        for column_name in index.column_names:
            columns.append(_render_identifier(column_name, "column"))
        unique_prefix = "UNIQUE " if index.unique else ""
        statements.append(
            f"CREATE {unique_prefix}INDEX {index_name} ON {table_name} ({', '.join(columns)});"
        )
    return tuple(statements)


def render_postgresql_phase1_schema_ddl(catalog: SchemaCatalog | None = None) -> RenderedSchemaDDL:
    active_catalog = catalog if catalog is not None else get_postgresql_phase1_schema_catalog()

    rendered_tables: list[RenderedTableDDL] = []
    for table_definition in active_catalog.tables:
        rendered_tables.append(
            RenderedTableDDL(
                table_name=_render_identifier(table_definition.name, "table"),
                create_table_statement=render_create_table_statement(table_definition),
                create_index_statements=render_create_index_statements(table_definition),
            )
        )

    return RenderedSchemaDDL(tables=tuple(rendered_tables))
