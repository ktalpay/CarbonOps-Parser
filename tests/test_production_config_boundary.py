from __future__ import annotations

import builtins
import inspect
import os
import sqlite3
import urllib.request

from carbonfactor_parser.persistence.production_config_boundary import (
    PRODUCTION_CONFIG_REQUIRED_ENV_VARS,
    PRODUCTION_CONFIG_SECRET_ENV_VARS,
    describe_production_config_boundary,
    validate_production_config_mapping,
)


def _valid_config(**overrides: str | None) -> dict[str, str | None]:
    values: dict[str, str | None] = {
        "CARBONOPS_PARSER_ENV": "production",
        "CARBONOPS_PARSER_DATABASE_PROVIDER": "postgres",
        "CARBONOPS_PARSER_POSTGRES_HOST": "db.internal.example",
        "CARBONOPS_PARSER_POSTGRES_PORT": "5432",
        "CARBONOPS_PARSER_POSTGRES_DATABASE": "carbonops_parser",
        "CARBONOPS_PARSER_POSTGRES_USERNAME": "carbonops_runtime",
        "CARBONOPS_PARSER_POSTGRES_PASSWORD": "runtime-secret-not-returned",
        "CARBONOPS_PARSER_POSTGRES_SCHEMA": "carbonops",
        "CARBONOPS_PARSER_RAW_ARCHIVE_PATH": "/var/lib/carbonops/raw",
        "CARBONOPS_PARSER_LOG_LEVEL": "info",
    }
    values.update(overrides)
    return values


def test_production_config_boundary_documents_aligned_required_env_vars() -> None:
    description = describe_production_config_boundary()

    assert description.required_env_vars == PRODUCTION_CONFIG_REQUIRED_ENV_VARS
    assert description.secret_env_vars == PRODUCTION_CONFIG_SECRET_ENV_VARS
    assert description.provider == "postgres"
    assert description.loads_environment is False
    assert description.loads_config_files is False
    assert description.loads_credentials is False
    assert description.logs_secret_values is False
    assert "CARBONOPS_PARSER_POSTGRES_PASSWORD" in description.secret_env_vars


def test_valid_production_config_mapping_passes_without_returning_secret() -> None:
    result = validate_production_config_mapping(_valid_config())

    assert result.is_valid
    assert result.issues == ()


def test_missing_required_production_keys_fail_closed_with_safe_messages() -> None:
    result = validate_production_config_mapping(
        _valid_config(
            CARBONOPS_PARSER_POSTGRES_PASSWORD=" ",
            CARBONOPS_PARSER_RAW_ARCHIVE_PATH=None,
        ),
    )

    assert not result.is_valid
    assert [issue.field_name for issue in result.issues] == [
        "CARBONOPS_PARSER_POSTGRES_PASSWORD",
        "CARBONOPS_PARSER_RAW_ARCHIVE_PATH",
    ]
    rendered = repr(result)
    assert "runtime-secret-not-returned" not in rendered
    assert "Password" + "=" not in rendered


def test_invalid_values_fail_with_actionable_key_only_messages() -> None:
    result = validate_production_config_mapping(
        _valid_config(
            CARBONOPS_PARSER_DATABASE_PROVIDER="mysql",
            CARBONOPS_PARSER_POSTGRES_PORT="not-a-port",
            CARBONOPS_PARSER_LOG_LEVEL="verbose",
            CARBONOPS_PARSER_POSTGRES_CONNECTION_STRING=(
                "Host=db;Username=svc;" + "Password" + "=raw-secret"
            ),
        ),
    )

    assert [issue.code for issue in result.issues] == [
        "PRODUCTION_CONFIG_UNSUPPORTED_DATABASE_PROVIDER",
        "PRODUCTION_CONFIG_INVALID_POSTGRES_PORT",
        "PRODUCTION_CONFIG_INVALID_LOG_LEVEL",
        "PRODUCTION_CONFIG_RAW_CONNECTION_STRING_NOT_ALLOWED",
    ]
    rendered = repr(result)
    assert "mysql" not in rendered
    assert "not-a-port" not in rendered
    assert "verbose" not in rendered
    assert "raw-secret" not in rendered


def test_production_config_validation_has_no_external_side_effects(monkeypatch) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("production config validation must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(os, "getenv", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    result = validate_production_config_mapping(_valid_config())

    assert result.is_valid


def test_production_config_module_does_not_load_environment_or_connect() -> None:
    import carbonfactor_parser.persistence.production_config_boundary as module

    source = inspect.getsource(module)
    lower_source = source.lower()

    assert "os.environ" not in source
    assert "getenv" not in source
    assert "open(" not in source
    assert "connect(" not in source
    assert "psycopg" not in lower_source
    assert "sqlalchemy" not in lower_source
