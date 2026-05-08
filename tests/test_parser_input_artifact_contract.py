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
    ParserInputArtifactValidationIssue,
    ParserInputArtifactValidationResult,
    create_phase1_parser_input_artifact,
    validate_parser_input_artifact,
)
from carbonfactor_parser.parsers.source_format_contract import ParserSourceFormat

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


def test_valid_artifact_metadata_can_be_constructed_for_phase1_adapters() -> None:
    registry = create_phase1_parser_adapter_registry()

    artifacts = tuple(
        create_phase1_parser_input_artifact(
            source_family=descriptor.source_family,
            artifact_reference=f"artifact://phase1/{descriptor.source_family}",
            original_filename=f"{descriptor.source_family}.csv",
            display_name=f"{descriptor.source_family} artifact",
            checksum_sha256="a" * 64,
            content_type="text/csv",
            extension=".csv",
            reporting_year=2024,
            registry=registry,
        )
        for descriptor in registry.descriptors
    )

    assert tuple(artifact.source_family for artifact in artifacts) == (
        EXPECTED_SOURCE_FAMILIES
    )
    assert tuple(artifact.source_key for artifact in artifacts) == (
        EXPECTED_SOURCE_FAMILIES
    )
    assert all(
        validate_parser_input_artifact(artifact, registry).is_valid
        for artifact in artifacts
    )


def test_artifact_source_and_parser_keys_align_with_adapter_registry() -> None:
    registry = create_phase1_parser_adapter_registry()

    for descriptor in registry.descriptors:
        artifact = create_phase1_parser_input_artifact(
            source_family=descriptor.source_family,
            artifact_reference=f"artifact://phase1/{descriptor.source_family}",
            registry=registry,
        )

        assert artifact.source_family == descriptor.source_family
        assert artifact.source_key == descriptor.source_family
        assert artifact.parser_key == descriptor.parser_key
        assert artifact.parser_source_format is (
            descriptor.capability.parser_source_format
        )
        assert artifact.format_hint == descriptor.capability.format_hint


def test_artifact_contract_preserves_metadata_without_normalizing_paths() -> None:
    artifact = create_phase1_parser_input_artifact(
        source_family="defra_desnz",
        artifact_reference="relative/missing/../source.xlsx",
        original_filename="conversion factors.xlsx",
        display_name="DEFRA/DESNZ conversion factors",
        checksum_sha256="b" * 64,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        extension=".xlsx",
        reporting_year=2025,
    )

    assert artifact.artifact_reference == "relative/missing/../source.xlsx"
    assert artifact.original_filename == "conversion factors.xlsx"
    assert artifact.display_name == "DEFRA/DESNZ conversion factors"
    assert artifact.checksum_sha256 == "b" * 64
    assert artifact.content_type == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert artifact.extension == ".xlsx"
    assert artifact.reporting_year == 2025


@pytest.mark.parametrize(
    ("field_name", "expected_code"),
    (
        ("source_family", "PARSER_INPUT_ARTIFACT_MISSING_SOURCE_FAMILY"),
        ("source_key", "PARSER_INPUT_ARTIFACT_MISSING_SOURCE_KEY"),
        ("parser_key", "PARSER_INPUT_ARTIFACT_MISSING_PARSER_KEY"),
        ("format_hint", "PARSER_INPUT_ARTIFACT_MISSING_FORMAT_HINT"),
        ("artifact_reference", "PARSER_INPUT_ARTIFACT_MISSING_REFERENCE"),
    ),
)
def test_required_artifact_metadata_fields_reject_empty_strings(
    field_name: str,
    expected_code: str,
) -> None:
    artifact = create_phase1_parser_input_artifact(
        source_family="ghg_protocol",
        artifact_reference="artifact://phase1/ghg_protocol",
    )
    invalid_artifact = replace(artifact, **{field_name: " "})

    result = validate_parser_input_artifact(invalid_artifact)

    assert result.is_valid is False
    assert expected_code in _issue_codes(result)


def test_parser_source_format_is_required() -> None:
    artifact = create_phase1_parser_input_artifact(
        source_family="ghg_protocol",
        artifact_reference="artifact://phase1/ghg_protocol",
    )
    invalid_artifact = replace(artifact, parser_source_format=None)  # type: ignore[arg-type]

    result = validate_parser_input_artifact(invalid_artifact)

    assert result.is_valid is False
    assert "PARSER_INPUT_ARTIFACT_MISSING_SOURCE_FORMAT" in _issue_codes(result)


def test_optional_artifact_metadata_fields_reject_empty_strings() -> None:
    artifact = create_phase1_parser_input_artifact(
        source_family="defra_desnz",
        artifact_reference="artifact://phase1/defra_desnz",
        original_filename=" ",
        display_name="",
        checksum_sha256=" ",
        content_type="",
        extension=" ",
    )

    result = validate_parser_input_artifact(artifact)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "PARSER_INPUT_ARTIFACT_BLANK_ORIGINAL_FILENAME",
        "PARSER_INPUT_ARTIFACT_BLANK_DISPLAY_NAME",
        "PARSER_INPUT_ARTIFACT_BLANK_CHECKSUM_SHA256",
        "PARSER_INPUT_ARTIFACT_BLANK_CONTENT_TYPE",
        "PARSER_INPUT_ARTIFACT_BLANK_EXTENSION",
    )


def test_unknown_source_metadata_returns_invalid_result() -> None:
    artifact = ParserInputArtifact(
        source_family="unknown",
        source_key="unknown",
        parser_key="unknown_phase1_parser",
        parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
        format_hint="discovery",
        artifact_reference="artifact://phase1/unknown",
    )

    result = validate_parser_input_artifact(artifact)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "PARSER_INPUT_ARTIFACT_UNKNOWN_SOURCE_FAMILY",
    )


def test_factory_rejects_unknown_source_without_inventing_parser_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="source_family is not registered for a Phase 1 parser adapter",
    ):
        create_phase1_parser_input_artifact(
            source_family="unknown",
            artifact_reference="artifact://phase1/unknown",
        )


def test_mismatched_parser_metadata_returns_invalid_result() -> None:
    artifact = create_phase1_parser_input_artifact(
        source_family="ipcc_efdb",
        artifact_reference="artifact://phase1/ipcc_efdb",
    )
    invalid_artifact = replace(
        artifact,
        source_key="ghg_protocol",
        parser_key="ghg_protocol_phase1_parser",
        format_hint="wrong",
    )

    result = validate_parser_input_artifact(invalid_artifact)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "PARSER_INPUT_ARTIFACT_SOURCE_KEY_MISMATCH",
        "PARSER_INPUT_ARTIFACT_PARSER_KEY_MISMATCH",
        "PARSER_INPUT_ARTIFACT_FORMAT_HINT_MISMATCH",
    )


def test_invalid_reporting_year_returns_invalid_result() -> None:
    artifact = create_phase1_parser_input_artifact(
        source_family="defra_desnz",
        artifact_reference="artifact://phase1/defra_desnz",
        reporting_year=0,
    )

    result = validate_parser_input_artifact(artifact)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "PARSER_INPUT_ARTIFACT_INVALID_REPORTING_YEAR",
    )


def test_artifact_contract_is_deterministic_and_read_only() -> None:
    first = create_phase1_parser_input_artifact(
        source_family="ghg_protocol",
        artifact_reference="artifact://phase1/ghg_protocol",
    )
    second = create_phase1_parser_input_artifact(
        source_family="ghg_protocol",
        artifact_reference="artifact://phase1/ghg_protocol",
    )

    assert first == second
    assert validate_parser_input_artifact(first) == validate_parser_input_artifact(
        second
    )
    with pytest.raises(FrozenInstanceError):
        first.parser_key = "changed"  # type: ignore[misc]


def test_validation_result_issue_shape_is_structured() -> None:
    artifact = create_phase1_parser_input_artifact(
        source_family="ghg_protocol",
        artifact_reference=" ",
    )

    issue = validate_parser_input_artifact(artifact).issues[0]

    assert isinstance(issue, ParserInputArtifactValidationIssue)
    assert issue.code == "PARSER_INPUT_ARTIFACT_MISSING_REFERENCE"
    assert issue.field_name == "artifact_reference"
    assert issue.severity == "error"
    assert issue.message == "artifact_reference must be a non-empty string."


def test_validation_result_shape_exposes_is_valid() -> None:
    assert ParserInputArtifactValidationResult().is_valid is True
    assert ParserInputArtifactValidationResult(
        issues=(
            ParserInputArtifactValidationIssue(
                code="TEST",
                message="test",
                field_name="field",
            ),
        ),
    ).is_valid is False


def test_artifact_creation_and_validation_do_not_read_or_check_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    import builtins
    import pathlib
    import sqlite3

    missing_artifact = tmp_path / "missing.csv"

    def fail_side_effect(*args: object, **kwargs: object) -> object:
        raise AssertionError("parser input artifact contract must use metadata only")

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
    result = validate_parser_input_artifact(artifact)

    assert artifact.artifact_reference == str(missing_artifact)
    assert result.is_valid is True


def test_artifact_contract_does_not_import_executable_parser_modules() -> None:
    imported_before = set(sys.modules)

    artifact = create_phase1_parser_input_artifact(
        source_family="ghg_protocol",
        artifact_reference="artifact://phase1/ghg_protocol",
    )

    imported_after = set(sys.modules)
    newly_imported = imported_after - imported_before
    assert artifact.parser_key == "ghg_protocol_phase1_parser"
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_EXECUTABLE_PARSER_MODULES
    )


def test_artifact_contract_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = "carbonfactor_parser.parsers.input_artifact_contract"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("parser input artifact contract import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError(
            "parser input artifact contract import read environment"
        )

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "create_phase1_parser_input_artifact")
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


def _issue_codes(
    result: ParserInputArtifactValidationResult,
) -> tuple[str, ...]:
    return tuple(issue.code for issue in result.issues)
