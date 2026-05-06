"""PostgreSQL persistence schema boundary descriptors."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PostgreSQLPersistenceColumn:
    """Logical PostgreSQL column descriptor without SQL generation."""

    name: str
    logical_type: str
    nullable: bool
    description: str


@dataclass(frozen=True)
class PostgreSQLPersistenceSchema:
    """Logical PostgreSQL table descriptor for future normalized records."""

    table_name: str
    columns: tuple[PostgreSQLPersistenceColumn, ...]
    idempotency_key_fields: tuple[str, ...]


def get_normalized_record_postgresql_schema() -> PostgreSQLPersistenceSchema:
    """Return deterministic logical schema metadata without database behavior."""

    return PostgreSQLPersistenceSchema(
        table_name="normalized_records",
        columns=(
            PostgreSQLPersistenceColumn(
                name="source_family",
                logical_type="text",
                nullable=False,
                description="Source family carried by PersistenceInput.",
            ),
            PostgreSQLPersistenceColumn(
                name="source_id",
                logical_type="text",
                nullable=False,
                description="Source id carried by PersistenceInput.",
            ),
            PostgreSQLPersistenceColumn(
                name="record_id",
                logical_type="text",
                nullable=False,
                description="Normalized record identity from NormalizedRecord.",
            ),
            PostgreSQLPersistenceColumn(
                name="record_index",
                logical_type="text",
                nullable=True,
                description="Parser or normalization record index when available.",
            ),
            PostgreSQLPersistenceColumn(
                name="row_number",
                logical_type="text",
                nullable=True,
                description="Source row number when available.",
            ),
            PostgreSQLPersistenceColumn(
                name="normalized_fields",
                logical_type="jsonb",
                nullable=False,
                description="NormalizedRecord.fields payload preserved as structured data.",
            ),
            PostgreSQLPersistenceColumn(
                name="source_reference",
                logical_type="text",
                nullable=True,
                description="Source reference metadata when available.",
            ),
            PostgreSQLPersistenceColumn(
                name="source_artifact_reference",
                logical_type="text",
                nullable=True,
                description="Future source artifact reference for idempotency context.",
            ),
            PostgreSQLPersistenceColumn(
                name="source_checksum_sha256",
                logical_type="text",
                nullable=True,
                description="Future source checksum metadata for idempotency context.",
            ),
            PostgreSQLPersistenceColumn(
                name="parser_metadata",
                logical_type="jsonb",
                nullable=True,
                description="Parser metadata when explicitly supplied.",
            ),
            PostgreSQLPersistenceColumn(
                name="normalization_metadata",
                logical_type="jsonb",
                nullable=True,
                description="Normalization metadata when explicitly supplied.",
            ),
            PostgreSQLPersistenceColumn(
                name="created_at",
                logical_type="timestamptz",
                nullable=True,
                description="Future operational creation timestamp.",
            ),
            PostgreSQLPersistenceColumn(
                name="updated_at",
                logical_type="timestamptz",
                nullable=True,
                description="Future operational update timestamp.",
            ),
        ),
        idempotency_key_fields=(
            "source_family",
            "source_id",
            "record_id",
            "source_artifact_reference",
            "source_checksum_sha256",
        ),
    )
