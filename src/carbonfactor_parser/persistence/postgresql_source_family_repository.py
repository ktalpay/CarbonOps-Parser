"""PostgreSQL runtime repository for source-specific master/detail tables."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import json
import uuid
from typing import Mapping

from carbonfactor_parser.diagnostics.redaction import redact_sensitive_text

from carbonfactor_parser.persistence.parsed_factor_persistence_writer import (
    persist_parsed_factor_records,
)
from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    SourceFamily,
    source_family_postgresql_value,
    source_family_table_prefix,
)
from carbonfactor_parser.persistence.source_family_repository import (
    SourceFamilyDetailRecord,
    SourceFamilyMasterRecord,
    SourceFamilyRepositoryIssue,
    SourceFamilyRepositoryPersistResult,
    SourceFamilyRepositoryPersistStatus,
    source_family_repository_table_names,
    validate_source_family_repository_inputs,
)


class PostgreSQLSourceSpecificFactorInsertStatus(str, Enum):
    """Status values for source-specific PostgreSQL inserts."""

    INSERTED = "inserted"
    FAILED_VALIDATION = "failed_validation"
    FAILED_DATABASE = "failed_database"
    NO_RECORDS = "no_records"


@dataclass(frozen=True)
class PostgreSQLSourceSpecificFactorInsertSummary:
    """User-visible source-specific master/detail insert counts."""

    status: PostgreSQLSourceSpecificFactorInsertStatus
    attempted: int
    inserted: int
    skipped_duplicate: int
    failed: int
    validation_error_count: int
    master_inserted: int = 0
    master_skipped: int = 0
    detail_inserted: int = 0
    detail_skipped: int = 0
    provider_name: str = "postgresql"
    issues: tuple[SourceFamilyRepositoryIssue, ...] = ()


class PostgreSQLSourceFamilyRuntimeRepository:
    """Insert parsed factor rows into PH-019 source-family tables."""

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
        batch: object,
    ) -> PostgreSQLSourceSpecificFactorInsertSummary:
        """Build and insert source-specific master/detail rows from a batch."""

        result = persist_parsed_factor_records(batch, self)
        attempted = result.attempted_detail_count
        inserted = result.persisted_detail_count
        skipped = result.skipped_detail_count
        if result.status.value == "no_records":
            status = PostgreSQLSourceSpecificFactorInsertStatus.NO_RECORDS
        elif any(
            issue.code == "POSTGRESQL_SOURCE_FAMILY_DATABASE_ERROR"
            for issue in result.issues
        ):
            status = PostgreSQLSourceSpecificFactorInsertStatus.FAILED_DATABASE
        elif result.status.value == "failed_validation":
            status = PostgreSQLSourceSpecificFactorInsertStatus.FAILED_VALIDATION
        else:
            status = PostgreSQLSourceSpecificFactorInsertStatus.INSERTED
        return PostgreSQLSourceSpecificFactorInsertSummary(
            status=status,
            attempted=attempted,
            inserted=inserted,
            skipped_duplicate=skipped,
            failed=attempted if status.name.startswith("FAILED") else 0,
            validation_error_count=result.validation_failure_count,
            master_inserted=result.persisted_master_count,
            master_skipped=result.skipped_master_count,
            detail_inserted=result.persisted_detail_count,
            detail_skipped=result.skipped_detail_count,
            issues=tuple(
                SourceFamilyRepositoryIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=issue.field_name,
                    severity=issue.severity,
                )
                for issue in result.issues
            ),
        )

    def persist_source_family_records(
        self,
        master_records: tuple[SourceFamilyMasterRecord, ...],
        detail_records: tuple[SourceFamilyDetailRecord, ...],
    ) -> SourceFamilyRepositoryPersistResult:
        """Insert source-family records with idempotent conflict handling."""

        validation = validate_source_family_repository_inputs(
            provider_name=self.provider_name,
            master_records=master_records,
            detail_records=detail_records,
        )
        if validation.issues:
            return SourceFamilyRepositoryPersistResult(
                provider_name=self.provider_name,
                status=SourceFamilyRepositoryPersistStatus.FAILED_VALIDATION,
                persisted_master_count=0,
                persisted_detail_count=0,
                validation_failure_count=len(validation.issues),
                issues=validation.issues,
            )

        inserted_masters = 0
        inserted_details = 0
        try:
            for master in master_records:
                self._ensure_ingestion_run(master)
                self._ensure_source_document(master)
                if _fetchone(
                    _execute(
                        self._connection,
                        _master_insert_sql(master.source_family),
                        _master_parameters(master),
                    )
                ) is not None:
                    inserted_masters += 1

            for detail in detail_records:
                if _fetchone(
                    _execute(
                        self._connection,
                        _detail_insert_sql(detail.source_family),
                        _detail_parameters(detail),
                    )
                ) is not None:
                    inserted_details += 1

            _commit(self._connection)
        except Exception as exc:  # pragma: no cover - driver type varies
            _rollback(self._connection)
            return SourceFamilyRepositoryPersistResult(
                provider_name=self.provider_name,
                status=SourceFamilyRepositoryPersistStatus.FAILED_DATABASE,
                persisted_master_count=0,
                persisted_detail_count=0,
                issues=(
                    SourceFamilyRepositoryIssue(
                        code="POSTGRESQL_SOURCE_FAMILY_DATABASE_ERROR",
                        message=_redact_sensitive_text(str(exc)),
                        field_name="database",
                    ),
                ),
            )

        return SourceFamilyRepositoryPersistResult(
            provider_name=self.provider_name,
            status=SourceFamilyRepositoryPersistStatus.DECLARED,
            persisted_master_count=inserted_masters,
            persisted_detail_count=inserted_details,
            skipped_master_count=len(master_records) - inserted_masters,
            skipped_detail_count=len(detail_records) - inserted_details,
        )

    def _ensure_ingestion_run(self, master: SourceFamilyMasterRecord) -> None:
        ingestion_run_id = _ingestion_run_uuid(master)
        if ingestion_run_id is None:
            return
        _execute(
            self._connection,
            """
            INSERT INTO ingestion_runs (
                ingestion_run_id,
                run_status,
                created_at,
                updated_at
            )
            VALUES (%s, %s, NOW(), NOW())
            ON CONFLICT (ingestion_run_id) DO NOTHING
            """,
            (str(ingestion_run_id), "completed"),
        )

    def _ensure_source_document(self, master: SourceFamilyMasterRecord) -> None:
        _execute(
            self._connection,
            """
            INSERT INTO source_documents (
                source_document_id,
                ingestion_run_id,
                source_family,
                source_document_uri,
                source_checksum_sha256,
                acquisition_status,
                acquired_at,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW())
            ON CONFLICT (source_family, source_document_uri, source_checksum_sha256)
            DO NOTHING
            """,
            (
                str(_source_document_uuid(master)),
                str(_ingestion_run_uuid(master)),
                source_family_postgresql_value(master.source_family),
                master.artifact_reference or master.source_document_id,
                master.artifact_checksum_sha256 or "checksum-unavailable",
                "downloaded",
            ),
        )


def _master_insert_sql(source_family: SourceFamily) -> str:
    master_table, _detail_table = source_family_repository_table_names(source_family)
    family_prefix = source_family_table_prefix(source_family)
    master_id = f"{family_prefix}_emission_factor_master_id"
    return f"""
        INSERT INTO {master_table} (
            {master_id},
            source_family,
            source_year,
            source_version,
            source_release,
            source_document_id,
            ingestion_run_id,
            run_id,
            master_external_key,
            status,
            artifact_reference,
            artifact_checksum_sha256,
            archive_reference,
            archive_checksum_sha256,
            effective_from,
            effective_to,
            record_checksum_sha256,
            metadata,
            created_at,
            updated_at
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s::jsonb, NOW(), NOW()
        )
        ON CONFLICT (source_family, source_year, source_version, master_external_key)
        DO NOTHING
        RETURNING {master_id}
        """


def _detail_insert_sql(source_family: SourceFamily) -> str:
    master_table, detail_table = source_family_repository_table_names(source_family)
    del master_table
    family_prefix = source_family_table_prefix(source_family)
    master_id = f"{family_prefix}_emission_factor_master_id"
    detail_id = f"{family_prefix}_emission_factor_detail_id"
    return f"""
        INSERT INTO {detail_table} (
            {detail_id},
            {master_id},
            detail_external_key,
            source_row_number,
            factor_id,
            factor_name,
            factor_value,
            factor_unit,
            status,
            record_checksum_sha256,
            raw_fields,
            normalized_fields,
            created_at,
            updated_at
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s::jsonb, %s::jsonb, NOW(), NOW()
        )
        ON CONFLICT ({master_id}, detail_external_key)
        DO NOTHING
        RETURNING {detail_id}
        """


def _master_parameters(record: SourceFamilyMasterRecord) -> tuple[object, ...]:
    return (
        str(_master_uuid(record.source_family, record.source_family_master_id)),
        source_family_postgresql_value(record.source_family),
        record.source_year,
        record.source_version,
        record.source_release,
        str(_source_document_uuid(record)),
        str(_ingestion_run_uuid(record)) if _ingestion_run_uuid(record) else None,
        record.run_id,
        record.master_external_key,
        record.status,
        record.artifact_reference,
        record.artifact_checksum_sha256,
        record.archive_reference,
        record.archive_checksum_sha256,
        record.effective_from,
        record.effective_to,
        record.record_checksum_sha256,
        _json_payload(record.metadata),
    )


def _detail_parameters(record: SourceFamilyDetailRecord) -> tuple[object, ...]:
    return (
        str(_detail_uuid(record.source_family, record.source_family_detail_id)),
        str(_master_uuid(record.source_family, record.source_family_master_id)),
        record.detail_external_key,
        record.source_row_number,
        record.factor_id,
        record.factor_name,
        str(Decimal(str(record.factor_value))),
        record.factor_unit,
        record.status,
        record.record_checksum_sha256,
        _json_payload(record.raw_fields),
        _json_payload(record.normalized_fields),
    )


def _source_document_uuid(record: SourceFamilyMasterRecord) -> uuid.UUID:
    return _stable_uuid(
        "source_document",
        source_family_postgresql_value(record.source_family),
        record.source_document_id,
    )


def _ingestion_run_uuid(record: SourceFamilyMasterRecord) -> uuid.UUID | None:
    source = record.ingestion_run_id or record.run_id
    if source is None:
        source = (
            f"{source_family_postgresql_value(record.source_family)}:"
            f"{record.source_year}:"
            f"{record.source_version}"
        )
    return _stable_uuid(
        "ingestion_run",
        source_family_postgresql_value(record.source_family),
        source,
    )


def _master_uuid(source_family: SourceFamily, master_id: str) -> uuid.UUID:
    return _stable_uuid("master", source_family_postgresql_value(source_family), master_id)


def _detail_uuid(source_family: SourceFamily, detail_id: str) -> uuid.UUID:
    return _stable_uuid("detail", source_family_postgresql_value(source_family), detail_id)


def _stable_uuid(*values: object) -> uuid.UUID:
    payload = json.dumps(tuple(str(value) for value in values), separators=(",", ":"))
    return uuid.uuid5(uuid.NAMESPACE_URL, payload)


def _json_payload(value: Mapping[str, object]) -> str:
    return json.dumps(_json_safe(value), sort_keys=True, separators=(",", ":"))


def _json_safe(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, tuple | list):
        return [_json_safe(item) for item in value]
    return value


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
    return redact_sensitive_text(value)


__all__ = (
    "PostgreSQLSourceFamilyRuntimeRepository",
    "PostgreSQLSourceSpecificFactorInsertStatus",
    "PostgreSQLSourceSpecificFactorInsertSummary",
)
