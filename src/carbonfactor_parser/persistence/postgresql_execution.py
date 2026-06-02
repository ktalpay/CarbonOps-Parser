"""PostgreSQL connection execution helpers."""

from __future__ import annotations


def execute(
    connection: object,
    statement: str,
    parameters: object | None = None,
) -> object:
    """Execute a statement against a connection-like object."""

    execute_method = getattr(connection, "execute")
    if parameters is None:
        return execute_method(statement)
    return execute_method(statement, parameters)


def fetchone(cursor: object) -> object | None:
    """Fetch one row from a cursor-like object."""

    fetchone_method = getattr(cursor, "fetchone")
    return fetchone_method()


def commit(connection: object) -> None:
    """Commit a connection-like object when it supports commit."""

    commit_method = getattr(connection, "commit", None)
    if commit_method is not None:
        commit_method()


def rollback(connection: object) -> None:
    """Rollback a connection-like object when it supports rollback."""

    rollback_method = getattr(connection, "rollback", None)
    if rollback_method is not None:
        rollback_method()


__all__ = ("commit", "execute", "fetchone", "rollback")
