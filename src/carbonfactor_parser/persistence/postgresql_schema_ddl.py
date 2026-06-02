"""Runtime-passive PostgreSQL Phase 1 schema DDL string contract."""

from __future__ import annotations

import hashlib
import re

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    ColumnDefinition,
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

__all__ = (
    "render_postgresql_phase1_create_table_ddl",
    "render_postgresql_phase1_index_ddl",
    "render_postgresql_phase1_schema_ddl",
    "render_postgresql_table_create_table_ddl",
    "render_postgresql_table_index_ddl",
)


def render_postgresql_phase1_schema_ddl(
    catalog: SchemaCatalog | None = None,
) -> tuple[str, ...]:
    """Return deterministic Phase 1 CREATE TABLE and index SQL strings."""

    active_catalog = _active_catalog(catalog)
    statements: list[str] = []
    for table_definition in active_catalog.tables:
        statements.append(render_postgresql_table_create_table_ddl(table_definition))
        statements.extend(render_postgresql_table_index_ddl(table_definition))
    return tuple(statements)


def render_postgresql_phase1_create_table_ddl(
    catalog: SchemaCatalog | None = None,
) -> tuple[str, ...]:
    """Return deterministic Phase 1 CREATE TABLE SQL strings."""

    return tuple(
        render_postgresql_table_create_table_ddl(table_definition)
        for table_definition in _active_catalog(catalog).tables
    )


def render_postgresql_phase1_index_ddl(
    catalog: SchemaCatalog | None = None,
) -> tuple[str, ...]:
    """Return deterministic Phase 1 CREATE INDEX SQL strings."""

    statements: list[str] = []
    for table_definition in _active_catalog(catalog).tables:
        statements.extend(render_postgresql_table_index_ddl(table_definition))
    return tuple(statements)


def render_postgresql_table_create_table_ddl(
    table_definition: TableDefinition,
) -> str:
    """Return one deterministic CREATE TABLE SQL string for a catalog table."""

    table_name = _render_identifier(table_definition.name, "table")
    column_names = _catalog_column_names(table_definition.columns)
    primary_key_columns: list[str] = []
    lines: list[str] = []

    for column in table_definition.columns:
        column_name = _render_identifier(column.name, "column")
        column_sql = f"{column_name} {_DATA_TYPE_SQL[column.data_type]}"
        if column.default_sql is not None:
            column_sql += f" DEFAULT {column.default_sql}"
        if not column.nullable:
            column_sql += " NOT NULL"
        lines.append(column_sql)
        if column.is_primary_key:
            primary_key_columns.append(column_name)

    if primary_key_columns:
        pk_name = _render_identifier(f"pk_{table_name}", "constraint")
        lines.append(
            f"CONSTRAINT {pk_name} PRIMARY KEY "
            f"({', '.join(primary_key_columns)})"
        )

    for unique_constraint in table_definition.unique_constraints:
        _validate_known_columns(unique_constraint.column_names, column_names)
        unique_constraint_name = _render_identifier(
            unique_constraint.name,
            "constraint",
        )
        unique_column_names = tuple(
            _render_identifier(column_name, "column")
            for column_name in unique_constraint.column_names
        )
        lines.append(
            f"CONSTRAINT {unique_constraint_name} UNIQUE "
            f"({', '.join(unique_column_names)})"
        )

    for foreign_key in table_definition.foreign_keys:
        _validate_known_columns((foreign_key.column_name,), column_names)
        column_name = _render_identifier(foreign_key.column_name, "column")
        referenced_table_name = _render_identifier(
            foreign_key.referenced_table_name,
            "table",
        )
        referenced_column_name = _render_identifier(
            foreign_key.referenced_column_name,
            "column",
        )
        fk_name = _render_identifier(f"fk_{table_name}_{column_name}", "constraint")
        lines.append(
            "CONSTRAINT "
            f"{fk_name} FOREIGN KEY ({column_name}) "
            f"REFERENCES {referenced_table_name} ({referenced_column_name})"
        )

    inner = ",\n    ".join(lines)
    return f"CREATE TABLE IF NOT EXISTS {table_name} (\n    {inner}\n);"


def render_postgresql_table_index_ddl(
    table_definition: TableDefinition,
) -> tuple[str, ...]:
    """Return deterministic CREATE INDEX SQL strings for catalog indexes."""

    table_name = _render_identifier(table_definition.name, "table")
    column_names = _catalog_column_names(table_definition.columns)
    statements: list[str] = []

    for index in table_definition.indexes:
        _validate_known_columns(index.column_names, column_names)
        index_name = _render_identifier(index.name, "index")
        index_column_names = tuple(
            _render_identifier(column_name, "column")
            for column_name in index.column_names
        )
        unique_prefix = "UNIQUE " if index.unique else ""
        statements.append(
            f"CREATE {unique_prefix}INDEX IF NOT EXISTS {index_name} "
            f"ON {table_name} ({', '.join(index_column_names)});"
        )

    return tuple(statements)


def _active_catalog(catalog: SchemaCatalog | None) -> SchemaCatalog:
    return catalog if catalog is not None else get_postgresql_phase1_schema_catalog()


def _catalog_column_names(columns: tuple[ColumnDefinition, ...]) -> frozenset[str]:
    column_names = frozenset(column.name for column in columns)
    if len(column_names) != len(columns):
        raise ValueError("Catalog table contains duplicate column names")
    return column_names


def _validate_known_columns(
    candidate_column_names: tuple[str, ...],
    known_column_names: frozenset[str],
) -> None:
    unknown_column_names = tuple(
        column_name
        for column_name in candidate_column_names
        if column_name not in known_column_names
    )
    if unknown_column_names:
        raise ValueError(
            "Catalog metadata references unknown columns: "
            f"{unknown_column_names!r}"
        )


def _render_identifier(identifier: str, kind: str) -> str:
    _validate_identifier(identifier, kind)
    if len(identifier.encode("utf-8")) <= _POSTGRESQL_IDENTIFIER_LIMIT_BYTES:
        return identifier

    suffix = hashlib.sha256(identifier.encode("utf-8")).hexdigest()[
        :_SHORT_IDENTIFIER_HASH_HEX_LENGTH
    ]
    prefix_limit = (
        _POSTGRESQL_IDENTIFIER_LIMIT_BYTES
        - len(_SHORT_IDENTIFIER_SEPARATOR)
        - _SHORT_IDENTIFIER_HASH_HEX_LENGTH
    )
    prefix = identifier[:prefix_limit].rstrip(_SHORT_IDENTIFIER_SEPARATOR)
    shortened_identifier = f"{prefix}{_SHORT_IDENTIFIER_SEPARATOR}{suffix}"
    _validate_identifier(shortened_identifier, kind)
    if len(shortened_identifier.encode("utf-8")) > _POSTGRESQL_IDENTIFIER_LIMIT_BYTES:
        raise ValueError(f"Invalid {kind} identifier length: {identifier!r}")
    return shortened_identifier


def _validate_identifier(identifier: str, kind: str) -> None:
    if not _IDENTIFIER_PATTERN.match(identifier):
        raise ValueError(f"Invalid {kind} identifier: {identifier!r}")
