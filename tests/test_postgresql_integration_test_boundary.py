import builtins
import inspect
import os
import socket
import sqlite3
import urllib.request

import carbonfactor_parser.persistence.integration_test_boundary as boundary_module
from carbonfactor_parser.persistence import (
    POSTGRESQL_INTEGRATION_TEST_MARKER,
    POSTGRESQL_INTEGRATION_TEST_SKIP_REASON,
    PostgreSQLIntegrationTestBoundary,
    create_postgresql_integration_test_boundary,
    should_skip_postgresql_integration_tests,
)


def test_integration_test_boundary_defaults_to_disabled_and_skipped() -> None:
    boundary = create_postgresql_integration_test_boundary()

    assert isinstance(boundary, PostgreSQLIntegrationTestBoundary)
    assert boundary.enabled is False
    assert boundary.marker_name == "postgresql_integration"
    assert boundary.enable_source is None
    assert boundary.skip_reason == POSTGRESQL_INTEGRATION_TEST_SKIP_REASON
    assert should_skip_postgresql_integration_tests(boundary)


def test_integration_test_marker_is_deterministic_public_constant() -> None:
    assert POSTGRESQL_INTEGRATION_TEST_MARKER == "postgresql_integration"
    assert "disabled by default" in POSTGRESQL_INTEGRATION_TEST_SKIP_REASON


def test_explicit_opt_in_boundary_can_be_represented_without_db_behavior() -> None:
    boundary = create_postgresql_integration_test_boundary(
        explicitly_enabled=True,
        enable_source="explicit-test-marker",
    )

    assert boundary.enabled is True
    assert boundary.marker_name == POSTGRESQL_INTEGRATION_TEST_MARKER
    assert boundary.enable_source == "explicit-test-marker"
    assert boundary.skip_reason is None
    assert not should_skip_postgresql_integration_tests(boundary)


def test_skip_helper_defaults_to_skip_without_boundary() -> None:
    assert should_skip_postgresql_integration_tests()


def test_boundary_creation_has_no_env_config_db_file_or_network_side_effects(
    monkeypatch,
) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("integration boundary must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(os, "getenv", fail_side_effect)
    monkeypatch.setattr(socket, "create_connection", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    boundary = create_postgresql_integration_test_boundary()

    assert should_skip_postgresql_integration_tests(boundary)


def test_boundary_module_has_no_db_dependency_env_config_or_sql_behavior() -> None:
    module_source = inspect.getsource(boundary_module)
    lower_source = module_source.lower()

    assert "os.environ" not in module_source
    assert "getenv" not in module_source
    assert "open(" not in module_source
    assert "psycopg" not in lower_source
    assert "asyncpg" not in lower_source
    assert "sqlalchemy" not in lower_source
    assert "connect(" not in module_source
    assert ".execute" not in module_source
    assert "CREATE TABLE" not in module_source
    assert "INSERT INTO" not in module_source
