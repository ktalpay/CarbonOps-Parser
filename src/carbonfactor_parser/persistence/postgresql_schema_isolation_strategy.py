"""PostgreSQL schema isolation and cleanup strategy without DB execution."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


POSTGRESQL_ISOLATED_SCHEMA_PREFIX = "carbonops_test_"
POSTGRESQL_RESERVED_SCHEMA_NAMES = (
    "public",
    "information_schema",
    "pg_catalog",
    "pg_toast",
)
_POSTGRESQL_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,62}$")


class PostgreSQLSchemaIsolationStrategyStatus(str, Enum):
    """Status values for schema isolation strategy validation."""

    READY = "ready"
    BLOCKED = "blocked"


class PostgreSQLSchemaIsolationCleanupMode(str, Enum):
    """Future cleanup mode markers for isolated test schemas."""

    FUTURE_DROP_SCHEMA = "future_drop_schema"


class PostgreSQLSchemaIsolationCleanupScope(str, Enum):
    """Future cleanup scope markers for isolated test schemas."""

    ISOLATED_SCHEMA_ONLY = "isolated_schema_only"


@dataclass(frozen=True)
class PostgreSQLSchemaIsolationStrategyIssue:
    """Issue explaining schema isolation strategy validation."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class PostgreSQLSchemaIsolationStrategy:
    """Schema isolation and cleanup metadata for future opt-in DB tests."""

    schema_name: str = "carbonops_test_isolated"
    required_schema_prefix: str = POSTGRESQL_ISOLATED_SCHEMA_PREFIX
    cleanup_mode: PostgreSQLSchemaIsolationCleanupMode = (
        PostgreSQLSchemaIsolationCleanupMode.FUTURE_DROP_SCHEMA
    )
    cleanup_scope: PostgreSQLSchemaIsolationCleanupScope = (
        PostgreSQLSchemaIsolationCleanupScope.ISOLATED_SCHEMA_ONLY
    )
    require_isolated_schema: bool = True
    cleanup_only_isolated_schema: bool = True
    runtime_cleanup_enabled: bool = False
    opens_connection: bool = False
    runs_sql: bool = False
    creates_schema: bool = False
    drops_schema: bool = False
    truncates_tables: bool = False
    loads_environment: bool = False
    loads_config_files: bool = False
    loads_credentials: bool = False
    notes: tuple[str, ...] = (
        "Schema isolation strategy metadata only.",
        "Future cleanup must target only isolated test schemas.",
        "No schema creation, table truncation, or schema deletion is executed.",
    )


@dataclass(frozen=True)
class PostgreSQLSchemaIsolationStrategyValidationResult:
    """Fail-closed validation result for schema isolation metadata."""

    status: PostgreSQLSchemaIsolationStrategyStatus
    issues: tuple[PostgreSQLSchemaIsolationStrategyIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return (
            self.status is PostgreSQLSchemaIsolationStrategyStatus.READY
            and not self.issues
        )


@dataclass(frozen=True)
class PostgreSQLSchemaIsolationStrategyDescription:
    """Side-effect-free description of schema isolation strategy."""

    strategy: PostgreSQLSchemaIsolationStrategy
    driver_neutral: bool
    runtime_cleanup_enabled: bool
    opens_connection: bool
    runs_sql: bool
    creates_schema: bool
    drops_schema: bool
    truncates_tables: bool
    loads_environment: bool
    loads_config_files: bool
    loads_credentials: bool
    reserved_schema_names: tuple[str, ...]
    notes: tuple[str, ...]


def build_default_postgresql_schema_isolation_strategy(
    *,
    schema_name: str = "carbonops_test_isolated",
) -> PostgreSQLSchemaIsolationStrategy:
    """Build deterministic isolated-schema cleanup strategy metadata."""

    return PostgreSQLSchemaIsolationStrategy(schema_name=schema_name)


def describe_postgresql_schema_isolation_strategy() -> (
    PostgreSQLSchemaIsolationStrategyDescription
):
    """Describe schema isolation and cleanup strategy without side effects."""

    strategy = build_default_postgresql_schema_isolation_strategy()
    return PostgreSQLSchemaIsolationStrategyDescription(
        strategy=strategy,
        driver_neutral=True,
        runtime_cleanup_enabled=False,
        opens_connection=False,
        runs_sql=False,
        creates_schema=False,
        drops_schema=False,
        truncates_tables=False,
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
        reserved_schema_names=POSTGRESQL_RESERVED_SCHEMA_NAMES,
        notes=(
            "Schema isolation strategy is metadata only.",
            "The default schema name uses a test-only prefix.",
            "Runtime cleanup remains disabled until a future safety-gated task.",
        ),
    )


def validate_postgresql_schema_isolation_strategy(
    strategy: PostgreSQLSchemaIsolationStrategy,
) -> PostgreSQLSchemaIsolationStrategyValidationResult:
    """Validate schema isolation strategy metadata without touching PostgreSQL."""

    issues: list[PostgreSQLSchemaIsolationStrategyIssue] = []
    _validate_schema_identifier(
        strategy.schema_name,
        "schema_name",
        "POSTGRESQL_SCHEMA_ISOLATION_SCHEMA_NAME_UNSAFE",
        "schema_name must be a safe unquoted PostgreSQL identifier.",
        issues,
    )
    _validate_schema_identifier(
        strategy.required_schema_prefix,
        "required_schema_prefix",
        "POSTGRESQL_SCHEMA_ISOLATION_PREFIX_UNSAFE",
        "required_schema_prefix must be a safe unquoted identifier prefix.",
        issues,
    )
    if isinstance(strategy.schema_name, str):
        normalized_schema = strategy.schema_name.strip()
        if normalized_schema in POSTGRESQL_RESERVED_SCHEMA_NAMES:
            issues.append(
                PostgreSQLSchemaIsolationStrategyIssue(
                    code="POSTGRESQL_SCHEMA_ISOLATION_RESERVED_SCHEMA",
                    message="schema_name must not target a reserved schema.",
                    field_name="schema_name",
                )
            )
        if normalized_schema.startswith("pg_"):
            issues.append(
                PostgreSQLSchemaIsolationStrategyIssue(
                    code="POSTGRESQL_SCHEMA_ISOLATION_SYSTEM_SCHEMA",
                    message="schema_name must not target a PostgreSQL system schema.",
                    field_name="schema_name",
                )
            )
        if isinstance(strategy.required_schema_prefix, str) and not (
            normalized_schema.startswith(strategy.required_schema_prefix)
        ):
            issues.append(
                PostgreSQLSchemaIsolationStrategyIssue(
                    code="POSTGRESQL_SCHEMA_ISOLATION_PREFIX_REQUIRED",
                    message=(
                        "schema_name must use the required isolated test "
                        "schema prefix."
                    ),
                    field_name="schema_name",
                )
            )
    if (
        strategy.cleanup_mode
        is not PostgreSQLSchemaIsolationCleanupMode.FUTURE_DROP_SCHEMA
    ):
        issues.append(
            PostgreSQLSchemaIsolationStrategyIssue(
                code="POSTGRESQL_SCHEMA_ISOLATION_CLEANUP_MODE_UNSAFE",
                message="cleanup_mode must remain future_drop_schema.",
                field_name="cleanup_mode",
            )
        )
    if (
        strategy.cleanup_scope
        is not PostgreSQLSchemaIsolationCleanupScope.ISOLATED_SCHEMA_ONLY
    ):
        issues.append(
            PostgreSQLSchemaIsolationStrategyIssue(
                code="POSTGRESQL_SCHEMA_ISOLATION_CLEANUP_SCOPE_UNSAFE",
                message="cleanup_scope must remain isolated_schema_only.",
                field_name="cleanup_scope",
            )
        )
    _validate_true(
        strategy.require_isolated_schema,
        "require_isolated_schema",
        "POSTGRESQL_SCHEMA_ISOLATION_REQUIRED",
        "require_isolated_schema must remain True.",
        issues,
    )
    _validate_true(
        strategy.cleanup_only_isolated_schema,
        "cleanup_only_isolated_schema",
        "POSTGRESQL_SCHEMA_ISOLATION_CLEANUP_SCOPE_REQUIRED",
        "cleanup_only_isolated_schema must remain True.",
        issues,
    )
    for field_name, value in (
        ("runtime_cleanup_enabled", strategy.runtime_cleanup_enabled),
        ("opens_connection", strategy.opens_connection),
        ("runs_sql", strategy.runs_sql),
        ("creates_schema", strategy.creates_schema),
        ("drops_schema", strategy.drops_schema),
        ("truncates_tables", strategy.truncates_tables),
        ("loads_environment", strategy.loads_environment),
        ("loads_config_files", strategy.loads_config_files),
        ("loads_credentials", strategy.loads_credentials),
    ):
        _validate_false(
            value,
            field_name,
            "POSTGRESQL_SCHEMA_ISOLATION_RUNTIME_FLAG_NOT_ALLOWED",
            f"{field_name} must remain False for this strategy boundary.",
            issues,
        )
    if not strategy.notes:
        issues.append(
            PostgreSQLSchemaIsolationStrategyIssue(
                code="POSTGRESQL_SCHEMA_ISOLATION_MISSING_NOTES",
                message="schema isolation strategy must include notes.",
                field_name="notes",
            )
        )

    return PostgreSQLSchemaIsolationStrategyValidationResult(
        status=(
            PostgreSQLSchemaIsolationStrategyStatus.BLOCKED
            if issues
            else PostgreSQLSchemaIsolationStrategyStatus.READY
        ),
        issues=tuple(issues),
    )


def _validate_schema_identifier(
    value: object,
    field_name: str,
    code: str,
    message: str,
    issues: list[PostgreSQLSchemaIsolationStrategyIssue],
) -> None:
    if (
        not isinstance(value, str)
        or value != value.strip()
        or not _POSTGRESQL_IDENTIFIER_PATTERN.fullmatch(value)
    ):
        issues.append(
            PostgreSQLSchemaIsolationStrategyIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )


def _validate_true(
    value: bool,
    field_name: str,
    code: str,
    message: str,
    issues: list[PostgreSQLSchemaIsolationStrategyIssue],
) -> None:
    if value is not True:
        issues.append(
            PostgreSQLSchemaIsolationStrategyIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )


def _validate_false(
    value: bool,
    field_name: str,
    code: str,
    message: str,
    issues: list[PostgreSQLSchemaIsolationStrategyIssue],
) -> None:
    if value is not False:
        issues.append(
            PostgreSQLSchemaIsolationStrategyIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )
