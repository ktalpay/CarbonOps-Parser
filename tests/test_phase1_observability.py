from __future__ import annotations

import json
import logging

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
