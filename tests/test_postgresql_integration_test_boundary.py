import builtins
import inspect
import os
import socket
import sqlite3
import urllib.request
from pathlib import Path

import carbonfactor_parser.persistence.integration_test_boundary as boundary_module
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PersistenceResultStatus,
    PostgreSQLPersistenceRepository,
    POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR,
    POSTGRESQL_INTEGRATION_TEST_MARKER,
    POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR,
    POSTGRESQL_INTEGRATION_TEST_OPT_IN_FALSE_VALUES,
    POSTGRESQL_INTEGRATION_TEST_OPT_IN_TRUE_VALUES,
    POSTGRESQL_INTEGRATION_TEST_SKIP_REASON,
    PostgreSQLIntegrationTestConfigIssue,
    PostgreSQLIntegrationTestOptInConfig,
    PostgreSQLIntegrationTestBoundary,
    create_postgresql_integration_test_boundary,
    evaluate_postgresql_integration_test_opt_in_config,
    should_skip_postgresql_integration_tests,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_integration_test_boundary_defaults_to_disabled_and_skipped() -> None:
    boundary = create_postgresql_integration_test_boundary()

    assert isinstance(boundary, PostgreSQLIntegrationTestBoundary)
    assert boundary.enabled is False
    assert boundary.marker_name == "postgresql_integration"
    assert boundary.enable_source is None
    assert boundary.skip_reason == POSTGRESQL_INTEGRATION_TEST_SKIP_REASON
    assert boundary.opt_in_control_name == POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR
    assert boundary.test_dsn_input_name == POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR
    assert should_skip_postgresql_integration_tests(boundary)


def test_integration_test_marker_and_opt_in_controls_are_deterministic() -> None:
    assert POSTGRESQL_INTEGRATION_TEST_MARKER == "postgresql_integration"
    assert (
        POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR
        == "CARBONOPS_RUN_POSTGRESQL_INTEGRATION"
    )
    assert POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR == "CARBONOPS_POSTGRESQL_TEST_DSN"
    assert "disabled by default" in POSTGRESQL_INTEGRATION_TEST_SKIP_REASON
    assert POSTGRESQL_INTEGRATION_TEST_OPT_IN_TRUE_VALUES == (
        "1",
        "true",
        "yes",
        "on",
    )
    assert POSTGRESQL_INTEGRATION_TEST_OPT_IN_FALSE_VALUES == (
        "",
        "0",
        "false",
        "no",
        "off",
    )


def test_explicit_opt_in_boundary_can_be_represented_without_db_behavior() -> None:
    boundary = create_postgresql_integration_test_boundary(
        explicitly_enabled=True,
        enable_source="explicit-test-marker",
    )

    assert boundary.enabled is True
    assert boundary.marker_name == POSTGRESQL_INTEGRATION_TEST_MARKER
    assert boundary.opt_in_control_name == POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR
    assert boundary.test_dsn_input_name == POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR
    assert boundary.enable_source == "explicit-test-marker"
    assert boundary.skip_reason is None
    assert not should_skip_postgresql_integration_tests(boundary)


def test_skip_helper_defaults_to_skip_without_boundary() -> None:
    assert should_skip_postgresql_integration_tests()


def test_opt_in_config_defaults_to_disabled_without_external_reads() -> None:
    config = evaluate_postgresql_integration_test_opt_in_config()

    assert isinstance(config, PostgreSQLIntegrationTestOptInConfig)
    assert config.enabled is False
    assert config.opt_in_requested is False
    assert config.test_dsn_configured is False
    assert config.marker_name == POSTGRESQL_INTEGRATION_TEST_MARKER
    assert config.opt_in_control_name == POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR
    assert config.test_dsn_input_name == POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR
    assert config.enable_source is None
    assert config.skip_reason == POSTGRESQL_INTEGRATION_TEST_SKIP_REASON
    assert config.issues == ()
    assert config.loads_environment is False
    assert config.loads_config_files is False
    assert config.loads_credentials is False
    assert config.stores_test_dsn_value is False
    assert config.opens_connection is False
    assert config.runs_sql is False


def test_opt_in_config_requires_dsn_when_enabled() -> None:
    config = evaluate_postgresql_integration_test_opt_in_config(
        {POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR: "true"},
    )

    assert config.enabled is False
    assert config.opt_in_requested is True
    assert config.test_dsn_configured is False
    assert config.issues == (
        PostgreSQLIntegrationTestConfigIssue(
            code="POSTGRESQL_INTEGRATION_TEST_DSN_MISSING",
            message=(
                "PostgreSQL integration test opt-in requires a caller-"
                "provided test DSN input name, but the DSN value is not "
                "stored by this boundary."
            ),
            field_name=POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR,
        ),
    )
    assert config.skip_reason == config.issues[0].message


def test_opt_in_config_enables_only_with_truthy_opt_in_and_dsn_presence() -> None:
    secret_dsn = "postgresql://carbonops:secret@example.invalid:5432/test"
    config = evaluate_postgresql_integration_test_opt_in_config(
        {
            POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR: "YES",
            POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR: secret_dsn,
        },
    )

    assert config.enabled is True
    assert config.opt_in_requested is True
    assert config.test_dsn_configured is True
    assert config.enable_source == "caller-provided-opt-in-config"
    assert config.skip_reason is None
    assert config.issues == ()
    assert config.stores_test_dsn_value is False
    assert secret_dsn not in repr(config)


def test_opt_in_config_disabled_for_false_values_even_with_dsn() -> None:
    for false_value in POSTGRESQL_INTEGRATION_TEST_OPT_IN_FALSE_VALUES:
        config = evaluate_postgresql_integration_test_opt_in_config(
            {
                POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR: false_value,
                POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR: "postgresql://example",
            },
        )

        assert config.enabled is False
        assert config.opt_in_requested is False
        assert config.test_dsn_configured is True
        assert config.issues == ()
        assert config.skip_reason == POSTGRESQL_INTEGRATION_TEST_SKIP_REASON


def test_opt_in_config_reports_invalid_opt_in_values() -> None:
    config = evaluate_postgresql_integration_test_opt_in_config(
        {
            POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR: "maybe",
            POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR: "postgresql://example",
        },
    )

    assert config.enabled is False
    assert config.opt_in_requested is False
    assert config.test_dsn_configured is True
    assert config.issues == (
        PostgreSQLIntegrationTestConfigIssue(
            code="POSTGRESQL_INTEGRATION_TEST_OPT_IN_INVALID",
            message=(
                "PostgreSQL integration test opt-in must be one of: "
                "1, true, yes, on."
            ),
            field_name=POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR,
        ),
    )
    assert config.skip_reason == config.issues[0].message


def test_pytest_marker_registry_declares_postgresql_integration_only() -> None:
    pyproject_text = (REPOSITORY_ROOT / "pyproject.toml").read_text(
        encoding="utf-8",
    )

    assert '"postgresql_integration:' in pyproject_text
    assert "CARBONOPS_RUN_POSTGRESQL_INTEGRATION" not in pyproject_text
    assert "CARBONOPS_POSTGRESQL_TEST_DSN" not in pyproject_text


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

    assert boundary.opt_in_control_name == "CARBONOPS_RUN_POSTGRESQL_INTEGRATION"
    assert boundary.test_dsn_input_name == "CARBONOPS_POSTGRESQL_TEST_DSN"
    assert should_skip_postgresql_integration_tests(boundary)


def test_boundary_does_not_read_opt_in_or_dsn_values(monkeypatch) -> None:
    def fail_getenv(name, *args, **kwargs):
        raise AssertionError(f"boundary must not read external input {name}")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    boundary = create_postgresql_integration_test_boundary(
        explicitly_enabled=True,
        enable_source="caller-provided-test-boundary",
    )

    assert boundary.enabled is True
    assert boundary.opt_in_control_name == POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR
    assert boundary.test_dsn_input_name == POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR
    assert not should_skip_postgresql_integration_tests(boundary)


def test_config_evaluation_has_no_env_config_db_file_or_network_side_effects(
    monkeypatch,
) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("integration config must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(os, "getenv", fail_side_effect)
    monkeypatch.setattr(socket, "create_connection", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    config = evaluate_postgresql_integration_test_opt_in_config(
        {
            POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR: "on",
            POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR: "postgresql://example",
        },
    )

    assert config.enabled is True
    assert config.opens_connection is False
    assert config.runs_sql is False


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
    assert "cursor(" not in module_source
    assert "execute(" not in module_source
    assert "commit(" not in module_source
    assert "rollback(" not in module_source
    assert "begin(" not in module_source
    assert "CREATE TABLE" not in module_source
    assert "INSERT INTO" not in module_source
