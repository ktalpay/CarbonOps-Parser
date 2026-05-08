"""Runtime-passive PostgreSQL DDL renderer for Phase 1 schema catalog."""

from __future__ import annotations

from dataclasses import dataclass
import re

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    PostgreSQLDataType,
    SchemaCatalog,
    TableDefinition,
    get_postgresql_phase1_schema_catalog,
)

_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
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


def render_create_table_statement(table_definition: TableDefinition) -> str:
    _validate_identifier(table_definition.name, "table")

    primary_key_columns: list[str] = []
    lines: list[str] = []

    for column in table_definition.columns:
        _validate_identifier(column.name, "column")
        column_sql = f"{column.name} {_DATA_TYPE_SQL[column.data_type]}"
        if not column.nullable:
            column_sql += " NOT NULL"
        lines.append(column_sql)
        if column.is_primary_key:
            primary_key_columns.append(column.name)

    if primary_key_columns:
        pk_name = f"pk_{table_definition.name}"
        _validate_identifier(pk_name, "constraint")
        lines.append(f"CONSTRAINT {pk_name} PRIMARY KEY ({', '.join(primary_key_columns)})")

    for unique_constraint in table_definition.unique_constraints:
        _validate_identifier(unique_constraint.name, "constraint")
        for column_name in unique_constraint.column_names:
            _validate_identifier(column_name, "column")
        column_list = ", ".join(unique_constraint.column_names)
        lines.append(f"CONSTRAINT {unique_constraint.name} UNIQUE ({column_list})")

    for foreign_key in table_definition.foreign_keys:
        _validate_identifier(foreign_key.column_name, "column")
        _validate_identifier(foreign_key.referenced_table_name, "table")
        _validate_identifier(foreign_key.referenced_column_name, "column")
        fk_name = f"fk_{table_definition.name}_{foreign_key.column_name}"
        _validate_identifier(fk_name, "constraint")
        lines.append(
            "CONSTRAINT "
            f"{fk_name} FOREIGN KEY ({foreign_key.column_name}) "
            f"REFERENCES {foreign_key.referenced_table_name} ({foreign_key.referenced_column_name})"
        )

    inner = ",\n    ".join(lines)
    return f"CREATE TABLE {table_definition.name} (\n    {inner}\n);"


def render_create_index_statements(table_definition: TableDefinition) -> tuple[str, ...]:
    _validate_identifier(table_definition.name, "table")

    statements: list[str] = []
    for index in table_definition.indexes:
        _validate_identifier(index.name, "index")
        columns: list[str] = []
        for column_name in index.column_names:
            _validate_identifier(column_name, "column")
            columns.append(column_name)
        unique_prefix = "UNIQUE " if index.unique else ""
        statements.append(
            f"CREATE {unique_prefix}INDEX {index.name} ON {table_definition.name} ({', '.join(columns)});"
        )
    return tuple(statements)


def render_postgresql_phase1_schema_ddl(catalog: SchemaCatalog | None = None) -> RenderedSchemaDDL:
    active_catalog = catalog if catalog is not None else get_postgresql_phase1_schema_catalog()

    rendered_tables: list[RenderedTableDDL] = []
    for table_definition in active_catalog.tables:
        rendered_tables.append(
            RenderedTableDDL(
                table_name=table_definition.name,
                create_table_statement=render_create_table_statement(table_definition),
                create_index_statements=render_create_index_statements(table_definition),
            )
        )

    return RenderedSchemaDDL(tables=tuple(rendered_tables))
