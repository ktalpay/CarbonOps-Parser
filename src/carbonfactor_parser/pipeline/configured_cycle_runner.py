"""Configured PostgreSQL-backed ingestion cycle runner.

The runner is the application/runtime layer over the existing year
orchestrator. It loads explicit local configuration, starts PostgreSQL, creates
missing Phase 1 tables, and repeatedly runs the configured source families.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import time
import uuid
from typing import Callable

from carbonfactor_parser.diagnostics.redaction import redact_sensitive_text

from carbonfactor_parser.persistence.ingestion_run_history import (
    ParserIngestionRunHistoryRepository,
)
from carbonfactor_parser.persistence.postgresql_ingestion_run_history_repository import (
    PostgreSQLIngestionRunHistoryRepository,
)
from carbonfactor_parser.persistence.postgresql_runtime import (
    PostgreSQLRuntimeStartupResult,
    start_postgresql_runtime,
)
from carbonfactor_parser.pipeline.configured_cycle_config import (
    CONFIGURED_CYCLE_SOURCE_FAMILIES,
    ConfiguredCycleRunnerConfig,
    ConfiguredSourceYearArtifact,
    load_configured_cycle_runner_config,
)
from carbonfactor_parser.pipeline.configured_cycle_dependencies import (
    ConfiguredCycleValidationBoundary,
    build_configured_cycle_dependencies,
)
from carbonfactor_parser.pipeline.configured_cycle_history import (
    persist_configured_cycle_history,
)
from carbonfactor_parser.pipeline.configured_cycle_models import (
    ConfiguredCycleResult,
    ConfiguredCycleRunnerResult,
)
from carbonfactor_parser.pipeline.configured_cycle_summary import (
    emit_configured_cycle_summary,
)
from carbonfactor_parser.pipeline.production_e2e_year_orchestrator import (
    ProductionE2EYearOrchestratorRequest,
    ProductionE2EYearRunStatus,
    run_production_e2e_year_orchestrator,
)


class ConfiguredCycleRunnerStatus(str, Enum):
    """Top-level configured cycle runner status."""

    COMPLETED = "completed"
    COMPLETED_WITH_FAILURES = "completed_with_failures"


def run_configured_cycle_runner(
    config: ConfiguredCycleRunnerConfig,
    *,
    startup: PostgreSQLRuntimeStartupResult | None = None,
    sleep: Callable[[float], None] = time.sleep,
    emit: Callable[[str], None] | None = print,
    run_history_repository: ParserIngestionRunHistoryRepository | None = None,
    run_history_repository_factory: (
        Callable[[object], ParserIngestionRunHistoryRepository] | None
    ) = None,
) -> ConfiguredCycleRunnerResult:
    """Start PostgreSQL runtime and execute configured ingestion cycles."""

    runtime = startup or start_postgresql_runtime(config.postgresql_config_result)
    if emit is not None:
        _emit_startup_summary(config, runtime, emit)

    dependencies = build_configured_cycle_dependencies(config, runtime)
    history_repository = run_history_repository
    if history_repository is None:
        history_repository_factory = (
            run_history_repository_factory or PostgreSQLIngestionRunHistoryRepository
        )
        history_repository = history_repository_factory(runtime.connection)
    cycles: list[ConfiguredCycleResult] = []
    cycle_number = 1
    while config.max_cycles is None or cycle_number <= config.max_cycles:
        run_id = f"configured-cycle-{cycle_number}-{uuid.uuid4().hex}"
        started_at = datetime.now(timezone.utc)
        result = run_production_e2e_year_orchestrator(
            ProductionE2EYearOrchestratorRequest(
                run_id=run_id,
                enabled_source_families=config.enabled_source_families,
                initial_year=config.initial_year,
            ),
            dependencies,
        )
        finished_at = datetime.now(timezone.utc)
        cycle = ConfiguredCycleResult(
            cycle_number=cycle_number,
            run_id=run_id,
            result=result,
        )
        if emit is not None:
            emit_configured_cycle_summary(cycle, emit=emit)
        cycle = persist_configured_cycle_history(
            cycle,
            history_repository=history_repository,
            started_at=started_at,
            finished_at=finished_at,
            emit=emit,
        )
        cycles.append(cycle)

        cycle_number += 1
        if config.max_cycles is not None and cycle_number > config.max_cycles:
            break
        if config.cycle_interval_seconds > 0:
            sleep(config.cycle_interval_seconds)

    failed = any(
        cycle.result.status is not ProductionE2EYearRunStatus.COMPLETED
        for cycle in cycles
    )
    return ConfiguredCycleRunnerResult(
        status=(
            ConfiguredCycleRunnerStatus.COMPLETED_WITH_FAILURES
            if failed
            else ConfiguredCycleRunnerStatus.COMPLETED
        ),
        cycles=tuple(cycles),
        schema_created_table_names=runtime.schema_bootstrap.created_table_names,
        schema_missing_table_names=runtime.schema_bootstrap.missing_table_names,
    )


def _emit_startup_summary(
    config: ConfiguredCycleRunnerConfig,
    runtime: PostgreSQLRuntimeStartupResult,
    emit: Callable[[str], None],
) -> None:
    emit("carbonops ingestion application started")
    emit(f"archive_root={config.archive_root}")
    emit(f"enabled_source_families={','.join(config.enabled_source_families)}")
    emit(f"initial_year={config.initial_year}")
    emit(f"cycle_interval_seconds={config.cycle_interval_seconds:g}")
    emit(f"max_cycles={config.max_cycles}")
    emit(f"allow_live_source_access={config.allow_live_source_access}")
    emit(
        "postgresql_schema "
        f"created={','.join(runtime.schema_bootstrap.created_table_names) or 'none'} "
        f"missing={','.join(runtime.schema_bootstrap.missing_table_names) or 'none'}"
    )


def _redact_sensitive_text(text: str) -> str:
    return redact_sensitive_text(text)


__all__ = (
    "CONFIGURED_CYCLE_SOURCE_FAMILIES",
    "ConfiguredCycleResult",
    "ConfiguredCycleRunnerConfig",
    "ConfiguredCycleRunnerResult",
    "ConfiguredCycleRunnerStatus",
    "ConfiguredCycleValidationBoundary",
    "ConfiguredSourceYearArtifact",
    "emit_configured_cycle_summary",
    "load_configured_cycle_runner_config",
    "run_configured_cycle_runner",
)
