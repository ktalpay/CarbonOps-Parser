"""PostgreSQL integration test boundary helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


POSTGRESQL_INTEGRATION_TEST_MARKER = "postgresql_integration"
POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR = (
    "CARBONOPS_RUN_POSTGRESQL_INTEGRATION"
)
POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR = "CARBONOPS_POSTGRESQL_TEST_DSN"
POSTGRESQL_INTEGRATION_TEST_SKIP_REASON = (
    "PostgreSQL integration tests are disabled by default and require an "
    "explicit opt-in test boundary."
)
POSTGRESQL_INTEGRATION_TEST_OPT_IN_TRUE_VALUES = ("1", "true", "yes", "on")
POSTGRESQL_INTEGRATION_TEST_OPT_IN_FALSE_VALUES = ("", "0", "false", "no", "off")


@dataclass(frozen=True)
class PostgreSQLIntegrationTestConfigIssue:
    """Issue explaining integration test opt-in configuration status."""

    code: str
    message: str
    field_name: str
    severity: str = "warning"


@dataclass(frozen=True)
class PostgreSQLIntegrationTestOptInConfig:
    """Caller-provided PostgreSQL integration test opt-in configuration."""

    enabled: bool
    opt_in_requested: bool
    test_dsn_configured: bool
    marker_name: str
    opt_in_control_name: str = POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR
    test_dsn_input_name: str = POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR
    enable_source: str | None = None
    skip_reason: str | None = None
    issues: tuple[PostgreSQLIntegrationTestConfigIssue, ...] = ()
    loads_environment: bool = False
    loads_config_files: bool = False
    loads_credentials: bool = False
    stores_test_dsn_value: bool = False
    opens_connection: bool = False
    runs_sql: bool = False


@dataclass(frozen=True)
class PostgreSQLIntegrationTestBoundary:
    """Explicit opt-in boundary for future PostgreSQL integration tests."""

    enabled: bool
    marker_name: str
    enable_source: str | None = None
    skip_reason: str | None = None
    opt_in_control_name: str = POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR
    test_dsn_input_name: str = POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR


def create_postgresql_integration_test_boundary(
    *,
    explicitly_enabled: bool = False,
    enable_source: str | None = None,
) -> PostgreSQLIntegrationTestBoundary:
    """Create an integration test boundary without reading env or config."""

    enabled = bool(explicitly_enabled)
    return PostgreSQLIntegrationTestBoundary(
        enabled=enabled,
        marker_name=POSTGRESQL_INTEGRATION_TEST_MARKER,
        enable_source=enable_source if enabled else None,
        skip_reason=None if enabled else POSTGRESQL_INTEGRATION_TEST_SKIP_REASON,
        opt_in_control_name=POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR,
        test_dsn_input_name=POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR,
    )


def evaluate_postgresql_integration_test_opt_in_config(
    caller_provided_values: Mapping[str, object] | None = None,
) -> PostgreSQLIntegrationTestOptInConfig:
    """Evaluate caller-provided opt-in values without reading env or secrets."""

    values = caller_provided_values or {}
    opt_in_value = values.get(POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR)
    test_dsn_value = values.get(POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR)
    opt_in_requested, opt_in_issue = _parse_opt_in_value(opt_in_value)
    test_dsn_configured = _is_non_empty_text(test_dsn_value)

    issues: list[PostgreSQLIntegrationTestConfigIssue] = []
    if opt_in_issue is not None:
        issues.append(opt_in_issue)
    if opt_in_requested and not test_dsn_configured:
        issues.append(
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

    enabled = opt_in_requested and test_dsn_configured and not issues
    return PostgreSQLIntegrationTestOptInConfig(
        enabled=enabled,
        opt_in_requested=opt_in_requested,
        test_dsn_configured=test_dsn_configured,
        marker_name=POSTGRESQL_INTEGRATION_TEST_MARKER,
        opt_in_control_name=POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR,
        test_dsn_input_name=POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR,
        enable_source="caller-provided-opt-in-config" if enabled else None,
        skip_reason=None if enabled else _configuration_skip_reason(issues),
        issues=tuple(issues),
    )


def should_skip_postgresql_integration_tests(
    boundary: PostgreSQLIntegrationTestBoundary | None = None,
) -> bool:
    """Return whether PostgreSQL integration tests should be skipped."""

    selected_boundary = boundary or create_postgresql_integration_test_boundary()
    return not selected_boundary.enabled


def _parse_opt_in_value(
    value: object,
) -> tuple[bool, PostgreSQLIntegrationTestConfigIssue | None]:
    if value is None:
        return False, None
    if isinstance(value, bool):
        return value, None
    if not isinstance(value, str):
        return False, _invalid_opt_in_issue()

    normalized = value.strip().lower()
    if normalized in POSTGRESQL_INTEGRATION_TEST_OPT_IN_TRUE_VALUES:
        return True, None
    if normalized in POSTGRESQL_INTEGRATION_TEST_OPT_IN_FALSE_VALUES:
        return False, None
    return False, _invalid_opt_in_issue()


def _invalid_opt_in_issue() -> PostgreSQLIntegrationTestConfigIssue:
    return PostgreSQLIntegrationTestConfigIssue(
        code="POSTGRESQL_INTEGRATION_TEST_OPT_IN_INVALID",
        message=(
            "PostgreSQL integration test opt-in must be one of: "
            + ", ".join(POSTGRESQL_INTEGRATION_TEST_OPT_IN_TRUE_VALUES)
            + "."
        ),
        field_name=POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR,
    )


def _configuration_skip_reason(
    issues: list[PostgreSQLIntegrationTestConfigIssue],
) -> str:
    if issues:
        return issues[0].message
    return POSTGRESQL_INTEGRATION_TEST_SKIP_REASON


def _is_non_empty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())
