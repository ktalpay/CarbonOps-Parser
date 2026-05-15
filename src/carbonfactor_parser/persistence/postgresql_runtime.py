"""PostgreSQL runtime startup helpers for Phase 1 ingestion state."""

from __future__ import annotations

from dataclasses import dataclass

from carbonfactor_parser.persistence.postgresql_runtime_config import (
    PostgreSQLRuntimeConfig,
    PostgreSQLRuntimeConfigIssue,
    PostgreSQLRuntimeConfigLoadResult,
)
from carbonfactor_parser.persistence.postgresql_runtime_schema_bootstrap import (
    PostgreSQLRuntimeSchemaBootstrapResult,
    bootstrap_postgresql_phase1_schema,
)
from carbonfactor_parser.persistence.postgresql_year_state_repository import (
    PostgreSQLSourceFamilyYearStateRepository,
)


@dataclass(frozen=True)
class PostgreSQLRuntimeStartupResult:
    """Started PostgreSQL runtime components."""

    connection: object
    schema_bootstrap: PostgreSQLRuntimeSchemaBootstrapResult
    year_state_repository: PostgreSQLSourceFamilyYearStateRepository


def connect_postgresql_runtime(config: PostgreSQLRuntimeConfig) -> object:
    """Open a psycopg PostgreSQL connection from validated runtime config."""

    import psycopg

    if config.uses_dsn:
        return psycopg.connect(config.dsn)

    kwargs: dict[str, object] = {
        "host": config.host,
        "port": config.port,
        "dbname": config.database,
        "user": config.username,
        "password": config.password,
    }
    if config.ssl_mode is not None:
        kwargs["sslmode"] = config.ssl_mode
    if config.application_name is not None:
        kwargs["application_name"] = config.application_name
    return psycopg.connect(**kwargs)


def start_postgresql_runtime(
    config_result: PostgreSQLRuntimeConfigLoadResult,
) -> PostgreSQLRuntimeStartupResult:
    """Fail closed on config issues, then connect and bootstrap schema."""

    if not config_result.is_ready or config_result.config is None:
        raise PostgreSQLRuntimeStartupBlockedError(config_result.issues)

    connection = connect_postgresql_runtime(config_result.config)
    schema_bootstrap = bootstrap_postgresql_phase1_schema(connection)
    repository = PostgreSQLSourceFamilyYearStateRepository(
        connection,
        initial_year=config_result.config.initial_year,
    )
    return PostgreSQLRuntimeStartupResult(
        connection=connection,
        schema_bootstrap=schema_bootstrap,
        year_state_repository=repository,
    )


class PostgreSQLRuntimeStartupBlockedError(RuntimeError):
    """Raised when PostgreSQL runtime startup is blocked by safe config checks."""

    def __init__(self, issues: tuple[PostgreSQLRuntimeConfigIssue, ...]) -> None:
        self.issues = issues
        codes = ", ".join(issue.code for issue in issues) or "unknown"
        super().__init__(f"PostgreSQL runtime startup blocked: {codes}")
