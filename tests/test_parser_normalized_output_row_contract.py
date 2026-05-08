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
    ParserNormalizedOutputBatch,
    ParserNormalizedOutputRow,
    ParserNormalizedOutputRowStatus,
    ParserNormalizedOutputRowValidationIssue,
    ParserNormalizedOutputRowValidationResult,
    create_parser_normalized_output_batch,
    create_parser_normalized_output_row,
    validate_parser_normalized_output_batch,
    validate_parser_normalized_output_row,
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


def test_valid_normalized_rows_can_be_constructed_for_phase1_adapters() -> None:
    registry = create_phase1_parser_adapter_registry()

    rows = tuple(
        create_parser_normalized_output_row(
            artifact=create_phase1_parser_input_artifact(
                source_family=descriptor.source_family,
                artifact_reference=f"artifact://phase1/{descriptor.source_family}",
                reporting_year=2024,
                registry=registry,
            ),
            row_id=f"{descriptor.source_family}-row-001",
            source_row_number=1,
            artifact_identifier=f"{descriptor.source_family}:artifact",
            normalized_fields={
                "activity_name": descriptor.source_family,
                "unit": "kg",
                "value": 1,
            },
            warnings=("metadata-only warning",),
        )
        for descriptor in registry.descriptors
    )

    assert tuple(row.source_family for row in rows) == EXPECTED_SOURCE_FAMILIES
    assert tuple(row.source_key for row in rows) == EXPECTED_SOURCE_FAMILIES
    assert all(validate_parser_normalized_output_row(row, registry).is_valid for row in rows)


def test_normalized_row_source_and_parser_keys_align_with_adapter_registry() -> None:
    registry = create_phase1_parser_adapter_registry()

    for descriptor in registry.descriptors:
        artifact = create_phase1_parser_input_artifact(
            source_family=descriptor.source_family,
            artifact_reference=f"artifact://phase1/{descriptor.source_family}",
            registry=registry,
        )
        row = create_parser_normalized_output_row(
            artifact=artifact,
            row_id="row-001",
            normalized_fields={"activity_name": descriptor.source_family},
        )

        assert row.source_family == descriptor.source_family
        assert row.source_key == descriptor.source_family
        assert row.parser_key == descriptor.parser_key
        assert row.artifact_reference == artifact.artifact_reference


def test_normalized_row_preserves_metadata_without_persistence_mapping() -> None:
    artifact = create_phase1_parser_input_artifact(
        source_family="defra_desnz",
        artifact_reference="relative/missing/source.xlsx",
        reporting_year=2025,
    )

    row = create_parser_normalized_output_row(
        artifact=artifact,
        row_id="defra-row-001",
        source_row_number=12,
        artifact_identifier="defra:2025:source",
        normalized_fields={
            "factor_unit": "kgco2e",
            "activity_name": "electricity",
        },
        errors=("metadata-only error",),
    )

    assert row.artifact_reference == "relative/missing/source.xlsx"
    assert row.row_id == "defra-row-001"
    assert row.source_row_number == 12
    assert row.artifact_identifier == "defra:2025:source"
    assert row.reporting_year == 2025
    assert row.status is ParserNormalizedOutputRowStatus.DECLARED
    assert row.errors == ("metadata-only error",)
    assert row.normalized_fields == (
        ("activity_name", "electricity"),
        ("factor_unit", "kgco2e"),
    )


@pytest.mark.parametrize(
    ("field_name", "expected_code"),
    (
        ("source_family", "PARSER_NORMALIZED_ROW_MISSING_SOURCE_FAMILY"),
        ("source_key", "PARSER_NORMALIZED_ROW_MISSING_SOURCE_KEY"),
        ("parser_key", "PARSER_NORMALIZED_ROW_MISSING_PARSER_KEY"),
        ("artifact_reference", "PARSER_NORMALIZED_ROW_MISSING_ARTIFACT_REFERENCE"),
        ("row_id", "PARSER_NORMALIZED_ROW_MISSING_ROW_ID"),
    ),
)
def test_required_metadata_fields_reject_empty_strings(
    field_name: str,
    expected_code: str,
) -> None:
    row = _valid_row("ghg_protocol")
    invalid_row = replace(row, **{field_name: " "})

    result = validate_parser_normalized_output_row(invalid_row)

    assert result.is_valid is False
    assert expected_code in _issue_codes(result)


def test_normalized_field_keys_reject_empty_strings() -> None:
    row = replace(
        _valid_row("defra_desnz"),
        normalized_fields=(("activity_name", "electricity"), (" ", 1)),
    )

    result = validate_parser_normalized_output_row(row)

    assert result.is_valid is False
    assert _issue_codes(result) == ("PARSER_NORMALIZED_ROW_BLANK_FIELD_KEY",)


def test_missing_normalized_fields_returns_invalid_result() -> None:
    row = replace(_valid_row("ipcc_efdb"), normalized_fields=())

    result = validate_parser_normalized_output_row(row)

    assert result.is_valid is False
    assert _issue_codes(result) == ("PARSER_NORMALIZED_ROW_MISSING_FIELDS",)


def test_invalid_field_item_returns_invalid_result() -> None:
    row = replace(
        _valid_row("ghg_protocol"),
        normalized_fields=(("activity_name", "scope 2"), ("invalid",)),  # type: ignore[list-item]
    )

    result = validate_parser_normalized_output_row(row)

    assert result.is_valid is False
    assert _issue_codes(result) == ("PARSER_NORMALIZED_ROW_INVALID_FIELD_ITEM",)


def test_row_and_batch_ordering_is_deterministic() -> None:
    first = _valid_row("ghg_protocol", row_id="row-001")
    second = _valid_row("defra_desnz", row_id="row-002")
    batch = create_parser_normalized_output_batch((second, first))

    assert batch == ParserNormalizedOutputBatch(rows=(second, first))
    assert batch.row_count == 2
    assert tuple(row.row_id for row in batch.rows) == ("row-002", "row-001")
    assert first.normalized_fields == (
        ("activity_name", "ghg_protocol"),
        ("unit", "kg"),
        ("value", 1),
    )
    assert create_parser_normalized_output_batch((second, first)) == batch


def test_batch_validation_prefixes_row_issue_locations() -> None:
    batch = create_parser_normalized_output_batch(
        (
            _valid_row("ghg_protocol"),
            replace(_valid_row("defra_desnz"), row_id=" "),
        )
    )

    result = validate_parser_normalized_output_batch(batch)

    assert result.is_valid is False
    assert result.issues[0].field_name == "rows[2].row_id"
    assert result.issues[0].code == "PARSER_NORMALIZED_ROW_MISSING_ROW_ID"


def test_unknown_source_metadata_returns_invalid_result() -> None:
    row = ParserNormalizedOutputRow(
        source_family="unknown",
        source_key="unknown",
        parser_key="unknown_phase1_parser",
        artifact_reference="artifact://phase1/unknown",
        row_id="unknown-row-001",
        normalized_fields=(("activity_name", "unknown"),),
    )

    result = validate_parser_normalized_output_row(row)

    assert result.is_valid is False
    assert _issue_codes(result) == ("PARSER_NORMALIZED_ROW_UNKNOWN_SOURCE_FAMILY",)


def test_mismatched_source_or_parser_metadata_returns_invalid_result() -> None:
    row = replace(
        _valid_row("ipcc_efdb"),
        source_key="ghg_protocol",
        parser_key="ghg_protocol_phase1_parser",
    )

    result = validate_parser_normalized_output_row(row)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "PARSER_NORMALIZED_ROW_SOURCE_KEY_MISMATCH",
        "PARSER_NORMALIZED_ROW_PARSER_KEY_MISMATCH",
    )


def test_invalid_optional_metadata_returns_invalid_result() -> None:
    row = replace(
        _valid_row("defra_desnz"),
        source_row_number=0,
        artifact_identifier=" ",
        reporting_year=0,
        warnings=(" ",),
        errors=("",),
    )

    result = validate_parser_normalized_output_row(row)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "PARSER_NORMALIZED_ROW_INVALID_SOURCE_ROW_NUMBER",
        "PARSER_NORMALIZED_ROW_INVALID_REPORTING_YEAR",
        "PARSER_NORMALIZED_ROW_BLANK_ARTIFACT_IDENTIFIER",
        "PARSER_NORMALIZED_ROW_BLANK_WARNING",
        "PARSER_NORMALIZED_ROW_BLANK_ERROR",
    )


def test_invalid_status_returns_invalid_result() -> None:
    row = replace(_valid_row("ghg_protocol"), status="declared")  # type: ignore[arg-type]

    result = validate_parser_normalized_output_row(row)

    assert result.is_valid is False
    assert _issue_codes(result) == ("PARSER_NORMALIZED_ROW_INVALID_STATUS",)


def test_normalized_row_contract_is_read_only() -> None:
    row = _valid_row("ghg_protocol")
    batch = create_parser_normalized_output_batch((row,))

    with pytest.raises(FrozenInstanceError):
        row.row_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        batch.rows = ()  # type: ignore[misc]


def test_validation_result_issue_shape_is_structured() -> None:
    row = replace(_valid_row("ghg_protocol"), row_id="")

    issue = validate_parser_normalized_output_row(row).issues[0]

    assert isinstance(issue, ParserNormalizedOutputRowValidationIssue)
    assert issue.code == "PARSER_NORMALIZED_ROW_MISSING_ROW_ID"
    assert issue.field_name == "row_id"
    assert issue.severity == "error"
    assert issue.message == "row_id must be a non-empty string."


def test_validation_result_shape_exposes_is_valid() -> None:
    assert ParserNormalizedOutputRowValidationResult().is_valid is True
    assert ParserNormalizedOutputRowValidationResult(
        issues=(
            ParserNormalizedOutputRowValidationIssue(
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
        raise AssertionError("normalized output row contract must use metadata only")

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
    row = create_parser_normalized_output_row(
        artifact=artifact,
        row_id="row-001",
        normalized_fields={"activity_name": "electricity"},
    )
    result = validate_parser_normalized_output_row(row)

    assert row.artifact_reference == str(missing_artifact)
    assert result.is_valid is True


def test_contract_does_not_import_executable_parser_modules() -> None:
    imported_before = set(sys.modules)

    row = _valid_row("ghg_protocol")

    imported_after = set(sys.modules)
    newly_imported = imported_after - imported_before
    assert row.parser_key == "ghg_protocol_phase1_parser"
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

    module_name = "carbonfactor_parser.parsers.normalized_output_row_contract"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("normalized output row contract import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError(
            "normalized output row contract import read environment"
        )

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "create_parser_normalized_output_row")
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


def _valid_row(
    source_family: str,
    *,
    row_id: str = "row-001",
) -> ParserNormalizedOutputRow:
    artifact = create_phase1_parser_input_artifact(
        source_family=source_family,
        artifact_reference=f"artifact://phase1/{source_family}",
    )
    return create_parser_normalized_output_row(
        artifact=artifact,
        row_id=row_id,
        normalized_fields={
            "value": 1,
            "activity_name": source_family,
            "unit": "kg",
        },
    )


def _issue_codes(
    result: ParserNormalizedOutputRowValidationResult,
) -> tuple[str, ...]:
    return tuple(issue.code for issue in result.issues)
