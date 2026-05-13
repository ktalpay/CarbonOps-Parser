from __future__ import annotations

import json
import logging

import pytest

from carbonfactor_parser.persistence.postgresql_options import (
    create_postgresql_persistence_options,
)
from carbonfactor_parser.persistence.postgresql_schema_bootstrap import (
    PostgreSQLSchemaBootstrapMode,
    build_postgresql_phase1_schema_bootstrap_report,
)
from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    get_required_table_names,
)
from carbonfactor_parser.source_acquisition.phase1_ingestion_orchestrator import (
    Phase1IngestionOrchestratorRequest,
    Phase1IngestionOrchestratorResult,
    Phase1IngestionRunStatus,
    Phase1IngestionRunSummary,
)
from carbonfactor_parser.source_acquisition.phase1_service_host import (
    Phase1ScheduledIngestionServiceHost,
    Phase1ScheduledRunStatus,
    Phase1ServiceHostConfig,
    Phase1ServiceHostStatus,
    validate_phase1_service_host_config,
)
from carbonfactor_parser.source_acquisition.phase1_observability import (
    PHASE1_OPERATIONAL_LOGGER_NAME,
    REDACTED,
)


def test_service_host_validates_required_postgresql_runtime_config() -> None:
    config = Phase1ServiceHostConfig(
        source_families=("ghg_protocol",),
        postgresql_options=create_postgresql_persistence_options(
            host="localhost",
            port=5432,
            database="carbonops",
            username="carbonops",
            password_set=False,
        ),
    )

    issues = validate_phase1_service_host_config(config)

    assert [issue.code for issue in issues] == [
        "PHASE1_SERVICE_HOST_POSTGRESQL_PASSWORD_NOT_CONFIRMED",
    ]
    assert issues[0].field_name == "postgresql_options.password_set"


def test_service_host_startup_checks_phase1_schema_before_ready() -> None:
    checker = _FakeSchemaBootstrapChecker(present=False)
    host = Phase1ScheduledIngestionServiceHost(
        _config(),
        schema_bootstrap_checker=checker,
        orchestrator_runner=_FakeOrchestratorRunner(),
    )

    result = host.start()

    assert result.status is Phase1ServiceHostStatus.BLOCKED
    assert host.status is Phase1ServiceHostStatus.BLOCKED
    assert checker.calls == (
        (PostgreSQLSchemaBootstrapMode.CHECK_ONLY, True),
    )
    assert result.schema_bootstrap_report is not None
    assert result.schema_bootstrap_report.missing_table_names
    assert result.issues[0].code == "PHASE1_SERVICE_HOST_POSTGRESQL_SCHEMA_NOT_READY"


def test_service_host_startup_logs_redacted_runtime_config(caplog) -> None:
    host = Phase1ScheduledIngestionServiceHost(
        _config(),
        schema_bootstrap_checker=_FakeSchemaBootstrapChecker(present=True),
        orchestrator_runner=_FakeOrchestratorRunner(),
    )

    with caplog.at_level(logging.INFO, logger=PHASE1_OPERATIONAL_LOGGER_NAME):
        host.start()

    starting = json.loads(caplog.records[0].message)

    assert starting["event"] == "phase1_service_host_starting"
    assert starting["postgresql_options"] == {
        "application_name": None,
        "connect_timeout_seconds": None,
        "database": REDACTED,
        "host": REDACTED,
        "password_set": True,
        "port": 5432,
        "ssl_mode": None,
        "username": REDACTED,
    }
    assert "localhost" not in caplog.records[0].message
    assert "carbonops" not in caplog.records[0].message


def test_scheduled_trigger_runs_orchestrator_for_selected_source_families() -> None:
    runner = _FakeOrchestratorRunner()
    host = Phase1ScheduledIngestionServiceHost(
        _config(source_families=("defra", "ipcc_efdb"), run_id_prefix="phase1-test"),
        schema_bootstrap_checker=_FakeSchemaBootstrapChecker(present=True),
        orchestrator_runner=runner,
    )

    startup = host.start()
    result = host.trigger_scheduled_run()

    assert startup.is_ready
    assert result.status is Phase1ScheduledRunStatus.STARTED
    assert result.run_id == "phase1-test-000001"
    assert runner.requests[0].source_families == ("defra", "ipcc_efdb")
    assert runner.requests[0].schema_bootstrap_report is not None
    assert runner.requests[0].schema_bootstrap_report.missing_table_names == ()
    assert result.orchestrator_result is not None
    assert result.orchestrator_result.status is Phase1IngestionRunStatus.COMPLETED
    assert host.status is Phase1ServiceHostStatus.READY


def test_scheduled_trigger_skips_overlapping_run() -> None:
    host_holder: dict[str, Phase1ScheduledIngestionServiceHost] = {}
    nested_result_holder = {}

    def runner(
        request: Phase1IngestionOrchestratorRequest,
    ) -> Phase1IngestionOrchestratorResult:
        nested_result_holder["result"] = host_holder["host"].trigger_scheduled_run()
        return _orchestrator_result(request)

    host = Phase1ScheduledIngestionServiceHost(
        _config(),
        schema_bootstrap_checker=_FakeSchemaBootstrapChecker(present=True),
        orchestrator_runner=runner,
    )
    host_holder["host"] = host

    host.start()
    result = host.trigger_scheduled_run()

    assert result.status is Phase1ScheduledRunStatus.STARTED
    nested_result = nested_result_holder["result"]
    assert nested_result.status is Phase1ScheduledRunStatus.SKIPPED_ALREADY_RUNNING
    assert nested_result.issues[0].code == (
        "PHASE1_SERVICE_HOST_RUN_ALREADY_IN_PROGRESS"
    )
    assert host.status is Phase1ServiceHostStatus.READY


def test_graceful_shutdown_blocks_new_runs_and_stops_after_active_run() -> None:
    host_holder: dict[str, Phase1ScheduledIngestionServiceHost] = {}
    nested_result_holder = {}

    def runner(
        request: Phase1IngestionOrchestratorRequest,
    ) -> Phase1IngestionOrchestratorResult:
        shutdown_status = host_holder["host"].request_shutdown()
        nested_result = host_holder["host"].trigger_scheduled_run()
        nested_result_holder["shutdown_status"] = shutdown_status
        nested_result_holder["result"] = nested_result
        return _orchestrator_result(request)

    host = Phase1ScheduledIngestionServiceHost(
        _config(),
        schema_bootstrap_checker=_FakeSchemaBootstrapChecker(present=True),
        orchestrator_runner=runner,
    )
    host_holder["host"] = host

    host.start()
    result = host.trigger_scheduled_run()
    after_shutdown_result = host.trigger_scheduled_run()

    assert result.status is Phase1ScheduledRunStatus.STARTED
    assert nested_result_holder["shutdown_status"] is (
        Phase1ServiceHostStatus.SHUTDOWN_REQUESTED
    )
    assert nested_result_holder["result"].status is (
        Phase1ScheduledRunStatus.SKIPPED_SHUTTING_DOWN
    )
    assert host.status is Phase1ServiceHostStatus.STOPPED
    assert after_shutdown_result.status is Phase1ScheduledRunStatus.SKIPPED_SHUTTING_DOWN


def test_scheduled_runner_error_releases_overlap_guard_and_returns_ready() -> None:
    failed_once = False

    def runner(
        request: Phase1IngestionOrchestratorRequest,
    ) -> Phase1IngestionOrchestratorResult:
        nonlocal failed_once
        if not failed_once:
            failed_once = True
            raise RuntimeError(f"boom: {request.run_id}")
        return _orchestrator_result(request)

    host = Phase1ScheduledIngestionServiceHost(
        _config(),
        schema_bootstrap_checker=_FakeSchemaBootstrapChecker(present=True),
        orchestrator_runner=runner,
    )

    host.start()
    with pytest.raises(RuntimeError, match="boom: phase1-scheduled-000001"):
        host.trigger_scheduled_run()

    assert host.status is Phase1ServiceHostStatus.READY
    follow_up = host.trigger_scheduled_run()
    assert follow_up.status is Phase1ScheduledRunStatus.STARTED
    assert follow_up.run_id == "phase1-scheduled-000002"


class _FakeSchemaBootstrapChecker:
    def __init__(self, *, present: bool) -> None:
        self.present = present
        self.calls: tuple[tuple[PostgreSQLSchemaBootstrapMode, bool], ...] = ()

    def __call__(
        self,
        mode: PostgreSQLSchemaBootstrapMode,
        fail_on_missing: bool,
    ):
        self.calls = (*self.calls, (mode, fail_on_missing))
        present_table_names = get_required_table_names() if self.present else ()
        return build_postgresql_phase1_schema_bootstrap_report(
            mode=mode,
            present_table_names=present_table_names,
            fail_on_missing=fail_on_missing,
        )


class _FakeOrchestratorRunner:
    def __init__(self) -> None:
        self.requests: tuple[Phase1IngestionOrchestratorRequest, ...] = ()

    def __call__(
        self,
        request: Phase1IngestionOrchestratorRequest,
    ) -> Phase1IngestionOrchestratorResult:
        self.requests = (*self.requests, request)
        return _orchestrator_result(request)


def _config(
    *,
    source_families: tuple[str, ...] = ("ghg_protocol",),
    run_id_prefix: str = "phase1-scheduled",
) -> Phase1ServiceHostConfig:
    return Phase1ServiceHostConfig(
        source_families=source_families,
        run_id_prefix=run_id_prefix,
        postgresql_options=create_postgresql_persistence_options(
            host="localhost",
            port=5432,
            database="carbonops",
            username="carbonops",
            password_set=True,
        ),
    )


def _orchestrator_result(
    request: Phase1IngestionOrchestratorRequest,
) -> Phase1IngestionOrchestratorResult:
    return Phase1IngestionOrchestratorResult(
        status=Phase1IngestionRunStatus.COMPLETED,
        request=request,
        selected_source_families=request.source_families,
        family_results=(),
        summary=Phase1IngestionRunSummary(
            requested_family_count=len(request.source_families),
            completed_family_count=len(request.source_families),
            failed_family_count=0,
            source_candidate_count=0,
            source_artifact_count=0,
            parser_run_count=0,
            parsed_factor_row_count=0,
            persisted_source_run_count=0,
            persisted_source_document_count=0,
            persisted_parser_run_count=0,
            persisted_master_count=0,
            persisted_detail_count=0,
            failure_count=0,
        ),
    )
