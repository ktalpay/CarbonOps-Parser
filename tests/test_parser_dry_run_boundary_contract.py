from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import importlib
import sys
import urllib.request

import pytest

from carbonfactor_parser.parsers.adapter_registry_contract import (
    create_phase1_parser_adapter_registry,
)
from carbonfactor_parser.parsers.input_artifact_contract import (
    ParserInputArtifact,
    create_phase1_parser_input_artifact,
)
from carbonfactor_parser.parsers.parser_run_contract import (
    ParserRunRequest,
    create_parser_run_request,
)
from carbonfactor_parser.parsers.dry_run_boundary_contract import (
    ParserDryRunBoundaryResult,
    ParserDryRunBoundaryStatus,
    ParserDryRunBoundaryValidationIssue,
    ParserDryRunBoundaryValidationResult,
    ParserDryRunEligibility,
    ParserDryRunSummary,
    plan_parser_dry_run_boundary,
    validate_parser_dry_run_boundary_result,
)
from carbonfactor_parser.parsers.source_format_contract import ParserSourceFormat
from carbonfactor_parser.parsers.validation_issue_contract import (
    ParserValidationIssueSeverity,
    create_parser_validation_issue,
)

EXPECTED_SOURCE_FAMILIES = (
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

BANNED_EXECUTABLE_PARSER_MODULES = (
    "carbonfactor_parser.parsers.defra_desnz_adapter",
    "carbonfactor_parser.parsers.defra_desnz_parser",
    "carbonfactor_parser.parsers.execution_runner",
    "carbonfactor_parser.parsers.file_content_loader",
)


def test_dry_run_boundary_can_be_constructed_for_phase1_adapters() -> None:
    registry = create_phase1_parser_adapter_registry()

    results = tuple(
        plan_parser_dry_run_boundary(
            _request_for_source(descriptor.source_family, registry=registry),
            registry,
        )
        for descriptor in registry.descriptors
    )

    assert tuple(result.source_family for result in results) == EXPECTED_SOURCE_FAMILIES
    assert tuple(result.source_key for result in results) == EXPECTED_SOURCE_FAMILIES
    assert all(result.status is ParserDryRunBoundaryStatus.PLANNED for result in results)
    assert all(
        validate_parser_dry_run_boundary_result(result, registry).is_valid
        for result in results
    )


def test_dry_run_request_metadata_aligns_with_adapter_registry() -> None:
    registry = create_phase1_parser_adapter_registry()

    for descriptor in registry.descriptors:
        request = _request_for_source(descriptor.source_family, registry=registry)
        result = plan_parser_dry_run_boundary(request, registry)

        assert result.source_family == descriptor.source_family
        assert result.source_key == descriptor.source_family
        assert result.parser_key == descriptor.parser_key
        assert result.request.source_key == result.source_key
        assert result.request.parser_key == result.parser_key
        assert result.eligibility.source_key == result.source_key
        assert result.eligibility.parser_key == result.parser_key


def test_dry_run_status_values_are_constrained() -> None:
    assert tuple(status.value for status in ParserDryRunBoundaryStatus) == (
        "planned",
        "structurally_invalid",
        "adapter_unregistered",
    )

    result = replace(
        plan_parser_dry_run_boundary(_request_for_source("ghg_protocol")),
        status="ready",  # type: ignore[arg-type]
    )

    validation = validate_parser_dry_run_boundary_result(result)

    assert validation.is_valid is False
    assert "PARSER_DRY_RUN_INVALID_STATUS" in _issue_codes(validation)


def test_dry_run_result_can_include_validation_issues() -> None:
    request = replace(_request_for_source("defra_desnz"), parser_key="")

    result = plan_parser_dry_run_boundary(request)

    assert result.status is ParserDryRunBoundaryStatus.STRUCTURALLY_INVALID
    assert tuple(issue.code for issue in result.issues) == (
        "PARSER_RUN_REQUEST_MISSING_PARSER_KEY",
        "PARSER_RUN_REQUEST_PARSER_KEY_MISMATCH",
        "PARSER_RUN_REQUEST_ARTIFACT_PARSER_KEY_MISMATCH",
    )
    assert all(
        issue.severity is ParserValidationIssueSeverity.ERROR
        for issue in result.issues
    )


def test_dry_run_summary_counts_are_deterministic() -> None:
    request = replace(_request_for_source("ipcc_efdb"), parser_key="")

    first = plan_parser_dry_run_boundary(request)
    second = plan_parser_dry_run_boundary(request)

    assert first.summary == ParserDryRunSummary(
        artifact_count=1,
        issue_count=3,
        info_count=0,
        warning_count=0,
        error_count=3,
    )
    assert first.summary == second.summary


def test_dry_run_helper_uses_readiness_metadata_without_execution_support() -> None:
    result = plan_parser_dry_run_boundary(_request_for_source("ghg_protocol"))

    assert result.eligibility == ParserDryRunEligibility(
        source_family="ghg_protocol",
        source_key="ghg_protocol",
        parser_key="ghg_protocol_phase1_parser",
        readiness="contract_only",
        execution_mode="dry_run",
        supports_parser_execution=False,
        supports_file_reads=False,
        supports_content_inspection=False,
        is_structurally_eligible=True,
    )


def test_dry_run_ordering_is_deterministic() -> None:
    request = _request_for_source("ghg_protocol")
    result = plan_parser_dry_run_boundary(request)

    assert result.request.artifacts == request.artifacts
    assert result == plan_parser_dry_run_boundary(request)


def test_unknown_source_metadata_returns_invalid_result() -> None:
    artifact = ParserInputArtifact(
        source_family="unknown",
        source_key="unknown",
        parser_key="unknown_phase1_parser",
        parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
        format_hint="discovery",
        artifact_reference="artifact://phase1/unknown",
    )
    request = ParserRunRequest(
        source_family="unknown",
        source_key="unknown",
        parser_key="unknown_phase1_parser",
        artifacts=(artifact,),
    )

    result = plan_parser_dry_run_boundary(request)
    validation = validate_parser_dry_run_boundary_result(result)

    assert result.status is ParserDryRunBoundaryStatus.ADAPTER_UNREGISTERED
    assert result.eligibility.readiness == "unregistered"
    assert validation.is_valid is False
    assert "PARSER_DRY_RUN_UNKNOWN_SOURCE_FAMILY" in _issue_codes(validation)


def test_issue_alignment_is_validated() -> None:
    result = plan_parser_dry_run_boundary(_request_for_source("ipcc_efdb"))
    issue = create_parser_validation_issue(
        source_family="ghg_protocol",
        severity=ParserValidationIssueSeverity.ERROR,
        code="WRONG_SOURCE",
        message="Wrong source diagnostic.",
    )
    invalid = replace(result, issues=(issue,), summary=replace(result.summary, issue_count=1))

    validation = validate_parser_dry_run_boundary_result(invalid)

    assert validation.is_valid is False
    assert "PARSER_DRY_RUN_ISSUE_SOURCE_FAMILY_MISMATCH" in _issue_codes(validation)
    assert "PARSER_DRY_RUN_ISSUE_SOURCE_KEY_MISMATCH" in _issue_codes(validation)
    assert "PARSER_DRY_RUN_ISSUE_PARSER_KEY_MISMATCH" in _issue_codes(validation)


def test_summary_count_mismatch_returns_invalid_result() -> None:
    result = replace(
        plan_parser_dry_run_boundary(_request_for_source("defra_desnz")),
        summary=ParserDryRunSummary(
            artifact_count=99,
            issue_count=99,
            info_count=0,
            warning_count=0,
            error_count=0,
        ),
    )

    validation = validate_parser_dry_run_boundary_result(result)

    assert validation.is_valid is False
    assert "PARSER_DRY_RUN_SUMMARY_COUNT_MISMATCH" in _issue_codes(validation)


def test_dry_run_boundary_contract_is_read_only() -> None:
    result = plan_parser_dry_run_boundary(_request_for_source("ghg_protocol"))

    with pytest.raises(FrozenInstanceError):
        result.parser_key = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.eligibility.parser_key = "changed"  # type: ignore[misc]


def test_validation_result_issue_shape_is_structured() -> None:
    result = replace(
        plan_parser_dry_run_boundary(_request_for_source("ghg_protocol")),
        parser_key="",
    )

    issue = validate_parser_dry_run_boundary_result(result).issues[0]

    assert isinstance(issue, ParserDryRunBoundaryValidationIssue)
    assert issue.code == "PARSER_DRY_RUN_MISSING_PARSER_KEY"
    assert issue.field_name == "result.parser_key"
    assert issue.severity == "error"
    assert issue.message == "parser_key must be a non-empty string."


def test_validation_result_shape_exposes_is_valid() -> None:
    assert ParserDryRunBoundaryValidationResult().is_valid is True
    assert ParserDryRunBoundaryValidationResult(
        issues=(
            ParserDryRunBoundaryValidationIssue(
                code="TEST",
                message="test",
                field_name="field",
            ),
        ),
    ).is_valid is False


def test_planner_and_validation_do_not_read_files_access_db_or_network(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    import builtins
    import pathlib
    import sqlite3

    missing_artifact = tmp_path / "missing.csv"

    def fail_side_effect(*args: object, **kwargs: object) -> object:
        raise AssertionError("parser dry-run boundary must use metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "exists", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "is_file", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "stat", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)

    artifact = create_phase1_parser_input_artifact(
        source_family="defra_desnz",
        artifact_reference=str(missing_artifact),
    )
    request = create_parser_run_request(
        source_family="defra_desnz",
        artifacts=(artifact,),
    )
    result = plan_parser_dry_run_boundary(request)

    assert validate_parser_dry_run_boundary_result(result).is_valid is True
    assert result.request.artifacts[0].artifact_reference == str(missing_artifact)


def test_planner_does_not_import_executable_parser_modules() -> None:
    imported_before = set(sys.modules)

    result = plan_parser_dry_run_boundary(_request_for_source("ghg_protocol"))

    imported_after = set(sys.modules)
    newly_imported = imported_after - imported_before
    assert result.parser_key == "ghg_protocol_phase1_parser"
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_EXECUTABLE_PARSER_MODULES
    )


def test_contract_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = "carbonfactor_parser.parsers.dry_run_boundary_contract"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("parser dry-run boundary import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("parser dry-run boundary import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "plan_parser_dry_run_boundary")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_modules_after - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_EXECUTABLE_PARSER_MODULES
    )


def _request_for_source(
    source_family: str,
    *,
    registry=None,
) -> ParserRunRequest:
    artifact = create_phase1_parser_input_artifact(
        source_family=source_family,
        artifact_reference=f"artifact://phase1/{source_family}",
        registry=registry,
    )
    return create_parser_run_request(
        source_family=source_family,
        artifacts=(artifact,),
        run_id=f"{source_family}-dry-run",
        correlation_id="correlation-001",
        registry=registry,
    )


def _issue_codes(
    result: ParserDryRunBoundaryValidationResult,
) -> tuple[str, ...]:
    return tuple(issue.code for issue in result.issues)
