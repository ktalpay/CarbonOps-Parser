from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import hashlib
import importlib
import sys
import urllib.request

import pytest

from carbonfactor_parser.parsers.dry_run_boundary_contract import (
    ParserDryRunBoundaryStatus,
)
from carbonfactor_parser.source_acquisition.phase1_orchestration_plan_contract import (
    Phase1OrchestrationPlan,
    Phase1OrchestrationPlanIssue,
    Phase1OrchestrationPlanStatus,
    Phase1OrchestrationPlanSummary,
    Phase1OrchestrationPlanValidationResult,
    create_phase1_orchestration_plan,
    create_phase1_orchestration_plans,
    validate_phase1_orchestration_plan,
    validate_phase1_orchestration_plans,
)
from carbonfactor_parser.source_acquisition.run_contract import (
    create_phase1_source_acquisition_run_results,
)

EXPECTED_SOURCE_KEYS = (
    "ghg_protocol",
    "defra_desnz",
    "ipcc_efdb",
)

BANNED_RUNTIME_MODULE_PREFIXES = (
    "requests",
    "psycopg",
    "sqlalchemy",
    "asyncpg",
    "dotenv",
    "boto3",
    "httpx",
    "urllib3",
)

BANNED_SOURCE_ACQUISITION_RUNTIME_MODULES = (
    "carbonfactor_parser.source_acquisition.cli",
    "carbonfactor_parser.source_acquisition.client",
    "carbonfactor_parser.source_acquisition.file_store",
    "carbonfactor_parser.source_acquisition.http_client",
    "carbonfactor_parser.source_acquisition.http_transport",
    "carbonfactor_parser.source_acquisition.manifest",
    "carbonfactor_parser.source_acquisition.run",
)

BANNED_EXECUTABLE_PARSER_MODULES = (
    "carbonfactor_parser.parsers.defra_desnz_adapter",
    "carbonfactor_parser.parsers.defra_desnz_parser",
    "carbonfactor_parser.parsers.execution_runner",
    "carbonfactor_parser.parsers.file_content_loader",
)


def test_valid_phase1_orchestration_plans_can_be_constructed() -> None:
    plans = create_phase1_orchestration_plans()

    assert tuple(plan.source_key for plan in plans) == EXPECTED_SOURCE_KEYS
    assert all(isinstance(plan, Phase1OrchestrationPlan) for plan in plans)
    assert all(plan.status is Phase1OrchestrationPlanStatus.PLANNED for plan in plans)
    assert all(validate_phase1_orchestration_plan(plan).is_valid for plan in plans)


def test_source_keys_remain_consistent_across_all_plan_metadata() -> None:
    for plan in create_phase1_orchestration_plans():
        parser_plan = plan.acquisition_to_parser_plan
        request = plan.parser_run_requests[0]
        dry_run = plan.dry_run_boundaries[0]

        assert plan.acquisition_request.source_key == plan.source_key
        assert plan.acquisition_result.source_key == plan.source_key
        assert parser_plan.source_key == plan.source_key
        assert request.source_key == plan.source_key
        assert request.artifacts[0].source_key == plan.source_key
        assert dry_run.source_key == plan.source_key
        assert dry_run.request.source_key == plan.source_key


def test_parser_keys_remain_consistent_across_parser_and_dry_run_metadata() -> None:
    for plan in create_phase1_orchestration_plans():
        request = plan.parser_run_requests[0]
        dry_run = plan.dry_run_boundaries[0]

        assert plan.parser_keys == (request.parser_key,)
        assert dry_run.parser_key == request.parser_key
        assert dry_run.eligibility.parser_key == request.parser_key
        assert dry_run.request.parser_key == request.parser_key


def test_plan_status_values_are_constrained_to_deterministic_allowed_set() -> None:
    assert tuple(status.value for status in Phase1OrchestrationPlanStatus) == (
        "declared",
        "planned",
        "planned_with_issues",
        "failed",
    )

    plan = replace(
        create_phase1_orchestration_plans()[0],
        status="ready",  # type: ignore[arg-type]
    )

    validation = validate_phase1_orchestration_plan(plan)

    assert validation.is_valid is False
    assert "PHASE1_ORCHESTRATION_PLAN_INVALID_STATUS" in _issue_codes(validation)


@pytest.mark.parametrize(
    ("field_name", "expected_code"),
    (
        ("source_family", "PHASE1_ORCHESTRATION_PLAN_MISSING_SOURCE_FAMILY"),
        ("source_key", "PHASE1_ORCHESTRATION_PLAN_MISSING_SOURCE_KEY"),
    ),
)
def test_required_plan_metadata_fields_reject_empty_strings(
    field_name: str,
    expected_code: str,
) -> None:
    plan = replace(
        create_phase1_orchestration_plans()[0],
        **{field_name: " "},
    )

    validation = validate_phase1_orchestration_plan(plan)

    assert validation.is_valid is False
    assert expected_code in _issue_codes(validation)


def test_optional_plan_identifiers_reject_blank_strings() -> None:
    plan = replace(
        create_phase1_orchestration_plan(
            create_phase1_source_acquisition_run_results()[0],
            plan_id="phase1-plan-001",
            correlation_id="correlation-001",
        ),
        plan_id=" ",
        correlation_id="",
    )

    validation = validate_phase1_orchestration_plan(plan)

    assert validation.is_valid is False
    assert "PHASE1_ORCHESTRATION_PLAN_BLANK_PLAN_ID" in _issue_codes(validation)
    assert "PHASE1_ORCHESTRATION_PLAN_BLANK_CORRELATION_ID" in (
        _issue_codes(validation)
    )


def test_summary_counts_are_deterministic() -> None:
    issue = Phase1OrchestrationPlanIssue(
        code="PHASE1_ORCHESTRATION_PLAN_TEST_WARNING",
        message="test warning",
        field_name="parser_run_requests[1]",
        severity="warning",
    )
    acquisition_result = create_phase1_source_acquisition_run_results()[0]
    plan = create_phase1_orchestration_plan(
        acquisition_result,
        status=Phase1OrchestrationPlanStatus.PLANNED_WITH_ISSUES,
        issues=(issue,),
    )

    assert plan.summary == Phase1OrchestrationPlanSummary(
        acquisition_candidate_count=1,
        acquisition_artifact_count=1,
        parser_plan_artifact_count=1,
        parser_input_artifact_count=1,
        parser_run_request_count=1,
        dry_run_boundary_count=1,
        dry_run_eligible_count=1,
        issue_count=1,
    )
    assert create_phase1_orchestration_plan(
        acquisition_result,
        status=Phase1OrchestrationPlanStatus.PLANNED_WITH_ISSUES,
        issues=(issue,),
    ).summary == plan.summary


def test_summary_count_mismatches_return_invalid_result() -> None:
    plan = replace(
        create_phase1_orchestration_plans()[1],
        summary=Phase1OrchestrationPlanSummary(
            acquisition_candidate_count=99,
            acquisition_artifact_count=99,
            parser_plan_artifact_count=99,
            parser_input_artifact_count=99,
            parser_run_request_count=99,
            dry_run_boundary_count=99,
            dry_run_eligible_count=99,
            issue_count=99,
        ),
    )

    validation = validate_phase1_orchestration_plan(plan)

    assert validation.is_valid is False
    assert "PHASE1_ORCHESTRATION_PLAN_SUMMARY_CANDIDATE_COUNT_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "PHASE1_ORCHESTRATION_PLAN_SUMMARY_ARTIFACT_COUNT_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "PHASE1_ORCHESTRATION_PLAN_SUMMARY_REQUEST_COUNT_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "PHASE1_ORCHESTRATION_PLAN_SUMMARY_DRY_RUN_COUNT_MISMATCH" in (
        _issue_codes(validation)
    )


def test_ordering_is_deterministic() -> None:
    first = create_phase1_orchestration_plans()
    second = create_phase1_orchestration_plans()

    assert first == second
    assert tuple(plan.source_key for plan in first) == EXPECTED_SOURCE_KEYS
    assert tuple(plan.dry_run_statuses for plan in first) == (
        (ParserDryRunBoundaryStatus.PLANNED,),
        (ParserDryRunBoundaryStatus.PLANNED,),
        (ParserDryRunBoundaryStatus.PLANNED,),
    )


def test_alignment_rejects_mismatched_acquisition_metadata() -> None:
    plan = create_phase1_orchestration_plans()[0]
    invalid_plan = replace(plan, source_key="defra_desnz")

    validation = validate_phase1_orchestration_plan(invalid_plan)

    assert validation.is_valid is False
    assert "PHASE1_ORCHESTRATION_PLAN_ACQUISITION_REQUEST_SOURCE_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "PHASE1_ORCHESTRATION_PLAN_ACQUISITION_RESULT_SOURCE_MISMATCH" in (
        _issue_codes(validation)
    )


def test_alignment_rejects_mismatched_parser_plan_metadata() -> None:
    plan = create_phase1_orchestration_plans()[1]
    invalid_parser_plan = replace(
        plan.acquisition_to_parser_plan,
        source_key="ghg_protocol",
    )
    invalid_plan = replace(plan, acquisition_to_parser_plan=invalid_parser_plan)

    validation = validate_phase1_orchestration_plan(invalid_plan)

    assert validation.is_valid is False
    assert "PHASE1_ORCHESTRATION_PLAN_PARSER_PLAN_SOURCE_KEY_MISMATCH" in (
        _issue_codes(validation)
    )


def test_alignment_rejects_mismatched_parser_run_request_metadata() -> None:
    plan = create_phase1_orchestration_plans()[1]
    invalid_request = replace(plan.parser_run_requests[0], source_key="ghg_protocol")
    invalid_plan = replace(plan, parser_run_requests=(invalid_request,))

    validation = validate_phase1_orchestration_plan(invalid_plan)

    assert validation.is_valid is False
    assert "PHASE1_ORCHESTRATION_PLAN_PARSER_REQUESTS_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "PHASE1_ORCHESTRATION_PLAN_REQUEST_SOURCE_KEY_MISMATCH" in (
        _issue_codes(validation)
    )


def test_alignment_rejects_mismatched_dry_run_metadata() -> None:
    plan = create_phase1_orchestration_plans()[2]
    invalid_dry_run = replace(plan.dry_run_boundaries[0], source_key="ghg_protocol")
    invalid_plan = replace(plan, dry_run_boundaries=(invalid_dry_run,))

    validation = validate_phase1_orchestration_plan(invalid_plan)

    assert validation.is_valid is False
    assert "PHASE1_ORCHESTRATION_PLAN_DRY_RUN_REQUESTS_MISMATCH" not in (
        _issue_codes(validation)
    )
    assert "PHASE1_ORCHESTRATION_PLAN_DRY_RUN_SOURCE_KEY_MISMATCH" in (
        _issue_codes(validation)
    )


def test_plan_issue_shape_is_structural_and_severity_constrained() -> None:
    issue = Phase1OrchestrationPlanIssue(
        code=" ",
        message="",
        field_name=" ",
        severity="critical",
    )
    plan = create_phase1_orchestration_plan(
        create_phase1_source_acquisition_run_results()[0],
        issues=(issue,),
    )

    validation = validate_phase1_orchestration_plan(plan)

    assert validation.is_valid is False
    assert "PHASE1_ORCHESTRATION_PLAN_ISSUE_MISSING_CODE" in _issue_codes(validation)
    assert "PHASE1_ORCHESTRATION_PLAN_ISSUE_MISSING_MESSAGE" in (
        _issue_codes(validation)
    )
    assert "PHASE1_ORCHESTRATION_PLAN_ISSUE_MISSING_FIELD_NAME" in (
        _issue_codes(validation)
    )
    assert "PHASE1_ORCHESTRATION_PLAN_ISSUE_INVALID_SEVERITY" in (
        _issue_codes(validation)
    )


def test_plan_batch_validation_prefixes_locations() -> None:
    plan = replace(create_phase1_orchestration_plans()[0], source_key="")

    validation = validate_phase1_orchestration_plans((plan,))

    assert validation.is_valid is False
    assert validation.issues[0].field_name == "plans[1].source_key"
    assert validation.issues[0].code == (
        "PHASE1_ORCHESTRATION_PLAN_MISSING_SOURCE_KEY"
    )


def test_validation_does_not_perform_network_file_db_downloader_or_parser_execution(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    import builtins
    import pathlib
    import sqlite3

    missing_artifact = tmp_path / "downloaded.csv"
    acquisition_result = create_phase1_source_acquisition_run_results()[0]
    acquisition_result = replace(
        acquisition_result,
        artifacts=(
            replace(
                acquisition_result.artifacts[0],
                source_reference_uri="discovery://not-fetched/source.csv",
                local_reference=str(missing_artifact),
            ),
        ),
    )
    plan = create_phase1_orchestration_plan(acquisition_result)

    def fail_side_effect(*args: object, **kwargs: object) -> object:
        raise AssertionError("orchestration plan validation must use metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "exists", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "is_file", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "stat", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "read_text", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "write_text", fail_side_effect)
    monkeypatch.setattr(hashlib, "sha256", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)

    assert validate_phase1_orchestration_plan(plan).is_valid is True


def test_phase1_orchestration_plan_contract_is_read_only() -> None:
    plan = create_phase1_orchestration_plans()[0]

    with pytest.raises(FrozenInstanceError):
        plan.source_key = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        plan.summary.parser_run_request_count = 99  # type: ignore[misc]


def test_validation_result_shape_exposes_is_valid() -> None:
    assert Phase1OrchestrationPlanValidationResult().is_valid is True
    assert Phase1OrchestrationPlanValidationResult(
        issues=(
            Phase1OrchestrationPlanIssue(
                code="TEST",
                message="test",
                field_name="field",
            ),
        ),
    ).is_valid is False


def test_import_remains_runtime_passive(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins
    import os

    module_name = (
        "carbonfactor_parser.source_acquisition."
        "phase1_orchestration_plan_contract"
    )
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("Phase 1 orchestration plan import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("Phase 1 orchestration plan import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_after = set(sys.modules)

    assert hasattr(module, "create_phase1_orchestration_plans")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_after - imported_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in (
            *BANNED_RUNTIME_MODULE_PREFIXES,
            *BANNED_SOURCE_ACQUISITION_RUNTIME_MODULES,
            *BANNED_EXECUTABLE_PARSER_MODULES,
        )
    )


def _issue_codes(
    result: Phase1OrchestrationPlanValidationResult,
) -> tuple[str, ...]:
    return tuple(issue.code for issue in result.issues)
