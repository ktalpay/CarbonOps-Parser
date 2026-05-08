from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import importlib
import sys
import urllib.request

import pytest

from carbonfactor_parser.source_acquisition.ghg_source_discovery_boundary import (
    GHGSourceDiscoveryIssue,
    GHGSourceDiscoveryMode,
    GHGSourceDiscoveryRequest,
    GHGSourceDiscoveryResult,
    GHGSourceDiscoveryStatus,
    GHGSourceDiscoveryValidationResult,
    GHGSourceDocumentCandidate,
    create_ghg_source_discovery_request,
    create_ghg_source_discovery_result,
    validate_ghg_source_discovery_request,
    validate_ghg_source_discovery_result,
    validate_ghg_source_document_candidate,
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
    "carbonfactor_parser.source_acquisition.checksum",
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


def test_ghg_discovery_request_is_deterministic_and_runtime_passive() -> None:
    first = create_ghg_source_discovery_request()
    second = create_ghg_source_discovery_request()

    assert first == second
    assert first == GHGSourceDiscoveryRequest(
        source_family="ghg_protocol",
        source_key="ghg_protocol",
        discovery_reference_uri="discovery://ghg_protocol/acquisition",
        mode=GHGSourceDiscoveryMode.RUNTIME_PASSIVE,
        allow_network=False,
        allow_download=False,
        allow_parse=False,
        allow_database_writes=False,
        allow_scheduler=False,
    )
    assert validate_ghg_source_discovery_request(first).is_valid is True


def test_ghg_discovery_result_declares_candidate_without_download() -> None:
    result = create_ghg_source_discovery_result()

    assert result.status is GHGSourceDiscoveryStatus.DECLARED
    assert result.candidate_count == 1
    assert result.candidate_ids == (
        "ghg_source_discovery_candidate_001_ghg_protocol",
    )
    assert result.no_network is True
    assert result.no_download is True
    assert result.no_parse is True
    assert result.no_database_writes is True
    assert result.no_sql is True
    assert result.no_scheduler is True
    assert validate_ghg_source_discovery_result(result).is_valid is True

    candidate = result.candidates[0]
    assert candidate == GHGSourceDocumentCandidate(
        source_family="ghg_protocol",
        source_key="ghg_protocol",
        candidate_id="ghg_source_discovery_candidate_001_ghg_protocol",
        title="GHG Protocol",
        reference_uri="discovery://ghg_protocol/acquisition",
        artifact_kind="discovery",
        status=GHGSourceDiscoveryStatus.DECLARED,
        version_label="py045_ghg_discovery_boundary",
        discovered_at_label="runtime_passive_discovery_unavailable",
        download_allowed=False,
    )


def test_ghg_discovery_boundary_is_ghg_only() -> None:
    result = create_ghg_source_discovery_result()

    assert tuple(candidate.source_key for candidate in result.candidates) == (
        "ghg_protocol",
    )
    assert "defra_desnz" not in result.candidate_ids
    assert "ipcc_efdb" not in result.candidate_ids


def test_invalid_request_fails_closed_with_no_candidates() -> None:
    request = replace(
        create_ghg_source_discovery_request(),
        source_key="defra_desnz",
        allow_network=True,
        allow_download=True,
        allow_parse=True,
        allow_database_writes=True,
        allow_scheduler=True,
    )

    result = create_ghg_source_discovery_result(request)

    assert result.status is GHGSourceDiscoveryStatus.INVALID
    assert result.candidates == ()
    assert result.no_network is True
    assert result.no_download is True
    assert result.no_parse is True
    assert result.no_database_writes is True
    assert _issue_codes(result.issues) == (
        "GHG_SOURCE_DISCOVERY_SOURCE_KEY_MISMATCH",
        "GHG_SOURCE_DISCOVERY_NETWORK_NOT_ALLOWED",
        "GHG_SOURCE_DISCOVERY_DOWNLOAD_NOT_ALLOWED",
        "GHG_SOURCE_DISCOVERY_PARSE_NOT_ALLOWED",
        "GHG_SOURCE_DISCOVERY_DATABASE_WRITES_NOT_ALLOWED",
        "GHG_SOURCE_DISCOVERY_SCHEDULER_NOT_ALLOWED",
    )


@pytest.mark.parametrize(
    ("field_name", "expected_code"),
    (
        ("source_family", "GHG_SOURCE_DISCOVERY_MISSING_SOURCE_FAMILY"),
        ("source_key", "GHG_SOURCE_DISCOVERY_MISSING_SOURCE_KEY"),
        ("discovery_reference_uri", "GHG_SOURCE_DISCOVERY_MISSING_REFERENCE_URI"),
    ),
)
def test_request_required_fields_fail_closed(
    field_name: str,
    expected_code: str,
) -> None:
    request = replace(create_ghg_source_discovery_request(), **{field_name: " "})

    result = validate_ghg_source_discovery_request(request)

    assert result.is_valid is False
    assert expected_code in _issue_codes(result.issues)


def test_candidate_invalid_inputs_fail_closed() -> None:
    candidate = replace(
        create_ghg_source_discovery_result().candidates[0],
        title="",
        source_family="defra_desnz",
        source_key="defra_desnz",
        artifact_kind="xlsx",
        status=GHGSourceDiscoveryStatus.INVALID,
        download_allowed=True,
        document_year=0,
        reporting_year=-1,
    )

    result = validate_ghg_source_document_candidate(candidate)

    assert result.is_valid is False
    assert _issue_codes(result.issues) == (
        "GHG_SOURCE_DISCOVERY_CANDIDATE_MISSING_TITLE",
        "GHG_SOURCE_DISCOVERY_CANDIDATE_INVALID_DOCUMENT_YEAR",
        "GHG_SOURCE_DISCOVERY_CANDIDATE_INVALID_REPORTING_YEAR",
        "GHG_SOURCE_DISCOVERY_CANDIDATE_SOURCE_FAMILY_MISMATCH",
        "GHG_SOURCE_DISCOVERY_CANDIDATE_SOURCE_KEY_MISMATCH",
        "GHG_SOURCE_DISCOVERY_CANDIDATE_ARTIFACT_KIND_MISMATCH",
        "GHG_SOURCE_DISCOVERY_CANDIDATE_UNSUPPORTED_STATUS",
        "GHG_SOURCE_DISCOVERY_CANDIDATE_DOWNLOAD_NOT_ALLOWED",
    )


def test_candidate_reference_is_not_fetched_or_downloaded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = replace(
        create_ghg_source_discovery_result().candidates[0],
        reference_uri="https://example.invalid/not-fetched.csv",
    )

    def fail_urlopen(*args: object, **kwargs: object) -> object:
        raise AssertionError("GHG discovery boundary must not fetch references")

    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)

    assert validate_ghg_source_document_candidate(candidate).is_valid is True


def test_validation_does_not_read_files_access_db_or_network(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    import builtins
    import pathlib
    import sqlite3

    missing_reference = tmp_path / "ghg-source.csv"

    def fail_side_effect(*args: object, **kwargs: object) -> object:
        raise AssertionError("GHG source discovery must use metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "exists", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "is_file", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "stat", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)

    candidate = replace(
        create_ghg_source_discovery_result().candidates[0],
        reference_uri=str(missing_reference),
    )

    assert validate_ghg_source_document_candidate(candidate).is_valid is True


def test_result_validation_rejects_side_effect_flags() -> None:
    result = replace(
        create_ghg_source_discovery_result(),
        no_network=False,
        no_sql=False,
    )

    validation = validate_ghg_source_discovery_result(result)

    assert validation.is_valid is False
    assert _issue_codes(validation.issues) == (
        "GHG_SOURCE_DISCOVERY_RESULT_SIDE_EFFECT_FLAG_ENABLED",
        "GHG_SOURCE_DISCOVERY_RESULT_SIDE_EFFECT_FLAG_ENABLED",
        "GHG_SOURCE_DISCOVERY_RESULT_STATUS_MISMATCH",
    )
    assert tuple(issue.field_name for issue in validation.issues[:2]) == (
        "no_network",
        "no_sql",
    )


def test_ghg_discovery_contract_dataclasses_are_immutable() -> None:
    request = create_ghg_source_discovery_request()
    result = create_ghg_source_discovery_result()
    candidate = result.candidates[0]

    with pytest.raises(FrozenInstanceError):
        request.source_key = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.candidates = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        candidate.title = "changed"  # type: ignore[misc]


def test_validation_result_issue_shape_is_structured() -> None:
    candidate = replace(create_ghg_source_discovery_result().candidates[0], title="")

    issue = validate_ghg_source_document_candidate(candidate).issues[0]

    assert isinstance(issue, GHGSourceDiscoveryIssue)
    assert issue.code == "GHG_SOURCE_DISCOVERY_CANDIDATE_MISSING_TITLE"
    assert issue.field_name == "title"
    assert issue.severity == "error"
    assert issue.message == "title must be a non-empty string."
    assert GHGSourceDiscoveryValidationResult().is_valid is True
    assert GHGSourceDiscoveryValidationResult(issues=(issue,)).is_valid is False


def test_ghg_discovery_boundary_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = (
        "carbonfactor_parser.source_acquisition.ghg_source_discovery_boundary"
    )
    cleared_modules = _clear_relevant_modules()

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("GHG discovery boundary import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("GHG discovery boundary import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    try:
        imported_before = set(sys.modules)
        module = importlib.import_module(module_name)
        imported_after = set(sys.modules)
    finally:
        _restore_modules(cleared_modules)

    assert hasattr(module, "create_ghg_source_discovery_result")
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


def test_ghg_boundary_exports_through_contract_api() -> None:
    from carbonfactor_parser.source_acquisition import contract_api

    result = contract_api.create_ghg_source_discovery_result()

    assert result.status is contract_api.GHGSourceDiscoveryStatus.DECLARED
    assert result.candidate_count == 1
    assert contract_api.validate_ghg_source_discovery_result(result).is_valid


def _issue_codes(
    issues: tuple[GHGSourceDiscoveryIssue, ...],
) -> tuple[str, ...]:
    return tuple(issue.code for issue in issues)


def _clear_relevant_modules() -> dict[str, object]:
    cleared_modules: dict[str, object] = {}
    for module_name in tuple(sys.modules):
        if module_name == "carbonfactor_parser" or module_name.startswith(
            "carbonfactor_parser.source_acquisition",
        ):
            module = sys.modules.pop(module_name, None)
            if module is not None:
                cleared_modules[module_name] = module
    return cleared_modules


def _restore_modules(cleared_modules: dict[str, object]) -> None:
    for module_name in tuple(sys.modules):
        if module_name == "carbonfactor_parser" or module_name.startswith(
            "carbonfactor_parser.source_acquisition",
        ):
            sys.modules.pop(module_name, None)
    sys.modules.update(cleared_modules)
