from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

import pytest

from carbonfactor_parser.persistence.ingestion_run_history_reader import (
    ParserIngestionRunHistoryReader,
    ParserIngestionRunReadModel,
    PostgreSQLIngestionRunHistoryReader,
)


class _FakeCursor:
    def __init__(self, rows: tuple[object, ...] = ()) -> None:
        self._rows = rows

    def fetchone(self) -> object | None:
        if not self._rows:
            return None
        return self._rows[0]

    def fetchall(self) -> tuple[object, ...]:
        return self._rows


class _FakeConnection:
    def __init__(self, cursors: tuple[_FakeCursor, ...]) -> None:
        self._cursors = list(cursors)
        self.statements: list[tuple[str, tuple[object, ...]]] = []

    def execute(self, statement: str, parameters: tuple[object, ...]) -> _FakeCursor:
        self.statements.append((statement, parameters))
        if not self._cursors:
            raise AssertionError("unexpected execute call")
        return self._cursors.pop(0)


def _run_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "run_id": "run-001",
        "started_at": datetime(2026, 6, 2, 12, 0, tzinfo=UTC),
        "finished_at": datetime(2026, 6, 2, 12, 5, tzinfo=UTC),
        "status": "completed",
        "trigger_type": "operator",
        "config_hash": "config-123",
        "enabled_source_families": ("ghg_protocol", "defra_desnz"),
        "initial_year": 2024,
        "cycle_count": 1,
        "total_parsed_rows": 10,
        "total_inserted_count": 8,
        "total_skipped_duplicate_count": 2,
        "failure_count": 0,
        "metadata": {"operator_note": "safe"},
    }
    row.update(overrides)
    return row


def _source_result_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "run_id": "run-001",
        "source_family": "ghg_protocol",
        "target_year": 2024,
        "latest_year": 2025,
        "status": "completed",
        "download_status": "completed",
        "parse_status": "completed",
        "validation_status": "completed",
        "insert_status": "completed",
        "parsed_rows": 10,
        "master_inserted": 2,
        "master_skipped": 1,
        "detail_inserted": 6,
        "detail_skipped": 1,
        "issue_count": 1,
        "metadata": {"source": "fixture"},
    }
    row.update(overrides)
    return row


def _issue_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "run_id": "run-001",
        "source_family": "ghg_protocol",
        "target_year": 2024,
        "stage": "validation",
        "code": "ROW_INVALID",
        "severity": "warning",
        "field_name": "emission_factor",
        "message": "row failed validation",
        "metadata": {"row": 3},
        "created_at": datetime(2026, 6, 2, 12, 3, tzinfo=UTC),
    }
    row.update(overrides)
    return row


def test_get_latest_ingestion_run_returns_none_when_no_row() -> None:
    connection = _FakeConnection((_FakeCursor(),))
    reader = PostgreSQLIngestionRunHistoryReader(connection)

    assert isinstance(reader, ParserIngestionRunHistoryReader)
    assert reader.get_latest_ingestion_run() is None
    assert connection.statements[0][1] == (1,)


def test_get_latest_ingestion_run_maps_row_into_read_model() -> None:
    connection = _FakeConnection((_FakeCursor((_run_row(),)),))

    result = PostgreSQLIngestionRunHistoryReader(connection).get_latest_ingestion_run()

    assert isinstance(result, ParserIngestionRunReadModel)
    assert result.run_id == "run-001"
    assert result.status == "completed"
    assert result.enabled_source_families == ("ghg_protocol", "defra_desnz")
    assert result.total_inserted_count == 8
    assert result.metadata == {"operator_note": "safe"}
    assert "ORDER BY started_at DESC, run_id DESC" in connection.statements[0][0]


@pytest.mark.parametrize("limit", [0, 101])
def test_list_recent_ingestion_runs_rejects_invalid_limit(limit: int) -> None:
    reader = PostgreSQLIngestionRunHistoryReader(_FakeConnection((_FakeCursor(),)))

    with pytest.raises(ValueError, match="limit must be between 1 and 100"):
        reader.list_recent_ingestion_runs(limit)


def test_get_ingestion_run_by_id_rejects_empty_run_id() -> None:
    reader = PostgreSQLIngestionRunHistoryReader(_FakeConnection((_FakeCursor(),)))

    with pytest.raises(ValueError, match="run_id must be a non-empty string"):
        reader.get_ingestion_run_by_id("  ")


def test_get_ingestion_run_by_id_returns_detail_with_run_sources_and_issues() -> None:
    connection = _FakeConnection(
        (
            _FakeCursor((_run_row(),)),
            _FakeCursor((_source_result_row(),)),
            _FakeCursor((_issue_row(),)),
        )
    )

    result = PostgreSQLIngestionRunHistoryReader(connection).get_ingestion_run_by_id("run-001")

    assert result is not None
    assert result.run.run_id == "run-001"
    assert len(result.source_results) == 1
    assert result.source_results[0].source_family == "ghg_protocol"
    assert result.source_results[0].target_year == 2024
    assert len(result.issues) == 1
    assert result.issues[0].code == "ROW_INVALID"
    assert result.issues[0].source_family == "ghg_protocol"
    assert [parameters for _, parameters in connection.statements] == [
        ("run-001",),
        ("run-001",),
        ("run-001",),
    ]


def test_source_results_ordered_query_uses_run_id_parameter() -> None:
    connection = _FakeConnection((_FakeCursor((_source_result_row(),)),))

    PostgreSQLIngestionRunHistoryReader(connection).list_ingestion_run_source_results("run-001")

    statement, parameters = connection.statements[0]
    assert parameters == ("run-001",)
    assert "WHERE run_id = %s" in statement
    assert "ORDER BY source_family ASC, target_year ASC" in statement


def test_issues_ordered_query_uses_run_id_parameter() -> None:
    connection = _FakeConnection((_FakeCursor((_issue_row(),)),))

    PostgreSQLIngestionRunHistoryReader(connection).list_ingestion_run_issues("run-001")

    statement, parameters = connection.statements[0]
    assert parameters == ("run-001",)
    assert "WHERE run_id = %s" in statement
    assert "ORDER BY created_at ASC, source_family ASC NULLS LAST, code ASC" in statement


def test_metadata_json_string_is_parsed_into_mapping() -> None:
    connection = _FakeConnection((_FakeCursor((_run_row(metadata='{"safe": true}'),)),))

    result = PostgreSQLIngestionRunHistoryReader(connection).get_latest_ingestion_run()

    assert result is not None
    assert isinstance(result.metadata, Mapping)
    assert result.metadata == {"safe": True}


@pytest.mark.parametrize(
    ("stored_value", "expected"),
    [
        ('["ghg_protocol", "ipcc_efdb"]', ("ghg_protocol", "ipcc_efdb")),
        (["defra_desnz"], ("defra_desnz",)),
    ],
)
def test_enabled_source_families_json_string_or_list_becomes_tuple(
    stored_value: object,
    expected: tuple[str, ...],
) -> None:
    connection = _FakeConnection(
        (_FakeCursor((_run_row(enabled_source_families=stored_value),)),)
    )

    result = PostgreSQLIngestionRunHistoryReader(connection).get_latest_ingestion_run()

    assert result is not None
    assert result.enabled_source_families == expected


def test_query_sql_does_not_interpolate_raw_run_id_into_sql_string() -> None:
    raw_run_id = "run-001'; DROP TABLE parser_ingestion_runs; --"
    connection = _FakeConnection((_FakeCursor((_source_result_row(run_id=raw_run_id),)),))

    PostgreSQLIngestionRunHistoryReader(connection).list_ingestion_run_source_results(raw_run_id)

    statement, parameters = connection.statements[0]
    assert raw_run_id not in statement
    assert parameters == (raw_run_id,)
