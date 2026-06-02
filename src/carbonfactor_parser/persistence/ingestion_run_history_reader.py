"""Read-side boundary for parser ingestion run history."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
import json
from typing import Protocol, runtime_checkable


_RUN_COLUMNS = (
    "run_id",
    "started_at",
    "finished_at",
    "status",
    "trigger_type",
    "config_hash",
    "enabled_source_families",
    "initial_year",
    "cycle_count",
    "total_parsed_rows",
    "total_inserted_count",
    "total_skipped_duplicate_count",
    "failure_count",
    "metadata",
)
_SOURCE_RESULT_COLUMNS = (
    "run_id",
    "source_family",
    "target_year",
    "latest_year",
    "status",
    "download_status",
    "parse_status",
    "validation_status",
    "insert_status",
    "parsed_rows",
    "master_inserted",
    "master_skipped",
    "detail_inserted",
    "detail_skipped",
    "issue_count",
    "metadata",
)
_ISSUE_COLUMNS = (
    "run_id",
    "source_family",
    "target_year",
    "stage",
    "code",
    "severity",
    "field_name",
    "message",
    "metadata",
    "created_at",
)
_MIN_RECENT_RUN_LIMIT = 1
_MAX_RECENT_RUN_LIMIT = 100
_DEFAULT_RECENT_RUN_LIMIT = 20


@dataclass(frozen=True)
class ParserIngestionRunReadModel:
    """Read model for one parser ingestion run history row."""

    run_id: str
    started_at: datetime | object
    finished_at: datetime | object | None
    status: str
    trigger_type: str
    config_hash: str | None
    enabled_source_families: tuple[str, ...]
    initial_year: int | None
    cycle_count: int | None
    total_parsed_rows: int
    total_inserted_count: int
    total_skipped_duplicate_count: int
    failure_count: int
    metadata: Mapping[str, object]


@dataclass(frozen=True)
class ParserIngestionSourceResultReadModel:
    """Read model for one source result in a parser ingestion run."""

    run_id: str
    source_family: str
    target_year: int
    latest_year: int | None
    status: str
    download_status: str | None
    parse_status: str | None
    validation_status: str | None
    insert_status: str | None
    parsed_rows: int
    master_inserted: int
    master_skipped: int
    detail_inserted: int
    detail_skipped: int
    issue_count: int
    metadata: Mapping[str, object]


@dataclass(frozen=True)
class ParserIngestionIssueReadModel:
    """Read model for one operational issue in a parser ingestion run."""

    run_id: str
    source_family: str | None
    target_year: int | None
    stage: str
    code: str
    severity: str
    field_name: str | None
    message: str
    metadata: Mapping[str, object]
    created_at: datetime | object


@dataclass(frozen=True)
class ParserIngestionRunDetailReadModel:
    """Read model containing a run and its source results and issues."""

    run: ParserIngestionRunReadModel
    source_results: tuple[ParserIngestionSourceResultReadModel, ...]
    issues: tuple[ParserIngestionIssueReadModel, ...]


@runtime_checkable
class ParserIngestionRunHistoryReader(Protocol):
    """Read repository boundary for parser ingestion run history."""

    @property
    def provider_name(self) -> str:
        """Return the reader provider name."""

    def get_latest_ingestion_run(self) -> ParserIngestionRunReadModel | None:
        """Return the most recent parser ingestion run, if present."""

    def get_ingestion_run_by_id(
        self,
        run_id: str,
    ) -> ParserIngestionRunDetailReadModel | None:
        """Return one parser ingestion run with source results and issues."""

    def list_recent_ingestion_runs(
        self,
        limit: int = _DEFAULT_RECENT_RUN_LIMIT,
    ) -> tuple[ParserIngestionRunReadModel, ...]:
        """Return recent parser ingestion runs."""

    def list_ingestion_run_source_results(
        self,
        run_id: str,
    ) -> tuple[ParserIngestionSourceResultReadModel, ...]:
        """Return source results for one parser ingestion run."""

    def list_ingestion_run_issues(
        self,
        run_id: str,
    ) -> tuple[ParserIngestionIssueReadModel, ...]:
        """Return issues for one parser ingestion run."""


class PostgreSQLIngestionRunHistoryReader:
    """Query parser ingestion run-history records from PostgreSQL."""

    def __init__(self, connection: object) -> None:
        if connection is None:
            raise ValueError("connection must be provided.")
        self._connection = connection

    @property
    def provider_name(self) -> str:
        """Return the reader provider name."""

        return "postgresql"

    def get_latest_ingestion_run(self) -> ParserIngestionRunReadModel | None:
        """Return the latest parser ingestion run, if one exists."""

        cursor = _execute(self._connection, _latest_run_sql(), (1,))
        row = _fetchone(cursor)
        if row is None:
            return None
        return _run_read_model(row)

    def get_ingestion_run_by_id(
        self,
        run_id: str,
    ) -> ParserIngestionRunDetailReadModel | None:
        """Return a parser ingestion run with source results and issues."""

        validated_run_id = _validated_run_id(run_id)
        cursor = _execute(self._connection, _run_by_id_sql(), (validated_run_id,))
        row = _fetchone(cursor)
        if row is None:
            return None
        return ParserIngestionRunDetailReadModel(
            run=_run_read_model(row),
            source_results=self.list_ingestion_run_source_results(validated_run_id),
            issues=self.list_ingestion_run_issues(validated_run_id),
        )

    def list_recent_ingestion_runs(
        self,
        limit: int = _DEFAULT_RECENT_RUN_LIMIT,
    ) -> tuple[ParserIngestionRunReadModel, ...]:
        """Return recent parser ingestion runs in deterministic order."""

        validated_limit = _validated_limit(limit)
        cursor = _execute(self._connection, _recent_runs_sql(), (validated_limit,))
        return tuple(_run_read_model(row) for row in _fetchall(cursor))

    def list_ingestion_run_source_results(
        self,
        run_id: str,
    ) -> tuple[ParserIngestionSourceResultReadModel, ...]:
        """Return source results for one parser ingestion run."""

        validated_run_id = _validated_run_id(run_id)
        cursor = _execute(self._connection, _source_results_sql(), (validated_run_id,))
        return tuple(_source_result_read_model(row) for row in _fetchall(cursor))

    def list_ingestion_run_issues(
        self,
        run_id: str,
    ) -> tuple[ParserIngestionIssueReadModel, ...]:
        """Return issues for one parser ingestion run."""

        validated_run_id = _validated_run_id(run_id)
        cursor = _execute(self._connection, _issues_sql(), (validated_run_id,))
        return tuple(_issue_read_model(row) for row in _fetchall(cursor))


def _latest_run_sql() -> str:
    return f"""
        SELECT {_run_select_list()}
        FROM parser_ingestion_runs
        ORDER BY started_at DESC, run_id DESC
        LIMIT %s
        """


def _recent_runs_sql() -> str:
    return _latest_run_sql()


def _run_by_id_sql() -> str:
    return f"""
        SELECT {_run_select_list()}
        FROM parser_ingestion_runs
        WHERE run_id = %s
        """


def _source_results_sql() -> str:
    return f"""
        SELECT {_source_result_select_list()}
        FROM parser_ingestion_source_results
        WHERE run_id = %s
        ORDER BY source_family ASC, target_year ASC
        """


def _issues_sql() -> str:
    return f"""
        SELECT {_issue_select_list()}
        FROM parser_ingestion_issues
        WHERE run_id = %s
        ORDER BY created_at ASC, source_family ASC NULLS LAST, code ASC
        """


def _run_select_list() -> str:
    return ", ".join(_RUN_COLUMNS)


def _source_result_select_list() -> str:
    return ", ".join(_SOURCE_RESULT_COLUMNS)


def _issue_select_list() -> str:
    return ", ".join(_ISSUE_COLUMNS)


def _run_read_model(row: object) -> ParserIngestionRunReadModel:
    return ParserIngestionRunReadModel(
        run_id=_string_value(row, "run_id", _RUN_COLUMNS),
        started_at=_row_value(row, "started_at", _RUN_COLUMNS),
        finished_at=_row_value(row, "finished_at", _RUN_COLUMNS),
        status=_string_value(row, "status", _RUN_COLUMNS),
        trigger_type=_string_value(row, "trigger_type", _RUN_COLUMNS),
        config_hash=_optional_string_value(row, "config_hash", _RUN_COLUMNS),
        enabled_source_families=_source_families_value(
            _row_value(row, "enabled_source_families", _RUN_COLUMNS)
        ),
        initial_year=_optional_int_value(row, "initial_year", _RUN_COLUMNS),
        cycle_count=_optional_int_value(row, "cycle_count", _RUN_COLUMNS),
        total_parsed_rows=_int_value(row, "total_parsed_rows", _RUN_COLUMNS),
        total_inserted_count=_int_value(row, "total_inserted_count", _RUN_COLUMNS),
        total_skipped_duplicate_count=_int_value(
            row,
            "total_skipped_duplicate_count",
            _RUN_COLUMNS,
        ),
        failure_count=_int_value(row, "failure_count", _RUN_COLUMNS),
        metadata=_metadata_value(_row_value(row, "metadata", _RUN_COLUMNS)),
    )


def _source_result_read_model(row: object) -> ParserIngestionSourceResultReadModel:
    return ParserIngestionSourceResultReadModel(
        run_id=_string_value(row, "run_id", _SOURCE_RESULT_COLUMNS),
        source_family=_string_value(row, "source_family", _SOURCE_RESULT_COLUMNS),
        target_year=_int_value(row, "target_year", _SOURCE_RESULT_COLUMNS),
        latest_year=_optional_int_value(row, "latest_year", _SOURCE_RESULT_COLUMNS),
        status=_string_value(row, "status", _SOURCE_RESULT_COLUMNS),
        download_status=_optional_string_value(row, "download_status", _SOURCE_RESULT_COLUMNS),
        parse_status=_optional_string_value(row, "parse_status", _SOURCE_RESULT_COLUMNS),
        validation_status=_optional_string_value(row, "validation_status", _SOURCE_RESULT_COLUMNS),
        insert_status=_optional_string_value(row, "insert_status", _SOURCE_RESULT_COLUMNS),
        parsed_rows=_int_value(row, "parsed_rows", _SOURCE_RESULT_COLUMNS),
        master_inserted=_int_value(row, "master_inserted", _SOURCE_RESULT_COLUMNS),
        master_skipped=_int_value(row, "master_skipped", _SOURCE_RESULT_COLUMNS),
        detail_inserted=_int_value(row, "detail_inserted", _SOURCE_RESULT_COLUMNS),
        detail_skipped=_int_value(row, "detail_skipped", _SOURCE_RESULT_COLUMNS),
        issue_count=_int_value(row, "issue_count", _SOURCE_RESULT_COLUMNS),
        metadata=_metadata_value(_row_value(row, "metadata", _SOURCE_RESULT_COLUMNS)),
    )


def _issue_read_model(row: object) -> ParserIngestionIssueReadModel:
    return ParserIngestionIssueReadModel(
        run_id=_string_value(row, "run_id", _ISSUE_COLUMNS),
        source_family=_optional_string_value(row, "source_family", _ISSUE_COLUMNS),
        target_year=_optional_int_value(row, "target_year", _ISSUE_COLUMNS),
        stage=_string_value(row, "stage", _ISSUE_COLUMNS),
        code=_string_value(row, "code", _ISSUE_COLUMNS),
        severity=_string_value(row, "severity", _ISSUE_COLUMNS),
        field_name=_optional_string_value(row, "field_name", _ISSUE_COLUMNS),
        message=_string_value(row, "message", _ISSUE_COLUMNS),
        metadata=_metadata_value(_row_value(row, "metadata", _ISSUE_COLUMNS)),
        created_at=_row_value(row, "created_at", _ISSUE_COLUMNS),
    )


def _execute(connection: object, statement: str, parameters: tuple[object, ...]) -> object:
    return getattr(connection, "execute")(statement, parameters)


def _fetchone(cursor: object) -> object | None:
    return getattr(cursor, "fetchone")()


def _fetchall(cursor: object) -> tuple[object, ...]:
    rows = getattr(cursor, "fetchall")()
    return tuple(rows or ())


def _row_value(row: object, column_name: str, column_names: Sequence[str]) -> object:
    if isinstance(row, Mapping):
        return row[column_name]
    if hasattr(row, column_name):
        return getattr(row, column_name)
    return row[column_names.index(column_name)]  # type: ignore[index]


def _string_value(row: object, column_name: str, column_names: Sequence[str]) -> str:
    return str(_row_value(row, column_name, column_names))


def _optional_string_value(
    row: object,
    column_name: str,
    column_names: Sequence[str],
) -> str | None:
    value = _row_value(row, column_name, column_names)
    if value is None:
        return None
    return str(value)


def _int_value(row: object, column_name: str, column_names: Sequence[str]) -> int:
    return int(_row_value(row, column_name, column_names))


def _optional_int_value(
    row: object,
    column_name: str,
    column_names: Sequence[str],
) -> int | None:
    value = _row_value(row, column_name, column_names)
    if value is None:
        return None
    return int(value)


def _metadata_value(value: object) -> Mapping[str, object]:
    decoded = _json_decoded_value(value)
    if isinstance(decoded, Mapping):
        return decoded
    return {}


def _source_families_value(value: object) -> tuple[str, ...]:
    decoded = _json_decoded_value(value)
    if isinstance(decoded, str):
        return (decoded,)
    if isinstance(decoded, Sequence):
        return tuple(str(item) for item in decoded)
    return ()


def _json_decoded_value(value: object) -> object:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _validated_limit(limit: int) -> int:
    if not isinstance(limit, int):
        raise ValueError("limit must be an integer.")
    if limit < _MIN_RECENT_RUN_LIMIT or limit > _MAX_RECENT_RUN_LIMIT:
        raise ValueError("limit must be between 1 and 100.")
    return limit


def _validated_run_id(run_id: str) -> str:
    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("run_id must be a non-empty string.")
    return run_id


__all__ = (
    "ParserIngestionIssueReadModel",
    "ParserIngestionRunDetailReadModel",
    "ParserIngestionRunHistoryReader",
    "ParserIngestionRunReadModel",
    "ParserIngestionSourceResultReadModel",
    "PostgreSQLIngestionRunHistoryReader",
    "_issues_sql",
    "_latest_run_sql",
    "_recent_runs_sql",
    "_run_by_id_sql",
    "_source_results_sql",
)
