"""PostgreSQL parser ingestion run-history repository."""

from __future__ import annotations

import json
import uuid

from carbonfactor_parser.diagnostics.redaction import redact_sensitive_text
from carbonfactor_parser.persistence.ingestion_run_history import (
    ParserIngestionIssueRecord,
    ParserIngestionRunHistoryCommand,
    ParserIngestionRunHistoryIssue,
    ParserIngestionRunHistoryPersistResult,
    ParserIngestionRunHistoryStatus,
    ParserIngestionRunRecord,
    ParserIngestionSourceResultRecord,
    json_payload,
    sanitized_ingestion_run_history_command,
    validate_ingestion_run_history_command,
)


class PostgreSQLIngestionRunHistoryRepository:
    """Persist parser ingestion run-history records with idempotent upserts."""

    def __init__(self, connection: object) -> None:
        if connection is None:
            raise ValueError("connection must be provided.")
        self._connection = connection

    @property
    def provider_name(self) -> str:
        """Return the repository provider name."""

        return "postgresql"

    def persist_ingestion_run_history(
        self,
        command: ParserIngestionRunHistoryCommand,
    ) -> ParserIngestionRunHistoryPersistResult:
        """Persist one parser ingestion run-history command."""

        validation_issues = validate_ingestion_run_history_command(command)
        if validation_issues:
            return ParserIngestionRunHistoryPersistResult(
                provider_name=self.provider_name,
                status=ParserIngestionRunHistoryStatus.FAILED_VALIDATION,
                validation_failure_count=len(validation_issues),
                issues=validation_issues,
            )

        sanitized = sanitized_ingestion_run_history_command(command)
        try:
            _execute(self._connection, _run_upsert_sql(), _run_parameters(sanitized.run))
            for source_result in sanitized.source_results:
                _execute(
                    self._connection,
                    _source_result_upsert_sql(),
                    _source_result_parameters(source_result),
                )
            for issue in sanitized.issues:
                _execute(
                    self._connection,
                    _issue_insert_sql(),
                    _issue_parameters(issue),
                )
            _commit(self._connection)
        except Exception as exc:  # pragma: no cover - driver type varies
            _rollback(self._connection)
            return ParserIngestionRunHistoryPersistResult(
                provider_name=self.provider_name,
                status=ParserIngestionRunHistoryStatus.FAILED_DATABASE,
                issues=(
                    ParserIngestionRunHistoryIssue(
                        code="POSTGRESQL_INGESTION_RUN_HISTORY_DATABASE_ERROR",
                        message=redact_sensitive_text(str(exc)),
                        field_name="database",
                    ),
                ),
            )

        return ParserIngestionRunHistoryPersistResult(
            provider_name=self.provider_name,
            status=ParserIngestionRunHistoryStatus.DECLARED,
            persisted_run_count=1,
            persisted_source_result_count=len(sanitized.source_results),
            persisted_issue_count=len(sanitized.issues),
        )


def _run_upsert_sql() -> str:
    return """
        INSERT INTO parser_ingestion_runs (
            run_id,
            started_at,
            finished_at,
            status,
            trigger_type,
            config_hash,
            enabled_source_families,
            initial_year,
            cycle_count,
            total_parsed_rows,
            total_inserted_count,
            total_skipped_duplicate_count,
            failure_count,
            metadata,
            created_at,
            updated_at
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s,
            %s, %s, %s, %s::jsonb, NOW(), NOW()
        )
        ON CONFLICT (run_id) DO UPDATE SET
            started_at = EXCLUDED.started_at,
            finished_at = EXCLUDED.finished_at,
            status = EXCLUDED.status,
            trigger_type = EXCLUDED.trigger_type,
            config_hash = EXCLUDED.config_hash,
            enabled_source_families = EXCLUDED.enabled_source_families,
            initial_year = EXCLUDED.initial_year,
            cycle_count = EXCLUDED.cycle_count,
            total_parsed_rows = EXCLUDED.total_parsed_rows,
            total_inserted_count = EXCLUDED.total_inserted_count,
            total_skipped_duplicate_count = EXCLUDED.total_skipped_duplicate_count,
            failure_count = EXCLUDED.failure_count,
            metadata = EXCLUDED.metadata,
            updated_at = NOW()
        """


def _source_result_upsert_sql() -> str:
    return """
        INSERT INTO parser_ingestion_source_results (
            parser_ingestion_source_result_id,
            run_id,
            source_family,
            target_year,
            latest_year,
            status,
            download_status,
            parse_status,
            validation_status,
            insert_status,
            parsed_rows,
            master_inserted,
            master_skipped,
            detail_inserted,
            detail_skipped,
            issue_count,
            metadata,
            created_at,
            updated_at
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s::jsonb, NOW(), NOW()
        )
        ON CONFLICT (run_id, source_family, target_year) DO UPDATE SET
            latest_year = EXCLUDED.latest_year,
            status = EXCLUDED.status,
            download_status = EXCLUDED.download_status,
            parse_status = EXCLUDED.parse_status,
            validation_status = EXCLUDED.validation_status,
            insert_status = EXCLUDED.insert_status,
            parsed_rows = EXCLUDED.parsed_rows,
            master_inserted = EXCLUDED.master_inserted,
            master_skipped = EXCLUDED.master_skipped,
            detail_inserted = EXCLUDED.detail_inserted,
            detail_skipped = EXCLUDED.detail_skipped,
            issue_count = EXCLUDED.issue_count,
            metadata = EXCLUDED.metadata,
            updated_at = NOW()
        """


def _issue_insert_sql() -> str:
    return """
        INSERT INTO parser_ingestion_issues (
            parser_ingestion_issue_id,
            run_id,
            source_family,
            target_year,
            stage,
            code,
            severity,
            field_name,
            message,
            metadata,
            created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, NOW())
        ON CONFLICT (parser_ingestion_issue_id) DO NOTHING
        """


def _run_parameters(record: ParserIngestionRunRecord) -> tuple[object, ...]:
    return (
        record.run_id,
        record.started_at,
        record.finished_at,
        record.status,
        record.trigger_type,
        record.config_hash,
        json_payload(tuple(record.enabled_source_families)),
        record.initial_year,
        record.cycle_count,
        record.total_parsed_rows,
        record.total_inserted_count,
        record.total_skipped_duplicate_count,
        record.failure_count,
        json_payload(record.metadata or {}),
    )


def _source_result_parameters(record: ParserIngestionSourceResultRecord) -> tuple[object, ...]:
    return (
        str(stable_source_result_uuid(record)),
        record.run_id,
        record.source_family,
        record.target_year,
        record.latest_year,
        record.status,
        record.download_status,
        record.parse_status,
        record.validation_status,
        record.insert_status,
        record.parsed_rows,
        record.master_inserted,
        record.master_skipped,
        record.detail_inserted,
        record.detail_skipped,
        record.issue_count,
        json_payload(record.metadata or {}),
    )


def _issue_parameters(record: ParserIngestionIssueRecord) -> tuple[object, ...]:
    return (
        str(stable_issue_uuid(record)),
        record.run_id,
        record.source_family,
        record.target_year,
        record.stage,
        record.code,
        record.severity,
        record.field_name,
        record.message,
        json_payload(record.metadata or {}),
    )


def stable_source_result_uuid(record: ParserIngestionSourceResultRecord) -> uuid.UUID:
    """Return a deterministic source result id for the natural upsert key."""

    return _stable_uuid("parser_ingestion_source_result", record.run_id, record.source_family, record.target_year)


def stable_issue_uuid(record: ParserIngestionIssueRecord) -> uuid.UUID:
    """Return a deterministic issue id from the sanitized issue identity."""

    sanitized_message = redact_sensitive_text(record.message)
    return _stable_uuid(
        "parser_ingestion_issue",
        record.run_id,
        record.source_family,
        record.target_year,
        record.stage,
        record.code,
        sanitized_message,
    )


def _stable_uuid(*values: object) -> uuid.UUID:
    payload = json.dumps(tuple(str(value) for value in values), separators=(",", ":"))
    return uuid.uuid5(uuid.NAMESPACE_URL, payload)


def _execute(connection: object, statement: str, parameters: object | None = None) -> object:
    execute = getattr(connection, "execute")
    if parameters is None:
        return execute(statement)
    return execute(statement, parameters)


def _commit(connection: object) -> None:
    commit = getattr(connection, "commit", None)
    if commit is not None:
        commit()


def _rollback(connection: object) -> None:
    rollback = getattr(connection, "rollback", None)
    if rollback is not None:
        rollback()


__all__ = (
    "PostgreSQLIngestionRunHistoryRepository",
    "stable_issue_uuid",
    "stable_source_result_uuid",
    "_issue_insert_sql",
    "_issue_parameters",
    "_run_upsert_sql",
    "_source_result_upsert_sql",
)
