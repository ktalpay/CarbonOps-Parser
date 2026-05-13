"""Tests for PostgreSQL runtime configuration gate metadata boundary."""

import builtins
import inspect
import os
import sqlite3
import urllib.request

import carbonfactor_parser.persistence.postgresql_runtime_config_gate as gate_module
from carbonfactor_parser.persistence import (
    PostgreSQLRuntimeConfigGate,
    PostgreSQLRuntimeConfigGateDecision,
    PostgreSQLRuntimeConfigGateDescription,
    PostgreSQLRuntimeConfigGateIssue,
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
    assert [issue.code for issue in decision.issues] == [
        "POSTGRESQL_RUNTIME_CONFIG_DISABLED_BY_DEFAULT",
    ]


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
    assert [issue.code for issue in decision.issues] == [
        "POSTGRESQL_RUNTIME_CONFIG_NOT_ENABLED",
    ]


def test_runtime_config_gate_status_values_are_stable_wire_names() -> None:
    assert [status.value for status in PostgreSQLRuntimeConfigGateStatus] == [
        "disabled",
        "blocked",
        "not_enabled",
    ]


def test_runtime_config_gate_decision_snapshots_collection_inputs() -> None:
    required_components = ["component"]
    notes = ["note"]
    issues = [PostgreSQLRuntimeConfigGateIssue("CODE", "message")]

    decision = PostgreSQLRuntimeConfigGateDecision(
        status=PostgreSQLRuntimeConfigGateStatus.BLOCKED,
        requested=True,
        reason="reason",
        config_loading_enabled=False,
        runtime_enabled=False,
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
        required_future_components=required_components,
        safe_operational_notes=notes,
        issues=issues,
    )
    required_components.clear()
    notes.clear()
    issues.clear()

    assert decision.required_future_components == ("component",)
    assert decision.safe_operational_notes == ("note",)
    assert [issue.code for issue in decision.issues] == ["CODE"]


def test_runtime_config_gate_description_snapshots_notes() -> None:
    notes = ["note"]

    description = PostgreSQLRuntimeConfigGateDescription(
        default_status=PostgreSQLRuntimeConfigGateStatus.DISABLED,
        disabled_by_default=True,
        accepts_caller_intent=True,
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
        opens_connection=False,
        runs_sql=False,
        notes=notes,
    )
    notes.clear()

    assert description.notes == ("note",)


def test_runtime_config_gate_has_no_external_side_effects(monkeypatch) -> None:
    def fail_side_effect(*args, **kwargs):
        raise AssertionError("runtime config gate must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(os, "getenv", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    decision = evaluate_postgresql_runtime_config_gate(
        PostgreSQLRuntimeConfigGate(requested=True),
    )

    assert decision.config_loading_enabled is False
    assert decision.runtime_enabled is False
    assert decision.loads_environment is False
    assert decision.loads_config_files is False
    assert decision.loads_credentials is False


def test_runtime_config_gate_module_has_no_driver_or_runtime_calls() -> None:
    source = inspect.getsource(gate_module)
    lower_source = source.lower()

    assert "import psycopg" not in source
    assert "from psycopg" not in source
    assert "asyncpg" not in lower_source
    assert "sqlalchemy" not in lower_source
    assert "create_engine" not in source
    assert "psycopg.connect" not in source
    assert "connect(" not in source
    assert "cursor(" not in source
    assert "execute(" not in source
    assert "commit(" not in source
    assert "rollback(" not in source
    assert "begin(" not in source
    assert "os.environ" not in source
    assert "getenv" not in source
