"""PostgreSQL integration test boundary helpers."""

from __future__ import annotations

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


def should_skip_postgresql_integration_tests(
    boundary: PostgreSQLIntegrationTestBoundary | None = None,
) -> bool:
    """Return whether PostgreSQL integration tests should be skipped."""

    selected_boundary = boundary or create_postgresql_integration_test_boundary()
    return not selected_boundary.enabled
