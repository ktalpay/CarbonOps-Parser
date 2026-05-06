from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pytest

from carbonfactor_parser.persistence import (
    PersistenceInput,
    PersistenceResultStatus,
    PostgreSQLPersistenceRepository,
    POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR,
    POSTGRESQL_INTEGRATION_TEST_MARKER,
    POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RUNBOOK_PATH = REPOSITORY_ROOT / "docs" / "postgresql-opt-in-integration-runbook.md"
THIS_TEST_PATH = Path(__file__).resolve()

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


def test_connection_smoke_state_uses_canonical_marker_and_controls() -> None:
    state = decide_postgresql_connection_smoke_state(
        opt_in_value=None,
        dsn_value=None,
    )

    assert state.marker_name == POSTGRESQL_INTEGRATION_TEST_MARKER
    assert state.opt_in_control_name == POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR
    assert state.test_dsn_input_name == POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR


def test_default_environment_keeps_connection_smoke_skipped(monkeypatch) -> None:
    monkeypatch.delenv(POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR, raising=False)
    monkeypatch.delenv(POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR, raising=False)

    state = decide_postgresql_connection_smoke_state(
        opt_in_value=os.getenv(POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR),
        dsn_value=os.getenv(POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR),
    )

    assert state.status == SMOKE_STATUS_DISABLED
    assert state.skip_reason is not None
    assert "disabled by default" in state.skip_reason
    assert "no_connection_attempted" in state.sanitized_notes


def test_runbook_documents_connection_smoke_controls_and_default_behavior() -> None:
    runbook_text = RUNBOOK_PATH.read_text(encoding="utf-8")
    normalized_runbook_text = " ".join(runbook_text.split())

    assert POSTGRESQL_INTEGRATION_TEST_MARKER in runbook_text
    assert POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR in runbook_text
    assert POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR in runbook_text
    assert "default test suite remains DB-free" in runbook_text
    assert "connection smoke skipped" in runbook_text
    assert "does not execute SQL" in runbook_text
    assert "does not write records" in runbook_text
    assert (
        "must not log DSNs, credentials, or secret values"
        in normalized_runbook_text
    )


def test_runbook_documents_manual_connection_smoke_checklist() -> None:
    runbook_text = RUNBOOK_PATH.read_text(encoding="utf-8")
    normalized_runbook_text = " ".join(runbook_text.split())

    assert "## Manual Connection Smoke Checklist" in runbook_text
    assert "git status --short" in runbook_text
    assert "python -m pytest" in runbook_text
    assert "<local-test-database>" in runbook_text
    assert "<local-test-role>" in runbook_text
    assert POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR in runbook_text
    assert POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR in runbook_text
    assert (
        "python -m pytest -m postgresql_integration "
        "tests/test_postgresql_connection_smoke_boundary.py"
    ) in normalized_runbook_text
    assert "The smoke performs no SQL execution." in runbook_text
    assert "The smoke performs no DB writes." in runbook_text
    assert "The smoke performs no migrations or table creation." in runbook_text
    assert "Repository persistence remains disabled/no-execution." in runbook_text
    assert "unset CARBONOPS_RUN_POSTGRESQL_INTEGRATION" in runbook_text
    assert "unset CARBONOPS_POSTGRESQL_TEST_DSN" in runbook_text


def test_runbook_documents_manual_connection_smoke_execution_record() -> None:
    runbook_text = RUNBOOK_PATH.read_text(encoding="utf-8")
    normalized_runbook_text = " ".join(runbook_text.split())

    assert "## Manual Connection Smoke Execution Record" in runbook_text
    assert "`not_run`" in runbook_text
    assert "`blocked_missing_local_postgresql`" in runbook_text
    assert "`blocked_missing_dsn`" in runbook_text
    assert "`passed`" in runbook_text
    assert "`failed_sanitized`" in runbook_text
    assert "status: `passed`" in runbook_text
    assert "<manual-run-timestamp-redacted>" in runbook_text
    assert "Docker-based local PostgreSQL container." in runbook_text
    assert "`postgres:16`" in runbook_text
    assert "PostgreSQL 16.11" in runbook_text
    assert "`carbonops-postgres-test`" in runbook_text
    assert "<redacted-test-database>" in runbook_text
    assert "database system was ready to accept connections" in normalized_runbook_text
    assert "manual `psql --version` smoke succeeded" in runbook_text
    assert "opt-in smoke result: 1 passed, 15 deselected." in runbook_text
    assert POSTGRESQL_INTEGRATION_TEST_MARKER in runbook_text
    assert POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR in runbook_text
    assert POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR in runbook_text
    assert (
        "python -m pytest -m postgresql_integration "
        "tests/test_postgresql_connection_smoke_boundary.py"
    ) in normalized_runbook_text
    assert "sanitized Docker-based manual run evidence" in normalized_runbook_text
    assert "The project opt-in smoke performed no SQL execution." in runbook_text
    assert "The project opt-in smoke performed no DB writes." in runbook_text
    assert "Repository persistence remained disabled/no-execution." in runbook_text
    assert "The default test suite remains DB-free." in runbook_text
    assert "`project.version`" in runbook_text
    assert "`psycopg>=3,<4`" in runbook_text
    assert "libpq or binary wrapper" in runbook_text
    assert "`psycopg[binary]>=3,<4`" in runbook_text
    assert "metadata in CO-103K" in runbook_text
    assert "libpq/binary packaging decision remains deferred" in runbook_text
    assert "DSN redacted." in runbook_text
    assert "Password redacted." in runbook_text
    assert "No secrets in logs" in runbook_text
    assert "Post-run cleanup checklist" in runbook_text
    assert "Unset `CARBONOPS_RUN_POSTGRESQL_INTEGRATION`." in runbook_text
    assert "Unset `CARBONOPS_POSTGRESQL_TEST_DSN`." in runbook_text
    assert "Confirm default `python -m pytest` still remains DB-free." in runbook_text
    assert "do not record a passed result" in normalized_runbook_text


def test_runbook_manual_connection_smoke_execution_record_has_one_current_status() -> None:
    runbook_text = RUNBOOK_PATH.read_text(encoding="utf-8")
    current_record = runbook_text.split("Current execution record:", maxsplit=1)[1]
    current_record = current_record.split("```bash", maxsplit=1)[0]

    status_lines = [
        line.strip()
        for line in current_record.splitlines()
        if line.strip().startswith("- status:")
    ]
    allowed_statuses = {
        "`not_run`",
        "`blocked_missing_local_postgresql`",
        "`blocked_missing_dsn`",
        "`passed`",
        "`failed_sanitized`",
    }

    assert status_lines == ["- status: `passed`"]
    current_status = status_lines[0].removeprefix("- status: ").strip()
    assert current_status in allowed_statuses
    assert current_status == "`passed`"
    assert "opt-in smoke result: 1 passed, 15 deselected." in current_record
    assert "postgresql" + "://" not in current_record
    assert "pass" + "word=" not in current_record


def test_runbook_successful_smoke_record_captures_deferred_packaging_issues() -> None:
    runbook_text = RUNBOOK_PATH.read_text(encoding="utf-8")
    current_record = runbook_text.split("Current execution record:", maxsplit=1)[1]
    current_record = current_record.split(
        "## Local PostgreSQL Setup Checklist",
        maxsplit=1,
    )[0]

    assert "Deferred local setup issues:" in current_record
    assert "editable-install metadata blocker" in current_record
    assert "`project.name`" in current_record
    assert "`project.version`" in current_record
    assert "metadata in CO-103K" in current_record
    assert "`psycopg>=3,<4` local import path failed" in current_record
    assert "libpq or binary wrapper" in current_record
    assert "`psycopg[binary]>=3,<4`" in current_record
    assert "libpq/binary packaging decision remains deferred" in current_record


def test_runbook_documents_local_postgresql_setup_checklist() -> None:
    runbook_text = RUNBOOK_PATH.read_text(encoding="utf-8")
    normalized_runbook_text = " ".join(runbook_text.split())

    assert "## Local PostgreSQL Setup Checklist" in runbook_text
    assert "brew install postgresql@<major-version>" in runbook_text
    assert "brew services status postgresql@<major-version>" in runbook_text
    assert "brew services start postgresql@<major-version>" in runbook_text
    assert "brew services stop postgresql@<major-version>" in runbook_text
    assert "<local-test-database>" in runbook_text
    assert "<local-test-role>" in runbook_text
    assert "<local-host>" in runbook_text
    assert "<local-port>" in runbook_text
    assert "<external-local-test-credential>" in runbook_text
    assert "createdb <local-test-database>" in runbook_text
    assert "createuser <local-test-role>" in runbook_text
    assert "CARBONOPS_POSTGRESQL_TEST_DSN" in runbook_text
    assert "Do not commit the DSN or credentials." in runbook_text
    assert "Do not paste a DSN with a password or credential" in runbook_text
    assert "default `python -m pytest` remains DB-free" in runbook_text
    assert "local setup alone does not enable repository persistence" in runbook_text
    assert "PostgreSQLPersistenceRepository.persist()" in normalized_runbook_text
    assert "remains unsupported/no-execution" in normalized_runbook_text
    assert "[Manual Connection Smoke Checklist]" in runbook_text
    assert "dropdb --if-exists <local-test-database>" in runbook_text
    assert "dropuser --if-exists <local-test-role>" in runbook_text
    assert "does not add project code execution" in normalized_runbook_text


def test_runbook_documents_system_level_postgresql_install_smoke() -> None:
    runbook_text = RUNBOOK_PATH.read_text(encoding="utf-8")
    normalized_runbook_text = " ".join(runbook_text.split())

    assert "## System-Level PostgreSQL Install Smoke" in runbook_text
    assert "external manual shell checks" in runbook_text
    assert "not executed by project code" in normalized_runbook_text
    assert "not part of default `python -m pytest`" in normalized_runbook_text
    assert "do not enable repository persistence" in normalized_runbook_text
    assert "brew services status postgresql@<major-version>" in runbook_text
    assert "psql --version" in runbook_text
    assert "psql -lqt | grep '<local-test-database>'" in runbook_text
    assert "psql -c \"\\\\du\" | grep '<local-test-role>'" in runbook_text
    assert "psql '<external test DSN supplied by the runner>'" in runbook_text
    assert "Keep these commands separate from project test commands." in runbook_text
    assert "python -m pytest" in runbook_text
    assert POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR in runbook_text
    assert POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR in runbook_text
    assert (
        "Project library behavior remains unchanged: library code does not "
        "create PostgreSQL connections, execute SQL, create tables, run "
        "migrations, write records, load credentials, or enable repository "
        "persistence."
    ) in normalized_runbook_text
    assert "must be redacted from logs, issues, PRs" in normalized_runbook_text


def test_runbook_manual_checklist_uses_placeholders_without_real_secret_values() -> None:
    runbook_text = RUNBOOK_PATH.read_text(encoding="utf-8")

    forbidden_fragments = (
        "postgresql" + "://",
        "pass" + "word=",
        "pass" + "word:",
        "secret" + "=",
        "token" + "=",
    )

    for fragment in forbidden_fragments:
        assert fragment not in runbook_text


def test_connection_smoke_test_source_has_no_write_sql_or_schema_terms() -> None:
    module_source = THIS_TEST_PATH.read_text(encoding="utf-8")

    forbidden_terms = (
        "IN" + "SERT",
        "UP" + "DATE",
        "DE" + "LETE",
        "CREATE " + "TABLE",
        "DROP " + "TABLE",
    )

    for term in forbidden_terms:
        assert term not in module_source


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
