from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from carbonfactor_parser.persistence.ingestion_run_history import (
    ParserIngestionIssueRecord,
    ParserIngestionRunHistoryCommand,
    ParserIngestionRunHistoryRepository,
    ParserIngestionRunHistoryStatus,
    ParserIngestionRunRecord,
    ParserIngestionSourceResultRecord,
    sanitized_ingestion_run_history_command,
    validate_ingestion_run_history_command,
)
from carbonfactor_parser.persistence.postgresql_ingestion_run_history_repository import (
    PostgreSQLIngestionRunHistoryRepository,
    _issue_parameters,
    _source_result_upsert_sql,
    stable_issue_uuid,
)


class _FakeConnection:
    def __init__(self) -> None:
        self.statements: list[tuple[str, object | None]] = []
        self.commit_count = 0
        self.rollback_count = 0

    def execute(self, statement: str, parameters: object | None = None) -> object:
        self.statements.append((statement, parameters))
        return object()

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


def _run(**overrides: object) -> ParserIngestionRunRecord:
    record = ParserIngestionRunRecord(
        run_id="run-001",
        started_at=datetime(2026, 6, 2, 12, 0, tzinfo=UTC),
        status="completed",
        enabled_source_families=("ghg_protocol", "defra_desnz"),
        total_parsed_rows=4,
        total_inserted_count=3,
        metadata={"operator_note": "safe"},
    )
    return replace(record, **overrides)


def _source(**overrides: object) -> ParserIngestionSourceResultRecord:
    record = ParserIngestionSourceResultRecord(
        run_id="run-001",
        source_family="ghg_protocol",
        target_year=2024,
        latest_year=2024,
        status="completed",
        parsed_rows=4,
        master_inserted=1,
        detail_inserted=3,
    )
    return replace(record, **overrides)


def _issue(**overrides: object) -> ParserIngestionIssueRecord:
    record = ParserIngestionIssueRecord(
        run_id="run-001",
        source_family="ghg_protocol",
        target_year=2024,
        stage="validation",
        code="ROW_INVALID",
        message="password=hunter2 token=abc api_key=secret",
        metadata={"url": "https://user:secret@example.com/file.csv?token=abc", "password": "hunter2"},
    )
    return replace(record, **overrides)


def _command() -> ParserIngestionRunHistoryCommand:
    return ParserIngestionRunHistoryCommand(
        run=_run(),
        source_results=(_source(),),
        issues=(_issue(),),
    )


def _codes(command: ParserIngestionRunHistoryCommand) -> tuple[str, ...]:
    return tuple(issue.code for issue in validate_ingestion_run_history_command(command))


def test_repository_implements_run_history_protocol_and_persists_command() -> None:
    connection = _FakeConnection()
    repository = PostgreSQLIngestionRunHistoryRepository(connection)

    assert isinstance(repository, ParserIngestionRunHistoryRepository)
    result = repository.persist_ingestion_run_history(_command())

    assert result.status is ParserIngestionRunHistoryStatus.DECLARED
    assert result.persisted_run_count == 1
    assert result.persisted_source_result_count == 1
    assert result.persisted_issue_count == 1
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert any("INSERT INTO parser_ingestion_runs" in statement for statement, _ in connection.statements)
    assert any("INSERT INTO parser_ingestion_source_results" in statement for statement, _ in connection.statements)
    assert any("INSERT INTO parser_ingestion_issues" in statement for statement, _ in connection.statements)


def test_validation_rejects_missing_run_id() -> None:
    assert "INGESTION_RUN_HISTORY_RUN_ID_REQUIRED" in _codes(
        ParserIngestionRunHistoryCommand(run=_run(run_id=""))
    )


def test_validation_rejects_negative_counts() -> None:
    assert "INGESTION_RUN_HISTORY_NON_NEGATIVE_COUNT_REQUIRED" in _codes(
        ParserIngestionRunHistoryCommand(run=_run(total_parsed_rows=-1))
    )
    assert "INGESTION_RUN_HISTORY_NON_NEGATIVE_COUNT_REQUIRED" in _codes(
        ParserIngestionRunHistoryCommand(
            run=_run(), source_results=(_source(parsed_rows=-1),)
        )
    )


def test_validation_rejects_invalid_source_family() -> None:
    assert "INGESTION_RUN_HISTORY_SOURCE_FAMILY_UNSUPPORTED" in _codes(
        ParserIngestionRunHistoryCommand(run=_run(enabled_source_families=("tenant_api",)))
    )
    assert "INGESTION_RUN_HISTORY_SOURCE_FAMILY_UNSUPPORTED" in _codes(
        ParserIngestionRunHistoryCommand(run=_run(), source_results=(_source(source_family="tenant_api"),))
    )


def test_validation_rejects_source_and_issue_run_id_mismatches() -> None:
    codes = _codes(
        ParserIngestionRunHistoryCommand(
            run=_run(),
            source_results=(_source(run_id="other-run"),),
            issues=(_issue(run_id="other-run"),),
        )
    )

    assert "INGESTION_RUN_HISTORY_SOURCE_RUN_ID_MISMATCH" in codes
    assert "INGESTION_RUN_HISTORY_ISSUE_RUN_ID_MISMATCH" in codes


def test_validation_rejects_non_positive_target_year() -> None:
    codes = _codes(
        ParserIngestionRunHistoryCommand(
            run=_run(),
            source_results=(_source(target_year=0),),
            issues=(_issue(target_year=-1),),
        )
    )

    assert codes.count("INGESTION_RUN_HISTORY_POSITIVE_INTEGER_REQUIRED") == 2


def test_redaction_sanitizes_issue_message_and_metadata_before_persistence() -> None:
    connection = _FakeConnection()
    result = PostgreSQLIngestionRunHistoryRepository(connection).persist_ingestion_run_history(_command())

    assert result.status is ParserIngestionRunHistoryStatus.DECLARED
    all_parameters = repr(tuple(parameters for _statement, parameters in connection.statements))
    assert "hunter2" not in all_parameters
    assert "token=abc" not in all_parameters
    assert "api_key=secret" not in all_parameters
    assert "user:secret" not in all_parameters
    assert "***" in all_parameters


def test_sanitized_command_redacts_issue_message_on_command_path() -> None:
    sanitized = sanitized_ingestion_run_history_command(_command())

    assert sanitized.issues[0].message == "password=*** token=*** api_key=***"
    assert "token=abc" not in repr(sanitized.issues[0].metadata)
    assert "hunter2" not in repr(sanitized.issues[0].metadata)
    assert sanitized.issues[0].metadata["password"] == "***"


def test_stable_issue_uuid_is_deterministic_for_same_sanitized_issue() -> None:
    first = _issue(message="password=hunter2")
    second = _issue(message="password=different-secret")

    assert stable_issue_uuid(first) == stable_issue_uuid(first)
    assert stable_issue_uuid(first) == stable_issue_uuid(second)


def test_issue_parameters_are_redacted_before_uuid_and_parameter_generation() -> None:
    sanitized_issue = sanitized_ingestion_run_history_command(_command()).issues[0]
    params = _issue_parameters(sanitized_issue)

    assert params[8] == "password=*** token=*** api_key=***"
    assert "hunter2" not in repr(params)


def test_source_result_upsert_targets_natural_unique_key() -> None:
    sql = " ".join(_source_result_upsert_sql().split())

    assert "ON CONFLICT (run_id, source_family, target_year) DO UPDATE" in sql
