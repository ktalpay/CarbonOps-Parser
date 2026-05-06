"""Preview-only PostgreSQL insert statement builder."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from carbonfactor_parser.persistence.input import (
    PersistenceInput,
    PersistenceInputRecord,
)
from carbonfactor_parser.persistence.schema import (
    PostgreSQLPersistenceSchema,
    get_normalized_record_postgresql_schema,
)


class PostgreSQLInsertBuildStatus(str, Enum):
    """Status for building a PostgreSQL insert statement boundary."""

    READY = "ready"
    FAILED = "failed"
    NO_RECORDS = "no_records"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class PostgreSQLInsertBuildIssue:
    """Issue explaining why an insert statement was not built."""

    code: str
    message: str
    field_name: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class PostgreSQLInsertStatement:
    """Parameterized PostgreSQL insert statement data without execution."""

    sql: str
    parameters: tuple[tuple[object, ...], ...]
    target_table_name: str
    column_names: tuple[str, ...]
    record_count: int
    idempotency_key_fields: tuple[str, ...]
    conflict_target_fields: tuple[str, ...]


@dataclass(frozen=True)
class PostgreSQLInsertBuildResult:
    """Structured result for building PostgreSQL insert statement data."""

    status: PostgreSQLInsertBuildStatus
    statement: PostgreSQLInsertStatement | None = None
    issues: tuple[PostgreSQLInsertBuildIssue, ...] = ()


def build_postgresql_insert_statement(
    persistence_input: PersistenceInput,
    *,
    schema: PostgreSQLPersistenceSchema | None = None,
) -> PostgreSQLInsertBuildResult:
    """Build deterministic parameterized insert data without executing SQL."""

    active_schema = schema or get_normalized_record_postgresql_schema()
    if not persistence_input.records:
        return PostgreSQLInsertBuildResult(
            status=PostgreSQLInsertBuildStatus.NO_RECORDS,
            issues=(
                PostgreSQLInsertBuildIssue(
                    code="POSTGRESQL_INSERT_NO_RECORDS",
                    message=(
                        "PersistenceInput must include records before an "
                        "insert statement can be built."
                    ),
                    field_name="records",
                    severity="warning",
                ),
            ),
        )

    issues = _record_shape_issues(persistence_input)
    if issues:
        return PostgreSQLInsertBuildResult(
            status=PostgreSQLInsertBuildStatus.FAILED,
            issues=tuple(issues),
        )

    column_names = tuple(column.name for column in active_schema.columns)
    parameter_rows = tuple(
        _record_parameters(record, column_names) for record in persistence_input.records
    )

    return PostgreSQLInsertBuildResult(
        status=PostgreSQLInsertBuildStatus.READY,
        statement=PostgreSQLInsertStatement(
            sql=_render_insert_sql(active_schema.table_name, column_names),
            parameters=parameter_rows,
            target_table_name=active_schema.table_name,
            column_names=column_names,
            record_count=len(parameter_rows),
            idempotency_key_fields=tuple(active_schema.idempotency_key_fields),
            conflict_target_fields=tuple(active_schema.idempotency_key_fields),
        ),
    )


def _record_shape_issues(
    persistence_input: PersistenceInput,
) -> list[PostgreSQLInsertBuildIssue]:
    issues: list[PostgreSQLInsertBuildIssue] = []
    for position, record in enumerate(persistence_input.records, start=1):
        if not isinstance(record.source_family, str) or not record.source_family.strip():
            issues.append(
                PostgreSQLInsertBuildIssue(
                    code="POSTGRESQL_INSERT_MISSING_SOURCE_FAMILY",
                    message="record source_family must be a non-empty string.",
                    field_name=f"records[{position}].source_family",
                ),
            )
        if not isinstance(record.source_id, str) or not record.source_id.strip():
            issues.append(
                PostgreSQLInsertBuildIssue(
                    code="POSTGRESQL_INSERT_MISSING_SOURCE_ID",
                    message="record source_id must be a non-empty string.",
                    field_name=f"records[{position}].source_id",
                ),
            )
        if not isinstance(record.record_id, str) or not record.record_id.strip():
            issues.append(
                PostgreSQLInsertBuildIssue(
                    code="POSTGRESQL_INSERT_MISSING_RECORD_ID",
                    message="record_id must be a non-empty string.",
                    field_name=f"records[{position}].record_id",
                ),
            )
        if not record.normalized_fields:
            issues.append(
                PostgreSQLInsertBuildIssue(
                    code="POSTGRESQL_INSERT_MISSING_NORMALIZED_FIELDS",
                    message="normalized_fields must be non-empty.",
                    field_name=f"records[{position}].normalized_fields",
                ),
            )

    return issues


def _record_parameters(
    record: PersistenceInputRecord,
    column_names: tuple[str, ...],
) -> tuple[object, ...]:
    values = {
        "source_family": record.source_family,
        "source_id": record.source_id,
        "record_id": record.record_id,
        "record_index": record.record_index,
        "row_number": record.row_number,
        "normalized_fields": tuple(record.normalized_fields),
        "source_reference": record.source_reference,
        "source_artifact_reference": _metadata_value(
            record.parser_metadata,
            "source_artifact_reference",
        ),
        "source_checksum_sha256": _metadata_value(
            record.parser_metadata,
            "source_checksum_sha256",
        ),
        "parser_metadata": _mapping_payload(record.parser_metadata),
        "normalization_metadata": _mapping_payload(record.normalization_metadata),
        "created_at": None,
        "updated_at": None,
    }
    return tuple(values[column_name] for column_name in column_names)


def _metadata_value(
    metadata: Mapping[str, object] | None,
    key: str,
) -> object | None:
    if metadata is None:
        return None
    return metadata.get(key)


def _mapping_payload(
    metadata: Mapping[str, object] | None,
) -> tuple[tuple[str, object], ...] | None:
    if metadata is None:
        return None
    return tuple(sorted(metadata.items()))


def _render_insert_sql(table_name: str, column_names: tuple[str, ...]) -> str:
    placeholders = ", ".join("%s" for _ in column_names)
    columns = ", ".join(column_names)
    return f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
