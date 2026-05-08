from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import hashlib
import importlib
import sys
import urllib.request

import pytest

from carbonfactor_parser.parsers.adapter_registry_contract import (
    create_phase1_parser_adapter_registry,
)
from carbonfactor_parser.parsers.parser_run_contract import ParserRunRequest
from carbonfactor_parser.source_acquisition.acquisition_to_parser_plan_contract import (
    AcquisitionToParserPlanIssue,
    AcquisitionToParserPlanResult,
    AcquisitionToParserPlanStatus,
    AcquisitionToParserPlanSummary,
    AcquisitionToParserPlanValidationResult,
    create_acquisition_to_parser_plan,
    create_phase1_acquisition_to_parser_plans,
    validate_acquisition_to_parser_plan,
    validate_acquisition_to_parser_plans,
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


def test_valid_acquisition_to_parser_plans_can_be_constructed_for_phase1() -> None:
    plans = create_phase1_acquisition_to_parser_plans()

    assert tuple(plan.source_key for plan in plans) == EXPECTED_SOURCE_KEYS
    assert all(isinstance(plan, AcquisitionToParserPlanResult) for plan in plans)
    assert all(
        isinstance(plan.parser_run_requests[0], ParserRunRequest)
        for plan in plans
    )
    assert all(validate_acquisition_to_parser_plan(plan).is_valid for plan in plans)


def test_source_acquisition_artifacts_become_parser_inputs_through_bridge() -> None:
    plan = create_phase1_acquisition_to_parser_plans()[0]

    assert tuple(
        entry.source_artifact_id for entry in plan.bridge_result.entries
    ) == plan.acquisition_result.artifact_ids
    assert plan.parser_run_requests[0].artifacts == (
        plan.bridge_result.parser_input_artifacts
    )
    assert tuple(
        artifact.artifact_reference
        for artifact in plan.parser_run_requests[0].artifacts
    ) == tuple(entry.artifact_reference for entry in plan.bridge_result.entries)


def test_generated_parser_run_requests_align_with_adapter_registry_parser_keys() -> None:
    adapter_registry = create_phase1_parser_adapter_registry()
    plans = create_phase1_acquisition_to_parser_plans(registry=adapter_registry)

    assert tuple(plan.parser_keys[0] for plan in plans) == tuple(
        descriptor.parser_key for descriptor in adapter_registry.descriptors
    )
    for plan, descriptor in zip(plans, adapter_registry.descriptors, strict=True):
        request = plan.parser_run_requests[0]
        assert request.parser_key == descriptor.parser_key
        assert all(
            artifact.parser_key == descriptor.parser_key
            for artifact in request.artifacts
        )


def test_source_keys_remain_consistent_across_plan_boundaries() -> None:
    for plan in create_phase1_acquisition_to_parser_plans():
        request = plan.parser_run_requests[0]

        assert plan.acquisition_result.source_key == plan.source_key
        assert plan.bridge_result.entries[0].source_key == plan.source_key
        assert request.source_key == plan.source_key
        assert request.artifacts[0].source_key == plan.source_key


def test_plan_status_values_are_constrained_to_deterministic_allowed_set() -> None:
    assert tuple(status.value for status in AcquisitionToParserPlanStatus) == (
        "declared",
        "planned",
        "planned_with_issues",
        "failed",
    )

    plan = replace(
        create_phase1_acquisition_to_parser_plans()[0],
        status="done",  # type: ignore[arg-type]
    )

    validation = validate_acquisition_to_parser_plan(plan)

    assert validation.is_valid is False
    assert "ACQUISITION_TO_PARSER_PLAN_INVALID_STATUS" in _issue_codes(validation)


@pytest.mark.parametrize(
    ("field_name", "expected_code"),
    (
        ("source_family", "ACQUISITION_TO_PARSER_PLAN_MISSING_SOURCE_FAMILY"),
        ("source_key", "ACQUISITION_TO_PARSER_PLAN_MISSING_SOURCE_KEY"),
    ),
)
def test_required_plan_metadata_fields_reject_empty_strings(
    field_name: str,
    expected_code: str,
) -> None:
    plan = replace(
        create_phase1_acquisition_to_parser_plans()[0],
        **{field_name: " "},
    )

    validation = validate_acquisition_to_parser_plan(plan)

    assert validation.is_valid is False
    assert expected_code in _issue_codes(validation)


def test_blank_acquisition_run_identifier_rejects_empty_string() -> None:
    plan = replace(
        create_phase1_acquisition_to_parser_plans()[0],
        acquisition_run_id="",
    )

    validation = validate_acquisition_to_parser_plan(plan)

    assert validation.is_valid is False
    assert "ACQUISITION_TO_PARSER_PLAN_BLANK_ACQUISITION_RUN_ID" in (
        _issue_codes(validation)
    )


def test_summary_counts_are_deterministic() -> None:
    issue = AcquisitionToParserPlanIssue(
        code="ACQUISITION_TO_PARSER_PLAN_TEST_WARNING",
        message="test warning",
        field_name="bridge_result.entries[1]",
        severity="warning",
    )
    acquisition_result = create_phase1_source_acquisition_run_results()[0]
    plan = create_acquisition_to_parser_plan(
        acquisition_result,
        status=AcquisitionToParserPlanStatus.PLANNED_WITH_ISSUES,
        issues=(issue,),
    )

    assert plan.summary == AcquisitionToParserPlanSummary(
        downloaded_artifact_count=1,
        bridge_entry_count=1,
        parser_input_artifact_count=1,
        parser_run_request_count=1,
        issue_count=1,
    )
    assert create_acquisition_to_parser_plan(
        acquisition_result,
        status=AcquisitionToParserPlanStatus.PLANNED_WITH_ISSUES,
        issues=(issue,),
    ).summary == plan.summary


def test_summary_count_mismatches_return_invalid_result() -> None:
    plan = replace(
        create_phase1_acquisition_to_parser_plans()[1],
        summary=AcquisitionToParserPlanSummary(
            downloaded_artifact_count=99,
            bridge_entry_count=99,
            parser_input_artifact_count=99,
            parser_run_request_count=99,
            issue_count=99,
        ),
    )

    validation = validate_acquisition_to_parser_plan(plan)

    assert validation.is_valid is False
    assert "ACQUISITION_TO_PARSER_PLAN_SUMMARY_ARTIFACT_COUNT_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "ACQUISITION_TO_PARSER_PLAN_SUMMARY_BRIDGE_COUNT_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "ACQUISITION_TO_PARSER_PLAN_SUMMARY_REQUEST_COUNT_MISMATCH" in (
        _issue_codes(validation)
    )


def test_ordering_is_deterministic() -> None:
    first = create_phase1_acquisition_to_parser_plans()
    second = create_phase1_acquisition_to_parser_plans()

    assert first == second
    assert tuple(plan.source_key for plan in first) == EXPECTED_SOURCE_KEYS
    assert tuple(plan.artifact_references for plan in first) == (
        ("download://phase1/ghg_protocol/artifact",),
        ("download://phase1/defra_desnz/artifact",),
        ("download://phase1/ipcc_efdb/artifact",),
    )


def test_plan_alignment_rejects_mismatched_acquisition_result() -> None:
    plan = create_phase1_acquisition_to_parser_plans()[0]
    invalid_plan = replace(
        plan,
        source_key="defra_desnz",
    )

    validation = validate_acquisition_to_parser_plan(invalid_plan)

    assert validation.is_valid is False
    assert "ACQUISITION_TO_PARSER_PLAN_ACQUISITION_SOURCE_KEY_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "ACQUISITION_TO_PARSER_PLAN_BRIDGE_SOURCE_KEY_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "ACQUISITION_TO_PARSER_PLAN_REQUEST_SOURCE_KEY_MISMATCH" in (
        _issue_codes(validation)
    )


def test_plan_alignment_rejects_mismatched_bridge_output() -> None:
    plan = create_phase1_acquisition_to_parser_plans()[2]
    invalid_entry = replace(
        plan.bridge_result.entries[0],
        source_key="ghg_protocol",
    )
    invalid_plan = replace(
        plan,
        bridge_result=replace(plan.bridge_result, entries=(invalid_entry,)),
    )

    validation = validate_acquisition_to_parser_plan(invalid_plan)

    assert validation.is_valid is False
    assert "ACQUISITION_TO_PARSER_PLAN_BRIDGE_SOURCE_KEY_MISMATCH" in (
        _issue_codes(validation)
    )


def test_plan_alignment_rejects_mismatched_parser_run_request() -> None:
    plan = create_phase1_acquisition_to_parser_plans()[1]
    request = plan.parser_run_requests[0]
    invalid_artifact = replace(request.artifacts[0], source_key="ghg_protocol")
    invalid_request = replace(
        request,
        source_key="ghg_protocol",
        artifacts=(invalid_artifact,),
    )
    invalid_plan = replace(plan, parser_run_requests=(invalid_request,))

    validation = validate_acquisition_to_parser_plan(invalid_plan)

    assert validation.is_valid is False
    assert "ACQUISITION_TO_PARSER_PLAN_REQUEST_SOURCE_KEY_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "ACQUISITION_TO_PARSER_PLAN_REQUEST_ARTIFACTS_MISMATCH" in (
        _issue_codes(validation)
    )


def test_plan_issue_shape_is_structural_and_severity_constrained() -> None:
    issue = AcquisitionToParserPlanIssue(
        code=" ",
        message="",
        field_name=" ",
        severity="critical",
    )
    plan = create_acquisition_to_parser_plan(
        create_phase1_source_acquisition_run_results()[0],
        issues=(issue,),
    )

    validation = validate_acquisition_to_parser_plan(plan)

    assert validation.is_valid is False
    assert "ACQUISITION_TO_PARSER_PLAN_ISSUE_MISSING_CODE" in _issue_codes(validation)
    assert "ACQUISITION_TO_PARSER_PLAN_ISSUE_MISSING_MESSAGE" in (
        _issue_codes(validation)
    )
    assert "ACQUISITION_TO_PARSER_PLAN_ISSUE_MISSING_FIELD_NAME" in (
        _issue_codes(validation)
    )
    assert "ACQUISITION_TO_PARSER_PLAN_ISSUE_INVALID_SEVERITY" in (
        _issue_codes(validation)
    )


def test_plan_batch_validation_prefixes_locations() -> None:
    plan = replace(
        create_phase1_acquisition_to_parser_plans()[0],
        source_key="",
    )

    validation = validate_acquisition_to_parser_plans((plan,))

    assert validation.is_valid is False
    assert validation.issues[0].field_name == "plans[1].source_key"
    assert validation.issues[0].code == (
        "ACQUISITION_TO_PARSER_PLAN_MISSING_SOURCE_KEY"
    )


def test_local_reference_metadata_is_not_opened_statted_read_written_or_hashed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    import builtins
    import pathlib

    missing_artifact = tmp_path / "downloaded.csv"
    acquisition_result = create_phase1_source_acquisition_run_results()[0]
    acquisition_result = replace(
        acquisition_result,
        artifacts=(
            replace(
                acquisition_result.artifacts[0],
                local_reference=str(missing_artifact),
            ),
        ),
    )
    plan = create_acquisition_to_parser_plan(acquisition_result)

    def fail_side_effect(*args: object, **kwargs: object) -> object:
        raise AssertionError("plan validation must treat references as metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "exists", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "is_file", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "stat", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "read_text", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "write_text", fail_side_effect)
    monkeypatch.setattr(hashlib, "sha256", fail_side_effect)

    assert validate_acquisition_to_parser_plan(plan).is_valid is True


def test_url_reference_metadata_is_not_fetched_or_network_validated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    acquisition_result = create_phase1_source_acquisition_run_results()[0]
    acquisition_result = replace(
        acquisition_result,
        artifacts=(
            replace(
                acquisition_result.artifacts[0],
                source_reference_uri="discovery://not-fetched/source.csv",
            ),
        ),
    )
    plan = create_acquisition_to_parser_plan(acquisition_result)

    def fail_urlopen(*args: object, **kwargs: object) -> object:
        raise AssertionError("plan validation must not fetch references")

    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)

    assert validate_acquisition_to_parser_plan(plan).is_valid is True


def test_validation_does_not_access_db_or_execute_parsers(
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
    plan = create_acquisition_to_parser_plan(acquisition_result)

    def fail_side_effect(*args: object, **kwargs: object) -> object:
        raise AssertionError("plan validation must use metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "exists", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "is_file", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "stat", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)

    assert validate_acquisition_to_parser_plan(plan).is_valid is True


def test_acquisition_to_parser_plan_contract_is_read_only() -> None:
    plan = create_phase1_acquisition_to_parser_plans()[0]

    with pytest.raises(FrozenInstanceError):
        plan.source_key = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        plan.summary.downloaded_artifact_count = 99  # type: ignore[misc]


def test_validation_result_shape_exposes_is_valid() -> None:
    assert AcquisitionToParserPlanValidationResult().is_valid is True
    assert AcquisitionToParserPlanValidationResult(
        issues=(
            AcquisitionToParserPlanIssue(
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
        "acquisition_to_parser_plan_contract"
    )
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("acquisition-to-parser plan import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("acquisition-to-parser plan import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_after = set(sys.modules)

    assert hasattr(module, "create_phase1_acquisition_to_parser_plans")
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
    result: AcquisitionToParserPlanValidationResult,
) -> tuple[str, ...]:
    return tuple(issue.code for issue in result.issues)
