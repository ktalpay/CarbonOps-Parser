from __future__ import annotations

from carbonfactor_parser.persistence.postgresql_execution import (
    commit,
    execute,
    fetchone,
    rollback,
)


class _RecordingConnection:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.committed = False
        self.rolled_back = False

    def execute(self, *args: object) -> object:
        self.calls.append(args)
        return "cursor"

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


class _ConnectionWithoutTransactionMethods:
    pass


class _RecordingCursor:
    def __init__(self) -> None:
        self.called = False

    def fetchone(self) -> tuple[str]:
        self.called = True
        return ("row",)


def test_execute_calls_connection_execute_without_parameters_when_none() -> None:
    connection = _RecordingConnection()

    result = execute(connection, "SELECT 1")

    assert result == "cursor"
    assert connection.calls == [("SELECT 1",)]


def test_execute_calls_connection_execute_with_parameters_when_provided() -> None:
    connection = _RecordingConnection()
    parameters = ("value",)

    result = execute(connection, "SELECT %s", parameters)

    assert result == "cursor"
    assert connection.calls == [("SELECT %s", parameters)]


def test_fetchone_calls_cursor_fetchone() -> None:
    cursor = _RecordingCursor()

    result = fetchone(cursor)

    assert result == ("row",)
    assert cursor.called is True


def test_commit_noops_when_method_missing() -> None:
    commit(_ConnectionWithoutTransactionMethods())


def test_commit_calls_connection_commit_when_present() -> None:
    connection = _RecordingConnection()

    commit(connection)

    assert connection.committed is True


def test_rollback_noops_when_method_missing() -> None:
    rollback(_ConnectionWithoutTransactionMethods())


def test_rollback_calls_connection_rollback_when_present() -> None:
    connection = _RecordingConnection()

    rollback(connection)

    assert connection.rolled_back is True
