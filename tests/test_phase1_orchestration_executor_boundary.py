from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import hashlib
import importlib
import sys
import urllib.request

import pytest

from carbonfactor_parser.source_acquisition.phase1_orchestration_executor_boundary import (
    Phase1OrchestrationExecutorIssue,
    Phase1OrchestrationExecutorReadiness,
    Phase1OrchestrationExecutorRequest,
    Phase1OrchestrationExecutorResult,
    Phase1OrchestrationExecutorStatus,
    Phase1OrchestrationExecutorSummary,
    Phase1OrchestrationExecutorValidationResult,
    create_phase1_orchestration_executor_boundaries,
    create_phase1_orchestration_executor_request,
    plan_phase1_orchestration_executor_boundary,
    validate_phase1_orchestration_executor_request,
    validate_phase1_orchestration_executor_result,
    validate_phase1_orchestration_executor_results,
)
from carbonfactor_parser.source_acquisition.phase1_orchestration_plan_contract import (
    create_phase1_orchestration_plans,
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


def test_executor_boundary_results_can_be_constructed_for_phase1() -> None:
    results = create_phase1_orchestration_executor_boundaries()

    assert tuple(result.source_key for result in results) == EXPECTED_SOURCE_KEYS
    assert all(isinstance(result, Phase1OrchestrationExecutorResult) for result in results)
    assert all(
        result.status is Phase1OrchestrationExecutorStatus.NOT_IMPLEMENTED
        for result in results
    )
    assert all(
        validate_phase1_orchestration_executor_result(result).is_valid
        for result in results
    )


def test_executor_status_values_are_constrained_to_deterministic_allowed_set() -> None:
    assert tuple(status.value for status in Phase1OrchestrationExecutorStatus) == (
        "planned",
        "not_executable",
        "not_implemented",
    )

    result = replace(
        create_phase1_orchestration_executor_boundaries()[0],
        status="executed",  # type: ignore[arg-type]
    )

    validation = validate_phase1_orchestration_executor_result(result)

    assert validation.is_valid is False
    assert "PHASE1_ORCHESTRATION_EXECUTOR_INVALID_STATUS" in _issue_codes(validation)


def test_executor_boundary_consumes_phase1_orchestration_plan_metadata() -> None:
    plan = create_phase1_orchestration_plans()[0]
    request = create_phase1_orchestration_executor_request(
        plan,
        executor_id="executor-001",
        correlation_id="correlation-001",
    )
    result = plan_phase1_orchestration_executor_boundary(request)

    assert isinstance(request, Phase1OrchestrationExecutorRequest)
    assert request.orchestration_plan == plan
    assert result.request == request
    assert result.executor_id == "executor-001"
    assert result.correlation_id == "correlation-001"
    assert result.summary.acquisition_candidate_count == (
        plan.summary.acquisition_candidate_count
    )
    assert result.summary.parser_run_request_count == (
        plan.summary.parser_run_request_count
    )


def test_source_keys_remain_consistent() -> None:
    for result in create_phase1_orchestration_executor_boundaries():
        plan = result.request.orchestration_plan

        assert result.source_key == plan.source_key
        assert result.request.source_key == plan.source_key
        assert result.readiness.source_key == plan.source_key
        assert result.source_family == plan.source_family
        assert result.request.source_family == plan.source_family
        assert result.readiness.source_family == plan.source_family


def test_required_metadata_fields_reject_empty_strings() -> None:
    result = replace(
        create_phase1_orchestration_executor_boundaries()[0],
        source_family="",
        source_key=" ",
    )

    validation = validate_phase1_orchestration_executor_result(result)

    assert validation.is_valid is False
    assert "PHASE1_ORCHESTRATION_EXECUTOR_MISSING_SOURCE_FAMILY" in (
        _issue_codes(validation)
    )
    assert "PHASE1_ORCHESTRATION_EXECUTOR_MISSING_SOURCE_KEY" in _issue_codes(validation)


def test_optional_executor_identifiers_reject_blank_strings() -> None:
    result = replace(
        create_phase1_orchestration_executor_boundaries()[0],
        executor_id=" ",
        correlation_id="",
    )

    validation = validate_phase1_orchestration_executor_result(result)

    assert validation.is_valid is False
    assert "PHASE1_ORCHESTRATION_EXECUTOR_BLANK_EXECUTOR_ID" in _issue_codes(validation)
    assert "PHASE1_ORCHESTRATION_EXECUTOR_BLANK_CORRELATION_ID" in (
        _issue_codes(validation)
    )


def test_summary_counts_are_deterministic() -> None:
    issue = Phase1OrchestrationExecutorIssue(
        code="PHASE1_ORCHESTRATION_EXECUTOR_TEST_WARNING",
        message="test warning",
        field_name="request",
        severity="warning",
    )
    plan = create_phase1_orchestration_plans()[0]
    request = create_phase1_orchestration_executor_request(plan)
    result = plan_phase1_orchestration_executor_boundary(request, issues=(issue,))

    assert result.summary == Phase1OrchestrationExecutorSummary(
        acquisition_candidate_count=1,
        acquisition_artifact_count=1,
        parser_run_request_count=1,
        dry_run_boundary_count=1,
        dry_run_eligible_count=1,
        plan_issue_count=0,
        executor_issue_count=1,
    )
    assert plan_phase1_orchestration_executor_boundary(
        request,
        issues=(issue,),
    ).summary == result.summary


def test_summary_count_mismatches_return_invalid_result() -> None:
    result = replace(
        create_phase1_orchestration_executor_boundaries()[1],
        summary=Phase1OrchestrationExecutorSummary(
            acquisition_candidate_count=99,
            acquisition_artifact_count=99,
            parser_run_request_count=99,
            dry_run_boundary_count=99,
            dry_run_eligible_count=99,
            plan_issue_count=99,
            executor_issue_count=99,
        ),
    )

    validation = validate_phase1_orchestration_executor_result(result)

    assert validation.is_valid is False
    assert "PHASE1_ORCHESTRATION_EXECUTOR_SUMMARY_CANDIDATE_COUNT_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "PHASE1_ORCHESTRATION_EXECUTOR_SUMMARY_REQUEST_COUNT_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "PHASE1_ORCHESTRATION_EXECUTOR_SUMMARY_DRY_RUN_COUNT_MISMATCH" in (
        _issue_codes(validation)
    )


def test_executor_reports_not_implemented_without_runtime_work() -> None:
    result = create_phase1_orchestration_executor_boundaries()[0]

    assert result.status is Phase1OrchestrationExecutorStatus.NOT_IMPLEMENTED
    assert result.readiness == Phase1OrchestrationExecutorReadiness(
        source_family="ghg_protocol",
        source_key="ghg_protocol",
        is_executable=False,
        reason="runtime_execution_not_implemented",
        plan_status="planned",
    )


def test_not_executable_status_remains_metadata_only() -> None:
    request = create_phase1_orchestration_executor_request(
        create_phase1_orchestration_plans()[0],
    )
    result = plan_phase1_orchestration_executor_boundary(
        request,
        status=Phase1OrchestrationExecutorStatus.NOT_EXECUTABLE,
    )

    assert result.status is Phase1OrchestrationExecutorStatus.NOT_EXECUTABLE
    assert result.readiness.is_executable is False
    assert validate_phase1_orchestration_executor_result(result).is_valid


def test_executor_request_validation_rejects_plan_mismatch() -> None:
    plan = create_phase1_orchestration_plans()[1]
    request = replace(
        create_phase1_orchestration_executor_request(plan),
        source_key="ghg_protocol",
    )

    validation = validate_phase1_orchestration_executor_request(request)

    assert validation.is_valid is False
    assert "PHASE1_ORCHESTRATION_EXECUTOR_REQUEST_PLAN_SOURCE_KEY_MISMATCH" in (
        _issue_codes(validation)
    )


def test_executor_result_validation_rejects_request_mismatch() -> None:
    result = create_phase1_orchestration_executor_boundaries()[2]
    invalid_request = replace(result.request, source_key="ghg_protocol")
    invalid_result = replace(result, request=invalid_request)

    validation = validate_phase1_orchestration_executor_result(invalid_result)

    assert validation.is_valid is False
    assert "PHASE1_ORCHESTRATION_EXECUTOR_RESULT_REQUEST_SOURCE_KEY_MISMATCH" in (
        _issue_codes(validation)
    )


def test_executor_result_validation_rejects_executable_readiness() -> None:
    result = create_phase1_orchestration_executor_boundaries()[0]
    invalid_readiness = replace(result.readiness, is_executable=True)
    invalid_result = replace(result, readiness=invalid_readiness)

    validation = validate_phase1_orchestration_executor_result(invalid_result)

    assert validation.is_valid is False
    assert "PHASE1_ORCHESTRATION_EXECUTOR_UNEXPECTED_EXECUTABLE_READINESS" in (
        _issue_codes(validation)
    )


def test_executor_issue_shape_is_structural_and_severity_constrained() -> None:
    issue = Phase1OrchestrationExecutorIssue(
        code=" ",
        message="",
        field_name=" ",
        severity="critical",
    )
    result = plan_phase1_orchestration_executor_boundary(
        create_phase1_orchestration_executor_request(
            create_phase1_orchestration_plans()[0],
        ),
        issues=(issue,),
    )

    validation = validate_phase1_orchestration_executor_result(result)

    assert validation.is_valid is False
    assert "PHASE1_ORCHESTRATION_EXECUTOR_ISSUE_MISSING_CODE" in _issue_codes(validation)
    assert "PHASE1_ORCHESTRATION_EXECUTOR_ISSUE_MISSING_MESSAGE" in (
        _issue_codes(validation)
    )
    assert "PHASE1_ORCHESTRATION_EXECUTOR_ISSUE_MISSING_FIELD_NAME" in (
        _issue_codes(validation)
    )
    assert "PHASE1_ORCHESTRATION_EXECUTOR_ISSUE_INVALID_SEVERITY" in (
        _issue_codes(validation)
    )


def test_executor_batch_validation_prefixes_locations() -> None:
    result = replace(
        create_phase1_orchestration_executor_boundaries()[0],
        source_key="",
    )

    validation = validate_phase1_orchestration_executor_results((result,))

    assert validation.is_valid is False
    assert validation.issues[0].field_name == "results[1].source_key"
    assert validation.issues[0].code == (
        "PHASE1_ORCHESTRATION_EXECUTOR_MISSING_SOURCE_KEY"
    )


def test_validation_does_not_perform_runtime_work(
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
    plan = create_phase1_orchestration_plans((acquisition_result,))[0]
    result = plan_phase1_orchestration_executor_boundary(
        create_phase1_orchestration_executor_request(plan),
    )

    def fail_side_effect(*args: object, **kwargs: object) -> object:
        raise AssertionError("executor boundary validation must use metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "exists", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "is_file", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "stat", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "read_text", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "write_text", fail_side_effect)
    monkeypatch.setattr(hashlib, "sha256", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)

    assert validate_phase1_orchestration_executor_result(result).is_valid is True


def test_executor_boundary_contract_is_read_only() -> None:
    result = create_phase1_orchestration_executor_boundaries()[0]

    with pytest.raises(FrozenInstanceError):
        result.source_key = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.summary.parser_run_request_count = 99  # type: ignore[misc]


def test_validation_result_shape_exposes_is_valid() -> None:
    assert Phase1OrchestrationExecutorValidationResult().is_valid is True
    assert Phase1OrchestrationExecutorValidationResult(
        issues=(
            Phase1OrchestrationExecutorIssue(
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
        "phase1_orchestration_executor_boundary"
    )
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("Phase 1 orchestration executor import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("Phase 1 orchestration executor import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_after = set(sys.modules)

    assert hasattr(module, "create_phase1_orchestration_executor_boundaries")
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
    result: Phase1OrchestrationExecutorValidationResult,
) -> tuple[str, ...]:
    return tuple(issue.code for issue in result.issues)
