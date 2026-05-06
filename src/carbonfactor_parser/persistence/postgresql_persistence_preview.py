"""Preview-only PostgreSQL persistence statement integration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.persistence.input import PersistenceInput
from carbonfactor_parser.persistence.postgresql_insert_builder import (
    PostgreSQLInsertBuildResult,
    PostgreSQLInsertBuildStatus,
    build_postgresql_insert_statement,
)
from carbonfactor_parser.persistence.schema import PostgreSQLPersistenceSchema


class PostgreSQLPersistencePreviewStatus(str, Enum):
    """Status for PostgreSQL persistence preview results."""

    READY = "ready"
    FAILED = "failed"
    NO_RECORDS = "no_records"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class PostgreSQLPersistencePreviewIssue:
    """Issue explaining why a PostgreSQL persistence preview is not ready."""

    code: str
    message: str
    field_name: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class PostgreSQLPersistencePreview:
    """PostgreSQL persistence preview data without execution."""

    sql: str
    parameters: tuple[tuple[object, ...], ...]
    target_table_name: str
    column_names: tuple[str, ...]
    record_count: int
    idempotency_key_fields: tuple[str, ...]
    conflict_target_fields: tuple[str, ...]


@dataclass(frozen=True)
class PostgreSQLPersistencePreviewResult:
    """Structured preview result for PostgreSQL persistence statement data."""

    status: PostgreSQLPersistencePreviewStatus
    insert_build_status: PostgreSQLInsertBuildStatus
    preview: PostgreSQLPersistencePreview | None = None
    issues: tuple[PostgreSQLPersistencePreviewIssue, ...] = ()


def build_postgresql_persistence_preview(
    persistence_input: PersistenceInput,
    *,
    schema: PostgreSQLPersistenceSchema | None = None,
) -> PostgreSQLPersistencePreviewResult:
    """Build a PostgreSQL persistence preview without executing SQL."""

    insert_result = build_postgresql_insert_statement(
        persistence_input,
        schema=schema,
    )
    if (
        insert_result.status != PostgreSQLInsertBuildStatus.READY
        or insert_result.statement is None
    ):
        return PostgreSQLPersistencePreviewResult(
            status=_preview_status(insert_result.status),
            insert_build_status=insert_result.status,
            issues=tuple(
                PostgreSQLPersistencePreviewIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=issue.field_name,
                    severity=issue.severity,
                )
                for issue in insert_result.issues
            ),
        )

    statement = insert_result.statement
    return PostgreSQLPersistencePreviewResult(
        status=PostgreSQLPersistencePreviewStatus.READY,
        insert_build_status=insert_result.status,
        preview=PostgreSQLPersistencePreview(
            sql=statement.sql,
            parameters=statement.parameters,
            target_table_name=statement.target_table_name,
            column_names=statement.column_names,
            record_count=statement.record_count,
            idempotency_key_fields=statement.idempotency_key_fields,
            conflict_target_fields=statement.conflict_target_fields,
        ),
    )


def _preview_status(
    insert_build_status: PostgreSQLInsertBuildStatus,
) -> PostgreSQLPersistencePreviewStatus:
    return PostgreSQLPersistencePreviewStatus(insert_build_status.value)
