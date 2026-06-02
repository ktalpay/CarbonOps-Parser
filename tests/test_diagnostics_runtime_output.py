from __future__ import annotations

from carbonfactor_parser.diagnostics.ingestion_runtime_events import (
    build_configured_cycle_summary_payload,
    build_configured_runner_summary_payload,
)
from carbonfactor_parser.diagnostics.redaction import redact_sensitive_text
from carbonfactor_parser.pipeline.configured_cycle_runner import (
    ConfiguredCycleResult,
    ConfiguredCycleRunnerResult,
    ConfiguredCycleRunnerStatus,
)
from carbonfactor_parser.pipeline.production_e2e_year_orchestrator import (
    ProductionE2EFailureDetail,
    ProductionE2EInsertSummary,
    ProductionE2EYearFamilyResult,
    ProductionE2EYearFamilyStatus,
    ProductionE2EYearOrchestratorRequest,
    ProductionE2EYearOrchestratorResult,
    ProductionE2EYearRunStatus,
    ProductionE2EYearRunSummary,
    ProductionE2EYearSelectionStatus,
    ProductionE2EYearState,
)


def test_redaction_sanitizes_postgresql_uri_userinfo() -> None:
    message = (
        "connect postgresql://carbonops:super-secret@example.invalid:5432/db"
        "?sslmode=require&token=abc123"
    )

    redacted = redact_sensitive_text(message)

    assert "super-secret" not in redacted
    assert "carbonops:super-secret" not in redacted
    assert "token=abc123" not in redacted
    assert "postgresql://***@example.invalid:5432/db" in redacted
    assert "token=***" in redacted


def test_redaction_sanitizes_sensitive_assignments() -> None:
    message = (
        "password=hunter2 passwd=other pwd=tiny token=tok-value secret=sec-value "
        "key=api dsn=postgresql://user:pass@example.invalid/db "
        "connection_string=postgresql://user:pass@example.invalid/db"
    )

    redacted = redact_sensitive_text(message)

    assert "hunter2" not in redacted
    assert "other" not in redacted
    assert "tiny" not in redacted
    assert "tok-value" not in redacted
    assert "sec-value" not in redacted
    assert "api" not in redacted
    assert "user:pass" not in redacted
    assert "password=***" in redacted
    assert "token=***" in redacted
    assert "dsn=***" in redacted
    assert "connection_string=***" in redacted


def test_redaction_keeps_non_sensitive_messages_readable() -> None:
    message = "download failed because source family ghg_protocol is disabled"

    assert redact_sensitive_text(message) == message


def test_configured_cycle_summary_payload_contains_sanitized_runtime_details() -> None:
    cycle = _configured_cycle_with_secret_issue()

    payload = build_configured_cycle_summary_payload(cycle)

    assert payload["cycle_number"] == 1
    assert payload["run_id"] == "run-001"
    assert payload["status"] == "completed_with_failures"
    assert payload["summary"] == {
        "completed_family_count": 0,
        "no_available_source_year_count": 0,
        "failed_family_count": 1,
        "parsed_rows": 7,
        "inserted": 3,
        "skipped_duplicates": 4,
    }
    assert payload["sources"] == [
        {
            "source_family": "ghg_protocol",
            "target_year": 2024,
            "latest_year": 2023,
            "status": "failed",
            "download_status": "not_run",
            "parse_status": "parsed",
            "parsed_rows": 7,
            "master_inserted": 1,
            "master_skipped": 2,
            "detail_inserted": 2,
            "detail_skipped": 2,
        }
    ]
    assert payload["issues"][0]["source_family"] == "ghg_protocol"
    assert payload["issues"][0]["stage"] == "parser"
    assert payload["issues"][0]["code"] == "PARSER_FAILED"
    assert "secret" not in str(payload)
    assert "password=***" in payload["issues"][0]["message"]


def test_configured_runner_summary_payload_contains_schema_and_cycles() -> None:
    result = ConfiguredCycleRunnerResult(
        status=ConfiguredCycleRunnerStatus.COMPLETED_WITH_FAILURES,
        cycles=(_configured_cycle_with_secret_issue(),),
        schema_created_table_names=("ghg_emission_factor_masters",),
        schema_missing_table_names=("missing_table",),
    )

    payload = build_configured_runner_summary_payload(result)

    assert payload["status"] == "completed_with_failures"
    assert payload["schema_created_table_names"] == ["ghg_emission_factor_masters"]
    assert payload["schema_missing_table_names"] == ["missing_table"]
    assert payload["cycles"][0]["run_id"] == "run-001"
    assert "secret" not in str(payload)


def _configured_cycle_with_secret_issue() -> ConfiguredCycleResult:
    failure = ProductionE2EFailureDetail(
        source_family="ghg_protocol",
        stage="parser",
        code="PARSER_FAILED",
        message="parser failed password=secret token=secret-token",
        field_name="parser",
    )
    family = ProductionE2EYearFamilyResult(
        source_family="ghg_protocol",
        status=ProductionE2EYearFamilyStatus.FAILED,
        year_state=ProductionE2EYearState(
            source_family="ghg_protocol",
            year_state_key="ghg",
            latest_year=2023,
            target_year=2024,
            initial_year=2024,
            selection_status=ProductionE2EYearSelectionStatus.NEXT_YEAR_SELECTED,
        ),
        parsed_row_count=7,
        insert_summary=ProductionE2EInsertSummary(
            status="failed_database",
            attempted=7,
            inserted=3,
            skipped_duplicate=4,
            failed=1,
            master_inserted=1,
            master_skipped=2,
            detail_inserted=2,
            detail_skipped=2,
        ),
        failures=(failure,),
    )
    return ConfiguredCycleResult(
        cycle_number=1,
        run_id="run-001",
        result=ProductionE2EYearOrchestratorResult(
            status=ProductionE2EYearRunStatus.COMPLETED_WITH_FAILURES,
            request=ProductionE2EYearOrchestratorRequest(run_id="run-001"),
            selected_source_families=("ghg_protocol",),
            family_results=(family,),
            summary=ProductionE2EYearRunSummary(
                requested_family_count=1,
                completed_family_count=0,
                no_available_source_year_count=0,
                failed_family_count=1,
                parsed_row_count=7,
                attempted_insert_count=7,
                inserted_count=3,
                skipped_duplicate_count=4,
                failed_insert_count=1,
                failure_count=1,
            ),
            failures=(),
        ),
    )
