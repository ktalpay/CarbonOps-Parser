"""Parser ingestion run-history persistence contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
import json
from typing import Mapping, Protocol, runtime_checkable

from carbonfactor_parser.diagnostics.redaction import redact_sensitive_text

_ALLOWED_SOURCE_FAMILIES = frozenset(
    ("ghg_protocol", "defra_desnz", "ipcc_efdb", "configured_runner")
)
_REDACTED_VALUE = "***"
_SENSITIVE_METADATA_KEYS = frozenset(
    (
        "password",
        "passwd",
        "pwd",
        "token",
        "secret",
        "key",
        "api_key",
        "apikey",
        "access_key",
        "accesskey",
        "private_key",
        "privatekey",
        "dsn",
        "connection_string",
        "connectionstring",
        "connection_uri",
        "connectionuri",
        "database_url",
        "databaseurl",
    )
)
_SENSITIVE_COMPACT_METADATA_KEYS = frozenset(
    key.replace("_", "") for key in _SENSITIVE_METADATA_KEYS
)


class ParserIngestionRunHistoryStatus(str, Enum):
    """Status values for run-history persistence attempts."""

    DECLARED = "declared"
    FAILED_VALIDATION = "failed_validation"
    FAILED_DATABASE = "failed_database"


@dataclass(frozen=True)
class ParserIngestionRunHistoryIssue:
    """Validation or database issue raised by the run-history boundary."""

    code: str
    message: str
    field_name: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class ParserIngestionRunRecord:
    """Top-level parser ingestion run history record."""

    run_id: str
    started_at: datetime
    status: str
    finished_at: datetime | None = None
    trigger_type: str = "operator"
    config_hash: str | None = None
    enabled_source_families: tuple[str, ...] = ()
    initial_year: int | None = None
    cycle_count: int | None = None
    total_parsed_rows: int = 0
    total_inserted_count: int = 0
    total_skipped_duplicate_count: int = 0
    failure_count: int = 0
    metadata: Mapping[str, object] | None = None


@dataclass(frozen=True)
class ParserIngestionSourceResultRecord:
    """Per-source parser ingestion result history record."""

    run_id: str
    source_family: str
    status: str
    target_year: int | None = None
    latest_year: int | None = None
    download_status: str | None = None
    parse_status: str | None = None
    validation_status: str | None = None
    insert_status: str | None = None
    parsed_rows: int = 0
    master_inserted: int = 0
    master_skipped: int = 0
    detail_inserted: int = 0
    detail_skipped: int = 0
    issue_count: int = 0
    metadata: Mapping[str, object] | None = None


@dataclass(frozen=True)
class ParserIngestionIssueRecord:
    """Parser ingestion operational issue history record."""

    run_id: str
    stage: str
    code: str
    message: str
    source_family: str | None = None
    target_year: int | None = None
    severity: str = "error"
    field_name: str | None = None
    metadata: Mapping[str, object] | None = None


@dataclass(frozen=True)
class ParserIngestionRunHistoryCommand:
    """Command payload for persisting one parser ingestion run history snapshot."""

    run: ParserIngestionRunRecord
    source_results: tuple[ParserIngestionSourceResultRecord, ...] = ()
    issues: tuple[ParserIngestionIssueRecord, ...] = ()


@dataclass(frozen=True)
class ParserIngestionRunHistoryPersistResult:
    """Result returned after a run-history persistence attempt."""

    provider_name: str
    status: ParserIngestionRunHistoryStatus
    persisted_run_count: int = 0
    persisted_source_result_count: int = 0
    persisted_issue_count: int = 0
    validation_failure_count: int = 0
    issues: tuple[ParserIngestionRunHistoryIssue, ...] = ()


@runtime_checkable
class ParserIngestionRunHistoryRepository(Protocol):
    """Repository boundary for parser ingestion run-history persistence."""

    @property
    def provider_name(self) -> str:
        """Return the repository provider name."""

    def persist_ingestion_run_history(
        self,
        command: ParserIngestionRunHistoryCommand,
    ) -> ParserIngestionRunHistoryPersistResult:
        """Persist a parser ingestion run history command."""


def validate_ingestion_run_history_command(
    command: ParserIngestionRunHistoryCommand,
) -> tuple[ParserIngestionRunHistoryIssue, ...]:
    """Validate a parser ingestion run-history command without persistence."""

    issues: list[ParserIngestionRunHistoryIssue] = []
    run = command.run
    if not str(run.run_id or "").strip():
        issues.append(_issue("INGESTION_RUN_HISTORY_RUN_ID_REQUIRED", "run_id is required.", "run_id"))
    if run.started_at is None:
        issues.append(_issue("INGESTION_RUN_HISTORY_STARTED_AT_REQUIRED", "started_at is required.", "started_at"))
    if not str(run.status or "").strip():
        issues.append(_issue("INGESTION_RUN_HISTORY_STATUS_REQUIRED", "status is required.", "status"))

    _validate_positive_optional("initial_year", run.initial_year, issues)
    _validate_non_negative_optional("cycle_count", run.cycle_count, issues)
    for field_name in (
        "total_parsed_rows",
        "total_inserted_count",
        "total_skipped_duplicate_count",
        "failure_count",
    ):
        _validate_non_negative(field_name, getattr(run, field_name), issues)

    for source_family in run.enabled_source_families:
        _validate_source_family(source_family, "enabled_source_families", issues)
    _validate_json_metadata(run.metadata or {}, "metadata", issues)

    for index, source_result in enumerate(command.source_results):
        prefix = f"source_results[{index}]"
        if source_result.run_id != run.run_id:
            issues.append(_issue("INGESTION_RUN_HISTORY_SOURCE_RUN_ID_MISMATCH", "source result run_id must match command run_id.", f"{prefix}.run_id"))
        if not str(source_result.status or "").strip():
            issues.append(_issue("INGESTION_RUN_HISTORY_SOURCE_STATUS_REQUIRED", "source result status is required.", f"{prefix}.status"))
        _validate_source_family(source_result.source_family, f"{prefix}.source_family", issues)
        _validate_positive_optional(f"{prefix}.target_year", source_result.target_year, issues)
        _validate_positive_optional(f"{prefix}.latest_year", source_result.latest_year, issues)
        for field_name in (
            "parsed_rows",
            "master_inserted",
            "master_skipped",
            "detail_inserted",
            "detail_skipped",
            "issue_count",
        ):
            _validate_non_negative(f"{prefix}.{field_name}", getattr(source_result, field_name), issues)
        _validate_json_metadata(source_result.metadata or {}, f"{prefix}.metadata", issues)

    for index, issue_record in enumerate(command.issues):
        prefix = f"issues[{index}]"
        if issue_record.run_id != run.run_id:
            issues.append(_issue("INGESTION_RUN_HISTORY_ISSUE_RUN_ID_MISMATCH", "issue run_id must match command run_id.", f"{prefix}.run_id"))
        if issue_record.source_family is not None:
            _validate_source_family(issue_record.source_family, f"{prefix}.source_family", issues)
        _validate_positive_optional(f"{prefix}.target_year", issue_record.target_year, issues)
        if not str(issue_record.stage or "").strip():
            issues.append(_issue("INGESTION_RUN_HISTORY_ISSUE_STAGE_REQUIRED", "issue stage is required.", f"{prefix}.stage"))
        if not str(issue_record.code or "").strip():
            issues.append(_issue("INGESTION_RUN_HISTORY_ISSUE_CODE_REQUIRED", "issue code is required.", f"{prefix}.code"))
        if not str(issue_record.message or "").strip():
            issues.append(_issue("INGESTION_RUN_HISTORY_ISSUE_MESSAGE_REQUIRED", "issue message is required.", f"{prefix}.message"))
        _validate_json_metadata(issue_record.metadata or {}, f"{prefix}.metadata", issues)

    return tuple(issues)


def sanitized_ingestion_run_history_command(
    command: ParserIngestionRunHistoryCommand,
) -> ParserIngestionRunHistoryCommand:
    """Return a JSON-safe command with text content redacted for persistence."""

    run = command.run
    sanitized_run = ParserIngestionRunRecord(
        run_id=run.run_id,
        started_at=run.started_at,
        status=run.status,
        finished_at=run.finished_at,
        trigger_type=run.trigger_type,
        config_hash=run.config_hash,
        enabled_source_families=tuple(run.enabled_source_families),
        initial_year=run.initial_year,
        cycle_count=run.cycle_count,
        total_parsed_rows=run.total_parsed_rows,
        total_inserted_count=run.total_inserted_count,
        total_skipped_duplicate_count=run.total_skipped_duplicate_count,
        failure_count=run.failure_count,
        metadata=_json_safe_redacted(run.metadata or {}),
    )
    source_results = tuple(
        ParserIngestionSourceResultRecord(
            run_id=record.run_id,
            source_family=record.source_family,
            status=record.status,
            target_year=record.target_year,
            latest_year=record.latest_year,
            download_status=record.download_status,
            parse_status=record.parse_status,
            validation_status=record.validation_status,
            insert_status=record.insert_status,
            parsed_rows=record.parsed_rows,
            master_inserted=record.master_inserted,
            master_skipped=record.master_skipped,
            detail_inserted=record.detail_inserted,
            detail_skipped=record.detail_skipped,
            issue_count=record.issue_count,
            metadata=_json_safe_redacted(record.metadata or {}),
        )
        for record in command.source_results
    )
    issues = tuple(
        ParserIngestionIssueRecord(
            run_id=record.run_id,
            source_family=record.source_family,
            target_year=record.target_year,
            stage=record.stage,
            code=record.code,
            severity=record.severity,
            field_name=record.field_name,
            message=redact_sensitive_text(record.message),
            metadata=_json_safe_redacted(record.metadata or {}),
        )
        for record in command.issues
    )
    return ParserIngestionRunHistoryCommand(
        run=sanitized_run,
        source_results=source_results,
        issues=issues,
    )


def json_payload(value: object) -> str:
    """Serialize a JSON-safe, redacted value for PostgreSQL jsonb parameters."""

    return json.dumps(_json_safe_redacted(value), sort_keys=True, separators=(",", ":"))


def _issue(code: str, message: str, field_name: str) -> ParserIngestionRunHistoryIssue:
    return ParserIngestionRunHistoryIssue(code=code, message=message, field_name=field_name)


def _validate_source_family(
    source_family: str,
    field_name: str,
    issues: list[ParserIngestionRunHistoryIssue],
) -> None:
    if source_family not in _ALLOWED_SOURCE_FAMILIES:
        issues.append(_issue("INGESTION_RUN_HISTORY_SOURCE_FAMILY_UNSUPPORTED", "source_family is unsupported.", field_name))


def _validate_positive_optional(
    field_name: str,
    value: int | None,
    issues: list[ParserIngestionRunHistoryIssue],
) -> None:
    if value is not None and value <= 0:
        issues.append(_issue("INGESTION_RUN_HISTORY_POSITIVE_INTEGER_REQUIRED", f"{field_name} must be positive when provided.", field_name))


def _validate_non_negative_optional(
    field_name: str,
    value: int | None,
    issues: list[ParserIngestionRunHistoryIssue],
) -> None:
    if value is not None:
        _validate_non_negative(field_name, value, issues)


def _validate_non_negative(
    field_name: str,
    value: int,
    issues: list[ParserIngestionRunHistoryIssue],
) -> None:
    if value < 0:
        issues.append(_issue("INGESTION_RUN_HISTORY_NON_NEGATIVE_COUNT_REQUIRED", f"{field_name} must be non-negative.", field_name))


def _validate_json_metadata(
    value: Mapping[str, object],
    field_name: str,
    issues: list[ParserIngestionRunHistoryIssue],
) -> None:
    try:
        json.dumps(_json_safe_redacted(value), sort_keys=True)
    except (TypeError, ValueError) as exc:
        issues.append(_issue("INGESTION_RUN_HISTORY_METADATA_JSON_REQUIRED", f"metadata must be JSON serializable: {redact_sensitive_text(str(exc))}", field_name))


def _is_sensitive_metadata_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_")
    return (
        normalized in _SENSITIVE_METADATA_KEYS
        or normalized.replace("_", "") in _SENSITIVE_COMPACT_METADATA_KEYS
    )


def _json_safe_redacted(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        redacted_mapping: dict[str, object] = {}
        for key, item in sorted(value.items(), key=lambda pair: str(pair[0])):
            key_text = str(key)
            if _is_sensitive_metadata_key(key_text):
                redacted_mapping[key_text] = _REDACTED_VALUE
            else:
                redacted_mapping[key_text] = _json_safe_redacted(item)
        return redacted_mapping
    if isinstance(value, tuple | list):
        return [_json_safe_redacted(item) for item in value]
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value


__all__ = (
    "ParserIngestionIssueRecord",
    "ParserIngestionRunHistoryCommand",
    "ParserIngestionRunHistoryIssue",
    "ParserIngestionRunHistoryPersistResult",
    "ParserIngestionRunHistoryRepository",
    "ParserIngestionRunHistoryStatus",
    "ParserIngestionRunRecord",
    "ParserIngestionSourceResultRecord",
    "json_payload",
    "sanitized_ingestion_run_history_command",
    "validate_ingestion_run_history_command",
)
