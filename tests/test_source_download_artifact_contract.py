from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import importlib
import sys
import urllib.request

import pytest

from carbonfactor_parser.source_acquisition.discovery_candidate_contract import (
    SourceDiscoveryCandidate,
    create_phase1_source_discovery_candidates,
)
from carbonfactor_parser.source_acquisition.download_artifact_contract import (
    SourceDownloadArtifact,
    SourceDownloadArtifactResult,
    SourceDownloadArtifactValidationIssue,
    SourceDownloadArtifactValidationResult,
    create_phase1_source_download_artifacts,
    create_source_download_artifact_from_candidate,
    validate_source_download_artifact,
    validate_source_download_artifact_result,
)
from carbonfactor_parser.source_acquisition.registry import (
    create_default_source_acquisition_registry,
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


def test_valid_downloaded_artifacts_can_be_constructed_for_phase1_sources() -> None:
    result = create_phase1_source_download_artifacts()

    assert isinstance(result, SourceDownloadArtifactResult)
    assert result.artifact_count == 3
    assert result.source_keys == EXPECTED_SOURCE_KEYS
    assert all(
        validate_source_download_artifact(artifact).is_valid
        for artifact in result.artifacts
    )


def test_download_artifacts_reuse_discovery_candidate_metadata() -> None:
    candidates = create_phase1_source_discovery_candidates()
    result = create_phase1_source_download_artifacts(candidates)

    for candidate, artifact in zip(
        candidates.candidates,
        result.artifacts,
        strict=True,
    ):
        assert artifact.source_family == candidate.source_family
        assert artifact.source_key == candidate.source_key
        assert artifact.candidate_id == candidate.candidate_id
        assert artifact.artifact_kind == candidate.artifact_kind
        assert artifact.source_reference_uri == candidate.reference_uri
        assert artifact.display_name == candidate.title
        assert artifact.version_label == candidate.version_label


def test_source_keys_align_with_existing_phase1_registry_metadata() -> None:
    registry = create_default_source_acquisition_registry()
    result = create_phase1_source_download_artifacts()

    assert tuple(artifact.source_key for artifact in result.artifacts) == tuple(
        descriptor.source_id for descriptor in registry
    )
    assert tuple(artifact.source_family for artifact in result.artifacts) == tuple(
        descriptor.source_family for descriptor in registry
    )
    assert tuple(artifact.artifact_kind for artifact in result.artifacts) == tuple(
        descriptor.expected_format for descriptor in registry
    )


def test_artifact_result_ordering_is_deterministic() -> None:
    first = create_phase1_source_download_artifacts()
    second = create_phase1_source_download_artifacts()

    assert first == second
    assert first.source_keys == EXPECTED_SOURCE_KEYS
    assert tuple(artifact.artifact_id for artifact in first.artifacts) == (
        "phase1_download_artifact_001_ghg_protocol",
        "phase1_download_artifact_002_defra_desnz",
        "phase1_download_artifact_003_ipcc_efdb",
    )


@pytest.mark.parametrize(
    ("field_name", "expected_code"),
    (
        ("candidate_id", "SOURCE_DOWNLOAD_ARTIFACT_MISSING_CANDIDATE_ID"),
        ("artifact_id", "SOURCE_DOWNLOAD_ARTIFACT_MISSING_ARTIFACT_ID"),
    ),
)
def test_artifact_and_candidate_identifiers_reject_empty_strings(
    field_name: str,
    expected_code: str,
) -> None:
    artifact = create_phase1_source_download_artifacts().artifacts[0]
    invalid_artifact = replace(artifact, **{field_name: " "})

    result = validate_source_download_artifact(invalid_artifact)

    assert result.is_valid is False
    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("field_name", "expected_code"),
    (
        ("source_family", "SOURCE_DOWNLOAD_ARTIFACT_MISSING_SOURCE_FAMILY"),
        ("source_key", "SOURCE_DOWNLOAD_ARTIFACT_MISSING_SOURCE_KEY"),
        ("artifact_kind", "SOURCE_DOWNLOAD_ARTIFACT_MISSING_ARTIFACT_KIND"),
        (
            "source_reference_uri",
            "SOURCE_DOWNLOAD_ARTIFACT_MISSING_SOURCE_REFERENCE_URI",
        ),
        ("local_reference", "SOURCE_DOWNLOAD_ARTIFACT_MISSING_LOCAL_REFERENCE"),
    ),
)
def test_required_metadata_fields_reject_empty_strings(
    field_name: str,
    expected_code: str,
) -> None:
    artifact = create_phase1_source_download_artifacts().artifacts[0]
    invalid_artifact = replace(artifact, **{field_name: ""})

    result = validate_source_download_artifact(invalid_artifact)

    assert result.is_valid is False
    assert expected_code in _issue_codes(result)


def test_optional_metadata_fields_reject_empty_strings() -> None:
    artifact = SourceDownloadArtifact(
        source_family="defra_desnz",
        source_key="defra_desnz",
        candidate_id="candidate-001",
        artifact_id="artifact-001",
        artifact_kind="discovery",
        source_reference_uri="discovery://defra_desnz/source",
        local_reference="download://defra_desnz/source",
        original_filename=" ",
        display_name="",
        content_type=" ",
        extension="",
        checksum_sha256=" ",
        version_label="",
    )

    result = validate_source_download_artifact(artifact)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "SOURCE_DOWNLOAD_ARTIFACT_BLANK_ORIGINAL_FILENAME",
        "SOURCE_DOWNLOAD_ARTIFACT_BLANK_DISPLAY_NAME",
        "SOURCE_DOWNLOAD_ARTIFACT_BLANK_CONTENT_TYPE",
        "SOURCE_DOWNLOAD_ARTIFACT_BLANK_EXTENSION",
        "SOURCE_DOWNLOAD_ARTIFACT_BLANK_CHECKSUM_SHA256",
        "SOURCE_DOWNLOAD_ARTIFACT_BLANK_VERSION_LABEL",
    )


def test_invalid_size_and_year_metadata_returns_invalid_result() -> None:
    artifact = replace(
        create_phase1_source_download_artifacts().artifacts[1],
        size_bytes=0,
        document_year=0,
        reporting_year=-1,
    )

    result = validate_source_download_artifact(artifact)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "SOURCE_DOWNLOAD_ARTIFACT_INVALID_SIZE_BYTES",
        "SOURCE_DOWNLOAD_ARTIFACT_INVALID_DOCUMENT_YEAR",
        "SOURCE_DOWNLOAD_ARTIFACT_INVALID_REPORTING_YEAR",
    )


def test_unknown_or_mismatched_source_metadata_returns_invalid_result() -> None:
    unknown = SourceDownloadArtifact(
        source_family="unknown",
        source_key="unknown",
        candidate_id="candidate-001",
        artifact_id="artifact-001",
        artifact_kind="discovery",
        source_reference_uri="discovery://unknown/source",
        local_reference="download://unknown/source",
    )
    mismatched = replace(
        create_phase1_source_download_artifacts().artifacts[2],
        source_family="ghg_protocol",
        artifact_kind="xlsx",
    )

    assert _issue_codes(validate_source_download_artifact(unknown)) == (
        "SOURCE_DOWNLOAD_ARTIFACT_UNKNOWN_SOURCE_KEY",
    )
    assert _issue_codes(validate_source_download_artifact(mismatched)) == (
        "SOURCE_DOWNLOAD_ARTIFACT_SOURCE_FAMILY_MISMATCH",
        "SOURCE_DOWNLOAD_ARTIFACT_KIND_MISMATCH",
    )


def test_download_artifact_result_validation_prefixes_locations() -> None:
    artifact = replace(
        create_phase1_source_download_artifacts().artifacts[1],
        artifact_id="",
    )
    result = SourceDownloadArtifactResult(artifacts=(artifact,))

    validation = validate_source_download_artifact_result(result)

    assert validation.is_valid is False
    assert validation.issues[0].field_name == "artifacts[1].artifact_id"
    assert validation.issues[0].code == "SOURCE_DOWNLOAD_ARTIFACT_MISSING_ARTIFACT_ID"


def test_url_reference_metadata_is_not_fetched_or_network_validated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = replace(
        create_phase1_source_download_artifacts().artifacts[0],
        source_reference_uri="discovery://not-fetched/source.csv",
    )

    def fail_urlopen(*args: object, **kwargs: object) -> object:
        raise AssertionError("download artifact validation must not fetch references")

    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)

    assert validate_source_download_artifact(artifact).is_valid is True


def test_local_reference_metadata_is_not_opened_statted_read_written_or_checked(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    import builtins
    import pathlib

    missing_artifact = tmp_path / "downloaded.csv"
    artifact = replace(
        create_phase1_source_download_artifacts().artifacts[0],
        local_reference=str(missing_artifact),
    )

    def fail_side_effect(*args: object, **kwargs: object) -> object:
        raise AssertionError("local_reference must remain metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "exists", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "is_file", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "stat", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "read_text", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "write_text", fail_side_effect)

    assert validate_source_download_artifact(artifact).is_valid is True


def test_validation_does_not_read_files_access_db_or_network(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    import builtins
    import pathlib
    import sqlite3

    missing_artifact = tmp_path / "downloaded.csv"

    def fail_side_effect(*args: object, **kwargs: object) -> object:
        raise AssertionError("source download artifacts must use metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "exists", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "is_file", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "stat", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)

    artifact = replace(
        create_phase1_source_download_artifacts().artifacts[0],
        source_reference_uri="discovery://not-fetched/source.csv",
        local_reference=str(missing_artifact),
    )

    assert validate_source_download_artifact(artifact).is_valid is True


def test_download_artifact_contract_is_read_only() -> None:
    result = create_phase1_source_download_artifacts()
    artifact = result.artifacts[0]

    with pytest.raises(FrozenInstanceError):
        artifact.artifact_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.artifacts = ()  # type: ignore[misc]


def test_validation_result_issue_shape_is_structured() -> None:
    artifact = replace(
        create_phase1_source_download_artifacts().artifacts[0],
        artifact_id="",
    )

    issue = validate_source_download_artifact(artifact).issues[0]

    assert isinstance(issue, SourceDownloadArtifactValidationIssue)
    assert issue.code == "SOURCE_DOWNLOAD_ARTIFACT_MISSING_ARTIFACT_ID"
    assert issue.field_name == "artifact_id"
    assert issue.severity == "error"
    assert issue.message == "artifact_id must be a non-empty string."


def test_validation_result_shape_exposes_is_valid() -> None:
    assert SourceDownloadArtifactValidationResult().is_valid is True
    assert SourceDownloadArtifactValidationResult(
        issues=(
            SourceDownloadArtifactValidationIssue(
                code="TEST",
                message="test",
                field_name="field",
            ),
        ),
    ).is_valid is False


def test_custom_artifact_creation_from_candidate_preserves_explicit_metadata() -> None:
    candidate = SourceDiscoveryCandidate(
        source_family="ghg_protocol",
        source_key="ghg_protocol",
        candidate_id="candidate-001",
        title="GHG Protocol custom source",
        reference_uri="discovery://ghg_protocol/custom",
        artifact_kind="discovery",
        document_year=2024,
        reporting_year=2024,
        content_type="text/csv",
        extension=".csv",
        checksum_sha256="a" * 64,
        version_label="v1",
    )

    artifact = create_source_download_artifact_from_candidate(
        candidate,
        artifact_id="artifact-001",
        local_reference="download://phase1/ghg_protocol/custom",
        original_filename="custom.csv",
        size_bytes=128,
    )

    assert artifact.display_name == "GHG Protocol custom source"
    assert artifact.content_type == "text/csv"
    assert artifact.extension == ".csv"
    assert artifact.checksum_sha256 == "a" * 64
    assert artifact.size_bytes == 128
    assert artifact.document_year == 2024
    assert artifact.reporting_year == 2024
    assert artifact.version_label == "v1"


def test_import_remains_runtime_passive(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins
    import os

    module_name = "carbonfactor_parser.source_acquisition.download_artifact_contract"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("source download artifact import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("source download artifact import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_after = set(sys.modules)

    assert hasattr(module, "create_phase1_source_download_artifacts")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_after - imported_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in (*BANNED_RUNTIME_MODULE_PREFIXES, *BANNED_EXECUTABLE_PARSER_MODULES)
    )


def _issue_codes(
    result: SourceDownloadArtifactValidationResult,
) -> tuple[str, ...]:
    return tuple(issue.code for issue in result.issues)
