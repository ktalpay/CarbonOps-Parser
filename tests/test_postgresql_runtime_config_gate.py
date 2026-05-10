"""Tests for PostgreSQL runtime configuration gate metadata boundary."""

from carbonfactor_parser.persistence import (
    PostgreSQLRuntimeConfigGate,
    PostgreSQLRuntimeConfigGateStatus,
    describe_postgresql_runtime_config_gate,
    evaluate_postgresql_runtime_config_gate,
)


def test_runtime_config_gate_description_is_side_effect_free() -> None:
    description = describe_postgresql_runtime_config_gate()

    assert description.default_status is PostgreSQLRuntimeConfigGateStatus.DISABLED
    assert description.disabled_by_default is True
    assert description.accepts_caller_intent is True
    assert description.loads_environment is False
    assert description.loads_config_files is False
    assert description.loads_credentials is False
    assert description.opens_connection is False
    assert description.runs_sql is False


def test_runtime_config_gate_defaults_to_disabled() -> None:
    decision = evaluate_postgresql_runtime_config_gate()

    assert decision.status is PostgreSQLRuntimeConfigGateStatus.DISABLED
    assert decision.requested is False
    assert decision.config_loading_enabled is False
    assert decision.runtime_enabled is False
    assert decision.loads_environment is False
    assert decision.loads_config_files is False
    assert decision.loads_credentials is False
    assert decision.required_future_components == (
        "postgresql_implementation_safety_gate",
        "postgresql_persistence_options_contract",
        "explicit_runtime_configuration_opt_in",
        "approved_secret_source",
    )


def test_runtime_config_gate_returns_blocked_when_requested_but_incomplete() -> None:
    decision = evaluate_postgresql_runtime_config_gate(
        PostgreSQLRuntimeConfigGate(
            requested=True,
            safety_gate_approved=True,
            options_contract_available=False,
            explicit_runtime_opt_in=True,
            secret_source_approved=False,
        )
    )

    assert decision.status is PostgreSQLRuntimeConfigGateStatus.BLOCKED
    assert decision.required_future_components == (
        "postgresql_persistence_options_contract",
        "approved_secret_source",
    )


def test_runtime_config_gate_reports_not_enabled_even_when_metadata_ready() -> None:
    decision = evaluate_postgresql_runtime_config_gate(
        PostgreSQLRuntimeConfigGate(
            requested=True,
            safety_gate_approved=True,
            options_contract_available=True,
            explicit_runtime_opt_in=True,
            secret_source_approved=True,
        )
    )

    assert decision.status is PostgreSQLRuntimeConfigGateStatus.NOT_ENABLED
    assert decision.required_future_components == ()
    assert decision.config_loading_enabled is False
    assert decision.runtime_enabled is False
