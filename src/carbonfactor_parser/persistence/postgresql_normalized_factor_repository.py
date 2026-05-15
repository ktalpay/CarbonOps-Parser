"""PostgreSQL runtime insert repository for parser normalized factor records."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
import hashlib
import json
import re
from typing import TYPE_CHECKING, Callable, Mapping, Sequence

from carbonfactor_parser.persistence.postgresql_runtime_config import (
    PostgreSQLRuntimeConfig,
    PostgreSQLRuntimeConfigLoadResult,
)

if TYPE_CHECKING:
    from carbonfactor_parser.parsers.normalized_output_row_contract import (
        ParserNormalizedOutputBatch,
        ParserNormalizedOutputRow,
    )
else:
    ParserNormalizedOutputBatch = object
    ParserNormalizedOutputRow = object


NORMALIZED_FACTOR_RECORDS_TABLE_NAME = "normalized_factor_records"


class PostgreSQLNormalizedFactorInsertStatus(str, Enum):
    """Status values for PostgreSQL normalized factor inserts."""

    INSERTED = "inserted"
    FAILED_VALIDATION = "failed_validation"
    FAILED_DATABASE = "failed_database"
    NO_RECORDS = "no_records"


@dataclass(frozen=True)
class PostgreSQLNormalizedFactorInsertIssue:
    """Safe structured insert issue."""

    code: str
    message: str
    field_name: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class PostgreSQLNormalizedFactorInsertSummary:
    """Deterministic insert summary for normalized factor records."""

    status: PostgreSQLNormalizedFactorInsertStatus
    attempted: int
    inserted: int
    skipped_duplicate: int
    failed: int
    validation_error_count: int
    provider_name: str = "postgresql"
    issues: tuple[PostgreSQLNormalizedFactorInsertIssue, ...] = ()


@dataclass(frozen=True)
class _InsertRecord:
    normalized_factor_record_id: str
    idempotency_key_sha256: str
    source_family: str
    source_id: str
    source_year: int | None
    source_version: str | None
    record_id: str
    source_row_number: int | None
    source_document_reference: str | None
    source_artifact_reference: str | None
    source_checksum_sha256: str | None
    factor_id: str | None
    factor_name: str | None
    factor_value: Decimal
    factor_unit: str
    validation_status: str
    run_id: str | None
    parser_key: str
    metadata_json: str
    normalized_fields_json: str
    warnings_json: str
    errors_json: str


class PostgreSQLNormalizedFactorRuntimeRepository:
    """Runtime PostgreSQL repository using a caller-provided connection."""

    def __init__(self, connection: object) -> None:
        if connection is None:
            raise ValueError("connection must be provided.")
        self._connection = connection

    @property
    def provider_name(self) -> str:
        """Return the repository provider name."""

        return "postgresql"

    def insert_normalized_factor_records(
        self,
        batch: ParserNormalizedOutputBatch,
    ) -> PostgreSQLNormalizedFactorInsertSummary:
        """Insert normalized factor rows with idempotent conflict handling."""

        records, validation_issues = _build_insert_records(batch)
        if validation_issues:
            return PostgreSQLNormalizedFactorInsertSummary(
                status=PostgreSQLNormalizedFactorInsertStatus.FAILED_VALIDATION,
                attempted=len(batch.rows),
                inserted=0,
                skipped_duplicate=0,
                failed=len(batch.rows),
                validation_error_count=len(validation_issues),
                issues=validation_issues,
            )
        if not records:
            return PostgreSQLNormalizedFactorInsertSummary(
                status=PostgreSQLNormalizedFactorInsertStatus.NO_RECORDS,
                attempted=0,
                inserted=0,
                skipped_duplicate=0,
                failed=0,
                validation_error_count=0,
                issues=(
                    PostgreSQLNormalizedFactorInsertIssue(
                        code="POSTGRESQL_NORMALIZED_FACTOR_NO_RECORDS",
                        message="batch must include records before insert.",
                        field_name="batch.rows",
                        severity="warning",
                    ),
                ),
            )

        inserted = 0
        try:
            for record in records:
                cursor = _execute(self._connection, _INSERT_SQL, _parameters(record))
                if _fetchone(cursor) is None:
                    continue
                inserted += 1
            _commit(self._connection)
        except Exception as exc:  # pragma: no cover - exact driver type varies
            _rollback(self._connection)
            return PostgreSQLNormalizedFactorInsertSummary(
                status=PostgreSQLNormalizedFactorInsertStatus.FAILED_DATABASE,
                attempted=len(records),
                inserted=0,
                skipped_duplicate=0,
                failed=len(records),
                validation_error_count=0,
                issues=(
                    PostgreSQLNormalizedFactorInsertIssue(
                        code="POSTGRESQL_NORMALIZED_FACTOR_DATABASE_ERROR",
                        message=_redact_sensitive_text(str(exc)),
                        field_name="database",
                    ),
                ),
            )

        skipped = len(records) - inserted
        return PostgreSQLNormalizedFactorInsertSummary(
            status=PostgreSQLNormalizedFactorInsertStatus.INSERTED,
            attempted=len(records),
            inserted=inserted,
            skipped_duplicate=skipped,
            failed=0,
            validation_error_count=0,
        )


def insert_postgresql_normalized_factor_records(
    batch: ParserNormalizedOutputBatch,
    *,
    config_result: PostgreSQLRuntimeConfigLoadResult,
    connection_factory: Callable[[PostgreSQLRuntimeConfig], object],
) -> PostgreSQLNormalizedFactorInsertSummary:
    """Insert via explicit config and connection factory, failing closed."""

    if not config_result.is_ready or config_result.config is None:
        return PostgreSQLNormalizedFactorInsertSummary(
            status=PostgreSQLNormalizedFactorInsertStatus.FAILED_VALIDATION,
            attempted=len(batch.rows),
            inserted=0,
            skipped_duplicate=0,
            failed=len(batch.rows),
            validation_error_count=len(config_result.issues),
            issues=tuple(
                PostgreSQLNormalizedFactorInsertIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=issue.field_name,
                    severity=issue.severity,
                )
                for issue in config_result.issues
            ),
        )

    try:
        connection = connection_factory(config_result.config)
    except Exception as exc:  # pragma: no cover - exact factory failures vary
        return PostgreSQLNormalizedFactorInsertSummary(
            status=PostgreSQLNormalizedFactorInsertStatus.FAILED_DATABASE,
            attempted=len(batch.rows),
            inserted=0,
            skipped_duplicate=0,
            failed=len(batch.rows),
            validation_error_count=0,
            issues=(
                PostgreSQLNormalizedFactorInsertIssue(
                    code="POSTGRESQL_NORMALIZED_FACTOR_CONNECTION_ERROR",
                    message=_redact_sensitive_text(str(exc)),
                    field_name="database",
                ),
            ),
        )

    return PostgreSQLNormalizedFactorRuntimeRepository(
        connection,
    ).insert_normalized_factor_records(batch)


def _build_insert_records(
    batch: ParserNormalizedOutputBatch,
) -> tuple[
    tuple[_InsertRecord, ...],
    tuple[PostgreSQLNormalizedFactorInsertIssue, ...],
]:
    from carbonfactor_parser.parsers.normalized_output_row_contract import (
        validate_parser_normalized_output_batch,
    )

    issues: list[PostgreSQLNormalizedFactorInsertIssue] = []
    for issue in validate_parser_normalized_output_batch(batch).issues:
        issues.append(
            PostgreSQLNormalizedFactorInsertIssue(
                code=issue.code,
                message=issue.message,
                field_name=issue.field_name,
                severity=issue.severity,
            ),
        )

    records: list[_InsertRecord] = []
    for position, row in enumerate(batch.rows, start=1):
        record, row_issues = _map_row(row, position)
        issues.extend(row_issues)
        if record is not None:
            records.append(record)

    if issues:
        return (), tuple(issues)
    return tuple(records), ()


def _map_row(
    row: ParserNormalizedOutputRow,
    position: int,
) -> tuple[_InsertRecord | None, tuple[PostgreSQLNormalizedFactorInsertIssue, ...]]:
    fields = dict(row.normalized_fields)
    issues: list[PostgreSQLNormalizedFactorInsertIssue] = []
    factor_value, factor_value_issue = _required_decimal(
        fields,
        ("factor_value", "value"),
        f"rows[{position}].factor_value",
    )
    if factor_value_issue is not None:
        issues.append(factor_value_issue)

    factor_unit = _text_or_none(_first_field(fields, "factor_unit", "unit"))
    if factor_unit is None:
        issues.append(
            PostgreSQLNormalizedFactorInsertIssue(
                code="POSTGRESQL_NORMALIZED_FACTOR_MISSING_FACTOR_UNIT",
                message="normalized factor row must include factor_unit or unit.",
                field_name=f"rows[{position}].factor_unit",
            ),
        )

    source_year = _positive_int_or_none(
        _first_field(fields, "source_year", "reporting_year"),
    )
    if source_year is None:
        source_year = row.reporting_year
    source_document_reference = _text_or_none(
        _first_field(fields, "source_document_id", "source_document_reference"),
    )
    source_artifact_reference = _text_or_none(
        _first_field(fields, "source_artifact_reference", "artifact_reference"),
    ) or row.artifact_reference
    source_checksum_sha256 = _text_or_none(
        _first_field(fields, "source_checksum_sha256", "checksum_sha256"),
    )

    if issues or factor_value is None or factor_unit is None:
        return None, tuple(issues)

    source_version = _text_or_none(_first_field(fields, "source_version"))
    factor_id = _text_or_none(_first_field(fields, "factor_id"))
    factor_name = _text_or_none(_first_field(fields, "factor_name", "name"))
    run_id = _text_or_none(_first_field(fields, "run_id", "ingestion_run_id"))
    validation_status = _text_or_none(
        _first_field(fields, "validation_status"),
    ) or row.status.value
    idempotency_key = _idempotency_key(
        row.source_family,
        row.source_key,
        source_year,
        source_document_reference or source_artifact_reference,
        source_checksum_sha256,
        row.row_id,
    )
    metadata = {
        "artifact_identifier": row.artifact_identifier,
        "parser_key": row.parser_key,
        "reporting_year": row.reporting_year,
        "source_row_number": row.source_row_number,
        "status": row.status.value,
    }

    return (
        _InsertRecord(
            normalized_factor_record_id=f"nfr_{idempotency_key[:32]}",
            idempotency_key_sha256=idempotency_key,
            source_family=row.source_family,
            source_id=row.source_key,
            source_year=source_year,
            source_version=source_version,
            record_id=row.row_id,
            source_row_number=row.source_row_number,
            source_document_reference=source_document_reference,
            source_artifact_reference=source_artifact_reference,
            source_checksum_sha256=source_checksum_sha256,
            factor_id=factor_id,
            factor_name=factor_name,
            factor_value=factor_value,
            factor_unit=factor_unit,
            validation_status=validation_status,
            run_id=run_id,
            parser_key=row.parser_key,
            metadata_json=_json_dumps(metadata),
            normalized_fields_json=_json_dumps(fields),
            warnings_json=_json_dumps(row.warnings),
            errors_json=_json_dumps(row.errors),
        ),
        (),
    )


def _idempotency_key(
    source_family: str,
    source_id: str,
    source_year: int | None,
    source_document_identity: str | None,
    source_checksum_sha256: str | None,
    record_id: str,
) -> str:
    payload = "\x1f".join(
        (
            source_family.strip().lower(),
            source_id.strip().lower(),
            "" if source_year is None else str(source_year),
            source_document_identity or "",
            source_checksum_sha256 or "",
            record_id,
        ),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _required_decimal(
    fields: Mapping[str, object],
    names: Sequence[str],
    field_name: str,
) -> tuple[Decimal | None, PostgreSQLNormalizedFactorInsertIssue | None]:
    value = _first_field(fields, *names)
    if value is None or _text_or_none(value) is None:
        return None, PostgreSQLNormalizedFactorInsertIssue(
            code="POSTGRESQL_NORMALIZED_FACTOR_MISSING_FACTOR_VALUE",
            message="normalized factor row must include factor_value or value.",
            field_name=field_name,
        )
    try:
        return Decimal(str(value)), None
    except (InvalidOperation, ValueError):
        return None, PostgreSQLNormalizedFactorInsertIssue(
            code="POSTGRESQL_NORMALIZED_FACTOR_INVALID_FACTOR_VALUE",
            message="factor_value must be numeric.",
            field_name=field_name,
        )


def _first_field(fields: Mapping[str, object], *names: str) -> object | None:
    for name in names:
        if name in fields:
            return fields[name]
    return None


def _text_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _positive_int_or_none(value: object | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _json_dumps(value: object) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _execute(
    connection: object,
    statement: str,
    parameters: object | None = None,
) -> object:
    execute = getattr(connection, "execute")
    if parameters is None:
        return execute(statement)
    return execute(statement, parameters)


def _fetchone(cursor: object) -> object | None:
    fetchone = getattr(cursor, "fetchone")
    return fetchone()


def _commit(connection: object) -> None:
    commit = getattr(connection, "commit", None)
    if commit is not None:
        commit()


def _rollback(connection: object) -> None:
    rollback = getattr(connection, "rollback", None)
    if rollback is not None:
        rollback()


def _redact_sensitive_text(value: str) -> str:
    redacted = _DSN_PATTERN.sub(r"\1//\2:***@", value)
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(r"\1=***", redacted)
    return redacted


_DSN_PATTERN = re.compile(r"([a-z][a-z0-9+.-]*:)//([^:@/\s]+):([^@/\s]+)@")
_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(password|passwd|pwd|dsn|connection_string)=([^\s,;]+)"),
)

_INSERT_SQL = """
INSERT INTO normalized_factor_records (
    normalized_factor_record_id,
    idempotency_key_sha256,
    source_family,
    source_id,
    source_year,
    source_version,
    record_id,
    source_row_number,
    source_document_reference,
    source_artifact_reference,
    source_checksum_sha256,
    factor_id,
    factor_name,
    factor_value,
    factor_unit,
    validation_status,
    run_id,
    parser_key,
    metadata,
    normalized_fields,
    warnings,
    errors,
    created_at,
    updated_at
)
VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb,
    NOW(), NOW()
)
ON CONFLICT (idempotency_key_sha256) DO NOTHING
RETURNING normalized_factor_record_id
"""


def _parameters(record: _InsertRecord) -> tuple[object, ...]:
    return (
        record.normalized_factor_record_id,
        record.idempotency_key_sha256,
        record.source_family,
        record.source_id,
        record.source_year,
        record.source_version,
        record.record_id,
        record.source_row_number,
        record.source_document_reference,
        record.source_artifact_reference,
        record.source_checksum_sha256,
        record.factor_id,
        record.factor_name,
        record.factor_value,
        record.factor_unit,
        record.validation_status,
        record.run_id,
        record.parser_key,
        record.metadata_json,
        record.normalized_fields_json,
        record.warnings_json,
        record.errors_json,
    )
