import builtins
import inspect
import os
import sqlite3
import urllib.request
from dataclasses import fields

import carbonfactor_parser.persistence.postgresql_options as options_module
from carbonfactor_parser.persistence import (
    PostgreSQLPersistenceOptions,
    PostgreSQLPersistenceOptionsValidationIssue,
    PostgreSQLPersistenceOptionsValidationResult,
    create_postgresql_persistence_options,
    validate_postgresql_persistence_options,
)


def _valid_options(**overrides) -> PostgreSQLPersistenceOptions:
    values = {
        "host": "localhost",
        "port": 5432,
        "database": "carbonops_test",
        "username": "carbonops",
        "password_set": True,
        "ssl_mode": "prefer",
        "application_name": "carbonops-parser",
        "connect_timeout_seconds": 5,
    }
    values.update(overrides)
    return create_postgresql_persistence_options(**values)


def test_valid_options_validate_successfully() -> None:
    result = validate_postgresql_persistence_options(_valid_options())

    assert isinstance(result, PostgreSQLPersistenceOptionsValidationResult)
    assert result.is_valid
    assert result.issues == ()


def test_options_preserve_caller_provided_fields() -> None:
    options = _valid_options()

    assert options.host == "localhost"
    assert options.port == 5432
    assert options.database == "carbonops_test"
    assert options.username == "carbonops"
    assert options.password_set is True
    assert options.ssl_mode == "prefer"
    assert options.application_name == "carbonops-parser"
    assert options.connect_timeout_seconds == 5


def test_missing_host_fails_validation() -> None:
    result = validate_postgresql_persistence_options(_valid_options(host=" "))

    assert not result.is_valid
    assert result.issues == (
        PostgreSQLPersistenceOptionsValidationIssue(
            code="POSTGRESQL_OPTIONS_MISSING_HOST",
            message="host must be a non-empty string.",
            field_name="host",
        ),
    )


def test_invalid_port_fails_validation() -> None:
    result = validate_postgresql_persistence_options(_valid_options(port=0))

    assert not result.is_valid
    assert result.issues[0].code == "POSTGRESQL_OPTIONS_INVALID_PORT"
    assert result.issues[0].field_name == "port"


def test_missing_database_fails_validation() -> None:
    result = validate_postgresql_persistence_options(_valid_options(database=""))

    assert not result.is_valid
    assert result.issues[0].code == "POSTGRESQL_OPTIONS_MISSING_DATABASE"
    assert result.issues[0].field_name == "database"


def test_missing_username_fails_validation() -> None:
    result = validate_postgresql_persistence_options(_valid_options(username=" "))

    assert not result.is_valid
    assert result.issues[0].code == "POSTGRESQL_OPTIONS_MISSING_USERNAME"
    assert result.issues[0].field_name == "username"


def test_missing_password_marker_does_not_fail_validation() -> None:
    result = validate_postgresql_persistence_options(
        _valid_options(password_set=False),
    )

    assert result.is_valid


def test_invalid_timeout_fails_validation() -> None:
    result = validate_postgresql_persistence_options(
        _valid_options(connect_timeout_seconds=-1),
    )

    assert not result.is_valid
    assert result.issues[0].code == "POSTGRESQL_OPTIONS_INVALID_CONNECT_TIMEOUT"
    assert result.issues[0].field_name == "connect_timeout_seconds"


def test_blank_optional_text_fails_when_provided() -> None:
    result = validate_postgresql_persistence_options(
        _valid_options(ssl_mode="", application_name=" "),
    )

    assert [issue.code for issue in result.issues] == [
        "POSTGRESQL_OPTIONS_BLANK_SSL_MODE",
        "POSTGRESQL_OPTIONS_BLANK_APPLICATION_NAME",
    ]


def test_password_value_is_not_part_of_options_repr_or_fields() -> None:
    options = _valid_options(password_set=True)
    option_fields = {field.name for field in fields(PostgreSQLPersistenceOptions)}
    rendered = f"{options!r} {options!s}"

    assert "password" not in option_fields
    assert "pass" + "word=" not in rendered
    assert "actual-secret-value" not in rendered
    assert "password_set=True" in rendered


def test_options_creation_has_no_env_config_db_file_or_network_side_effects(
    monkeypatch,
) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("options contract must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(os, "getenv", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    options = _valid_options()
    result = validate_postgresql_persistence_options(options)

    assert result.is_valid


def test_options_module_has_no_env_config_db_dependency_or_sql_behavior() -> None:
    module_source = inspect.getsource(options_module)
    lower_source = module_source.lower()

    assert "os.environ" not in module_source
    assert "getenv" not in module_source
    assert "path(" not in lower_source
    assert "open(" not in module_source
    assert "psycopg" not in lower_source
    assert "asyncpg" not in lower_source
    assert "sqlalchemy" not in lower_source
    assert "connect(" not in module_source
    assert ".execute" not in module_source
    assert "CREATE TABLE" not in module_source
    assert "INSERT INTO" not in module_source
