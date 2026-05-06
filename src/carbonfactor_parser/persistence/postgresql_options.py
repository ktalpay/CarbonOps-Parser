"""Explicit PostgreSQL persistence options without loading or connecting."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PostgreSQLPersistenceOptions:
    """Caller-provided PostgreSQL options for a future repository boundary."""

    host: str
    port: int
    database: str
    username: str
    password_set: bool = False
    ssl_mode: str | None = None
    application_name: str | None = None
    connect_timeout_seconds: int | None = None


@dataclass(frozen=True)
class PostgreSQLPersistenceOptionsValidationIssue:
    """Validation issue for PostgreSQL persistence options."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class PostgreSQLPersistenceOptionsValidationResult:
    """Validation result for PostgreSQL persistence options."""

    issues: tuple[PostgreSQLPersistenceOptionsValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def create_postgresql_persistence_options(
    *,
    host: str,
    port: int,
    database: str,
    username: str,
    password_set: bool = False,
    ssl_mode: str | None = None,
    application_name: str | None = None,
    connect_timeout_seconds: int | None = None,
) -> PostgreSQLPersistenceOptions:
    """Create caller-provided options without loading config or credentials."""

    return PostgreSQLPersistenceOptions(
        host=host,
        port=port,
        database=database,
        username=username,
        password_set=password_set,
        ssl_mode=ssl_mode,
        application_name=application_name,
        connect_timeout_seconds=connect_timeout_seconds,
    )


def validate_postgresql_persistence_options(
    options: PostgreSQLPersistenceOptions,
) -> PostgreSQLPersistenceOptionsValidationResult:
    """Validate PostgreSQL options without connecting or loading secrets."""

    issues: list[PostgreSQLPersistenceOptionsValidationIssue] = []

    _validate_required_text(
        options.host,
        "host",
        "POSTGRESQL_OPTIONS_MISSING_HOST",
        "host must be a non-empty string.",
        issues,
    )
    _validate_port(options.port, issues)
    _validate_required_text(
        options.database,
        "database",
        "POSTGRESQL_OPTIONS_MISSING_DATABASE",
        "database must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        options.username,
        "username",
        "POSTGRESQL_OPTIONS_MISSING_USERNAME",
        "username must be a non-empty string.",
        issues,
    )
    _validate_password_set(options.password_set, issues)
    _validate_optional_text(
        options.ssl_mode,
        "ssl_mode",
        "POSTGRESQL_OPTIONS_BLANK_SSL_MODE",
        "ssl_mode must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        options.application_name,
        "application_name",
        "POSTGRESQL_OPTIONS_BLANK_APPLICATION_NAME",
        "application_name must be non-empty when provided.",
        issues,
    )
    _validate_timeout(options.connect_timeout_seconds, issues)

    return PostgreSQLPersistenceOptionsValidationResult(issues=tuple(issues))


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[PostgreSQLPersistenceOptionsValidationIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            PostgreSQLPersistenceOptionsValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            ),
        )


def _validate_optional_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[PostgreSQLPersistenceOptionsValidationIssue],
) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        issues.append(
            PostgreSQLPersistenceOptionsValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            ),
        )


def _validate_port(
    value: int,
    issues: list[PostgreSQLPersistenceOptionsValidationIssue],
) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 65535:
        issues.append(
            PostgreSQLPersistenceOptionsValidationIssue(
                code="POSTGRESQL_OPTIONS_INVALID_PORT",
                message="port must be an integer between 1 and 65535.",
                field_name="port",
            ),
        )


def _validate_password_set(
    value: bool,
    issues: list[PostgreSQLPersistenceOptionsValidationIssue],
) -> None:
    if not isinstance(value, bool):
        issues.append(
            PostgreSQLPersistenceOptionsValidationIssue(
                code="POSTGRESQL_OPTIONS_INVALID_PASSWORD_SET_MARKER",
                message="password_set must be a boolean marker.",
                field_name="password_set",
            ),
        )


def _validate_timeout(
    value: int | None,
    issues: list[PostgreSQLPersistenceOptionsValidationIssue],
) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        issues.append(
            PostgreSQLPersistenceOptionsValidationIssue(
                code="POSTGRESQL_OPTIONS_INVALID_CONNECT_TIMEOUT",
                message=(
                    "connect_timeout_seconds must be a positive integer when "
                    "provided."
                ),
                field_name="connect_timeout_seconds",
            ),
        )
