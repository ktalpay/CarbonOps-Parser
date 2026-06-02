from __future__ import annotations

import json
from pathlib import Path

from carbonfactor_parser import cli as parser_cli
from carbonfactor_parser.pipeline.configured_cycle_runner import (
    ConfiguredCycleResult,
    ConfiguredCycleRunnerResult,
    ConfiguredCycleRunnerStatus,
)
from carbonfactor_parser.pipeline import configured_cycle_runner
from carbonfactor_parser.pipeline.production_e2e_year_orchestrator import (
    ProductionE2EFailureDetail,
    ProductionE2EYearFamilyResult,
    ProductionE2EYearFamilyStatus,
    ProductionE2EYearOrchestratorRequest,
    ProductionE2EYearOrchestratorResult,
    ProductionE2EYearRunStatus,
    ProductionE2EYearRunSummary,
    ProductionE2EYearSelectionStatus,
    ProductionE2EYearState,
)


def test_run_ingestion_summary_output_writes_sanitized_json(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    summary_path = tmp_path / "nested" / "summary.json"
    result = _runner_result_with_secret_issue()

    monkeypatch.setattr(
        configured_cycle_runner,
        "load_configured_cycle_runner_config",
        lambda path, *, max_cycles=None: {"path": path, "max_cycles": max_cycles},
    )
    monkeypatch.setattr(
        configured_cycle_runner,
        "run_configured_cycle_runner",
        lambda settings: result,
    )

    exit_code = parser_cli.main(
        ["run-ingestion", "--cycles", "1", "--summary-output", str(summary_path)]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["status"] == "completed"
    assert payload["cycles"][0]["run_id"] == "run-123"
    assert payload["cycles"][0]["issues"][0]["code"] == "DOWNLOAD_FAILED"
    serialized = json.dumps(payload)
    assert "secret" not in serialized
    assert "postgresql://user:secret" not in serialized
    assert "token=abc" not in serialized
    assert "password=***" in serialized


def test_run_ingestion_default_behavior_does_not_write_summary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    result = _runner_result_with_secret_issue()

    monkeypatch.setattr(
        configured_cycle_runner,
        "load_configured_cycle_runner_config",
        lambda path, *, max_cycles=None: {"path": path, "max_cycles": max_cycles},
    )
    monkeypatch.setattr(
        configured_cycle_runner,
        "run_configured_cycle_runner",
        lambda settings: result,
    )

    exit_code = parser_cli.main(["run-ingestion", "--cycles", "1"])

    assert exit_code == 0
    assert not list(tmp_path.glob("*.json"))


def _runner_result_with_secret_issue() -> ConfiguredCycleRunnerResult:
    failure = ProductionE2EFailureDetail(
        source_family="ghg_protocol",
        stage="download",
        code="DOWNLOAD_FAILED",
        message=(
            "download failed dsn=postgresql://user:secret@example.invalid/db "
            "password=secret token=abc"
        ),
    )
    family = ProductionE2EYearFamilyResult(
        source_family="ghg_protocol",
        status=ProductionE2EYearFamilyStatus.FAILED,
        year_state=ProductionE2EYearState(
            source_family="ghg_protocol",
            year_state_key="ghg",
            latest_year=None,
            target_year=2024,
            initial_year=2024,
            selection_status=ProductionE2EYearSelectionStatus.INITIAL_YEAR_SELECTED,
        ),
        failures=(failure,),
    )
    cycle = ConfiguredCycleResult(
        cycle_number=1,
        run_id="run-123",
        result=ProductionE2EYearOrchestratorResult(
            status=ProductionE2EYearRunStatus.COMPLETED,
            request=ProductionE2EYearOrchestratorRequest(run_id="run-123"),
            selected_source_families=("ghg_protocol",),
            family_results=(family,),
            summary=ProductionE2EYearRunSummary(
                requested_family_count=1,
                completed_family_count=1,
                no_available_source_year_count=0,
                failed_family_count=0,
                parsed_row_count=0,
                attempted_insert_count=0,
                inserted_count=0,
                skipped_duplicate_count=0,
                failed_insert_count=0,
                failure_count=1,
            ),
        ),
    )
    return ConfiguredCycleRunnerResult(
        status=ConfiguredCycleRunnerStatus.COMPLETED,
        cycles=(cycle,),
        schema_created_table_names=(),
        schema_missing_table_names=(),
    )
