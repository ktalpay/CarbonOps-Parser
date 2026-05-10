import builtins
import inspect
import os
import socket
import sqlite3
import urllib.request
from dataclasses import replace

import carbonfactor_parser.persistence.postgresql_schema_isolation_strategy as strategy_module
from carbonfactor_parser.persistence import (
    POSTGRESQL_ISOLATED_SCHEMA_PREFIX,
    POSTGRESQL_RESERVED_SCHEMA_NAMES,
    PersistenceInput,
    PostgreSQLPersistenceRepository,
    PostgreSQLSchemaIsolationCleanupMode,
    PostgreSQLSchemaIsolationCleanupScope,
    PostgreSQLSchemaIsolationStrategy,
    PostgreSQLSchemaIsolationStrategyIssue,
    PostgreSQLSchemaIsolationStrategyStatus,
    build_default_postgresql_schema_isolation_strategy,
    describe_postgresql_schema_isolation_strategy,
    validate_postgresql_schema_isolation_strategy,
)
from carbonfactor_parser.persistence.repository import PersistenceResultStatus


def test_schema_isolation_strategy_imports_from_public_api() -> None:
    strategy = build_default_postgresql_schema_isolation_strategy()
    description = describe_postgresql_schema_isolation_strategy()

    assert POSTGRESQL_ISOLATED_SCHEMA_PREFIX == "carbonops_test_"
    assert "public" in POSTGRESQL_RESERVED_SCHEMA_NAMES
    assert strategy.schema_name == "carbonops_test_isolated"
    assert strategy.cleanup_mode is PostgreSQLSchemaIsolationCleanupMode.FUTURE_DROP_SCHEMA
    assert (
        strategy.cleanup_scope
        is PostgreSQLSchemaIsolationCleanupScope.ISOLATED_SCHEMA_ONLY
    )
    assert description.strategy == strategy
    assert description.runtime_cleanup_enabled is False
    assert description.opens_connection is False
    assert description.runs_sql is False


def test_default_schema_isolation_strategy_is_no_execution_metadata() -> None:
    strategy = build_default_postgresql_schema_isolation_strategy(
        schema_name="carbonops_test_run_001",
    )

    assert strategy == PostgreSQLSchemaIsolationStrategy(
        schema_name="carbonops_test_run_001",
        required_schema_prefix="carbonops_test_",
        cleanup_mode=PostgreSQLSchemaIsolationCleanupMode.FUTURE_DROP_SCHEMA,
        cleanup_scope=PostgreSQLSchemaIsolationCleanupScope.ISOLATED_SCHEMA_ONLY,
        require_isolated_schema=True,
        cleanup_only_isolated_schema=True,
        runtime_cleanup_enabled=False,
        opens_connection=False,
        runs_sql=False,
        creates_schema=False,
        drops_schema=False,
        truncates_tables=False,
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
        notes=(
            "Schema isolation strategy metadata only.",
            "Future cleanup must target only isolated test schemas.",
            "No schema creation, table truncation, or schema deletion is executed.",
        ),
    )
    assert validate_postgresql_schema_isolation_strategy(strategy).is_valid is True


def test_schema_isolation_strategy_fails_closed_for_reserved_or_shared_schema() -> None:
    public_validation = validate_postgresql_schema_isolation_strategy(
        build_default_postgresql_schema_isolation_strategy(schema_name="public"),
    )
    unsafe_validation = validate_postgresql_schema_isolation_strategy(
        build_default_postgresql_schema_isolation_strategy(
            schema_name="carbonops_prod",
        ),
    )
    system_validation = validate_postgresql_schema_isolation_strategy(
        build_default_postgresql_schema_isolation_strategy(schema_name="pg_temp"),
    )

    assert public_validation.status is PostgreSQLSchemaIsolationStrategyStatus.BLOCKED
    assert _issue_codes(public_validation.issues) == (
        "POSTGRESQL_SCHEMA_ISOLATION_RESERVED_SCHEMA",
        "POSTGRESQL_SCHEMA_ISOLATION_PREFIX_REQUIRED",
    )
    assert unsafe_validation.status is PostgreSQLSchemaIsolationStrategyStatus.BLOCKED
    assert _issue_codes(unsafe_validation.issues) == (
        "POSTGRESQL_SCHEMA_ISOLATION_PREFIX_REQUIRED",
    )
    assert system_validation.status is PostgreSQLSchemaIsolationStrategyStatus.BLOCKED
    assert _issue_codes(system_validation.issues) == (
        "POSTGRESQL_SCHEMA_ISOLATION_SYSTEM_SCHEMA",
        "POSTGRESQL_SCHEMA_ISOLATION_PREFIX_REQUIRED",
    )


def test_schema_isolation_strategy_fails_closed_for_unsafe_identifier() -> None:
    validation = validate_postgresql_schema_isolation_strategy(
        build_default_postgresql_schema_isolation_strategy(
            schema_name='carbonops_test_unsafe";drop',
        ),
    )
    whitespace_validation = validate_postgresql_schema_isolation_strategy(
        build_default_postgresql_schema_isolation_strategy(
            schema_name=" carbonops_test_unsafe ",
        ),
    )

    assert validation.status is PostgreSQLSchemaIsolationStrategyStatus.BLOCKED
    assert _issue_codes(validation.issues) == (
        "POSTGRESQL_SCHEMA_ISOLATION_SCHEMA_NAME_UNSAFE",
    )
    assert whitespace_validation.status is (
        PostgreSQLSchemaIsolationStrategyStatus.BLOCKED
    )
    assert _issue_codes(whitespace_validation.issues) == (
        "POSTGRESQL_SCHEMA_ISOLATION_SCHEMA_NAME_UNSAFE",
    )


def test_schema_isolation_strategy_fails_closed_for_runtime_cleanup_flags() -> None:
    strategy = replace(
        build_default_postgresql_schema_isolation_strategy(),
        cleanup_mode="drop_now",  # type: ignore[arg-type]
        cleanup_scope="all_schemas",  # type: ignore[arg-type]
        require_isolated_schema=False,
        cleanup_only_isolated_schema=False,
        runtime_cleanup_enabled=True,
        opens_connection=True,
        runs_sql=True,
        creates_schema=True,
        drops_schema=True,
        truncates_tables=True,
        loads_environment=True,
        loads_config_files=True,
        loads_credentials=True,
        notes=(),
    )

    validation = validate_postgresql_schema_isolation_strategy(strategy)

    assert validation.status is PostgreSQLSchemaIsolationStrategyStatus.BLOCKED
    assert _issue_codes(validation.issues) == (
        "POSTGRESQL_SCHEMA_ISOLATION_CLEANUP_MODE_UNSAFE",
        "POSTGRESQL_SCHEMA_ISOLATION_CLEANUP_SCOPE_UNSAFE",
        "POSTGRESQL_SCHEMA_ISOLATION_REQUIRED",
        "POSTGRESQL_SCHEMA_ISOLATION_CLEANUP_SCOPE_REQUIRED",
        "POSTGRESQL_SCHEMA_ISOLATION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_SCHEMA_ISOLATION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_SCHEMA_ISOLATION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_SCHEMA_ISOLATION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_SCHEMA_ISOLATION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_SCHEMA_ISOLATION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_SCHEMA_ISOLATION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_SCHEMA_ISOLATION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_SCHEMA_ISOLATION_RUNTIME_FLAG_NOT_ALLOWED",
        "POSTGRESQL_SCHEMA_ISOLATION_MISSING_NOTES",
    )


def test_schema_isolation_helpers_have_no_external_side_effects(monkeypatch) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("schema isolation strategy must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(os, "getenv", fail_side_effect)
    monkeypatch.setattr(socket, "create_connection", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    strategy = build_default_postgresql_schema_isolation_strategy()
    description = describe_postgresql_schema_isolation_strategy()
    validation = validate_postgresql_schema_isolation_strategy(strategy)

    assert description.loads_environment is False
    assert description.loads_config_files is False
    assert description.loads_credentials is False
    assert validation.is_valid is True


def test_repository_persist_remains_unsupported_no_execution() -> None:
    result = PostgreSQLPersistenceRepository().persist(
        PersistenceInput(
            source_family="defra_desnz",
            source_id="defra_desnz",
            records=(),
        ),
    )

    assert result.status == PersistenceResultStatus.UNSUPPORTED
    assert result.persisted_record_count == 0
    assert result.repository_metadata["database_connection"] is False
    assert result.repository_metadata["runtime_write"] is False


def test_schema_isolation_module_has_no_runtime_db_behavior() -> None:
    module_source = inspect.getsource(strategy_module)
    lower_source = module_source.lower()

    assert "psycopg" not in lower_source
    assert "asyncpg" not in lower_source
    assert "sqlalchemy" not in lower_source
    assert "create_engine" not in module_source
    assert "connect(" not in module_source
    assert "cursor(" not in module_source
    assert "execute(" not in module_source
    assert "commit(" not in module_source
    assert "rollback(" not in module_source


def _issue_codes(
    issues: tuple[PostgreSQLSchemaIsolationStrategyIssue, ...],
) -> tuple[str, ...]:
    return tuple(issue.code for issue in issues)
