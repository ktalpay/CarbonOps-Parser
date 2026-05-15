"""Explicit PostgreSQL runtime configuration loading for local/test startup."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum


POSTGRESQL_RUNTIME_DSN_ENV_VAR = "CARBONOPS_POSTGRESQL_DSN"
POSTGRESQL_RUNTIME_HOST_ENV_VAR = "CARBONOPS_POSTGRESQL_HOST"
POSTGRESQL_RUNTIME_PORT_ENV_VAR = "CARBONOPS_POSTGRESQL_PORT"
POSTGRESQL_RUNTIME_DATABASE_ENV_VAR = "CARBONOPS_POSTGRESQL_DATABASE"
POSTGRESQL_RUNTIME_USERNAME_ENV_VAR = "CARBONOPS_POSTGRESQL_USERNAME"
POSTGRESQL_RUNTIME_PASSWORD_ENV_VAR = "CARBONOPS_POSTGRESQL_PASSWORD"
POSTGRESQL_RUNTIME_SSL_MODE_ENV_VAR = "CARBONOPS_POSTGRESQL_SSL_MODE"
POSTGRESQL_RUNTIME_APPLICATION_NAME_ENV_VAR = (
    "CARBONOPS_POSTGRESQL_APPLICATION_NAME"
)
POSTGRESQL_RUNTIME_INITIAL_YEAR_ENV_VAR = (
    "CARBONOPS_POSTGRESQL_INITIAL_YEAR"
)
POSTGRESQL_RUNTIME_DEFAULT_PORT = 5432
POSTGRESQL_RUNTIME_DEFAULT_INITIAL_YEAR = 2024


class PostgreSQLRuntimeConfigStatus(str, Enum):
    """Runtime configuration loading status."""

    READY = "ready"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class PostgreSQLRuntimeConfigIssue:
    """Safe runtime configuration issue without secret values."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class PostgreSQLRuntimeConfig:
    """Validated PostgreSQL runtime configuration."""

    dsn: str | None = field(default=None, repr=False)
    host: str | None = None
    port: int = POSTGRESQL_RUNTIME_DEFAULT_PORT
    database: str | None = None
    username: str | None = None
    password: str | None = field(default=None, repr=False)
    ssl_mode: str | None = None
    application_name: str | None = None
    initial_year: int = POSTGRESQL_RUNTIME_DEFAULT_INITIAL_YEAR

    @property
    def uses_dsn(self) -> bool:
        """Return whether the connection should use a DSN string."""

        return bool(self.dsn and self.dsn.strip())

    @property
    def password_configured(self) -> bool:
        """Return a safe password-presence marker."""

        return bool(self.password)


@dataclass(frozen=True)
class PostgreSQLRuntimeConfigLoadResult:
    """Result of explicit/env PostgreSQL runtime configuration loading."""

    status: PostgreSQLRuntimeConfigStatus
    config: PostgreSQLRuntimeConfig | None
    issues: tuple[PostgreSQLRuntimeConfigIssue, ...] = ()
    loaded_from_environment: bool = False
    loaded_from_explicit_values: bool = False

    @property
    def is_ready(self) -> bool:
        """Return whether the config is complete enough to open PostgreSQL."""

        return self.status is PostgreSQLRuntimeConfigStatus.READY


def load_postgresql_runtime_config_from_environment(
    environ: Mapping[str, str] | None = None,
) -> PostgreSQLRuntimeConfigLoadResult:
    """Load runtime config from environment variables only when called."""

    return load_postgresql_runtime_config(
        os.environ if environ is None else environ,
        loaded_from_environment=True,
    )


def load_postgresql_runtime_config(
    values: Mapping[str, object] | None = None,
    *,
    loaded_from_environment: bool = False,
) -> PostgreSQLRuntimeConfigLoadResult:
    """Load runtime config from caller-provided values and fail closed."""

    source = values or {}
    dsn = _optional_text(source.get(POSTGRESQL_RUNTIME_DSN_ENV_VAR))
    host = _optional_text(source.get(POSTGRESQL_RUNTIME_HOST_ENV_VAR))
    database = _optional_text(source.get(POSTGRESQL_RUNTIME_DATABASE_ENV_VAR))
    username = _optional_text(source.get(POSTGRESQL_RUNTIME_USERNAME_ENV_VAR))
    password = _optional_text(source.get(POSTGRESQL_RUNTIME_PASSWORD_ENV_VAR))
    ssl_mode = _optional_text(source.get(POSTGRESQL_RUNTIME_SSL_MODE_ENV_VAR))
    application_name = _optional_text(
        source.get(POSTGRESQL_RUNTIME_APPLICATION_NAME_ENV_VAR),
    )
    port, port_issue = _parse_int(
        source.get(POSTGRESQL_RUNTIME_PORT_ENV_VAR),
        default=POSTGRESQL_RUNTIME_DEFAULT_PORT,
        field_name=POSTGRESQL_RUNTIME_PORT_ENV_VAR,
        code="POSTGRESQL_RUNTIME_CONFIG_INVALID_PORT",
        message="PostgreSQL runtime port must be an integer between 1 and 65535.",
    )
    initial_year, initial_year_issue = _parse_int(
        source.get(POSTGRESQL_RUNTIME_INITIAL_YEAR_ENV_VAR),
        default=POSTGRESQL_RUNTIME_DEFAULT_INITIAL_YEAR,
        field_name=POSTGRESQL_RUNTIME_INITIAL_YEAR_ENV_VAR,
        code="POSTGRESQL_RUNTIME_CONFIG_INVALID_INITIAL_YEAR",
        message="PostgreSQL runtime initial year must be a positive integer.",
    )

    issues: list[PostgreSQLRuntimeConfigIssue] = []
    if port_issue is not None:
        issues.append(port_issue)
    elif port < 1 or port > 65535:
        issues.append(
            PostgreSQLRuntimeConfigIssue(
                code="POSTGRESQL_RUNTIME_CONFIG_INVALID_PORT",
                message="PostgreSQL runtime port must be between 1 and 65535.",
                field_name=POSTGRESQL_RUNTIME_PORT_ENV_VAR,
            ),
        )
    if initial_year_issue is not None:
        issues.append(initial_year_issue)
    elif initial_year < 1:
        issues.append(
            PostgreSQLRuntimeConfigIssue(
                code="POSTGRESQL_RUNTIME_CONFIG_INVALID_INITIAL_YEAR",
                message="PostgreSQL runtime initial year must be positive.",
                field_name=POSTGRESQL_RUNTIME_INITIAL_YEAR_ENV_VAR,
            ),
        )

    if not dsn:
        _append_missing_required(
            issues,
            host,
            POSTGRESQL_RUNTIME_HOST_ENV_VAR,
            "POSTGRESQL_RUNTIME_CONFIG_MISSING_HOST",
        )
        _append_missing_required(
            issues,
            database,
            POSTGRESQL_RUNTIME_DATABASE_ENV_VAR,
            "POSTGRESQL_RUNTIME_CONFIG_MISSING_DATABASE",
        )
        _append_missing_required(
            issues,
            username,
            POSTGRESQL_RUNTIME_USERNAME_ENV_VAR,
            "POSTGRESQL_RUNTIME_CONFIG_MISSING_USERNAME",
        )
        _append_missing_required(
            issues,
            password,
            POSTGRESQL_RUNTIME_PASSWORD_ENV_VAR,
            "POSTGRESQL_RUNTIME_CONFIG_MISSING_PASSWORD",
        )

    config = PostgreSQLRuntimeConfig(
        dsn=dsn,
        host=host,
        port=port,
        database=database,
        username=username,
        password=password,
        ssl_mode=ssl_mode,
        application_name=application_name,
        initial_year=initial_year,
    )
    status = (
        PostgreSQLRuntimeConfigStatus.BLOCKED
        if issues
        else PostgreSQLRuntimeConfigStatus.READY
    )
    return PostgreSQLRuntimeConfigLoadResult(
        status=status,
        config=None if issues else config,
        issues=tuple(issues),
        loaded_from_environment=loaded_from_environment,
        loaded_from_explicit_values=not loaded_from_environment,
    )


def _append_missing_required(
    issues: list[PostgreSQLRuntimeConfigIssue],
    value: str | None,
    field_name: str,
    code: str,
) -> None:
    if value:
        return
    issues.append(
        PostgreSQLRuntimeConfigIssue(
            code=code,
            message=f"PostgreSQL runtime configuration is missing {field_name}.",
            field_name=field_name,
        ),
    )


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _parse_int(
    value: object,
    *,
    default: int,
    field_name: str,
    code: str,
    message: str,
) -> tuple[int, PostgreSQLRuntimeConfigIssue | None]:
    if value is None or value == "":
        return default, None
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return default, PostgreSQLRuntimeConfigIssue(
            code=code,
            message=message,
            field_name=field_name,
        )
    return parsed, None
