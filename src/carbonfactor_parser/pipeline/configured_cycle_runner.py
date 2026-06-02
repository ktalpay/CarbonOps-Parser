"""Configured PostgreSQL-backed ingestion cycle runner.

The runner is the application/runtime layer over the existing year
orchestrator. It loads explicit local configuration, starts PostgreSQL, creates
missing Phase 1 tables, and repeatedly runs the configured source families.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import time
import uuid
from typing import Callable, Mapping

from carbonfactor_parser.diagnostics.redaction import redact_sensitive_text

from carbonfactor_parser.persistence.ingestion_run_history import (
    ParserIngestionRunHistoryRepository,
    ParserIngestionRunHistoryStatus,
)
from carbonfactor_parser.persistence.ingestion_run_history_mapping import (
    build_ingestion_run_history_command_from_configured_cycle,
)
from carbonfactor_parser.persistence.postgresql_ingestion_run_history_repository import (
    PostgreSQLIngestionRunHistoryRepository,
)
from carbonfactor_parser.persistence.postgresql_runtime import (
    PostgreSQLRuntimeStartupResult,
    start_postgresql_runtime,
)
from carbonfactor_parser.persistence.postgresql_source_family_repository import (
    PostgreSQLSourceFamilyRuntimeRepository,
)
from carbonfactor_parser.pipeline.configured_cycle_config import (
    CONFIGURED_CYCLE_SOURCE_FAMILIES,
    ConfiguredCycleRunnerConfig,
    ConfiguredSourceYearArtifact,
    load_configured_cycle_runner_config,
)
from carbonfactor_parser.pipeline.defra_desnz_production_e2e import (
    DEFRA_DESNZ_SOURCE_FAMILY,
    DefraDesnzPhase2ValidationBoundary,
    DefraDesnzProductionParserBoundary,
    DefraDesnzProductionSourceAdapter,
    DefraDesnzSourceYear,
)
from carbonfactor_parser.pipeline.ghg_protocol_production_e2e import (
    GHG_PROTOCOL_SOURCE_FAMILY,
    GHGProtocolPhase2ValidationBoundary,
    GHGProtocolProductionParserBoundary,
    GHGProtocolProductionSourceAdapter,
    GHGProtocolSourceYear,
)
from carbonfactor_parser.pipeline.ipcc_efdb_production_e2e import (
    IPCC_EFDB_SOURCE_FAMILY,
    IpccEfdbPhase2ValidationBoundary,
    IpccEfdbProductionParserBoundary,
    IpccEfdbProductionSourceAdapter,
    IpccEfdbSourceYear,
)
from carbonfactor_parser.pipeline.production_e2e_year_orchestrator import (
    ProductionE2EValidationResult,
    ProductionE2EYearOrchestratorDependencies,
    ProductionE2EYearOrchestratorRequest,
    ProductionE2EYearOrchestratorResult,
    ProductionE2EYearRunStatus,
    run_production_e2e_year_orchestrator,
)
from carbonfactor_parser.pipeline.source_artifact_transport import (
    build_configured_artifact_transport,
)


class ConfiguredCycleRunnerStatus(str, Enum):
    """Top-level configured cycle runner status."""

    COMPLETED = "completed"
    COMPLETED_WITH_FAILURES = "completed_with_failures"


@dataclass(frozen=True)
class ConfiguredCycleResult:
    """One completed application cycle."""

    cycle_number: int
    run_id: str
    result: ProductionE2EYearOrchestratorResult
    history_persistence_status: str | None = None
    history_persistence_issue_count: int = 0


@dataclass(frozen=True)
class ConfiguredCycleRunnerResult:
    """All cycles run by one application invocation."""

    status: ConfiguredCycleRunnerStatus
    cycles: tuple[ConfiguredCycleResult, ...]
    schema_created_table_names: tuple[str, ...]
    schema_missing_table_names: tuple[str, ...]


class ConfiguredCycleValidationBoundary:
    """Route validation to the source-family-specific validation boundary."""

    def __init__(self) -> None:
        self._boundaries = {
            GHG_PROTOCOL_SOURCE_FAMILY: GHGProtocolPhase2ValidationBoundary(),
            DEFRA_DESNZ_SOURCE_FAMILY: DefraDesnzPhase2ValidationBoundary(),
            IPCC_EFDB_SOURCE_FAMILY: IpccEfdbPhase2ValidationBoundary(),
        }

    def validate(self, batch: object) -> ProductionE2EValidationResult:
        rows = tuple(getattr(batch, "rows", ()))
        source_family = rows[0].source_family if rows else GHG_PROTOCOL_SOURCE_FAMILY
        boundary = self._boundaries.get(source_family)
        if boundary is None:
            boundary = GHGProtocolPhase2ValidationBoundary()
        return boundary.validate(batch)


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

    dependencies = _build_dependencies(config, runtime)
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
        cycle = _persist_configured_cycle_history(
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



def _persist_configured_cycle_history(
    cycle: ConfiguredCycleResult,
    *,
    history_repository: ParserIngestionRunHistoryRepository,
    started_at: datetime,
    finished_at: datetime,
    emit: Callable[[str], None] | None,
) -> ConfiguredCycleResult:
    command = build_ingestion_run_history_command_from_configured_cycle(
        cycle,
        started_at=started_at,
        finished_at=finished_at,
    )
    try:
        persist_result = history_repository.persist_ingestion_run_history(command)
    except Exception as exc:  # pragma: no cover - defensive boundary protection
        safe_message = _redact_sensitive_text(str(exc))
        if emit is not None:
            emit(
                "history_persistence "
                f"status=failed run_id={cycle.run_id} "
                "issue code=INGESTION_RUN_HISTORY_PERSISTENCE_EXCEPTION "
                f"message={safe_message}"
            )
        return ConfiguredCycleResult(
            cycle_number=cycle.cycle_number,
            run_id=cycle.run_id,
            result=cycle.result,
            history_persistence_status="failed",
            history_persistence_issue_count=1,
        )

    issue_count = len(persist_result.issues)
    if persist_result.status is ParserIngestionRunHistoryStatus.DECLARED:
        if emit is not None:
            emit(f"history_persistence status=declared run_id={cycle.run_id}")
    else:
        if emit is not None:
            for issue in persist_result.issues or ():
                safe_message = _redact_sensitive_text(str(issue.message))
                emit(
                    "history_persistence "
                    f"status=failed run_id={cycle.run_id} "
                    f"issue code={issue.code} message={safe_message}"
                )
            if not persist_result.issues:
                emit(
                    "history_persistence "
                    f"status=failed run_id={cycle.run_id} "
                    "issue code=INGESTION_RUN_HISTORY_PERSISTENCE_FAILED "
                    "message=run history persistence failed"
                )
                issue_count = 1
    return ConfiguredCycleResult(
        cycle_number=cycle.cycle_number,
        run_id=cycle.run_id,
        result=cycle.result,
        history_persistence_status=(
            "declared"
            if persist_result.status is ParserIngestionRunHistoryStatus.DECLARED
            else "failed"
        ),
        history_persistence_issue_count=issue_count,
    )

def emit_configured_cycle_summary(
    cycle: ConfiguredCycleResult,
    *,
    emit: Callable[[str], None] = print,
) -> None:
    """Print user-readable summary output for one cycle."""

    summary = cycle.result.summary
    emit(
        "cycle="
        f"{cycle.cycle_number} run_id={cycle.run_id} status={cycle.result.status.value}"
    )
    emit(
        "summary "
        f"completed={summary.completed_family_count} "
        f"no_available_source_year={summary.no_available_source_year_count} "
        f"failed={summary.failed_family_count} "
        f"parsed_rows={summary.parsed_row_count} "
        f"inserted={summary.inserted_count} "
        f"skipped_duplicates={summary.skipped_duplicate_count}"
    )
    for family in cycle.result.family_results:
        insert_summary = family.insert_summary
        emit(
            "source "
            f"family={family.source_family} "
            f"target_year={family.year_state.target_year} "
            f"latest_year={family.year_state.latest_year} "
            f"status={family.status.value} "
            f"download_status={_download_status_value(family.download_result)} "
            f"parse_status={_parse_status_value(family)} "
            f"parsed_rows={family.parsed_row_count} "
            f"master_inserted={getattr(insert_summary, 'master_inserted', 0)} "
            f"master_skipped={getattr(insert_summary, 'master_skipped', 0)} "
            f"detail_inserted={getattr(insert_summary, 'detail_inserted', 0)} "
            f"detail_skipped={getattr(insert_summary, 'detail_skipped', 0)}"
        )
        for failure in family.failures:
            safe_message = _redact_sensitive_text(str(failure.message))
            emit(
                "issue "
                f"family={failure.source_family} stage={failure.stage} "
                f"code={failure.code} message={safe_message}"
            )


def _build_dependencies(
    config: ConfiguredCycleRunnerConfig,
    runtime: PostgreSQLRuntimeStartupResult,
) -> ProductionE2EYearOrchestratorDependencies:
    transport = build_configured_artifact_transport(
        allow_live_source_access=config.allow_live_source_access,
    )
    source_years = config.source_years or {}
    return ProductionE2EYearOrchestratorDependencies(
        year_state_repository=runtime.year_state_repository,
        source_adapters={
            GHG_PROTOCOL_SOURCE_FAMILY: GHGProtocolProductionSourceAdapter(
                target_root=config.archive_root,
                source_years=_ghg_source_years(
                    source_years.get(GHG_PROTOCOL_SOURCE_FAMILY, {}),
                ),
                transport=transport,
            ),
            DEFRA_DESNZ_SOURCE_FAMILY: DefraDesnzProductionSourceAdapter(
                target_root=config.archive_root,
                source_years=_defra_source_years(
                    source_years.get(DEFRA_DESNZ_SOURCE_FAMILY, {}),
                ),
                transport=transport,
            ),
            IPCC_EFDB_SOURCE_FAMILY: IpccEfdbProductionSourceAdapter(
                target_root=config.archive_root,
                source_years=_ipcc_source_years(
                    source_years.get(IPCC_EFDB_SOURCE_FAMILY, {}),
                ),
                transport=transport,
            ),
        },
        parser_boundaries={
            GHG_PROTOCOL_SOURCE_FAMILY: GHGProtocolProductionParserBoundary(),
            DEFRA_DESNZ_SOURCE_FAMILY: DefraDesnzProductionParserBoundary(),
            IPCC_EFDB_SOURCE_FAMILY: IpccEfdbProductionParserBoundary(),
        },
        validation_boundary=ConfiguredCycleValidationBoundary(),
        insert_repository=PostgreSQLSourceFamilyRuntimeRepository(runtime.connection),
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


def _ghg_source_years(
    values: Mapping[int, ConfiguredSourceYearArtifact],
) -> Mapping[int, GHGProtocolSourceYear]:
    return {
        year: GHGProtocolSourceYear(
            year=entry.year,
            publication_url=entry.publication_url,
            artifact_url=entry.artifact_url,
            title=entry.title,
            version_label=entry.version_label,
            content_type=entry.content_type,
            format_hint=entry.format_hint,
        )
        for year, entry in values.items()
    }


def _defra_source_years(
    values: Mapping[int, ConfiguredSourceYearArtifact],
) -> Mapping[int, DefraDesnzSourceYear]:
    return {
        year: DefraDesnzSourceYear(
            year=entry.year,
            publication_url=entry.publication_url,
            artifact_url=entry.artifact_url,
            title=entry.title,
            version_label=entry.version_label,
            content_type=entry.content_type,
            format_hint=entry.format_hint,
        )
        for year, entry in values.items()
    }


def _ipcc_source_years(
    values: Mapping[int, ConfiguredSourceYearArtifact],
) -> Mapping[int, IpccEfdbSourceYear]:
    return {
        year: IpccEfdbSourceYear(
            year=entry.year,
            publication_url=entry.publication_url,
            artifact_url=entry.artifact_url,
            title=entry.title,
            version_label=entry.version_label,
            content_type=entry.content_type,
            format_hint=entry.format_hint,
        )
        for year, entry in values.items()
    }


def _download_status_value(download_result: object | None) -> str:
    if download_result is None:
        return "not_run"
    return str(getattr(getattr(download_result, "status", None), "value", "unknown"))


def _parse_status_value(family: object) -> str:
    if getattr(family, "parsed_row_count", 0) > 0:
        return "parsed"
    failures = tuple(getattr(family, "failures", ()))
    if any(getattr(failure, "stage", "") == "parser" for failure in failures):
        return "failed"
    download_result = getattr(family, "download_result", None)
    if download_result is None or _download_status_value(download_result) != "downloaded":
        return "not_run"
    return "no_rows"


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
