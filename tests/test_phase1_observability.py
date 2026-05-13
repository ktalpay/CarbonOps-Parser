from __future__ import annotations

import json
import logging
from pathlib import Path

from carbonfactor_parser.persistence.postgresql_options import (
    create_postgresql_persistence_options,
)
from carbonfactor_parser.source_acquisition.phase1_observability import (
    PHASE1_OPERATIONAL_LOGGER_NAME,
    REDACTED,
    emit_phase1_operational_event,
    redact_diagnostic_value,
    summarize_postgresql_options_for_diagnostics,
)


PARITY_FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures/parity/phase1_operational_diagnostics_expectations.json"
)


def _parity_expectations() -> dict[str, object]:
    return json.loads(PARITY_FIXTURE_PATH.read_text(encoding="utf-8"))


def test_postgresql_options_diagnostics_redact_sensitive_runtime_values() -> None:
    options = create_postgresql_persistence_options(
        host="db.internal.example",
        port=5432,
        database="carbonops_prod",
        username="service_user",
        password_set=True,
        ssl_mode="require",
        application_name="carbonops-phase1",
        connect_timeout_seconds=10,
    )

    summary = summarize_postgresql_options_for_diagnostics(options)

    assert summary == {
        "application_name": REDACTED,
        "connect_timeout_seconds": 10,
        "database": REDACTED,
        "host": REDACTED,
        "password_set": True,
        "port": 5432,
        "ssl_mode": "require",
        "username": REDACTED,
    }


def test_redaction_removes_secret_fields_and_connection_userinfo() -> None:
    value = {
        "password": "super-secret",
        "nested": {
            "message": (
                "failed dsn=postgresql://svc:secret@db.internal/carbonops "
                "token=abc123"
            ),
        },
        "safe_count": 3,
    }

    redacted = redact_diagnostic_value("payload", value)

    assert redacted == {
        "nested": {
            "message": f"failed dsn={REDACTED} token={REDACTED}",
        },
        "password": REDACTED,
        "safe_count": 3,
    }


def test_operational_event_log_shape_is_stable_json(
    caplog,
) -> None:
    logger = logging.getLogger(PHASE1_OPERATIONAL_LOGGER_NAME)

    with caplog.at_level(logging.INFO, logger=PHASE1_OPERATIONAL_LOGGER_NAME):
        event = emit_phase1_operational_event(
            "phase1_test_event",
            {
                "z_count": 2,
                "a_context": {"source_family": "ghg_protocol"},
            },
            logger=logger,
        )

    assert event == {
        "a_context": {"source_family": "ghg_protocol"},
        "event": "phase1_test_event",
        "z_count": 2,
    }
    assert json.loads(caplog.records[-1].message) == event
    assert caplog.records[-1].message == (
        '{"a_context":{"source_family":"ghg_protocol"},'
        '"event":"phase1_test_event","z_count":2}'
    )


def test_phase1_operational_diagnostics_shared_parity_shape() -> None:
    expectations = _parity_expectations()

    assert expectations["request_keys"] == [
        "correlation_id",
        "execution_mode",
        "max_degree_of_parallelism",
        "run_id",
        "source_families",
    ]
    assert expectations["family_keys"] == [
        "correlation_id",
        "documents",
        "failures",
        "parser",
        "persistence",
        "run_id",
        "source_family",
        "source_key",
        "status",
    ]
    assert expectations["document_keys"] == [
        "checksum_sha256",
        "document_id",
        "source_family",
        "source_key",
    ]
    assert expectations["parser_keys"] == [
        "accepted_row_count",
        "failure_count",
        "result_status",
        "run_id",
        "validation_issue_count",
    ]
    assert expectations["failure_keys"] == [
        "code",
        "field_name",
        "message",
        "severity",
        "source_family",
        "source_key",
        "stage",
    ]
    assert expectations["summary_keys"] == [
        "completed_family_count",
        "failed_family_count",
        "failure_count",
        "parsed_factor_row_count",
        "parser_run_count",
        "persisted_detail_count",
        "persisted_master_count",
        "persisted_parser_run_count",
        "persisted_source_document_count",
        "persisted_source_run_count",
        "requested_family_count",
        "source_artifact_count",
        "source_candidate_count",
    ]
    assert expectations["orchestrator_event_names"] == [
        "phase1_ingestion_orchestrator_started",
        "phase1_source_family_completed",
        "phase1_ingestion_orchestrator_completed",
    ]
    assert expectations["service_host_event_names"] == [
        "phase1_service_host_starting",
        "phase1_service_host_started",
        "phase1_service_host_scheduled_run_started",
        "phase1_service_host_scheduled_run_completed",
        "phase1_service_host_scheduled_run_skipped",
    ]
    assert expectations["redacted"] == REDACTED
