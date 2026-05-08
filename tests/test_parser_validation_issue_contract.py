from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import importlib
import sys
import urllib.request

import pytest

from carbonfactor_parser.parsers.adapter_registry_contract import (
    create_phase1_parser_adapter_registry,
)
from carbonfactor_parser.parsers.validation_issue_contract import (
    ParserValidationIssue,
    ParserValidationIssueCollection,
    ParserValidationIssueSeverity,
    ParserValidationIssueValidationIssue,
    ParserValidationIssueValidationResult,
    create_parser_validation_issue,
    create_parser_validation_issue_collection,
    validate_parser_validation_issue,
    validate_parser_validation_issue_collection,
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


def test_valid_validation_issues_can_be_constructed_for_phase1_adapters() -> None:
    registry = create_phase1_parser_adapter_registry()

    issues = tuple(
        create_parser_validation_issue(
            source_family=descriptor.source_family,
            severity=ParserValidationIssueSeverity.WARNING,
            code=f"{descriptor.source_family.upper()}_METADATA_ONLY",
            message=f"{descriptor.source_family} metadata-only diagnostic.",
            artifact_reference=f"artifact://phase1/{descriptor.source_family}",
            row_id=f"{descriptor.source_family}-row-001",
            source_row_number=1,
            field_key="activity_name",
            context={"source": descriptor.source_family, "phase": "1"},
            registry=registry,
        )
        for descriptor in registry.descriptors
    )

    assert tuple(issue.source_family for issue in issues) == EXPECTED_SOURCE_FAMILIES
    assert tuple(issue.source_key for issue in issues) == EXPECTED_SOURCE_FAMILIES
    assert all(
        validate_parser_validation_issue(issue, registry).is_valid
        for issue in issues
    )


def test_validation_issue_source_and_parser_keys_align_with_registry() -> None:
    registry = create_phase1_parser_adapter_registry()

    for descriptor in registry.descriptors:
        issue = create_parser_validation_issue(
            source_family=descriptor.source_family,
            severity=ParserValidationIssueSeverity.INFO,
            code="METADATA_ONLY",
            message="Metadata-only diagnostic.",
            registry=registry,
        )

        assert issue.source_family == descriptor.source_family
        assert issue.source_key == descriptor.source_family
        assert issue.parser_key == descriptor.parser_key


def test_validation_issue_severity_values_are_constrained() -> None:
    assert tuple(severity.value for severity in ParserValidationIssueSeverity) == (
        "info",
        "warning",
        "error",
    )

    issue = replace(
        _valid_issue("ghg_protocol"),
        severity="critical",  # type: ignore[arg-type]
    )

    result = validate_parser_validation_issue(issue)

    assert result.is_valid is False
    assert _issue_codes(result) == ("PARSER_VALIDATION_ISSUE_INVALID_SEVERITY",)


@pytest.mark.parametrize(
    ("field_name", "expected_code"),
    (
        ("source_family", "PARSER_VALIDATION_ISSUE_MISSING_SOURCE_FAMILY"),
        ("source_key", "PARSER_VALIDATION_ISSUE_MISSING_SOURCE_KEY"),
        ("parser_key", "PARSER_VALIDATION_ISSUE_MISSING_PARSER_KEY"),
        ("code", "PARSER_VALIDATION_ISSUE_MISSING_CODE"),
        ("message", "PARSER_VALIDATION_ISSUE_MISSING_MESSAGE"),
    ),
)
def test_required_metadata_fields_reject_empty_strings(
    field_name: str,
    expected_code: str,
) -> None:
    issue = replace(_valid_issue("defra_desnz"), **{field_name: " "})

    result = validate_parser_validation_issue(issue)

    assert result.is_valid is False
    assert expected_code in _issue_codes(result)


def test_optional_metadata_fields_reject_empty_strings() -> None:
    issue = create_parser_validation_issue(
        source_family="ipcc_efdb",
        severity=ParserValidationIssueSeverity.ERROR,
        code="METADATA_ONLY",
        message="Metadata-only diagnostic.",
        artifact_reference=" ",
        row_id="",
        field_key=" ",
    )

    result = validate_parser_validation_issue(issue)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "PARSER_VALIDATION_ISSUE_BLANK_ARTIFACT_REFERENCE",
        "PARSER_VALIDATION_ISSUE_BLANK_ROW_ID",
        "PARSER_VALIDATION_ISSUE_BLANK_FIELD_KEY",
    )


def test_context_keys_reject_empty_strings() -> None:
    issue = replace(
        _valid_issue("ghg_protocol"),
        context=(("phase", "1"), (" ", "blank-key")),
    )

    result = validate_parser_validation_issue(issue)

    assert result.is_valid is False
    assert _issue_codes(result) == ("PARSER_VALIDATION_ISSUE_BLANK_CONTEXT_KEY",)


def test_context_values_must_be_strings() -> None:
    issue = replace(
        _valid_issue("defra_desnz"),
        context=(("phase", "1"), ("row", 1)),  # type: ignore[list-item]
    )

    result = validate_parser_validation_issue(issue)

    assert result.is_valid is False
    assert _issue_codes(result) == ("PARSER_VALIDATION_ISSUE_INVALID_CONTEXT_VALUE",)


def test_issue_context_ordering_is_deterministic() -> None:
    issue = create_parser_validation_issue(
        source_family="ghg_protocol",
        severity=ParserValidationIssueSeverity.INFO,
        code="METADATA_ONLY",
        message="Metadata-only diagnostic.",
        context={"zeta": "last", "alpha": "first"},
    )

    assert issue.context == (("alpha", "first"), ("zeta", "last"))
    assert issue == create_parser_validation_issue(
        source_family="ghg_protocol",
        severity=ParserValidationIssueSeverity.INFO,
        code="METADATA_ONLY",
        message="Metadata-only diagnostic.",
        context={"zeta": "last", "alpha": "first"},
    )


def test_issue_collection_ordering_is_deterministic() -> None:
    first = _valid_issue("ghg_protocol", code="FIRST")
    second = _valid_issue("defra_desnz", code="SECOND")
    collection = create_parser_validation_issue_collection((second, first))

    assert collection == ParserValidationIssueCollection(issues=(second, first))
    assert collection.issue_count == 2
    assert tuple(issue.code for issue in collection.issues) == ("SECOND", "FIRST")
    assert create_parser_validation_issue_collection((second, first)) == collection


def test_collection_validation_prefixes_issue_locations() -> None:
    collection = create_parser_validation_issue_collection(
        (
            _valid_issue("ghg_protocol"),
            replace(_valid_issue("defra_desnz"), code=" "),
        )
    )

    result = validate_parser_validation_issue_collection(collection)

    assert result.is_valid is False
    assert result.issues[0].field_name == "issues[2].code"
    assert result.issues[0].code == "PARSER_VALIDATION_ISSUE_MISSING_CODE"


def test_unknown_source_metadata_returns_invalid_result() -> None:
    issue = ParserValidationIssue(
        source_family="unknown",
        source_key="unknown",
        parser_key="unknown_phase1_parser",
        severity=ParserValidationIssueSeverity.WARNING,
        code="UNKNOWN_SOURCE",
        message="Unknown source diagnostic.",
    )

    result = validate_parser_validation_issue(issue)

    assert result.is_valid is False
    assert _issue_codes(result) == ("PARSER_VALIDATION_ISSUE_UNKNOWN_SOURCE_FAMILY",)


def test_factory_rejects_unknown_source_without_inventing_parser_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="source_family is not registered for a Phase 1 parser adapter",
    ):
        create_parser_validation_issue(
            source_family="unknown",
            severity=ParserValidationIssueSeverity.ERROR,
            code="UNKNOWN_SOURCE",
            message="Unknown source diagnostic.",
        )


def test_mismatched_source_or_parser_metadata_returns_invalid_result() -> None:
    issue = replace(
        _valid_issue("ipcc_efdb"),
        source_key="ghg_protocol",
        parser_key="ghg_protocol_phase1_parser",
    )

    result = validate_parser_validation_issue(issue)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "PARSER_VALIDATION_ISSUE_SOURCE_KEY_MISMATCH",
        "PARSER_VALIDATION_ISSUE_PARSER_KEY_MISMATCH",
    )


def test_invalid_source_row_number_returns_invalid_result() -> None:
    issue = replace(_valid_issue("defra_desnz"), source_row_number=0)

    result = validate_parser_validation_issue(issue)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "PARSER_VALIDATION_ISSUE_INVALID_SOURCE_ROW_NUMBER",
    )


def test_validation_issue_contract_is_read_only() -> None:
    issue = _valid_issue("ghg_protocol")
    collection = create_parser_validation_issue_collection((issue,))

    with pytest.raises(FrozenInstanceError):
        issue.code = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        collection.issues = ()  # type: ignore[misc]


def test_validation_result_issue_shape_is_structured() -> None:
    issue = replace(_valid_issue("ghg_protocol"), message="")

    validation_issue = validate_parser_validation_issue(issue).issues[0]

    assert isinstance(validation_issue, ParserValidationIssueValidationIssue)
    assert validation_issue.code == "PARSER_VALIDATION_ISSUE_MISSING_MESSAGE"
    assert validation_issue.field_name == "message"
    assert validation_issue.severity == "error"
    assert validation_issue.message == "message must be a non-empty string."


def test_validation_result_shape_exposes_is_valid() -> None:
    assert ParserValidationIssueValidationResult().is_valid is True
    assert ParserValidationIssueValidationResult(
        issues=(
            ParserValidationIssueValidationIssue(
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
        raise AssertionError("parser validation issue contract must use metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "exists", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "is_file", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "stat", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)

    issue = create_parser_validation_issue(
        source_family="defra_desnz",
        severity=ParserValidationIssueSeverity.WARNING,
        code="MISSING_OPTIONAL_FIELD",
        message="Optional metadata was absent.",
        artifact_reference=str(missing_artifact),
    )
    result = validate_parser_validation_issue(issue)

    assert issue.artifact_reference == str(missing_artifact)
    assert result.is_valid is True


def test_contract_does_not_import_executable_parser_modules() -> None:
    imported_before = set(sys.modules)

    issue = _valid_issue("ghg_protocol")

    imported_after = set(sys.modules)
    newly_imported = imported_after - imported_before
    assert issue.parser_key == "ghg_protocol_phase1_parser"
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

    module_name = "carbonfactor_parser.parsers.validation_issue_contract"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("parser validation issue contract import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError(
            "parser validation issue contract import read environment"
        )

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "create_parser_validation_issue")
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


def _valid_issue(
    source_family: str,
    *,
    code: str = "METADATA_ONLY",
) -> ParserValidationIssue:
    return create_parser_validation_issue(
        source_family=source_family,
        severity=ParserValidationIssueSeverity.WARNING,
        code=code,
        message="Metadata-only diagnostic.",
        artifact_reference=f"artifact://phase1/{source_family}",
        row_id="row-001",
        source_row_number=1,
        field_key="activity_name",
        context={"phase": "1", "source_family": source_family},
    )


def _issue_codes(
    result: ParserValidationIssueValidationResult,
) -> tuple[str, ...]:
    return tuple(issue.code for issue in result.issues)
