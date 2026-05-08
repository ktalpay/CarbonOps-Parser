from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import importlib
import sys
import urllib.request

import pytest

from carbonfactor_parser.source_acquisition.discovery_candidate_contract import (
    SourceDiscoveryCandidateResult,
    create_phase1_source_discovery_candidates,
)
from carbonfactor_parser.source_acquisition.download_artifact_contract import (
    SourceDownloadArtifactResult,
    create_phase1_source_download_artifacts,
)
from carbonfactor_parser.source_acquisition.registry import (
    create_default_source_acquisition_registry,
)
from carbonfactor_parser.source_acquisition.run_contract import (
    SourceAcquisitionRunIssue,
    SourceAcquisitionRunRequest,
    SourceAcquisitionRunResult,
    SourceAcquisitionRunStatus,
    SourceAcquisitionRunSummary,
    SourceAcquisitionRunValidationResult,
    create_phase1_source_acquisition_run_requests,
    create_phase1_source_acquisition_run_results,
    create_source_acquisition_run_request,
    create_source_acquisition_run_result,
    validate_source_acquisition_run_request,
    validate_source_acquisition_run_result,
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

BANNED_EXECUTABLE_PARSER_MODULES = (
    "carbonfactor_parser.parsers.defra_desnz_adapter",
    "carbonfactor_parser.parsers.defra_desnz_parser",
    "carbonfactor_parser.parsers.execution_runner",
    "carbonfactor_parser.parsers.file_content_loader",
)


def test_valid_source_acquisition_run_request_and_result_for_phase1_sources() -> None:
    requests = create_phase1_source_acquisition_run_requests()
    results = create_phase1_source_acquisition_run_results()

    assert tuple(request.source_key for request in requests) == EXPECTED_SOURCE_KEYS
    assert tuple(result.source_key for result in results) == EXPECTED_SOURCE_KEYS
    assert all(
        validate_source_acquisition_run_request(request).is_valid
        for request in requests
    )
    assert all(
        validate_source_acquisition_run_result(result).is_valid
        for result in results
    )


def test_run_requests_align_with_existing_phase1_registry_metadata() -> None:
    registry = create_default_source_acquisition_registry()
    requests = create_phase1_source_acquisition_run_requests()

    assert tuple(request.source_key for request in requests) == tuple(
        descriptor.source_id for descriptor in registry
    )
    assert tuple(request.source_family for request in requests) == tuple(
        descriptor.source_family for descriptor in registry
    )


def test_candidates_and_artifacts_align_with_the_run_source_key() -> None:
    for result in create_phase1_source_acquisition_run_results():
        assert all(
            candidate.source_key == result.source_key
            and candidate.source_family == result.source_family
            for candidate in result.candidates
        )
        assert all(
            artifact.source_key == result.source_key
            and artifact.source_family == result.source_family
            for artifact in result.artifacts
        )
        assert tuple(artifact.candidate_id for artifact in result.artifacts) == (
            result.candidate_ids
        )


def test_run_status_values_are_constrained_to_deterministic_allowed_set() -> None:
    assert tuple(status.value for status in SourceAcquisitionRunStatus) == (
        "declared",
        "completed",
        "completed_with_issues",
        "failed",
    )

    result = replace(
        create_phase1_source_acquisition_run_results()[0],
        status="done",  # type: ignore[arg-type]
    )

    validation = validate_source_acquisition_run_result(result)

    assert validation.is_valid is False
    assert "SOURCE_ACQUISITION_RUN_RESULT_INVALID_STATUS" in _issue_codes(validation)


@pytest.mark.parametrize(
    ("field_name", "expected_code"),
    (
        ("source_family", "SOURCE_ACQUISITION_RUN_REQUEST_MISSING_SOURCE_FAMILY"),
        ("source_key", "SOURCE_ACQUISITION_RUN_REQUEST_MISSING_SOURCE_KEY"),
    ),
)
def test_request_required_metadata_fields_reject_empty_strings(
    field_name: str,
    expected_code: str,
) -> None:
    request = replace(
        create_source_acquisition_run_request(source_key="ghg_protocol"),
        **{field_name: " "},
    )

    validation = validate_source_acquisition_run_request(request)

    assert validation.is_valid is False
    assert expected_code in _issue_codes(validation)


@pytest.mark.parametrize(
    ("field_name", "expected_code"),
    (
        ("source_family", "SOURCE_ACQUISITION_RUN_RESULT_MISSING_SOURCE_FAMILY"),
        ("source_key", "SOURCE_ACQUISITION_RUN_RESULT_MISSING_SOURCE_KEY"),
    ),
)
def test_result_required_metadata_fields_reject_empty_strings(
    field_name: str,
    expected_code: str,
) -> None:
    result = replace(
        create_source_acquisition_run_result(
            create_source_acquisition_run_request(source_key="defra_desnz"),
        ),
        **{field_name: ""},
    )

    validation = validate_source_acquisition_run_result(result)

    assert validation.is_valid is False
    assert expected_code in _issue_codes(validation)


def test_optional_request_metadata_rejects_blank_strings_and_invalid_years() -> None:
    request = replace(
        create_source_acquisition_run_request(
            source_key="ipcc_efdb",
            run_id="run-001",
            requested_document_year=2024,
            requested_reporting_year=2024,
            version_label="v1",
        ),
        run_id=" ",
        version_label="",
        requested_document_year=0,
        requested_reporting_year=-1,
    )

    validation = validate_source_acquisition_run_request(request)

    assert validation.is_valid is False
    assert _issue_codes(validation) == (
        "SOURCE_ACQUISITION_RUN_REQUEST_BLANK_RUN_ID",
        "SOURCE_ACQUISITION_RUN_REQUEST_BLANK_VERSION_LABEL",
        "SOURCE_ACQUISITION_RUN_REQUEST_INVALID_DOCUMENT_YEAR",
        "SOURCE_ACQUISITION_RUN_REQUEST_INVALID_REPORTING_YEAR",
    )


def test_missing_candidates_return_invalid_request() -> None:
    request = replace(
        create_source_acquisition_run_request(source_key="ghg_protocol"),
        candidates=(),
    )

    validation = validate_source_acquisition_run_request(request)

    assert validation.is_valid is False
    assert _issue_codes(validation) == (
        "SOURCE_ACQUISITION_RUN_REQUEST_MISSING_CANDIDATES",
    )


def test_request_rejects_candidate_source_mismatch() -> None:
    request = create_source_acquisition_run_request(source_key="defra_desnz")
    invalid_candidate = replace(
        request.candidates[0],
        source_family="ghg_protocol",
        source_key="ghg_protocol",
    )
    invalid_request = replace(request, candidates=(invalid_candidate,))

    validation = validate_source_acquisition_run_request(invalid_request)

    assert validation.is_valid is False
    assert "SOURCE_ACQUISITION_RUN_REQUEST_CANDIDATE_SOURCE_FAMILY_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "SOURCE_ACQUISITION_RUN_REQUEST_CANDIDATE_SOURCE_KEY_MISMATCH" in (
        _issue_codes(validation)
    )


def test_result_rejects_candidate_and_artifact_source_mismatch() -> None:
    result = create_source_acquisition_run_result(
        create_source_acquisition_run_request(source_key="ipcc_efdb"),
    )
    invalid_candidate = replace(
        result.candidates[0],
        source_family="ghg_protocol",
        source_key="ghg_protocol",
    )
    invalid_artifact = replace(
        result.artifacts[0],
        source_family="ghg_protocol",
        source_key="ghg_protocol",
        candidate_id="not-a-run-candidate",
    )
    invalid_result = replace(
        result,
        candidates=(invalid_candidate,),
        artifacts=(invalid_artifact,),
    )

    validation = validate_source_acquisition_run_result(invalid_result)

    assert validation.is_valid is False
    assert "SOURCE_ACQUISITION_RUN_RESULT_CANDIDATE_SOURCE_FAMILY_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "SOURCE_ACQUISITION_RUN_RESULT_CANDIDATE_SOURCE_KEY_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "SOURCE_ACQUISITION_RUN_RESULT_ARTIFACT_SOURCE_FAMILY_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "SOURCE_ACQUISITION_RUN_RESULT_ARTIFACT_SOURCE_KEY_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "SOURCE_ACQUISITION_RUN_RESULT_ARTIFACT_CANDIDATE_ID_MISMATCH" in (
        _issue_codes(validation)
    )


def test_unknown_source_metadata_fails_clearly() -> None:
    candidate = create_phase1_source_discovery_candidates().candidates[0]
    artifact = create_phase1_source_download_artifacts().artifacts[0]
    request = SourceAcquisitionRunRequest(
        source_family="unknown",
        source_key="unknown",
        candidates=(replace(candidate, source_family="unknown", source_key="unknown"),),
    )
    result = SourceAcquisitionRunResult(
        source_family="unknown",
        source_key="unknown",
        status=SourceAcquisitionRunStatus.DECLARED,
        candidates=request.candidates,
        artifacts=(replace(artifact, source_family="unknown", source_key="unknown"),),
        issues=(),
        summary=SourceAcquisitionRunSummary(
            candidate_count=1,
            artifact_count=1,
            issue_count=0,
            info_count=0,
            warning_count=0,
            error_count=0,
        ),
    )

    assert "SOURCE_ACQUISITION_RUN_REQUEST_UNKNOWN_SOURCE_KEY" in _issue_codes(
        validate_source_acquisition_run_request(request)
    )
    assert "SOURCE_ACQUISITION_RUN_RESULT_UNKNOWN_SOURCE_KEY" in _issue_codes(
        validate_source_acquisition_run_result(result)
    )


def test_factory_rejects_unknown_source_without_inventing_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="source_key is not registered for a Phase 1 source",
    ):
        create_source_acquisition_run_request(source_key="unknown")


def test_candidate_and_artifact_ordering_is_deterministic() -> None:
    first_requests = create_phase1_source_acquisition_run_requests()
    second_requests = create_phase1_source_acquisition_run_requests()
    first_results = create_phase1_source_acquisition_run_results()
    second_results = create_phase1_source_acquisition_run_results()

    assert first_requests == second_requests
    assert first_results == second_results
    assert tuple(request.source_key for request in first_requests) == EXPECTED_SOURCE_KEYS
    assert tuple(result.source_key for result in first_results) == EXPECTED_SOURCE_KEYS
    assert tuple(result.candidate_ids for result in first_results) == (
        ("phase1_candidate_001_ghg_protocol",),
        ("phase1_candidate_002_defra_desnz",),
        ("phase1_candidate_003_ipcc_efdb",),
    )


def test_summary_counts_are_deterministic() -> None:
    issue = SourceAcquisitionRunIssue(
        code="SOURCE_ACQUISITION_RUN_TEST_WARNING",
        message="test warning",
        field_name="candidates[1]",
        severity="warning",
    )
    request = create_source_acquisition_run_request(source_key="ghg_protocol")
    result = create_source_acquisition_run_result(
        request,
        status=SourceAcquisitionRunStatus.COMPLETED_WITH_ISSUES,
        issues=(issue,),
    )

    assert result.summary == SourceAcquisitionRunSummary(
        candidate_count=1,
        artifact_count=1,
        issue_count=1,
        info_count=0,
        warning_count=1,
        error_count=0,
    )
    assert create_source_acquisition_run_result(
        request,
        status=SourceAcquisitionRunStatus.COMPLETED_WITH_ISSUES,
        issues=(issue,),
    ).summary == result.summary


def test_summary_count_mismatches_return_invalid_result() -> None:
    result = replace(
        create_source_acquisition_run_result(
            create_source_acquisition_run_request(source_key="defra_desnz"),
        ),
        summary=SourceAcquisitionRunSummary(
            candidate_count=99,
            artifact_count=99,
            issue_count=99,
            info_count=99,
            warning_count=99,
            error_count=99,
        ),
    )

    validation = validate_source_acquisition_run_result(result)

    assert validation.is_valid is False
    assert "SOURCE_ACQUISITION_RUN_RESULT_SUMMARY_CANDIDATE_COUNT_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "SOURCE_ACQUISITION_RUN_RESULT_SUMMARY_ARTIFACT_COUNT_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "SOURCE_ACQUISITION_RUN_RESULT_SUMMARY_ISSUE_COUNT_MISMATCH" in (
        _issue_codes(validation)
    )


def test_run_issue_shape_is_structural_and_severity_constrained() -> None:
    issue = SourceAcquisitionRunIssue(
        code=" ",
        message="",
        field_name=" ",
        severity="critical",
    )
    result = create_source_acquisition_run_result(
        create_source_acquisition_run_request(source_key="ghg_protocol"),
        issues=(issue,),
    )

    validation = validate_source_acquisition_run_result(result)

    assert validation.is_valid is False
    assert "SOURCE_ACQUISITION_RUN_RESULT_ISSUE_MISSING_CODE" in _issue_codes(validation)
    assert "SOURCE_ACQUISITION_RUN_RESULT_ISSUE_MISSING_MESSAGE" in (
        _issue_codes(validation)
    )
    assert "SOURCE_ACQUISITION_RUN_RESULT_ISSUE_MISSING_FIELD_NAME" in (
        _issue_codes(validation)
    )
    assert "SOURCE_ACQUISITION_RUN_RESULT_ISSUE_INVALID_SEVERITY" in (
        _issue_codes(validation)
    )


def test_result_can_use_explicit_discovery_and_download_contract_objects() -> None:
    candidates = create_phase1_source_discovery_candidates()
    request = create_source_acquisition_run_request(
        source_key="ghg_protocol",
        candidates=SourceDiscoveryCandidateResult(candidates=(candidates.candidates[0],)),
        run_id="run-001",
        version_label="phase1",
    )
    artifacts = create_phase1_source_download_artifacts(
        SourceDiscoveryCandidateResult(candidates=request.candidates),
    )
    result = create_source_acquisition_run_result(
        request,
        status=SourceAcquisitionRunStatus.COMPLETED,
        artifacts=SourceDownloadArtifactResult(artifacts=artifacts.artifacts),
    )

    assert result.run_id == "run-001"
    assert result.version_label == "phase1"
    assert result.candidates == request.candidates
    assert result.artifacts == artifacts.artifacts
    assert validate_source_acquisition_run_result(result).is_valid is True


def test_validation_does_not_perform_network_file_db_or_parser_execution(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    import builtins
    import pathlib
    import sqlite3

    missing_artifact = tmp_path / "downloaded.csv"

    def fail_side_effect(*args: object, **kwargs: object) -> object:
        raise AssertionError("source acquisition run contract must use metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "exists", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "is_file", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "stat", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "read_text", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "write_text", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)

    result = create_source_acquisition_run_result(
        create_source_acquisition_run_request(source_key="ghg_protocol"),
    )
    result = replace(
        result,
        artifacts=(
            replace(
                result.artifacts[0],
                source_reference_uri="discovery://not-fetched/source.csv",
                local_reference=str(missing_artifact),
            ),
        ),
    )

    assert validate_source_acquisition_run_result(result).is_valid is True


def test_source_acquisition_run_contract_is_read_only() -> None:
    result = create_phase1_source_acquisition_run_results()[0]

    with pytest.raises(FrozenInstanceError):
        result.source_key = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.summary.candidate_count = 99  # type: ignore[misc]


def test_validation_result_shape_exposes_is_valid() -> None:
    assert SourceAcquisitionRunValidationResult().is_valid is True
    assert SourceAcquisitionRunValidationResult(
        issues=(
            SourceAcquisitionRunIssue(
                code="TEST",
                message="test",
                field_name="field",
            ),
        ),
    ).is_valid is False


def test_import_remains_runtime_passive(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins
    import os

    module_name = "carbonfactor_parser.source_acquisition.run_contract"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("source acquisition run contract import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("source acquisition run contract import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_after = set(sys.modules)

    assert hasattr(module, "create_phase1_source_acquisition_run_results")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_after - imported_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in (*BANNED_RUNTIME_MODULE_PREFIXES, *BANNED_EXECUTABLE_PARSER_MODULES)
    )


def _issue_codes(
    result: SourceAcquisitionRunValidationResult,
) -> tuple[str, ...]:
    return tuple(issue.code for issue in result.issues)
