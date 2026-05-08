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
from carbonfactor_parser.parsers.normalized_output_row_contract import (
    create_parser_normalized_output_row,
)
from carbonfactor_parser.parsers.parser_run_contract import (
    ParserRunContractValidationIssue,
    ParserRunContractValidationResult,
    ParserRunRequest,
    ParserRunResult,
    ParserRunStatus,
    ParserRunSummary,
    create_parser_run_request,
    create_parser_run_result,
    validate_parser_run_request,
    validate_parser_run_result,
)
from carbonfactor_parser.parsers.source_format_contract import ParserSourceFormat
from carbonfactor_parser.parsers.validation_issue_contract import (
    ParserValidationIssue,
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


def test_valid_parser_run_request_and_result_can_be_constructed_for_phase1() -> None:
    registry = create_phase1_parser_adapter_registry()

    requests = tuple(
        _request_for_source(descriptor.source_family, registry=registry)
        for descriptor in registry.descriptors
    )
    results = tuple(
        _result_for_request(request, status=ParserRunStatus.COMPLETED)
        for request in requests
    )

    assert tuple(request.source_family for request in requests) == (
        EXPECTED_SOURCE_FAMILIES
    )
    assert tuple(result.source_key for result in results) == EXPECTED_SOURCE_FAMILIES
    assert all(validate_parser_run_request(request, registry).is_valid for request in requests)
    assert all(validate_parser_run_result(result, registry).is_valid for result in results)


def test_request_artifacts_align_with_adapter_registry_source_and_parser_keys() -> None:
    registry = create_phase1_parser_adapter_registry()

    for descriptor in registry.descriptors:
        request = _request_for_source(descriptor.source_family, registry=registry)
        artifact = request.artifacts[0]

        assert request.source_family == descriptor.source_family
        assert request.source_key == descriptor.source_family
        assert request.parser_key == descriptor.parser_key
        assert artifact.source_family == request.source_family
        assert artifact.source_key == request.source_key
        assert artifact.parser_key == request.parser_key


def test_result_rows_and_issues_align_with_adapter_registry_keys() -> None:
    registry = create_phase1_parser_adapter_registry()

    for descriptor in registry.descriptors:
        request = _request_for_source(descriptor.source_family, registry=registry)
        result = _result_for_request(request)

        assert result.source_family == descriptor.source_family
        assert result.parser_key == descriptor.parser_key
        assert result.rows[0].source_key == result.source_key
        assert result.rows[0].parser_key == result.parser_key
        assert result.issues[0].source_key == result.source_key
        assert result.issues[0].parser_key == result.parser_key


def test_run_status_values_are_constrained_to_deterministic_allowed_set() -> None:
    assert tuple(status.value for status in ParserRunStatus) == (
        "declared",
        "completed",
        "completed_with_issues",
        "failed",
    )

    result = replace(_result_for_request(_request_for_source("ghg_protocol")), status="done")  # type: ignore[arg-type]

    validation = validate_parser_run_result(result)

    assert validation.is_valid is False
    assert "PARSER_RUN_RESULT_INVALID_STATUS" in _issue_codes(validation)


@pytest.mark.parametrize(
    ("field_name", "expected_code"),
    (
        ("source_family", "PARSER_RUN_REQUEST_MISSING_SOURCE_FAMILY"),
        ("source_key", "PARSER_RUN_REQUEST_MISSING_SOURCE_KEY"),
        ("parser_key", "PARSER_RUN_REQUEST_MISSING_PARSER_KEY"),
    ),
)
def test_request_required_metadata_fields_reject_empty_strings(
    field_name: str,
    expected_code: str,
) -> None:
    request = replace(_request_for_source("defra_desnz"), **{field_name: " "})

    validation = validate_parser_run_request(request)

    assert validation.is_valid is False
    assert expected_code in _issue_codes(validation)


@pytest.mark.parametrize(
    ("field_name", "expected_code"),
    (
        ("source_family", "PARSER_RUN_RESULT_MISSING_SOURCE_FAMILY"),
        ("source_key", "PARSER_RUN_RESULT_MISSING_SOURCE_KEY"),
        ("parser_key", "PARSER_RUN_RESULT_MISSING_PARSER_KEY"),
    ),
)
def test_result_required_metadata_fields_reject_empty_strings(
    field_name: str,
    expected_code: str,
) -> None:
    result = replace(_result_for_request(_request_for_source("ipcc_efdb")), **{field_name: ""})

    validation = validate_parser_run_result(result)

    assert validation.is_valid is False
    assert expected_code in _issue_codes(validation)


def test_request_rejects_missing_artifacts() -> None:
    request = replace(_request_for_source("ghg_protocol"), artifacts=())

    validation = validate_parser_run_request(request)

    assert validation.is_valid is False
    assert _issue_codes(validation) == ("PARSER_RUN_REQUEST_MISSING_ARTIFACTS",)


def test_request_rejects_artifact_source_or_parser_mismatch() -> None:
    request = _request_for_source("ipcc_efdb")
    invalid_artifact = replace(
        request.artifacts[0],
        source_family="ghg_protocol",
        source_key="ghg_protocol",
        parser_key="ghg_protocol_phase1_parser",
    )
    invalid_request = replace(request, artifacts=(invalid_artifact,))

    validation = validate_parser_run_request(invalid_request)

    assert validation.is_valid is False
    assert _issue_codes(validation) == (
        "PARSER_RUN_REQUEST_ARTIFACT_SOURCE_FAMILY_MISMATCH",
        "PARSER_RUN_REQUEST_ARTIFACT_SOURCE_KEY_MISMATCH",
        "PARSER_RUN_REQUEST_ARTIFACT_PARSER_KEY_MISMATCH",
    )


def test_result_rejects_row_and_issue_source_or_parser_mismatch() -> None:
    request = _request_for_source("defra_desnz")
    result = _result_for_request(request)
    invalid_row = replace(
        result.rows[0],
        source_family="ghg_protocol",
        source_key="ghg_protocol",
        parser_key="ghg_protocol_phase1_parser",
    )
    invalid_issue = replace(
        result.issues[0],
        source_family="ghg_protocol",
        source_key="ghg_protocol",
        parser_key="ghg_protocol_phase1_parser",
    )
    invalid_result = replace(result, rows=(invalid_row,), issues=(invalid_issue,))

    validation = validate_parser_run_result(invalid_result)

    assert validation.is_valid is False
    assert "PARSER_RUN_RESULT_ROW_SOURCE_FAMILY_MISMATCH" in _issue_codes(validation)
    assert "PARSER_RUN_RESULT_ROW_SOURCE_KEY_MISMATCH" in _issue_codes(validation)
    assert "PARSER_RUN_RESULT_ROW_PARSER_KEY_MISMATCH" in _issue_codes(validation)
    assert "PARSER_RUN_RESULT_ISSUE_SOURCE_FAMILY_MISMATCH" in _issue_codes(validation)
    assert "PARSER_RUN_RESULT_ISSUE_SOURCE_KEY_MISMATCH" in _issue_codes(validation)
    assert "PARSER_RUN_RESULT_ISSUE_PARSER_KEY_MISMATCH" in _issue_codes(validation)


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
    result = ParserRunResult(
        source_family="unknown",
        source_key="unknown",
        parser_key="unknown_phase1_parser",
        status=ParserRunStatus.DECLARED,
        rows=(),
        issues=(),
        summary=ParserRunSummary(
            artifact_count=1,
            row_count=0,
            issue_count=0,
            info_count=0,
            warning_count=0,
            error_count=0,
        ),
    )

    assert _issue_codes(validate_parser_run_request(request)) == (
        "PARSER_RUN_REQUEST_UNKNOWN_SOURCE_FAMILY",
    )
    assert _issue_codes(validate_parser_run_result(result)) == (
        "PARSER_RUN_RESULT_UNKNOWN_SOURCE_FAMILY",
        "PARSER_RUN_RESULT_SUMMARY_ARTIFACT_COUNT_MISMATCH",
    )


def test_factory_rejects_unknown_source_without_inventing_parser_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="source_family is not registered for a Phase 1 parser adapter",
    ):
        create_parser_run_request(
            source_family="unknown",
            artifacts=(),
        )


def test_summary_counts_are_deterministic() -> None:
    request = _request_for_source("ghg_protocol")
    result = _result_for_request(request)

    assert result.summary == ParserRunSummary(
        artifact_count=1,
        row_count=1,
        issue_count=1,
        info_count=0,
        warning_count=1,
        error_count=0,
    )
    assert result.artifact_references == ("artifact://phase1/ghg_protocol",)
    assert _result_for_request(request).summary == result.summary


def test_summary_count_mismatch_returns_invalid_result() -> None:
    result = replace(
        _result_for_request(_request_for_source("defra_desnz")),
        summary=ParserRunSummary(
            artifact_count=1,
            row_count=99,
            issue_count=99,
            info_count=0,
            warning_count=0,
            error_count=0,
        ),
    )

    validation = validate_parser_run_result(result)

    assert validation.is_valid is False
    assert "PARSER_RUN_RESULT_SUMMARY_ROW_COUNT_MISMATCH" in _issue_codes(validation)
    assert "PARSER_RUN_RESULT_SUMMARY_ISSUE_COUNT_MISMATCH" in _issue_codes(validation)


def test_artifact_row_and_issue_ordering_is_deterministic() -> None:
    first_artifact = create_phase1_parser_input_artifact(
        source_family="ghg_protocol",
        artifact_reference="artifact://phase1/ghg_protocol/1",
    )
    second_artifact = create_phase1_parser_input_artifact(
        source_family="ghg_protocol",
        artifact_reference="artifact://phase1/ghg_protocol/2",
    )
    request = create_parser_run_request(
        source_family="ghg_protocol",
        artifacts=(second_artifact, first_artifact),
        run_metadata={"zeta": "last", "alpha": "first"},
    )
    first_row = _row_for_artifact(first_artifact, "row-001")
    second_row = _row_for_artifact(second_artifact, "row-002")
    first_issue = _issue_for_source("ghg_protocol", "FIRST")
    second_issue = _issue_for_source("ghg_protocol", "SECOND")
    result = create_parser_run_result(
        request=request,
        status=ParserRunStatus.COMPLETED_WITH_ISSUES,
        rows=(second_row, first_row),
        issues=(second_issue, first_issue),
        run_metadata={"zeta": "last", "alpha": "first"},
    )

    assert request.artifacts == (second_artifact, first_artifact)
    assert request.run_metadata == (("alpha", "first"), ("zeta", "last"))
    assert result.artifact_references == (
        "artifact://phase1/ghg_protocol/2",
        "artifact://phase1/ghg_protocol/1",
    )
    assert tuple(row.row_id for row in result.rows) == ("row-002", "row-001")
    assert tuple(issue.code for issue in result.issues) == ("SECOND", "FIRST")
    assert result.run_metadata == (("alpha", "first"), ("zeta", "last"))


def test_optional_metadata_rejects_blank_or_invalid_values() -> None:
    request = replace(
        _request_for_source("ghg_protocol"),
        run_id=" ",
        correlation_id="",
        requested_reporting_year=0,
        run_metadata=((" ", "blank-key"), ("valid", 1)),  # type: ignore[list-item]
    )

    validation = validate_parser_run_request(request)

    assert validation.is_valid is False
    assert _issue_codes(validation) == (
        "PARSER_RUN_REQUEST_BLANK_RUN_ID",
        "PARSER_RUN_REQUEST_BLANK_CORRELATION_ID",
        "PARSER_RUN_REQUEST_INVALID_REPORTING_YEAR",
        "PARSER_RUN_REQUEST_INVALID_RUN_METADATA",
        "PARSER_RUN_REQUEST_INVALID_RUN_METADATA",
    )


def test_contracts_are_read_only() -> None:
    request = _request_for_source("ghg_protocol")
    result = _result_for_request(request)

    with pytest.raises(FrozenInstanceError):
        request.parser_key = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows = ()  # type: ignore[misc]


def test_validation_result_issue_shape_is_structured() -> None:
    request = replace(_request_for_source("ghg_protocol"), parser_key="")

    issue = validate_parser_run_request(request).issues[0]

    assert isinstance(issue, ParserRunContractValidationIssue)
    assert issue.code == "PARSER_RUN_REQUEST_MISSING_PARSER_KEY"
    assert issue.field_name == "request.parser_key"
    assert issue.severity == "error"
    assert issue.message == "parser_key must be a non-empty string."


def test_validation_result_shape_exposes_is_valid() -> None:
    assert ParserRunContractValidationResult().is_valid is True
    assert ParserRunContractValidationResult(
        issues=(
            ParserRunContractValidationIssue(
                code="TEST",
                message="test",
                field_name="field",
            ),
        ),
    ).is_valid is False


def test_validation_does_not_read_files_access_db_or_network(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    import builtins
    import pathlib
    import sqlite3

    missing_artifact = tmp_path / "missing.csv"

    def fail_side_effect(*args: object, **kwargs: object) -> object:
        raise AssertionError("parser run contract must use metadata only")

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
    result = create_parser_run_result(
        request=request,
        status=ParserRunStatus.DECLARED,
        rows=(_row_for_artifact(artifact, "row-001"),),
        issues=(_issue_for_source("defra_desnz", "METADATA_ONLY"),),
    )

    assert validate_parser_run_request(request).is_valid is True
    assert validate_parser_run_result(result).is_valid is True


def test_contract_does_not_import_executable_parser_modules() -> None:
    imported_before = set(sys.modules)

    request = _request_for_source("ghg_protocol")
    result = _result_for_request(request)

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

    module_name = "carbonfactor_parser.parsers.parser_run_contract"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("parser run contract import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("parser run contract import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "create_parser_run_request")
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
        reporting_year=2024,
        registry=registry,
    )
    return create_parser_run_request(
        source_family=source_family,
        artifacts=(artifact,),
        run_id=f"{source_family}-run-001",
        correlation_id="correlation-001",
        requested_reporting_year=2024,
        registry=registry,
    )


def _result_for_request(
    request: ParserRunRequest,
    *,
    status: ParserRunStatus = ParserRunStatus.COMPLETED_WITH_ISSUES,
) -> ParserRunResult:
    artifact = request.artifacts[0]
    return create_parser_run_result(
        request=request,
        status=status,
        rows=(_row_for_artifact(artifact, "row-001"),),
        issues=(_issue_for_source(request.source_family, "METADATA_ONLY"),),
        artifact_metadata={"artifact_count": str(len(request.artifacts))},
        run_metadata={"mode": "metadata-only"},
    )


def _row_for_artifact(
    artifact: ParserInputArtifact,
    row_id: str,
):
    return create_parser_normalized_output_row(
        artifact=artifact,
        row_id=row_id,
        normalized_fields={
            "activity_name": artifact.source_family,
            "unit": "kg",
            "value": 1,
        },
    )


def _issue_for_source(
    source_family: str,
    code: str,
) -> ParserValidationIssue:
    return create_parser_validation_issue(
        source_family=source_family,
        severity=ParserValidationIssueSeverity.WARNING,
        code=code,
        message="Metadata-only parser diagnostic.",
    )


def _issue_codes(
    result: ParserRunContractValidationResult,
) -> tuple[str, ...]:
    return tuple(issue.code for issue in result.issues)
