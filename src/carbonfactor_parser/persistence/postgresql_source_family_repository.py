"""PostgreSQL runtime repository for source-specific master/detail tables."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.diagnostics.redaction import redact_sensitive_text

from carbonfactor_parser.persistence.parsed_factor_persistence_writer import (
    persist_parsed_factor_records,
)
from carbonfactor_parser.persistence.postgresql_source_family_parameters import (
    detail_parameters,
    master_parameters,
)
from carbonfactor_parser.persistence.postgresql_source_family_sql import (
    detail_insert_sql,
    master_insert_sql,
)
from carbonfactor_parser.persistence.postgresql_source_family_upserts import (
    ensure_ingestion_run,
    ensure_source_document,
)
from carbonfactor_parser.persistence.source_family_repository import (
    SourceFamilyDetailRecord,
    SourceFamilyMasterRecord,
    SourceFamilyRepositoryIssue,
    SourceFamilyRepositoryPersistResult,
    SourceFamilyRepositoryPersistStatus,
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
                ensure_ingestion_run(self._connection, master)
                ensure_source_document(self._connection, master)
                if _fetchone(
                    _execute(
                        self._connection,
                        master_insert_sql(master.source_family),
                        master_parameters(master),
                    )
                ) is not None:
                    inserted_masters += 1

            for detail in detail_records:
                if _fetchone(
                    _execute(
                        self._connection,
                        detail_insert_sql(detail.source_family),
                        detail_parameters(detail),
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
