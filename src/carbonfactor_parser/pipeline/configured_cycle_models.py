"""Configured ingestion cycle result models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from carbonfactor_parser.pipeline.production_e2e_year_orchestrator import (
    ProductionE2EYearOrchestratorResult,
)

if TYPE_CHECKING:
    from carbonfactor_parser.pipeline.configured_cycle_runner import (
        ConfiguredCycleRunnerStatus,
    )


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
