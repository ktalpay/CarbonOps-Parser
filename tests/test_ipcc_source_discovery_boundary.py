from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import importlib
import sys
import urllib.request

import pytest

from carbonfactor_parser.source_acquisition.ipcc_source_discovery_boundary import (
    IPCCSourceDiscoveryIssue,
    IPCCSourceDiscoveryMode,
    IPCCSourceDiscoveryRequest,
    IPCCSourceDiscoveryResult,
    IPCCSourceDiscoveryStatus,
    IPCCSourceDiscoveryValidationResult,
    IPCCSourceDocumentCandidate,
    create_ipcc_source_discovery_request,
    create_ipcc_source_discovery_result,
    validate_ipcc_source_discovery_request,
    validate_ipcc_source_discovery_result,
    validate_ipcc_source_document_candidate,
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
    "carbonfactor_parser.parsers.ipcc_efdb_adapter",
    "carbonfactor_parser.parsers.ipcc_efdb_parser",
    "carbonfactor_parser.parsers.execution_runner",
    "carbonfactor_parser.parsers.file_content_loader",
)


def test_ipcc_discovery_request_is_deterministic_and_runtime_passive() -> None:
    first = create_ipcc_source_discovery_request()
    second = create_ipcc_source_discovery_request()

    assert first == second
    assert first == IPCCSourceDiscoveryRequest(
        source_family="ipcc_efdb",
        source_key="ipcc_efdb",
        discovery_reference_uri="discovery://ipcc_efdb/homepage",
        mode=IPCCSourceDiscoveryMode.RUNTIME_PASSIVE,
        allow_network=False,
        allow_download=False,
        allow_parse=False,
        allow_database_writes=False,
        allow_scheduler=False,
    )
    assert validate_ipcc_source_discovery_request(first).is_valid is True


def test_ipcc_discovery_result_declares_candidate_without_download() -> None:
    result = create_ipcc_source_discovery_result()

    assert result.status is IPCCSourceDiscoveryStatus.DECLARED
    assert result.candidate_count == 1
    assert result.candidate_ids == (
        "ipcc_source_discovery_candidate_001_ipcc_efdb",
    )
    assert result.no_network is True
    assert result.no_download is True
    assert result.no_parse is True
    assert result.no_database_writes is True
    assert result.no_sql is True
    assert result.no_scheduler is True
    assert validate_ipcc_source_discovery_result(result).is_valid is True

    candidate = result.candidates[0]
    assert candidate == IPCCSourceDocumentCandidate(
        source_family="ipcc_efdb",
        source_key="ipcc_efdb",
        candidate_id="ipcc_source_discovery_candidate_001_ipcc_efdb",
        title="IPCC EFDB",
        reference_uri="discovery://ipcc_efdb/homepage",
        artifact_kind="discovery",
        status=IPCCSourceDiscoveryStatus.DECLARED,
        version_label="py049_ipcc_discovery_boundary",
        discovered_at_label="runtime_passive_discovery_unavailable",
        download_allowed=False,
    )


def test_ipcc_discovery_boundary_is_ipcc_only() -> None:
    result = create_ipcc_source_discovery_result()

    assert tuple(candidate.source_key for candidate in result.candidates) == (
        "ipcc_efdb",
    )
    assert tuple(candidate.source_family for candidate in result.candidates) == (
        "ipcc_efdb",
    )
    assert "ghg_protocol" not in {
        candidate.source_family for candidate in result.candidates
    }
    assert "defra_desnz" not in {
        candidate.source_family for candidate in result.candidates
    }


def test_invalid_request_fails_closed_with_no_candidates() -> None:
    request = replace(
        create_ipcc_source_discovery_request(),
        source_key="ghg_protocol",
        allow_network=True,
        allow_download=True,
        allow_parse=True,
        allow_database_writes=True,
        allow_scheduler=True,
    )

    result = create_ipcc_source_discovery_result(request)

    assert result.status is IPCCSourceDiscoveryStatus.INVALID
    assert result.candidates == ()
    assert result.no_network is True
    assert result.no_download is True
    assert result.no_parse is True
    assert result.no_database_writes is True
    assert _issue_codes(result.issues) == (
        "IPCC_SOURCE_DISCOVERY_SOURCE_KEY_MISMATCH",
        "IPCC_SOURCE_DISCOVERY_NETWORK_NOT_ALLOWED",
        "IPCC_SOURCE_DISCOVERY_DOWNLOAD_NOT_ALLOWED",
        "IPCC_SOURCE_DISCOVERY_PARSE_NOT_ALLOWED",
        "IPCC_SOURCE_DISCOVERY_DATABASE_WRITES_NOT_ALLOWED",
        "IPCC_SOURCE_DISCOVERY_SCHEDULER_NOT_ALLOWED",
    )


@pytest.mark.parametrize(
    ("field_name", "expected_code"),
    (
        ("source_family", "IPCC_SOURCE_DISCOVERY_MISSING_SOURCE_FAMILY"),
        ("source_key", "IPCC_SOURCE_DISCOVERY_MISSING_SOURCE_KEY"),
        ("discovery_reference_uri", "IPCC_SOURCE_DISCOVERY_MISSING_REFERENCE_URI"),
    ),
)
def test_request_required_fields_fail_closed(
    field_name: str,
    expected_code: str,
) -> None:
    request = replace(create_ipcc_source_discovery_request(), **{field_name: " "})

    result = validate_ipcc_source_discovery_request(request)

    assert result.is_valid is False
    assert expected_code in _issue_codes(result.issues)


def test_candidate_invalid_inputs_fail_closed() -> None:
    candidate = replace(
        create_ipcc_source_discovery_result().candidates[0],
        title="",
        source_family="ghg_protocol",
        source_key="ghg_protocol",
        artifact_kind="xlsx",
        status=IPCCSourceDiscoveryStatus.INVALID,
        download_allowed=True,
        document_year=0,
        reporting_year=-1,
    )

    result = validate_ipcc_source_document_candidate(candidate)

    assert result.is_valid is False
    assert _issue_codes(result.issues) == (
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_TITLE",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_INVALID_DOCUMENT_YEAR",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_INVALID_REPORTING_YEAR",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_SOURCE_FAMILY_MISMATCH",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_SOURCE_KEY_MISMATCH",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_ARTIFACT_KIND_MISMATCH",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_UNSUPPORTED_STATUS",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_DOWNLOAD_NOT_ALLOWED",
    )


def test_candidate_reference_is_not_fetched_or_downloaded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = replace(
        create_ipcc_source_discovery_result().candidates[0],
        reference_uri="https://example.invalid/not-fetched.csv",
    )

    def fail_urlopen(*args: object, **kwargs: object) -> object:
        raise AssertionError("IPCC discovery boundary must not fetch references")

    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)

    assert validate_ipcc_source_document_candidate(candidate).is_valid is True


def test_validation_does_not_read_write_files_access_db_or_network(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    import builtins
    import pathlib
    import sqlite3

    missing_reference = tmp_path / "ipcc-source.csv"

    def fail_side_effect(*args: object, **kwargs: object) -> object:
        raise AssertionError("IPCC source discovery must use metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "exists", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "is_file", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "stat", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "write_text", fail_side_effect)
    monkeypatch.setattr(pathlib.Path, "write_bytes", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)

    candidate = replace(
        create_ipcc_source_discovery_result().candidates[0],
        reference_uri=str(missing_reference),
    )

    assert validate_ipcc_source_document_candidate(candidate).is_valid is True


def test_result_validation_rejects_side_effect_flags() -> None:
    result = replace(
        create_ipcc_source_discovery_result(),
        no_network=False,
        no_sql=False,
    )

    validation = validate_ipcc_source_discovery_result(result)

    assert validation.is_valid is False
    assert _issue_codes(validation.issues) == (
        "IPCC_SOURCE_DISCOVERY_RESULT_SIDE_EFFECT_FLAG_ENABLED",
        "IPCC_SOURCE_DISCOVERY_RESULT_SIDE_EFFECT_FLAG_ENABLED",
        "IPCC_SOURCE_DISCOVERY_RESULT_STATUS_MISMATCH",
    )
    assert tuple(issue.field_name for issue in validation.issues[:2]) == (
        "no_network",
        "no_sql",
    )


def test_result_validation_rejects_declared_results_with_issue_metadata() -> None:
    result = replace(
        create_ipcc_source_discovery_result(),
        issues=(
            IPCCSourceDiscoveryIssue(
                code="IPCC_SOURCE_DISCOVERY_TEST_ISSUE",
                message="test issue",
                field_name="test",
            ),
        ),
    )

    validation = validate_ipcc_source_discovery_result(result)

    assert validation.is_valid is False
    assert _issue_codes(validation.issues) == (
        "IPCC_SOURCE_DISCOVERY_RESULT_DECLARED_WITH_ISSUES",
        "IPCC_SOURCE_DISCOVERY_RESULT_STATUS_MISMATCH",
    )


def test_result_validation_rejects_undefined_status() -> None:
    result = replace(
        create_ipcc_source_discovery_result(),
        status="declared",  # type: ignore[arg-type]
    )

    validation = validate_ipcc_source_discovery_result(result)

    assert validation.is_valid is False
    assert _issue_codes(validation.issues) == (
        "IPCC_SOURCE_DISCOVERY_RESULT_INVALID_STATUS",
    )


def test_ipcc_discovery_contract_dataclasses_are_immutable() -> None:
    request = create_ipcc_source_discovery_request()
    result = create_ipcc_source_discovery_result()
    candidate = result.candidates[0]

    with pytest.raises(FrozenInstanceError):
        request.source_key = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.candidates = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        candidate.title = "changed"  # type: ignore[misc]


def test_validation_result_issue_shape_is_structured() -> None:
    candidate = replace(create_ipcc_source_discovery_result().candidates[0], title="")

    issue = validate_ipcc_source_document_candidate(candidate).issues[0]

    assert isinstance(issue, IPCCSourceDiscoveryIssue)
    assert issue.code == "IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_TITLE"
    assert issue.field_name == "title"
    assert issue.severity == "error"
    assert issue.message == "title must be a non-empty string."
    assert IPCCSourceDiscoveryValidationResult().is_valid is True
    assert IPCCSourceDiscoveryValidationResult(issues=(issue,)).is_valid is False


def test_ipcc_discovery_boundary_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = (
        "carbonfactor_parser.source_acquisition.ipcc_source_discovery_boundary"
    )
    cleared_modules = _clear_relevant_modules()

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("IPCC discovery boundary import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("IPCC discovery boundary import read environment")

    def guard_urlopen(*args: object, **kwargs: object) -> object:
        raise AssertionError("IPCC discovery boundary import opened network")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})
    monkeypatch.setattr(urllib.request, "urlopen", guard_urlopen)

    try:
        imported_before = set(sys.modules)
        module = importlib.import_module(module_name)
        imported_after = set(sys.modules)
    finally:
        _restore_modules(cleared_modules)

    assert hasattr(module, "create_ipcc_source_discovery_result")
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


def test_ipcc_boundary_exports_through_contract_api() -> None:
    from carbonfactor_parser.source_acquisition import contract_api

    result = contract_api.create_ipcc_source_discovery_result()

    assert result.status is contract_api.IPCCSourceDiscoveryStatus.DECLARED
    assert result.candidate_count == 1
    assert contract_api.validate_ipcc_source_discovery_result(result).is_valid


def test_ipcc_boundary_does_not_regress_existing_ghg_defra_boundaries(
    tmp_path,
) -> None:
    from carbonfactor_parser.source_acquisition.defra_source_discovery_boundary import (
        create_defra_source_discovery_result,
        validate_defra_source_discovery_result,
    )
    from carbonfactor_parser.source_acquisition.defra_source_download_execution_boundary import (
        create_defra_source_download_execution_request,
        validate_defra_source_download_execution_request,
    )
    from carbonfactor_parser.source_acquisition.ghg_source_discovery_boundary import (
        create_ghg_source_discovery_result,
        validate_ghg_source_discovery_result,
    )
    from carbonfactor_parser.source_acquisition.ghg_source_download_execution_boundary import (
        create_ghg_source_download_execution_request,
        validate_ghg_source_download_execution_request,
    )

    defra_discovery = create_defra_source_discovery_result()
    defra_download_request = create_defra_source_download_execution_request(
        defra_discovery.candidates[0],
        target_root=str(tmp_path / "defra"),
        target_relative_path="defra/source.discovery",
    )
    ghg_discovery = create_ghg_source_discovery_result()
    ghg_download_request = create_ghg_source_download_execution_request(
        ghg_discovery.candidates[0],
        target_root=str(tmp_path / "ghg"),
        target_relative_path="ghg/source.discovery",
    )

    assert validate_defra_source_discovery_result(defra_discovery).is_valid
    assert (
        validate_defra_source_download_execution_request(
            defra_download_request,
        ).is_valid
        is False
    )
    assert validate_ghg_source_discovery_result(ghg_discovery).is_valid
    assert (
        validate_ghg_source_download_execution_request(
            ghg_download_request,
        ).is_valid
        is False
    )


def _issue_codes(
    issues: tuple[IPCCSourceDiscoveryIssue, ...],
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
