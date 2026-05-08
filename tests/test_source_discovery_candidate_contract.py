from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import importlib
import sys
import urllib.request

import pytest

from carbonfactor_parser.source_acquisition.discovery_candidate_contract import (
    SourceDiscoveryCandidate,
    SourceDiscoveryCandidateResult,
    SourceDiscoveryCandidateValidationIssue,
    SourceDiscoveryCandidateValidationResult,
    create_phase1_source_discovery_candidates,
    validate_source_discovery_candidate,
    validate_source_discovery_candidate_result,
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


def test_valid_discovery_candidates_can_be_constructed_for_phase1_sources() -> None:
    result = create_phase1_source_discovery_candidates()

    assert isinstance(result, SourceDiscoveryCandidateResult)
    assert result.candidate_count == 3
    assert result.source_keys == EXPECTED_SOURCE_KEYS
    assert all(
        validate_source_discovery_candidate(candidate).is_valid
        for candidate in result.candidates
    )


def test_source_keys_align_with_existing_phase1_registry_metadata() -> None:
    registry = create_default_source_acquisition_registry()
    result = create_phase1_source_discovery_candidates()

    assert tuple(candidate.source_key for candidate in result.candidates) == tuple(
        descriptor.source_id for descriptor in registry
    )
    assert tuple(candidate.source_family for candidate in result.candidates) == tuple(
        descriptor.source_family for descriptor in registry
    )
    assert tuple(candidate.title for candidate in result.candidates) == tuple(
        descriptor.display_name for descriptor in registry
    )
    assert tuple(candidate.reference_uri for candidate in result.candidates) == tuple(
        descriptor.acquisition_url for descriptor in registry
    )
    assert tuple(candidate.artifact_kind for candidate in result.candidates) == tuple(
        descriptor.expected_format for descriptor in registry
    )


def test_candidate_result_ordering_is_deterministic() -> None:
    first = create_phase1_source_discovery_candidates()
    second = create_phase1_source_discovery_candidates()

    assert first == second
    assert first.source_keys == EXPECTED_SOURCE_KEYS
    assert tuple(candidate.candidate_id for candidate in first.candidates) == (
        "phase1_candidate_001_ghg_protocol",
        "phase1_candidate_002_defra_desnz",
        "phase1_candidate_003_ipcc_efdb",
    )


@pytest.mark.parametrize(
    ("field_name", "expected_code"),
    (
        ("source_family", "SOURCE_DISCOVERY_CANDIDATE_MISSING_SOURCE_FAMILY"),
        ("source_key", "SOURCE_DISCOVERY_CANDIDATE_MISSING_SOURCE_KEY"),
        ("candidate_id", "SOURCE_DISCOVERY_CANDIDATE_MISSING_CANDIDATE_ID"),
        ("title", "SOURCE_DISCOVERY_CANDIDATE_MISSING_TITLE"),
        ("reference_uri", "SOURCE_DISCOVERY_CANDIDATE_MISSING_REFERENCE_URI"),
        ("artifact_kind", "SOURCE_DISCOVERY_CANDIDATE_MISSING_ARTIFACT_KIND"),
    ),
)
def test_required_metadata_fields_reject_empty_strings(
    field_name: str,
    expected_code: str,
) -> None:
    candidate = create_phase1_source_discovery_candidates().candidates[0]
    invalid_candidate = replace(candidate, **{field_name: " "})

    result = validate_source_discovery_candidate(invalid_candidate)

    assert result.is_valid is False
    assert expected_code in _issue_codes(result)


def test_optional_metadata_fields_reject_empty_strings() -> None:
    candidate = SourceDiscoveryCandidate(
        source_family="defra_desnz",
        source_key="defra_desnz",
        candidate_id="candidate-001",
        title="DEFRA/DESNZ",
        reference_uri="discovery://defra_desnz/source",
        artifact_kind="discovery",
        content_type=" ",
        extension="",
        checksum_sha256=" ",
        version_label="",
        discovered_at_label=" ",
    )

    result = validate_source_discovery_candidate(candidate)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "SOURCE_DISCOVERY_CANDIDATE_BLANK_CONTENT_TYPE",
        "SOURCE_DISCOVERY_CANDIDATE_BLANK_EXTENSION",
        "SOURCE_DISCOVERY_CANDIDATE_BLANK_CHECKSUM_SHA256",
        "SOURCE_DISCOVERY_CANDIDATE_BLANK_VERSION_LABEL",
        "SOURCE_DISCOVERY_CANDIDATE_BLANK_DISCOVERED_AT_LABEL",
    )


def test_invalid_year_metadata_returns_invalid_result() -> None:
    candidate = replace(
        create_phase1_source_discovery_candidates().candidates[1],
        document_year=0,
        reporting_year=-1,
    )

    result = validate_source_discovery_candidate(candidate)

    assert result.is_valid is False
    assert _issue_codes(result) == (
        "SOURCE_DISCOVERY_CANDIDATE_INVALID_DOCUMENT_YEAR",
        "SOURCE_DISCOVERY_CANDIDATE_INVALID_REPORTING_YEAR",
    )


def test_unknown_or_mismatched_source_metadata_returns_invalid_result() -> None:
    unknown = SourceDiscoveryCandidate(
        source_family="unknown",
        source_key="unknown",
        candidate_id="unknown-candidate",
        title="Unknown",
        reference_uri="discovery://unknown/source",
        artifact_kind="discovery",
    )
    mismatched = replace(
        create_phase1_source_discovery_candidates().candidates[2],
        source_family="ghg_protocol",
        artifact_kind="xlsx",
    )

    assert _issue_codes(validate_source_discovery_candidate(unknown)) == (
        "SOURCE_DISCOVERY_CANDIDATE_UNKNOWN_SOURCE_KEY",
    )
    assert _issue_codes(validate_source_discovery_candidate(mismatched)) == (
        "SOURCE_DISCOVERY_CANDIDATE_SOURCE_FAMILY_MISMATCH",
        "SOURCE_DISCOVERY_CANDIDATE_ARTIFACT_KIND_MISMATCH",
    )


def test_candidate_result_validation_prefixes_candidate_locations() -> None:
    candidate = replace(
        create_phase1_source_discovery_candidates().candidates[1],
        title="",
    )
    result = SourceDiscoveryCandidateResult(candidates=(candidate,))

    validation = validate_source_discovery_candidate_result(result)

    assert validation.is_valid is False
    assert validation.issues[0].field_name == "candidates[1].title"
    assert validation.issues[0].code == "SOURCE_DISCOVERY_CANDIDATE_MISSING_TITLE"


def test_url_reference_metadata_is_not_fetched_or_network_validated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = SourceDiscoveryCandidate(
        source_family="ghg_protocol",
        source_key="ghg_protocol",
        candidate_id="candidate-001",
        title="GHG Protocol",
        reference_uri="discovery://not-fetched/source.csv",
        artifact_kind="discovery",
    )

    def fail_urlopen(*args: object, **kwargs: object) -> object:
        raise AssertionError("candidate validation must not fetch references")

    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)

    assert validate_source_discovery_candidate(candidate).is_valid is True


def test_validation_does_not_read_files_access_db_or_network(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    import builtins
    import pathlib
    import sqlite3

    missing_artifact = tmp_path / "candidate.csv"

    def fail_side_effect(*args: object, **kwargs: object) -> object:
        raise AssertionError("source discovery candidates must use metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "exists", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "is_file", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "stat", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)

    candidate = replace(
        create_phase1_source_discovery_candidates().candidates[0],
        reference_uri=str(missing_artifact),
    )

    assert validate_source_discovery_candidate(candidate).is_valid is True


def test_candidate_contract_is_read_only() -> None:
    result = create_phase1_source_discovery_candidates()
    candidate = result.candidates[0]

    with pytest.raises(FrozenInstanceError):
        candidate.source_key = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.candidates = ()  # type: ignore[misc]


def test_validation_result_issue_shape_is_structured() -> None:
    candidate = replace(
        create_phase1_source_discovery_candidates().candidates[0],
        title="",
    )

    issue = validate_source_discovery_candidate(candidate).issues[0]

    assert isinstance(issue, SourceDiscoveryCandidateValidationIssue)
    assert issue.code == "SOURCE_DISCOVERY_CANDIDATE_MISSING_TITLE"
    assert issue.field_name == "title"
    assert issue.severity == "error"
    assert issue.message == "title must be a non-empty string."


def test_validation_result_shape_exposes_is_valid() -> None:
    assert SourceDiscoveryCandidateValidationResult().is_valid is True
    assert SourceDiscoveryCandidateValidationResult(
        issues=(
            SourceDiscoveryCandidateValidationIssue(
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
        "carbonfactor_parser.source_acquisition.discovery_candidate_contract"
    )
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("source discovery candidate import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("source discovery candidate import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_after = set(sys.modules)

    assert hasattr(module, "create_phase1_source_discovery_candidates")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_after - imported_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in (*BANNED_RUNTIME_MODULE_PREFIXES, *BANNED_EXECUTABLE_PARSER_MODULES)
    )


def _issue_codes(
    result: SourceDiscoveryCandidateValidationResult,
) -> tuple[str, ...]:
    return tuple(issue.code for issue in result.issues)
