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
from carbonfactor_parser.parsers.input_artifact_contract import ParserInputArtifact
from carbonfactor_parser.source_acquisition.download_artifact_contract import (
    SourceDownloadArtifact,
    SourceDownloadArtifactResult,
    create_phase1_source_download_artifacts,
)
from carbonfactor_parser.source_acquisition.registry import (
    create_default_source_acquisition_registry,
)
from carbonfactor_parser.source_acquisition.source_artifact_parser_input_bridge_contract import (
    SourceArtifactParserInputBridgeEntry,
    SourceArtifactParserInputBridgeResult,
    SourceArtifactParserInputBridgeValidationIssue,
    SourceArtifactParserInputBridgeValidationResult,
    create_phase1_source_artifact_parser_input_bridge,
    create_source_artifact_parser_input_bridge_entry,
    validate_source_artifact_parser_input_bridge_entry,
    validate_source_artifact_parser_input_bridge_result,
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


def test_valid_parser_input_artifact_metadata_can_be_derived_for_phase1() -> None:
    result = create_phase1_source_artifact_parser_input_bridge()

    assert isinstance(result, SourceArtifactParserInputBridgeResult)
    assert result.entry_count == 3
    assert result.source_keys == EXPECTED_SOURCE_KEYS
    assert all(
        isinstance(entry.parser_input_artifact, ParserInputArtifact)
        for entry in result.entries
    )
    assert all(
        validate_source_artifact_parser_input_bridge_entry(entry).is_valid
        for entry in result.entries
    )


def test_source_keys_align_with_existing_phase1_source_metadata() -> None:
    registry = create_default_source_acquisition_registry()
    result = create_phase1_source_artifact_parser_input_bridge()

    assert tuple(entry.source_key for entry in result.entries) == tuple(
        descriptor.source_id for descriptor in registry
    )
    assert tuple(entry.source_family for entry in result.entries) == tuple(
        descriptor.source_family for descriptor in registry
    )
    assert tuple(entry.artifact_kind for entry in result.entries) == tuple(
        descriptor.expected_format for descriptor in registry
    )


def test_parser_keys_align_with_adapter_registry_metadata() -> None:
    adapter_registry = create_phase1_parser_adapter_registry()
    result = create_phase1_source_artifact_parser_input_bridge(
        registry=adapter_registry,
    )

    assert tuple(entry.parser_key for entry in result.entries) == tuple(
        descriptor.parser_key for descriptor in adapter_registry.descriptors
    )
    assert tuple(entry.parser_input_artifact.parser_key for entry in result.entries) == (
        tuple(descriptor.parser_key for descriptor in adapter_registry.descriptors)
    )


@pytest.mark.parametrize(
    ("field_name", "expected_code"),
    (
        (
            "source_artifact_id",
            "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_MISSING_SOURCE_ARTIFACT_ID",
        ),
        (
            "parser_input_artifact_id",
            "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_MISSING_PARSER_INPUT_ARTIFACT_ID",
        ),
    ),
)
def test_artifact_identifiers_and_parser_input_identifiers_reject_empty_strings(
    field_name: str,
    expected_code: str,
) -> None:
    entry = create_phase1_source_artifact_parser_input_bridge().entries[0]
    invalid_entry = replace(entry, **{field_name: " "})

    validation = validate_source_artifact_parser_input_bridge_entry(invalid_entry)

    assert validation.is_valid is False
    assert expected_code in _issue_codes(validation)


@pytest.mark.parametrize(
    ("field_name", "expected_code"),
    (
        (
            "source_family",
            "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_MISSING_SOURCE_FAMILY",
        ),
        ("source_key", "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_MISSING_SOURCE_KEY"),
        ("parser_key", "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_MISSING_PARSER_KEY"),
        (
            "artifact_kind",
            "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_MISSING_ARTIFACT_KIND",
        ),
        (
            "artifact_reference",
            "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_MISSING_ARTIFACT_REFERENCE",
        ),
    ),
)
def test_required_bridge_metadata_fields_reject_empty_strings(
    field_name: str,
    expected_code: str,
) -> None:
    entry = create_phase1_source_artifact_parser_input_bridge().entries[0]
    invalid_entry = replace(entry, **{field_name: ""})

    validation = validate_source_artifact_parser_input_bridge_entry(invalid_entry)

    assert validation.is_valid is False
    assert expected_code in _issue_codes(validation)


def test_derived_parser_input_metadata_preserves_source_artifact_metadata() -> None:
    source_artifact = SourceDownloadArtifact(
        source_family="ghg_protocol",
        source_key="ghg_protocol",
        candidate_id="candidate-001",
        artifact_id="artifact-001",
        artifact_kind="discovery",
        source_reference_uri="discovery://ghg_protocol/source",
        local_reference="download://phase1/ghg_protocol/custom.csv",
        original_filename="custom.csv",
        display_name="GHG Protocol custom source",
        content_type="text/csv",
        extension=".csv",
        checksum_sha256="a" * 64,
        document_year=2024,
        reporting_year=2024,
    )

    entry = create_source_artifact_parser_input_bridge_entry(
        source_artifact,
        parser_input_artifact_id="parser-input-001",
    )

    assert entry.source_artifact_id == "artifact-001"
    assert entry.parser_input_artifact_id == "parser-input-001"
    assert entry.artifact_kind == "discovery"
    assert entry.artifact_reference == source_artifact.local_reference
    assert entry.original_filename == source_artifact.original_filename
    assert entry.display_name == source_artifact.display_name
    assert entry.content_type == source_artifact.content_type
    assert entry.extension == source_artifact.extension
    assert entry.checksum_sha256 == source_artifact.checksum_sha256
    assert entry.document_year == source_artifact.document_year
    assert entry.reporting_year == source_artifact.reporting_year
    assert entry.parser_input_artifact.artifact_reference == source_artifact.local_reference
    assert entry.parser_input_artifact.original_filename == source_artifact.original_filename
    assert entry.parser_input_artifact.display_name == source_artifact.display_name
    assert entry.parser_input_artifact.checksum_sha256 == source_artifact.checksum_sha256
    assert entry.parser_input_artifact.content_type == source_artifact.content_type
    assert entry.parser_input_artifact.extension == source_artifact.extension
    assert entry.parser_input_artifact.reporting_year == source_artifact.reporting_year


def test_batch_conversion_ordering_is_deterministic() -> None:
    first = create_phase1_source_artifact_parser_input_bridge()
    second = create_phase1_source_artifact_parser_input_bridge()

    assert first == second
    assert first.source_keys == EXPECTED_SOURCE_KEYS
    assert tuple(entry.parser_input_artifact_id for entry in first.entries) == (
        "parser_input_from_phase1_download_artifact_001_ghg_protocol",
        "parser_input_from_phase1_download_artifact_002_defra_desnz",
        "parser_input_from_phase1_download_artifact_003_ipcc_efdb",
    )


def test_batch_conversion_accepts_explicit_source_download_artifact_result() -> None:
    artifacts = create_phase1_source_download_artifacts()
    result = create_phase1_source_artifact_parser_input_bridge(
        SourceDownloadArtifactResult(artifacts=artifacts.artifacts[:2]),
    )

    assert result.entry_count == 2
    assert result.source_keys == ("ghg_protocol", "defra_desnz")
    assert result.parser_input_artifacts == tuple(
        entry.parser_input_artifact for entry in result.entries
    )


def test_source_artifact_metadata_mismatch_returns_invalid_result() -> None:
    entry = create_phase1_source_artifact_parser_input_bridge().entries[1]
    invalid_entry = replace(
        entry,
        source_key="ghg_protocol",
        artifact_reference="download://phase1/defra_desnz/different",
    )

    validation = validate_source_artifact_parser_input_bridge_entry(invalid_entry)

    assert validation.is_valid is False
    assert "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_SOURCE_KEY_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_SOURCE_ARTIFACT_MISMATCH" in (
        _issue_codes(validation)
    )


def test_parser_input_metadata_mismatch_returns_invalid_result() -> None:
    entry = create_phase1_source_artifact_parser_input_bridge().entries[2]
    invalid_parser_input = replace(
        entry.parser_input_artifact,
        parser_key="ghg_protocol_phase1_parser",
        artifact_reference="download://phase1/ipcc_efdb/different",
    )
    invalid_entry = replace(
        entry,
        parser_key="ghg_protocol_phase1_parser",
        parser_input_artifact=invalid_parser_input,
    )

    validation = validate_source_artifact_parser_input_bridge_entry(invalid_entry)

    assert validation.is_valid is False
    assert "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_PARSER_KEY_MISMATCH" in (
        _issue_codes(validation)
    )
    assert "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_PARSER_INPUT_MISMATCH" in (
        _issue_codes(validation)
    )


def test_unknown_source_metadata_fails_clearly() -> None:
    source_artifact = SourceDownloadArtifact(
        source_family="unknown",
        source_key="unknown",
        candidate_id="candidate-001",
        artifact_id="artifact-001",
        artifact_kind="discovery",
        source_reference_uri="discovery://unknown/source",
        local_reference="download://unknown/source",
    )

    with pytest.raises(
        ValueError,
        match="source_family is not registered for a Phase 1 parser adapter",
    ):
        create_source_artifact_parser_input_bridge_entry(source_artifact)


def test_bridge_result_validation_prefixes_locations() -> None:
    entry = replace(
        create_phase1_source_artifact_parser_input_bridge().entries[0],
        parser_input_artifact_id="",
    )

    validation = validate_source_artifact_parser_input_bridge_result(
        SourceArtifactParserInputBridgeResult(entries=(entry,)),
    )

    assert validation.is_valid is False
    assert validation.issues[0].field_name == "entries[1].parser_input_artifact_id"
    assert validation.issues[0].code == (
        "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_MISSING_PARSER_INPUT_ARTIFACT_ID"
    )


def test_local_reference_metadata_is_not_opened_statted_read_written_or_hashed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    import builtins
    import pathlib

    missing_artifact = tmp_path / "downloaded.csv"
    entry = create_phase1_source_artifact_parser_input_bridge().entries[0]
    source_artifact = replace(entry.source_artifact, local_reference=str(missing_artifact))
    bridge = create_source_artifact_parser_input_bridge_entry(source_artifact)

    def fail_side_effect(*args: object, **kwargs: object) -> object:
        raise AssertionError("bridge validation must treat references as metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "exists", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "is_file", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "stat", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "read_text", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "write_text", fail_side_effect)
    monkeypatch.setattr(hashlib, "sha256", fail_side_effect)

    assert validate_source_artifact_parser_input_bridge_entry(bridge).is_valid is True


def test_url_reference_metadata_is_not_fetched_or_network_validated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_artifact = replace(
        create_phase1_source_download_artifacts().artifacts[0],
        source_reference_uri="discovery://not-fetched/source.csv",
    )
    bridge = create_source_artifact_parser_input_bridge_entry(source_artifact)

    def fail_urlopen(*args: object, **kwargs: object) -> object:
        raise AssertionError("bridge validation must not fetch references")

    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)

    assert validate_source_artifact_parser_input_bridge_entry(bridge).is_valid is True


def test_validation_does_not_access_db_or_execute_parsers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    import builtins
    import pathlib
    import sqlite3

    missing_artifact = tmp_path / "downloaded.csv"
    source_artifact = replace(
        create_phase1_source_download_artifacts().artifacts[0],
        source_reference_uri="discovery://not-fetched/source.csv",
        local_reference=str(missing_artifact),
    )
    bridge = create_source_artifact_parser_input_bridge_entry(source_artifact)

    def fail_side_effect(*args: object, **kwargs: object) -> object:
        raise AssertionError("bridge validation must use metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "exists", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "is_file", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "stat", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)

    assert validate_source_artifact_parser_input_bridge_entry(bridge).is_valid is True


def test_bridge_contract_is_read_only() -> None:
    entry = create_phase1_source_artifact_parser_input_bridge().entries[0]

    with pytest.raises(FrozenInstanceError):
        entry.source_key = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        entry.parser_input_artifact.artifact_reference = "changed"  # type: ignore[misc]


def test_validation_result_issue_shape_is_structured() -> None:
    entry = replace(
        create_phase1_source_artifact_parser_input_bridge().entries[0],
        parser_input_artifact_id="",
    )

    issue = validate_source_artifact_parser_input_bridge_entry(entry).issues[0]

    assert isinstance(issue, SourceArtifactParserInputBridgeValidationIssue)
    assert issue.code == (
        "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_MISSING_PARSER_INPUT_ARTIFACT_ID"
    )
    assert issue.field_name == "parser_input_artifact_id"
    assert issue.severity == "error"


def test_validation_result_shape_exposes_is_valid() -> None:
    assert SourceArtifactParserInputBridgeValidationResult().is_valid is True
    assert SourceArtifactParserInputBridgeValidationResult(
        issues=(
            SourceArtifactParserInputBridgeValidationIssue(
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
        "source_artifact_parser_input_bridge_contract"
    )
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("source artifact bridge import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("source artifact bridge import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_after = set(sys.modules)

    assert hasattr(module, "create_phase1_source_artifact_parser_input_bridge")
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
    result: SourceArtifactParserInputBridgeValidationResult,
) -> tuple[str, ...]:
    return tuple(issue.code for issue in result.issues)
