from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from carbonfactor_parser.persistence.ingestion_run_history_mapping import (
    build_ingestion_run_history_command_from_configured_cycle,
)
from carbonfactor_parser.pipeline.configured_cycle_runner import ConfiguredCycleResult
from carbonfactor_parser.pipeline.production_e2e_year_orchestrator import (
    ProductionE2EFailureDetail,
    ProductionE2EInsertSummary,
    ProductionE2ESourceYearDownloadResult,
    ProductionE2ESourceYearDownloadStatus,
    ProductionE2EValidationResult,
    ProductionE2EValidationStatus,
    ProductionE2EYearFamilyResult,
    ProductionE2EYearFamilyStatus,
    ProductionE2EYearOrchestratorRequest,
    ProductionE2EYearOrchestratorResult,
    ProductionE2EYearRunStatus,
    ProductionE2EYearRunSummary,
    ProductionE2EYearSelectionStatus,
    ProductionE2EYearState,
)


def test_configured_cycle_maps_to_ingestion_run_history_command() -> None:
    started_at = datetime(2026, 1, 2, 3, 4, tzinfo=timezone.utc)
    finished_at = datetime(2026, 1, 2, 3, 5, tzinfo=timezone.utc)
    duplicate_family_failure = ProductionE2EFailureDetail(
        source_family="ghg_protocol",
        stage="validator",
        code="VALIDATION_FAILED",
        message="invalid factor password=secret",
        field_name="factor_value",
    )
    top_level_failure = ProductionE2EFailureDetail(
        source_family="configured_runner",
        stage="runner",
        code="RUNNER_WARNING",
        message="operator warning token=abc",
        severity="warning",
    )
    cycle = ConfiguredCycleResult(
        cycle_number=2,
        run_id="run-history-123",
        result=ProductionE2EYearOrchestratorResult(
            status=ProductionE2EYearRunStatus.COMPLETED_WITH_FAILURES,
            request=ProductionE2EYearOrchestratorRequest(
                run_id="run-history-123",
                enabled_source_families=("ghg_protocol",),
                initial_year=2024,
            ),
            selected_source_families=("ghg_protocol",),
            family_results=(
                ProductionE2EYearFamilyResult(
                    source_family="ghg_protocol",
                    status=ProductionE2EYearFamilyStatus.FAILED,
                    year_state=ProductionE2EYearState(
                        source_family="ghg_protocol",
                        year_state_key="ghg",
                        latest_year=2023,
                        target_year=2024,
                        initial_year=2024,
                        selection_status=(
                            ProductionE2EYearSelectionStatus.INITIAL_YEAR_SELECTED
                        ),
                    ),
                    download_result=ProductionE2ESourceYearDownloadResult(
                        status=ProductionE2ESourceYearDownloadStatus.DOWNLOADED,
                        source_family="ghg_protocol",
                        target_year=2024,
                    ),
                    parsed_row_count=7,
                    validation_result=ProductionE2EValidationResult(
                        status=ProductionE2EValidationStatus.FAILED_VALIDATION,
                        blocking_error_count=1,
                    ),
                    insert_summary=ProductionE2EInsertSummary(
                        status="inserted_with_duplicates",
                        attempted=7,
                        inserted=5,
                        skipped_duplicate=2,
                        master_inserted=3,
                        master_skipped=1,
                        detail_inserted=2,
                        detail_skipped=1,
                    ),
                    failures=(duplicate_family_failure,),
                ),
            ),
            summary=ProductionE2EYearRunSummary(
                requested_family_count=1,
                completed_family_count=0,
                no_available_source_year_count=0,
                failed_family_count=1,
                parsed_row_count=7,
                attempted_insert_count=7,
                inserted_count=5,
                skipped_duplicate_count=2,
                failed_insert_count=0,
                failure_count=2,
            ),
            failures=(duplicate_family_failure, top_level_failure),
        ),
    )

    command = build_ingestion_run_history_command_from_configured_cycle(
        cycle,
        started_at=started_at,
        finished_at=finished_at,
        metadata={"safe_flag": True},
    )

    assert command.run.run_id == "run-history-123"
    assert command.run.started_at == started_at
    assert command.run.finished_at == finished_at
    assert command.run.status == "completed_with_failures"
    assert command.run.trigger_type == "operator"
    assert command.run.enabled_source_families == ("ghg_protocol",)
    assert command.run.initial_year == 2024
    assert command.run.cycle_count == 2
    assert command.run.total_parsed_rows == 7
    assert command.run.total_inserted_count == 5
    assert command.run.total_skipped_duplicate_count == 2
    assert command.run.failure_count == 2
    assert command.run.metadata == {
        "requested_family_count": 1,
        "completed_family_count": 0,
        "failed_family_count": 1,
        "no_available_source_year_count": 0,
        "safe_flag": True,
    }

    assert len(command.source_results) == 1
    source = command.source_results[0]
    assert source.run_id == "run-history-123"
    assert source.source_family == "ghg_protocol"
    assert source.target_year == 2024
    assert source.latest_year == 2023
    assert source.status == "failed"
    assert source.download_status == "downloaded"
    assert source.parse_status == "parsed"
    assert source.validation_status == "failed_validation"
    assert source.insert_status == "inserted_with_duplicates"
    assert source.parsed_rows == 7
    assert source.master_inserted == 3
    assert source.master_skipped == 1
    assert source.detail_inserted == 2
    assert source.detail_skipped == 1
    assert source.issue_count == 1
    assert source.metadata == {"selection_status": "initial_year_selected"}

    assert len(command.issues) == 2
    family_issue = command.issues[0]
    assert family_issue.source_family == "ghg_protocol"
    assert family_issue.target_year == 2024
    assert family_issue.stage == "validator"
    assert family_issue.code == "VALIDATION_FAILED"
    assert family_issue.field_name == "factor_value"
    assert "secret" not in family_issue.message

    runner_issue = command.issues[1]
    assert runner_issue.source_family == "configured_runner"
    assert runner_issue.target_year is None
    assert runner_issue.stage == "runner"
    assert runner_issue.severity == "warning"
    assert "token=abc" not in runner_issue.message


def test_configured_cycle_mapping_normalizes_enum_like_insert_status() -> None:
    cycle = _cycle_with_insert_status(_EnumLikeStatus("inserted"))

    command = build_ingestion_run_history_command_from_configured_cycle(cycle)

    assert command.source_results[0].insert_status == "inserted"


def test_configured_cycle_mapping_keeps_string_insert_status() -> None:
    cycle = _cycle_with_insert_status("inserted_with_duplicates")

    command = build_ingestion_run_history_command_from_configured_cycle(cycle)

    assert command.source_results[0].insert_status == "inserted_with_duplicates"


def _cycle_with_insert_status(status: object) -> ConfiguredCycleResult:
    cycle = _minimal_cycle()
    family = cycle.result.family_results[0]
    assert family.insert_summary is not None
    updated_family = replace(
        family,
        insert_summary=replace(family.insert_summary, status=status),
    )
    return replace(
        cycle,
        result=replace(cycle.result, family_results=(updated_family,)),
    )


def _minimal_cycle() -> ConfiguredCycleResult:
    return ConfiguredCycleResult(
        cycle_number=1,
        run_id="run-history-status",
        result=ProductionE2EYearOrchestratorResult(
            status=ProductionE2EYearRunStatus.COMPLETED,
            request=ProductionE2EYearOrchestratorRequest(
                run_id="run-history-status",
                enabled_source_families=("ghg_protocol",),
                initial_year=2024,
            ),
            selected_source_families=("ghg_protocol",),
            family_results=(
                ProductionE2EYearFamilyResult(
                    source_family="ghg_protocol",
                    status=ProductionE2EYearFamilyStatus.COMPLETED,
                    year_state=ProductionE2EYearState(
                        source_family="ghg_protocol",
                        year_state_key="ghg",
                        latest_year=None,
                        target_year=2024,
                        initial_year=2024,
                        selection_status=(
                            ProductionE2EYearSelectionStatus.INITIAL_YEAR_SELECTED
                        ),
                    ),
                    parsed_row_count=1,
                    validation_result=ProductionE2EValidationResult(
                        status=ProductionE2EValidationStatus.VALIDATED,
                    ),
                    insert_summary=ProductionE2EInsertSummary(
                        status="inserted",
                        attempted=1,
                        inserted=1,
                    ),
                ),
            ),
            summary=ProductionE2EYearRunSummary(
                requested_family_count=1,
                completed_family_count=1,
                no_available_source_year_count=0,
                failed_family_count=0,
                parsed_row_count=1,
                attempted_insert_count=1,
                inserted_count=1,
                skipped_duplicate_count=0,
                failed_insert_count=0,
                failure_count=0,
            ),
        ),
    )


class _EnumLikeStatus:
    def __init__(self, value: str) -> None:
        self.value = value
