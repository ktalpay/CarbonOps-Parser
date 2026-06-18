"""Python service host boundary for scheduled Phase 1 ingestion."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from threading import Lock

from carbonfactor_parser.persistence.postgresql_options import (
    PostgreSQLPersistenceOptions,
    validate_postgresql_persistence_options,
)
from carbonfactor_parser.persistence.postgresql_runtime_config_gate import (
    PostgreSQLRuntimeConfigGateDecision,
)
from carbonfactor_parser.persistence.postgresql_schema_bootstrap import (
    PostgreSQLSchemaBootstrapMode,
    PostgreSQLSchemaBootstrapReport,
    build_postgresql_phase1_schema_bootstrap_report,
)
from carbonfactor_parser.source_acquisition.phase1_ingestion_orchestrator import (
    Phase1IngestionExecutionMode,
    Phase1IngestionOrchestratorRequest,
    Phase1IngestionOrchestratorResult,
)
from carbonfactor_parser.source_acquisition.phase1_observability import (
    emit_phase1_operational_event,
    summarize_phase1_orchestrator_result_for_diagnostics,
    summarize_postgresql_options_for_diagnostics,
)


_SOURCE_FAMILY_ALIASES = {
    "ghg",
    "ghg_protocol",
    "defra",
    "desnz",
    "defra_desnz",
    "ipcc",
    "ipcc_efdb",
}


class Phase1ServiceHostStatus(str, Enum):
    """Lifecycle status values for the service host boundary."""

    CREATED = "created"
    READY = "ready"
    BLOCKED = "blocked"
    RUNNING = "running"
    SHUTDOWN_REQUESTED = "shutdown_requested"
    STOPPED = "stopped"


class Phase1ScheduledRunStatus(str, Enum):
    """Scheduled run trigger status values."""

    STARTED = "started"
    SKIPPED_NOT_STARTED = "skipped_not_started"
    SKIPPED_ALREADY_RUNNING = "skipped_already_running"
    SKIPPED_SHUTTING_DOWN = "skipped_shutting_down"


@dataclass(frozen=True)
class Phase1ServiceHostConfig:
    """Required startup configuration for scheduled Phase 1 ingestion."""

    source_families: tuple[str, ...]
    postgresql_options: PostgreSQLPersistenceOptions
    run_id_prefix: str = "phase1-scheduled"
    schedule_interval_seconds: int = 3600
    execution_mode: Phase1IngestionExecutionMode = (
        Phase1IngestionExecutionMode.SEQUENTIAL
    )
    max_parallelism: int = 1
    schema_bootstrap_mode: PostgreSQLSchemaBootstrapMode = (
        PostgreSQLSchemaBootstrapMode.CHECK_ONLY
    )
    fail_on_missing_schema: bool = True
    runtime_config_decision: PostgreSQLRuntimeConfigGateDecision | None = None


@dataclass(frozen=True)
class Phase1ServiceHostIssue:
    """Validation or lifecycle issue reported by the service host."""

    code: str
    message: str
    field_name: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class Phase1ServiceHostStartupResult:
    """Startup validation and bootstrap check result."""

    status: Phase1ServiceHostStatus
    issues: tuple[Phase1ServiceHostIssue, ...]
    schema_bootstrap_report: PostgreSQLSchemaBootstrapReport | None = None

    @property
    def is_ready(self) -> bool:
        return self.status is Phase1ServiceHostStatus.READY


@dataclass(frozen=True)
class Phase1ScheduledRunResult:
    """Result of one scheduled trigger attempt."""

    status: Phase1ScheduledRunStatus
    run_id: str | None = None
    orchestrator_result: Phase1IngestionOrchestratorResult | None = None
    issues: tuple[Phase1ServiceHostIssue, ...] = ()


Phase1SchemaBootstrapChecker = Callable[
    [PostgreSQLSchemaBootstrapMode, bool],
    PostgreSQLSchemaBootstrapReport,
]
Phase1OrchestratorRunner = Callable[
    [Phase1IngestionOrchestratorRequest],
    Phase1IngestionOrchestratorResult,
]


class Phase1ScheduledIngestionServiceHost:
    """Synchronous service host boundary for scheduled Phase 1 runs."""

    def __init__(
        self,
        config: Phase1ServiceHostConfig,
        *,
        schema_bootstrap_checker: Phase1SchemaBootstrapChecker | None = None,
        orchestrator_runner: Phase1OrchestratorRunner,
    ) -> None:
        self.config = config
        self._schema_bootstrap_checker = (
            schema_bootstrap_checker or _default_schema_bootstrap_checker
        )
        self._orchestrator_runner = orchestrator_runner
        self._lock = Lock()
        self._status = Phase1ServiceHostStatus.CREATED
        self._startup_result: Phase1ServiceHostStartupResult | None = None
        self._schema_bootstrap_report: PostgreSQLSchemaBootstrapReport | None = None
        self._run_in_progress = False
        self._shutdown_requested = False
        self._run_sequence = 0

    @property
    def status(self) -> Phase1ServiceHostStatus:
        return self._status

    def start(self) -> Phase1ServiceHostStartupResult:
        """Validate config and check schema readiness before scheduled runs."""

        emit_phase1_operational_event(
            "phase1_service_host_starting",
            {
                "postgresql_options": summarize_postgresql_options_for_diagnostics(
                    self.config.postgresql_options,
                ),
                "run_id_prefix": self.config.run_id_prefix,
                "schedule_interval_seconds": self.config.schedule_interval_seconds,
                "source_families": self.config.source_families,
            },
        )
        issues = list(validate_phase1_service_host_config(self.config))
        schema_report = None
        if not issues:
            schema_report = self._schema_bootstrap_checker(
                self.config.schema_bootstrap_mode,
                self.config.fail_on_missing_schema,
            )
            issues.extend(_schema_bootstrap_issues(schema_report))

        status = (
            Phase1ServiceHostStatus.BLOCKED
            if issues
            else Phase1ServiceHostStatus.READY
        )
        result = Phase1ServiceHostStartupResult(
            status=status,
            issues=tuple(issues),
            schema_bootstrap_report=schema_report,
        )

        with self._lock:
            if self._shutdown_requested:
                self._status = Phase1ServiceHostStatus.STOPPED
                self._startup_result = Phase1ServiceHostStartupResult(
                    status=Phase1ServiceHostStatus.BLOCKED,
                    issues=(
                        Phase1ServiceHostIssue(
                            code="PHASE1_SERVICE_HOST_SHUTDOWN_REQUESTED",
                            message="Service host startup is blocked after shutdown.",
                            field_name="status",
                        ),
                    ),
                    schema_bootstrap_report=schema_report,
                )
                emit_phase1_operational_event(
                    "phase1_service_host_started",
                    _startup_diagnostic_payload(self._startup_result),
                )
                return self._startup_result

            self._status = status
            self._startup_result = result
            self._schema_bootstrap_report = schema_report

        emit_phase1_operational_event(
            "phase1_service_host_started",
            _startup_diagnostic_payload(result),
        )
        return result

    def trigger_scheduled_run(self) -> Phase1ScheduledRunResult:
        """Trigger one scheduled Phase 1 orchestrator run if host is ready."""

        with self._lock:
            if self._shutdown_requested:
                result = Phase1ScheduledRunResult(
                    status=Phase1ScheduledRunStatus.SKIPPED_SHUTTING_DOWN,
                    issues=(_shutdown_issue(),),
                )
                emit_phase1_operational_event(
                    "phase1_service_host_scheduled_run_skipped",
                    _scheduled_run_diagnostic_payload(result),
                )
                return result
            if self._run_in_progress:
                result = Phase1ScheduledRunResult(
                    status=Phase1ScheduledRunStatus.SKIPPED_ALREADY_RUNNING,
                    issues=(
                        Phase1ServiceHostIssue(
                            code="PHASE1_SERVICE_HOST_RUN_ALREADY_IN_PROGRESS",
                            message="Scheduled trigger skipped while a run is active.",
                            field_name="run_in_progress",
                        ),
                    ),
                )
                emit_phase1_operational_event(
                    "phase1_service_host_scheduled_run_skipped",
                    _scheduled_run_diagnostic_payload(result),
                )
                return result
            if self._status is not Phase1ServiceHostStatus.READY:
                result = Phase1ScheduledRunResult(
                    status=Phase1ScheduledRunStatus.SKIPPED_NOT_STARTED,
                    issues=(
                        Phase1ServiceHostIssue(
                            code="PHASE1_SERVICE_HOST_NOT_READY",
                            message="Service host must start successfully first.",
                            field_name="status",
                        ),
                    ),
                )
                emit_phase1_operational_event(
                    "phase1_service_host_scheduled_run_skipped",
                    _scheduled_run_diagnostic_payload(result),
                )
                return result

            self._run_in_progress = True
            self._status = Phase1ServiceHostStatus.RUNNING
            self._run_sequence += 1
            run_id = f"{self.config.run_id_prefix}-{self._run_sequence:06d}"
            request = self._build_orchestrator_request(run_id)

        emit_phase1_operational_event(
            "phase1_service_host_scheduled_run_started",
            {
                "correlation_id": request.correlation_id,
                "run_id": run_id,
                "source_families": request.source_families,
            },
        )
        try:
            orchestrator_result = self._orchestrator_runner(request)
        finally:
            with self._lock:
                self._run_in_progress = False
                self._status = (
                    Phase1ServiceHostStatus.STOPPED
                    if self._shutdown_requested
                    else Phase1ServiceHostStatus.READY
                )

        result = Phase1ScheduledRunResult(
            status=Phase1ScheduledRunStatus.STARTED,
            run_id=run_id,
            orchestrator_result=orchestrator_result,
        )
        emit_phase1_operational_event(
            "phase1_service_host_scheduled_run_completed",
            _scheduled_run_diagnostic_payload(result),
        )
        return result

    def request_shutdown(self) -> Phase1ServiceHostStatus:
        """Request graceful shutdown without interrupting an active run."""

        with self._lock:
            self._shutdown_requested = True
            if self._run_in_progress:
                self._status = Phase1ServiceHostStatus.SHUTDOWN_REQUESTED
            else:
                self._status = Phase1ServiceHostStatus.STOPPED
            return self._status

    def _build_orchestrator_request(
        self,
        run_id: str,
    ) -> Phase1IngestionOrchestratorRequest:
        return Phase1IngestionOrchestratorRequest(
            source_families=self.config.source_families,
            run_id=run_id,
            execution_mode=self.config.execution_mode,
            max_parallelism=self.config.max_parallelism,
            runtime_config_decision=self.config.runtime_config_decision,
            schema_bootstrap_report=self._schema_bootstrap_report,
        )


def validate_phase1_service_host_config(
    config: Phase1ServiceHostConfig,
) -> tuple[Phase1ServiceHostIssue, ...]:
    """Validate required service-host startup configuration."""

    issues: list[Phase1ServiceHostIssue] = []
    if not config.source_families:
        issues.append(
            Phase1ServiceHostIssue(
                code="PHASE1_SERVICE_HOST_MISSING_SOURCE_FAMILIES",
                message="At least one Phase 1 source family must be configured.",
                field_name="source_families",
            )
        )
    for index, source_family in enumerate(config.source_families):
        if source_family not in _SOURCE_FAMILY_ALIASES:
            issues.append(
                Phase1ServiceHostIssue(
                    code="PHASE1_SERVICE_HOST_UNSUPPORTED_SOURCE_FAMILY",
                    message="Configured source family must be a Phase 1 family.",
                    field_name=f"source_families[{index}]",
                )
            )

    if not config.run_id_prefix.strip():
        issues.append(
            Phase1ServiceHostIssue(
                code="PHASE1_SERVICE_HOST_MISSING_RUN_ID_PREFIX",
                message="run_id_prefix must be a non-empty string.",
                field_name="run_id_prefix",
            )
        )

    if (
        isinstance(config.schedule_interval_seconds, bool)
        or not isinstance(config.schedule_interval_seconds, int)
        or config.schedule_interval_seconds <= 0
    ):
        issues.append(
            Phase1ServiceHostIssue(
                code="PHASE1_SERVICE_HOST_INVALID_SCHEDULE_INTERVAL",
                message="schedule_interval_seconds must be a positive integer.",
                field_name="schedule_interval_seconds",
            )
        )

    if config.execution_mode is Phase1IngestionExecutionMode.SEQUENTIAL:
        if config.max_parallelism != 1:
            issues.append(
                Phase1ServiceHostIssue(
                    code="PHASE1_SERVICE_HOST_INVALID_SEQUENTIAL_PARALLELISM",
                    message="Sequential scheduled execution requires max_parallelism=1.",
                    field_name="max_parallelism",
                )
            )
    else:
        issues.append(
            Phase1ServiceHostIssue(
                code="PHASE1_SERVICE_HOST_UNSUPPORTED_EXECUTION_MODE",
                message="Only sequential scheduled execution is enabled.",
                field_name="execution_mode",
            )
        )

    options_result = validate_postgresql_persistence_options(
        config.postgresql_options,
    )
    for option_issue in options_result.issues:
        issues.append(
            Phase1ServiceHostIssue(
                code=option_issue.code,
                message=option_issue.message,
                field_name=f"postgresql_options.{option_issue.field_name}",
                severity=option_issue.severity,
            )
        )
    if not config.postgresql_options.password_set:
        issues.append(
            Phase1ServiceHostIssue(
                code="PHASE1_SERVICE_HOST_POSTGRESQL_PASSWORD_NOT_CONFIRMED",
                message=(
                    "postgresql_options.password_set must confirm that a "
                    "credential is available outside this config object."
                ),
                field_name="postgresql_options.password_set",
            )
        )

    return tuple(issues)


def _schema_bootstrap_issues(
    report: PostgreSQLSchemaBootstrapReport,
) -> tuple[Phase1ServiceHostIssue, ...]:
    if not report.fail_on_missing or not report.missing_table_names:
        return ()
    return (
        Phase1ServiceHostIssue(
            code="PHASE1_SERVICE_HOST_POSTGRESQL_SCHEMA_NOT_READY",
            message="Required Phase 1 PostgreSQL tables are missing.",
            field_name="schema_bootstrap_report.missing_table_names",
        ),
    )


def _default_schema_bootstrap_checker(
    mode: PostgreSQLSchemaBootstrapMode,
    fail_on_missing: bool,
) -> PostgreSQLSchemaBootstrapReport:
    return build_postgresql_phase1_schema_bootstrap_report(
        mode=mode,
        fail_on_missing=fail_on_missing,
    )


def _shutdown_issue() -> Phase1ServiceHostIssue:
    return Phase1ServiceHostIssue(
        code="PHASE1_SERVICE_HOST_SHUTTING_DOWN",
        message="Scheduled trigger skipped because shutdown was requested.",
        field_name="status",
    )


def _startup_diagnostic_payload(
    result: Phase1ServiceHostStartupResult,
) -> dict[str, object]:
    report = result.schema_bootstrap_report
    return {
        "issues": tuple(_service_host_issue_payload(issue) for issue in result.issues),
        "schema_bootstrap": {
            "fail_on_missing": getattr(report, "fail_on_missing", None),
            "missing_table_count": len(getattr(report, "missing_table_names", ())),
            "mode": getattr(getattr(report, "mode", None), "value", None),
            "status": getattr(getattr(report, "status", None), "value", None),
        },
        "status": result.status.value,
    }


def _scheduled_run_diagnostic_payload(
    result: Phase1ScheduledRunResult,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "issues": tuple(_service_host_issue_payload(issue) for issue in result.issues),
        "run_id": result.run_id,
        "status": result.status.value,
    }
    if result.orchestrator_result is not None:
        payload["orchestrator"] = summarize_phase1_orchestrator_result_for_diagnostics(
            result.orchestrator_result,
        )
    return payload


def _service_host_issue_payload(issue: Phase1ServiceHostIssue) -> dict[str, object]:
    return {
        "code": issue.code,
        "field_name": issue.field_name,
        "message": issue.message,
        "severity": issue.severity,
    }


__all__ = (
    "Phase1OrchestratorRunner",
    "Phase1ScheduledIngestionServiceHost",
    "Phase1ScheduledRunResult",
    "Phase1ScheduledRunStatus",
    "Phase1SchemaBootstrapChecker",
    "Phase1ServiceHostConfig",
    "Phase1ServiceHostIssue",
    "Phase1ServiceHostStartupResult",
    "Phase1ServiceHostStatus",
    "validate_phase1_service_host_config",
)
