from __future__ import annotations

import os
from dataclasses import dataclass

import pytest

from carbonfactor_parser.persistence import (
    PersistenceInput,
    PersistenceResultStatus,
    PostgreSQLPersistenceRepository,
    POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR,
    POSTGRESQL_INTEGRATION_TEST_MARKER,
    POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR,
)


SMOKE_STATUS_DISABLED = "disabled"
SMOKE_STATUS_MISSING_DSN = "missing_dsn"
SMOKE_STATUS_ELIGIBLE = "eligible"


@dataclass(frozen=True)
class PostgreSQLConnectionSmokeState:
    status: str
    marker_name: str
    opt_in_control_name: str
    test_dsn_input_name: str
    opt_in_requested: bool
    dsn_provided: bool
    skip_reason: str | None
    sanitized_notes: tuple[str, ...]


def decide_postgresql_connection_smoke_state(
    *,
    opt_in_value: str | None,
    dsn_value: str | None,
) -> PostgreSQLConnectionSmokeState:
    opt_in_requested = opt_in_value == "1"
    dsn_provided = bool(dsn_value and dsn_value.strip())

    if not opt_in_requested:
        return PostgreSQLConnectionSmokeState(
            status=SMOKE_STATUS_DISABLED,
            marker_name=POSTGRESQL_INTEGRATION_TEST_MARKER,
            opt_in_control_name=POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR,
            test_dsn_input_name=POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR,
            opt_in_requested=False,
            dsn_provided=dsn_provided,
            skip_reason=(
                "PostgreSQL connection smoke is disabled by default; set "
                f"{POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR}=1 and provide "
                f"{POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR} externally to run."
            ),
            sanitized_notes=(
                "default_test_suite_db_free",
                "no_connection_attempted",
            ),
        )

    if not dsn_provided:
        return PostgreSQLConnectionSmokeState(
            status=SMOKE_STATUS_MISSING_DSN,
            marker_name=POSTGRESQL_INTEGRATION_TEST_MARKER,
            opt_in_control_name=POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR,
            test_dsn_input_name=POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR,
            opt_in_requested=True,
            dsn_provided=False,
            skip_reason=(
                "PostgreSQL connection smoke opt-in was requested, but the "
                f"external {POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR} input "
                "was not provided."
            ),
            sanitized_notes=(
                "missing_external_test_input",
                "no_connection_attempted",
            ),
        )

    return PostgreSQLConnectionSmokeState(
        status=SMOKE_STATUS_ELIGIBLE,
        marker_name=POSTGRESQL_INTEGRATION_TEST_MARKER,
        opt_in_control_name=POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR,
        test_dsn_input_name=POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR,
        opt_in_requested=True,
        dsn_provided=True,
        skip_reason=None,
        sanitized_notes=(
            "explicit_opt_in_detected",
            "external_test_input_present",
            "connection_only_no_sql",
        ),
    )


def test_connection_smoke_state_defaults_to_disabled() -> None:
    state = decide_postgresql_connection_smoke_state(
        opt_in_value=None,
        dsn_value=None,
    )

    assert state.status == SMOKE_STATUS_DISABLED
    assert state.marker_name == "postgresql_integration"
    assert state.opt_in_control_name == "CARBONOPS_RUN_POSTGRESQL_INTEGRATION"
    assert state.test_dsn_input_name == "CARBONOPS_POSTGRESQL_TEST_DSN"
    assert state.opt_in_requested is False
    assert state.dsn_provided is False
    assert state.skip_reason is not None
    assert "disabled by default" in state.skip_reason
    assert state.sanitized_notes == (
        "default_test_suite_db_free",
        "no_connection_attempted",
    )


def test_connection_smoke_state_opt_in_without_dsn_is_missing_dsn() -> None:
    state = decide_postgresql_connection_smoke_state(
        opt_in_value="1",
        dsn_value=None,
    )

    assert state.status == SMOKE_STATUS_MISSING_DSN
    assert state.opt_in_requested is True
    assert state.dsn_provided is False
    assert state.skip_reason is not None
    assert POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR in state.skip_reason
    assert state.sanitized_notes == (
        "missing_external_test_input",
        "no_connection_attempted",
    )


def test_connection_smoke_state_opt_in_with_placeholder_dsn_is_eligible() -> None:
    state = decide_postgresql_connection_smoke_state(
        opt_in_value="1",
        dsn_value="external-test-runner-input",
    )

    assert state.status == SMOKE_STATUS_ELIGIBLE
    assert state.opt_in_requested is True
    assert state.dsn_provided is True
    assert state.skip_reason is None
    assert state.sanitized_notes == (
        "explicit_opt_in_detected",
        "external_test_input_present",
        "connection_only_no_sql",
    )


def test_connection_smoke_state_does_not_expose_dsn_value() -> None:
    private_input = "private-runner-value-with-sensitive-details"

    state = decide_postgresql_connection_smoke_state(
        opt_in_value="1",
        dsn_value=private_input,
    )

    rendered = repr(state)
    assert private_input not in rendered
    assert state.skip_reason is None


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


@pytest.mark.postgresql_integration
def test_postgresql_opt_in_connection_open_close_smoke() -> None:
    dsn_value = os.getenv(POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR)
    state = decide_postgresql_connection_smoke_state(
        opt_in_value=os.getenv(POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR),
        dsn_value=dsn_value,
    )

    if state.status != SMOKE_STATUS_ELIGIBLE:
        pytest.skip(state.skip_reason or "PostgreSQL connection smoke skipped.")

    import psycopg

    connection = None
    try:
        connection = psycopg.connect(dsn_value)
    except Exception as exc:
        pytest.fail(
            "PostgreSQL connection smoke failed for the external opt-in test "
            f"input: {type(exc).__name__}",
        )
    finally:
        if connection is not None:
            connection.close()
