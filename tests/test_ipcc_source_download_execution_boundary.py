from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
import importlib
import json
from pathlib import Path
import shutil
import sys
import urllib.request

import pytest

from carbonfactor_parser.source_acquisition import (
    ipcc_source_download_execution_boundary as download_boundary,
)
from carbonfactor_parser.source_acquisition.ipcc_source_discovery_boundary import (
    create_ipcc_source_discovery_result,
)
from carbonfactor_parser.source_acquisition.ipcc_source_download_execution_boundary import (
    IPCCSourceDownloadExecutionIssue,
    IPCCSourceDownloadExecutionRequest,
    IPCCSourceDownloadExecutionResult,
    IPCCSourceDownloadExecutionStatus,
    IPCCSourceDownloadExecutionValidationResult,
    IPCCSourceDownloadTransportResponse,
    IPCCSourceDownloadedArtifact,
    create_ipcc_source_download_execution_request,
    execute_ipcc_source_download,
    validate_ipcc_source_download_execution_request,
    validate_ipcc_source_download_execution_result,
)

IPCC_XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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

PARITY_FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures/parity/ipcc_source_download_execution_expectations.json"
)


def test_download_request_from_candidate_is_explicit_opt_in(tmp_path: Path) -> None:
    candidate = _downloadable_candidate()

    request = create_ipcc_source_download_execution_request(
        candidate,
        target_root=str(tmp_path),
        target_relative_path="ipcc/efdb.xlsx",
    )

    assert request == IPCCSourceDownloadExecutionRequest(
        source_family="ipcc_efdb",
        source_key="ipcc_efdb",
        candidate_id="ipcc_source_discovery_candidate_001_ipcc_efdb",
        candidate_title="IPCC EFDB",
        source_reference_uri="mock://ipcc_efdb/efdb.xlsx",
        artifact_kind="xlsx",
        target_root=str(tmp_path),
        target_relative_path="ipcc/efdb.xlsx",
        candidate_download_allowed=True,
        allow_download_execution=False,
        allow_file_write=False,
        content_type=IPCC_XLSX_CONTENT_TYPE,
        extension=".xlsx",
        version_label="py053_mock_download",
    )
    validation = validate_ipcc_source_download_execution_request(request)
    assert validation.is_valid is False
    assert _issue_codes(validation.issues) == (
        "IPCC_SOURCE_DOWNLOAD_EXECUTION_NOT_ALLOWED",
        "IPCC_SOURCE_DOWNLOAD_FILE_WRITE_NOT_ALLOWED",
    )


def test_default_discovery_candidate_is_not_downloadable(tmp_path: Path) -> None:
    candidate = create_ipcc_source_discovery_result().candidates[0]
    request = create_ipcc_source_download_execution_request(
        candidate,
        target_root=str(tmp_path),
        target_relative_path="ipcc/source.discovery",
        allow_download_execution=True,
        allow_file_write=True,
    )

    result = execute_ipcc_source_download(request, _unexpected_transport)

    assert result.status is IPCCSourceDownloadExecutionStatus.BLOCKED
    assert result.artifact is None
    assert _issue_codes(result.issues) == (
        "IPCC_SOURCE_DOWNLOAD_CANDIDATE_NOT_DOWNLOADABLE",
        "IPCC_SOURCE_DOWNLOAD_DISCOVERY_REFERENCE_NOT_DOWNLOADABLE",
    )
    assert not (tmp_path / "ipcc/source.discovery").exists()


def test_invalid_download_requests_fail_closed_before_transport(
    tmp_path: Path,
) -> None:
    request = replace(
        _valid_request(tmp_path),
        source_family="ghg_protocol",
        source_key="ghg_protocol",
        allow_parse=True,
        allow_database_writes=True,
        allow_scheduler=True,
    )

    result = execute_ipcc_source_download(request, _unexpected_transport)

    assert result.status is IPCCSourceDownloadExecutionStatus.BLOCKED
    assert result.downloaded is False
    assert result.artifact is None
    assert result.no_parse is True
    assert result.no_database_writes is True
    assert result.no_sql is True
    assert result.no_scheduler is True
    assert _issue_codes(result.issues) == (
        "IPCC_SOURCE_DOWNLOAD_SOURCE_FAMILY_MISMATCH",
        "IPCC_SOURCE_DOWNLOAD_SOURCE_KEY_MISMATCH",
        "IPCC_SOURCE_DOWNLOAD_PARSE_NOT_ALLOWED",
        "IPCC_SOURCE_DOWNLOAD_DATABASE_WRITES_NOT_ALLOWED",
        "IPCC_SOURCE_DOWNLOAD_SCHEDULER_NOT_ALLOWED",
    )


@pytest.mark.parametrize(
    ("field_name", "value", "expected_code"),
    (
        (
            "source_reference_uri",
            "https://example.invalid/ipcc.xlsx",
            "IPCC_SOURCE_DOWNLOAD_NETWORK_NOT_ALLOWED",
        ),
        (
            "source_reference_uri",
            "http" + "://example.invalid/ipcc.xlsx",
            "IPCC_SOURCE_DOWNLOAD_INSECURE_HTTP_NOT_ALLOWED",
        ),
        (
            "source_reference_uri",
            "file:///tmp/ipcc.xlsx",
            "IPCC_SOURCE_DOWNLOAD_UNSAFE_SOURCE_REFERENCE_URI",
        ),
        (
            "source_reference_uri",
            "s3://bucket/ipcc.xlsx",
            "IPCC_SOURCE_DOWNLOAD_UNSAFE_SOURCE_REFERENCE_URI",
        ),
        (
            "source_reference_uri",
            "ipcc/efdb.xlsx",
            "IPCC_SOURCE_DOWNLOAD_SOURCE_REFERENCE_URI_MISSING_SCHEME",
        ),
        (
            "source_reference_uri",
            "://ipcc/efdb.xlsx",
            "IPCC_SOURCE_DOWNLOAD_MALFORMED_SOURCE_REFERENCE_URI",
        ),
        (
            "source_reference_uri",
            "https:///ipcc.xlsx",
            "IPCC_SOURCE_DOWNLOAD_MALFORMED_SOURCE_REFERENCE_URI",
        ),
        (
            "target_root",
            "relative/root",
            "IPCC_SOURCE_DOWNLOAD_TARGET_ROOT_NOT_ABSOLUTE",
        ),
        (
            "target_relative_path",
            "../outside.xlsx",
            "IPCC_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_UNSAFE",
        ),
        (
            "target_relative_path",
            "/absolute.xlsx",
            "IPCC_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_ABSOLUTE",
        ),
        (
            "target_relative_path",
            "download://ipcc/source.xlsx",
            "IPCC_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_URI",
        ),
    ),
)
def test_unsafe_request_inputs_fail_closed(
    tmp_path: Path,
    field_name: str,
    value: str,
    expected_code: str,
) -> None:
    request = replace(_valid_request(tmp_path), **{field_name: value})

    validation = validate_ipcc_source_download_execution_request(request)

    assert validation.is_valid is False
    assert expected_code in _issue_codes(validation.issues)


def test_successful_download_is_explicit_and_uses_injected_transport(
    tmp_path: Path,
) -> None:
    payload = b"deterministic ipcc source bytes"
    calls: list[str] = []

    def transport(source_reference_uri: str) -> IPCCSourceDownloadTransportResponse:
        calls.append(source_reference_uri)
        return IPCCSourceDownloadTransportResponse(
            content=payload,
            content_type=IPCC_XLSX_CONTENT_TYPE,
            final_uri="mock://ipcc_efdb/final.xlsx",
        )

    request = _valid_request(tmp_path)
    result = execute_ipcc_source_download(request, transport)

    target_path = tmp_path / "ipcc/efdb.xlsx"
    checksum = sha256(payload).hexdigest()
    assert calls == ["mock://ipcc_efdb/efdb.xlsx"]
    assert target_path.read_bytes() == payload
    assert result == IPCCSourceDownloadExecutionResult(
        status=IPCCSourceDownloadExecutionStatus.DOWNLOADED,
        request=request,
        artifact=IPCCSourceDownloadedArtifact(
            source_family="ipcc_efdb",
            source_key="ipcc_efdb",
            candidate_id="ipcc_source_discovery_candidate_001_ipcc_efdb",
            artifact_id=(
                "ipcc_source_download_artifact_"
                "ipcc_source_discovery_candidate_001_ipcc_efdb"
            ),
            artifact_kind="xlsx",
            source_reference_uri="mock://ipcc_efdb/efdb.xlsx",
            local_path=str(target_path),
            original_filename="efdb.xlsx",
            checksum_sha256=checksum,
            size_bytes=len(payload),
            content_type=IPCC_XLSX_CONTENT_TYPE,
            extension=".xlsx",
            final_uri="mock://ipcc_efdb/final.xlsx",
            storage_identity=str(target_path),
            version_label="py053_mock_download",
            retrieved_at_label="download_execution_retrieved_at_caller_boundary",
        ),
    )
    assert result.downloaded is True
    assert validate_ipcc_source_download_execution_result(result).is_valid is True


def test_download_execution_matches_shared_parity_fixture(tmp_path: Path) -> None:
    fixture = _load_parity_fixture()
    request = replace(
        _fixture_request(tmp_path, fixture),
        expected_checksum_sha256=fixture["successful_download"]["checksum_sha256"],
    )
    payload = fixture["successful_download"]["payload_text"].encode()

    successful = execute_ipcc_source_download(
        request,
        lambda _: IPCCSourceDownloadTransportResponse(
            content=payload,
            content_type=fixture["content_type"],
            final_uri=fixture["successful_download"]["final_uri"],
        ),
    )

    assert successful.status.value == fixture["successful_download"]["status"]
    assert successful.downloaded is fixture["successful_download"]["downloaded"]
    assert successful.artifact is not None
    assert successful.artifact.source_family == fixture["source_family"]
    assert successful.artifact.source_key == fixture["source_key"]
    assert successful.artifact.candidate_id == fixture["candidate_id"]
    assert successful.artifact.artifact_kind == fixture["artifact_kind"]
    assert successful.artifact.checksum_sha256 == (
        fixture["successful_download"]["checksum_sha256"]
    )
    assert successful.artifact.size_bytes == fixture["successful_download"]["size_bytes"]
    assert successful.artifact.content_type == fixture["content_type"]
    assert successful.artifact.extension == fixture["extension"]
    assert successful.artifact.final_uri == fixture["successful_download"]["final_uri"]
    assert successful.artifact.document_year == fixture["document_year"]
    assert successful.artifact.reporting_year == fixture["reporting_year"]
    assert successful.artifact.version_label == fixture["version_label"]
    assert successful.artifact.reused_existing is (
        fixture["successful_download"]["reused_existing"]
    )
    assert _issue_codes(successful.issues) == tuple(
        fixture["successful_download"]["issue_codes"]
    )

    existing_root = tmp_path / "existing"
    existing_request = replace(
        _fixture_request(existing_root, fixture),
        expected_checksum_sha256=fixture["existing_known_document"]["checksum_sha256"],
    )
    existing_target = existing_root / fixture["target_relative_path"]
    existing_target.parent.mkdir(parents=True)
    existing_target.write_bytes(fixture["existing_known_document"]["payload_text"].encode())

    existing = execute_ipcc_source_download(existing_request, _unexpected_transport)

    assert existing.status.value == fixture["existing_known_document"]["python"]["status"]
    assert existing.downloaded is fixture["existing_known_document"]["python"]["downloaded"]
    assert existing.artifact is not None
    assert existing.artifact.reused_existing is (
        fixture["existing_known_document"]["python"]["reused_existing"]
    )
    assert existing.artifact.checksum_sha256 == (
        fixture["existing_known_document"]["checksum_sha256"]
    )
    assert existing.artifact.size_bytes == fixture["existing_known_document"]["size_bytes"]
    assert _issue_codes(existing.issues) == tuple(
        fixture["existing_known_document"]["issue_codes"]
    )

    mismatch = execute_ipcc_source_download(
        replace(
            _fixture_request(tmp_path / "mismatch", fixture),
            expected_checksum_sha256=fixture["checksum_mismatch"][
                "expected_checksum_sha256"
            ],
        ),
        lambda _: IPCCSourceDownloadTransportResponse(
            content=fixture["checksum_mismatch"]["payload_text"].encode()
        ),
    )
    assert mismatch.status.value == fixture["checksum_mismatch"]["status"]
    assert mismatch.artifact is fixture["checksum_mismatch"]["artifact"]
    assert _issue_codes(mismatch.issues) == tuple(
        fixture["checksum_mismatch"]["issue_codes"]
    )

    blank_metadata = execute_ipcc_source_download(
        _fixture_request(tmp_path / "blank-metadata", fixture),
        lambda _: IPCCSourceDownloadTransportResponse(
            content=b"content",
            content_type=" ",
            final_uri=" ",
        ),
    )
    assert blank_metadata.status.value == fixture["blank_response_metadata"]["status"]
    assert blank_metadata.artifact is fixture["blank_response_metadata"]["artifact"]
    assert _issue_codes(blank_metadata.issues) == tuple(
        fixture["blank_response_metadata"]["issue_codes"]
    )

    default_candidate_request = create_ipcc_source_download_execution_request(
        create_ipcc_source_discovery_result().candidates[0],
        target_root=str(tmp_path / "default-candidate"),
        target_relative_path=fixture["target_relative_path"],
        allow_download_execution=True,
        allow_file_write=True,
    )
    default_candidate = execute_ipcc_source_download(
        default_candidate_request,
        _unexpected_transport,
    )
    assert default_candidate.status.value == fixture["default_candidate_blocked"]["status"]
    assert default_candidate.artifact is fixture["default_candidate_blocked"]["artifact"]
    assert _issue_codes(default_candidate.issues) == tuple(
        fixture["default_candidate_blocked"]["issue_codes"]
    )


def test_existing_known_target_is_idempotent_without_transport(
    tmp_path: Path,
) -> None:
    request = _valid_request(tmp_path)
    target_path = tmp_path / request.target_relative_path
    payload = b"existing ipcc bytes"
    target_path.parent.mkdir(parents=True)
    target_path.write_bytes(payload)

    result = execute_ipcc_source_download(request, _unexpected_transport)

    assert result.status is IPCCSourceDownloadExecutionStatus.DOWNLOADED
    assert result.downloaded is True
    assert result.issues == ()
    assert result.artifact is not None
    assert result.artifact.local_path == str(target_path)
    assert result.artifact.storage_identity == str(target_path)
    assert result.artifact.source_reference_uri == request.source_reference_uri
    assert result.artifact.version_label == "py053_mock_download"
    assert result.artifact.retrieved_at_label == (
        "download_execution_retrieved_at_caller_boundary"
    )
    assert result.artifact.reused_existing is True
    assert result.artifact.checksum_sha256 == sha256(payload).hexdigest()
    assert target_path.read_bytes() == payload


def test_existing_known_target_checksum_mismatch_fails_without_transport(
    tmp_path: Path,
) -> None:
    request = replace(_valid_request(tmp_path), expected_checksum_sha256="a" * 64)
    target_path = tmp_path / request.target_relative_path
    target_path.parent.mkdir(parents=True)
    target_path.write_bytes(b"existing ipcc bytes")

    result = execute_ipcc_source_download(request, _unexpected_transport)

    assert result.status is IPCCSourceDownloadExecutionStatus.FAILED
    assert result.artifact is None
    assert _issue_codes(result.issues) == (
        "IPCC_SOURCE_DOWNLOAD_EXISTING_CHECKSUM_MISMATCH",
    )


def test_symlinked_parent_path_cannot_escape_target_root(tmp_path: Path) -> None:
    target_root = tmp_path / "target-root"
    outside = tmp_path / "outside"
    target_root.mkdir()
    outside.mkdir()
    _create_directory_symlink(outside, target_root / "link")
    request = replace(
        _valid_request(target_root),
        target_relative_path="link/escape.xlsx",
    )

    result = execute_ipcc_source_download(
        request,
        lambda _: IPCCSourceDownloadTransportResponse(content=b"escape"),
    )

    assert result.status is IPCCSourceDownloadExecutionStatus.BLOCKED
    assert result.downloaded is False
    assert result.artifact is None
    assert _issue_codes(result.issues) == (
        "IPCC_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE",
    )
    assert not (outside / "escape.xlsx").exists()
    assert not (target_root / "link/escape.xlsx").exists()


def test_existing_final_target_symlink_is_rejected(tmp_path: Path) -> None:
    target_root = tmp_path / "target-root"
    outside = tmp_path / "outside"
    target_parent = target_root / "ipcc"
    target_parent.mkdir(parents=True)
    outside.mkdir()
    (target_parent / "escape.xlsx").symlink_to(outside / "escape.xlsx")
    request = replace(
        _valid_request(target_root),
        target_relative_path="ipcc/escape.xlsx",
        allow_overwrite=True,
    )

    result = execute_ipcc_source_download(
        request,
        lambda _: IPCCSourceDownloadTransportResponse(content=b"escape"),
    )

    assert result.status is IPCCSourceDownloadExecutionStatus.BLOCKED
    assert result.downloaded is False
    assert result.artifact is None
    assert _issue_codes(result.issues) == (
        "IPCC_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE",
    )
    assert not (outside / "escape.xlsx").exists()
    assert (target_parent / "escape.xlsx").is_symlink()


def test_parent_symlink_swap_during_transport_cannot_escape_target_root(
    tmp_path: Path,
) -> None:
    target_root = tmp_path / "target-root"
    outside = tmp_path / "outside"
    target_parent = target_root / "ipcc"
    target_parent.mkdir(parents=True)
    outside.mkdir()
    request = replace(
        _valid_request(target_root),
        target_relative_path="ipcc/escape.xlsx",
    )

    def swapping_transport(_: str) -> IPCCSourceDownloadTransportResponse:
        shutil.rmtree(target_parent)
        _create_directory_symlink(outside, target_parent)
        return IPCCSourceDownloadTransportResponse(content=b"escape")

    result = execute_ipcc_source_download(request, swapping_transport)

    assert result.status is not IPCCSourceDownloadExecutionStatus.DOWNLOADED
    assert result.downloaded is False
    assert result.artifact is None
    assert not (outside / "escape.xlsx").exists()
    assert target_parent.is_symlink()


def test_missing_no_follow_support_fails_closed_before_transport(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delattr(download_boundary.os, "O_NOFOLLOW", raising=False)

    result = execute_ipcc_source_download(
        _valid_request(tmp_path),
        _unexpected_transport,
    )

    assert result.status is IPCCSourceDownloadExecutionStatus.BLOCKED
    assert result.downloaded is False
    assert _issue_codes(result.issues) == (
        "IPCC_SOURCE_DOWNLOAD_TARGET_FD_UNSUPPORTED",
    )


def test_missing_directory_flag_support_fails_closed_before_transport(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delattr(download_boundary.os, "O_DIRECTORY", raising=False)

    result = execute_ipcc_source_download(
        _valid_request(tmp_path),
        _unexpected_transport,
    )

    assert result.status is IPCCSourceDownloadExecutionStatus.BLOCKED
    assert result.downloaded is False
    assert _issue_codes(result.issues) == (
        "IPCC_SOURCE_DOWNLOAD_TARGET_FD_UNSUPPORTED",
    )


def test_missing_dir_fd_support_fails_closed_before_transport(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(download_boundary.os, "supports_dir_fd", set())

    result = execute_ipcc_source_download(
        _valid_request(tmp_path),
        _unexpected_transport,
    )

    assert result.status is IPCCSourceDownloadExecutionStatus.BLOCKED
    assert result.downloaded is False
    assert _issue_codes(result.issues) == (
        "IPCC_SOURCE_DOWNLOAD_TARGET_FD_UNSUPPORTED",
    )


def test_checksum_mismatch_fails_without_writing_file(tmp_path: Path) -> None:
    request = replace(_valid_request(tmp_path), expected_checksum_sha256="a" * 64)

    result = execute_ipcc_source_download(
        request,
        lambda _: IPCCSourceDownloadTransportResponse(content=b"unexpected"),
    )

    assert result.status is IPCCSourceDownloadExecutionStatus.FAILED
    assert result.artifact is None
    assert _issue_codes(result.issues) == (
        "IPCC_SOURCE_DOWNLOAD_CHECKSUM_MISMATCH",
    )
    assert not (tmp_path / request.target_relative_path).exists()


def test_transport_errors_and_empty_content_are_failed_results(
    tmp_path: Path,
) -> None:
    failed = execute_ipcc_source_download(
        _valid_request(tmp_path),
        lambda _: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    empty = execute_ipcc_source_download(
        _valid_request(tmp_path / "other"),
        lambda _: IPCCSourceDownloadTransportResponse(content=b""),
    )

    assert failed.status is IPCCSourceDownloadExecutionStatus.FAILED
    assert _issue_codes(failed.issues) == ("IPCC_SOURCE_DOWNLOAD_TRANSPORT_FAILED",)
    assert empty.status is IPCCSourceDownloadExecutionStatus.FAILED
    assert _issue_codes(empty.issues) == (
        "IPCC_SOURCE_DOWNLOAD_RESPONSE_EMPTY_CONTENT",
    )


def test_transport_response_validation_fails_closed(tmp_path: Path) -> None:
    missing_response = execute_ipcc_source_download(
        _valid_request(tmp_path / "missing"),
        lambda _: None,  # type: ignore[return-value]
    )
    missing_content_response = execute_ipcc_source_download(
        _valid_request(tmp_path / "missing-content"),
        lambda _: IPCCSourceDownloadTransportResponse(
            content=None,  # type: ignore[arg-type]
        ),
    )
    blank_metadata_response = execute_ipcc_source_download(
        _valid_request(tmp_path / "blank-metadata"),
        lambda _: IPCCSourceDownloadTransportResponse(
            content=b"content",
            content_type=" ",
            final_uri=" ",
        ),
    )

    assert missing_response.status is IPCCSourceDownloadExecutionStatus.FAILED
    assert _issue_codes(missing_response.issues) == (
        "IPCC_SOURCE_DOWNLOAD_RESPONSE_MISSING",
    )
    assert (
        missing_content_response.status is IPCCSourceDownloadExecutionStatus.FAILED
    )
    assert _issue_codes(missing_content_response.issues) == (
        "IPCC_SOURCE_DOWNLOAD_RESPONSE_MISSING_CONTENT",
    )
    assert blank_metadata_response.status is IPCCSourceDownloadExecutionStatus.FAILED
    assert _issue_codes(blank_metadata_response.issues) == (
        "IPCC_SOURCE_DOWNLOAD_RESPONSE_BLANK_CONTENT_TYPE",
        "IPCC_SOURCE_DOWNLOAD_RESPONSE_BLANK_FINAL_URI",
    )


def test_download_execution_dataclasses_are_immutable(tmp_path: Path) -> None:
    request = _valid_request(tmp_path)
    result = execute_ipcc_source_download(
        request,
        lambda _: IPCCSourceDownloadTransportResponse(content=b"content"),
    )

    with pytest.raises(FrozenInstanceError):
        request.source_key = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.status = IPCCSourceDownloadExecutionStatus.FAILED  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.artifact.local_path = "changed"  # type: ignore[union-attr,misc]


def test_validation_result_issue_shape_is_structured(tmp_path: Path) -> None:
    request = replace(_valid_request(tmp_path), candidate_title="")

    issue = validate_ipcc_source_download_execution_request(request).issues[0]

    assert isinstance(issue, IPCCSourceDownloadExecutionIssue)
    assert issue.code == "IPCC_SOURCE_DOWNLOAD_MISSING_CANDIDATE_TITLE"
    assert issue.field_name == "candidate_title"
    assert issue.severity == "error"
    assert issue.message == "candidate_title must be a non-empty string."
    assert IPCCSourceDownloadExecutionValidationResult().is_valid is True
    assert (
        IPCCSourceDownloadExecutionValidationResult(issues=(issue,)).is_valid
        is False
    )


def test_result_validation_rejects_side_effect_flags(tmp_path: Path) -> None:
    result = replace(
        execute_ipcc_source_download(
            _valid_request(tmp_path),
            lambda _: IPCCSourceDownloadTransportResponse(content=b"content"),
        ),
        no_database_writes=False,
        no_sql=False,
    )

    validation = validate_ipcc_source_download_execution_result(result)

    assert validation.is_valid is False
    assert _issue_codes(validation.issues) == (
        "IPCC_SOURCE_DOWNLOAD_RESULT_SIDE_EFFECT_FLAG_ENABLED",
        "IPCC_SOURCE_DOWNLOAD_RESULT_SIDE_EFFECT_FLAG_ENABLED",
    )
    assert tuple(issue.field_name for issue in validation.issues) == (
        "no_database_writes",
        "no_sql",
    )


def test_result_validation_rejects_invalid_status(tmp_path: Path) -> None:
    result = IPCCSourceDownloadExecutionResult(
        status="unknown",  # type: ignore[arg-type]
        request=_valid_request(tmp_path),
        issues=(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_TEST_ISSUE",
                message="test issue.",
                field_name="status",
            ),
        ),
    )

    validation = validate_ipcc_source_download_execution_result(result)

    assert validation.is_valid is False
    assert "IPCC_SOURCE_DOWNLOAD_RESULT_INVALID_STATUS" in _issue_codes(
        validation.issues
    )


def test_download_execution_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = (
        "carbonfactor_parser.source_acquisition."
        "ipcc_source_download_execution_boundary"
    )
    cleared_modules = _clear_relevant_modules()

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("IPCC download execution import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("IPCC download execution import read environment")

    def guard_urlopen(*args: object, **kwargs: object) -> object:
        raise AssertionError("IPCC download execution import opened network")

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

    assert hasattr(module, "execute_ipcc_source_download")
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


def test_ipcc_download_execution_boundary_exports_through_contract_api(
    tmp_path: Path,
) -> None:
    from carbonfactor_parser.source_acquisition import contract_api

    request = contract_api.create_ipcc_source_download_execution_request(
        _downloadable_candidate(),
        target_root=str(tmp_path),
        target_relative_path="ipcc/efdb.xlsx",
        allow_download_execution=True,
        allow_file_write=True,
    )

    result = contract_api.execute_ipcc_source_download(
        request,
        lambda _: contract_api.IPCCSourceDownloadTransportResponse(content=b"content"),
    )

    assert result.status is contract_api.IPCCSourceDownloadExecutionStatus.DOWNLOADED
    assert result.artifact is not None
    assert contract_api.validate_ipcc_source_download_execution_result(result).is_valid


def _downloadable_candidate():
    return replace(
        create_ipcc_source_discovery_result().candidates[0],
        reference_uri="mock://ipcc_efdb/efdb.xlsx",
        artifact_kind="xlsx",
        content_type=IPCC_XLSX_CONTENT_TYPE,
        extension=".xlsx",
        version_label="py053_mock_download",
        download_allowed=True,
    )


def _valid_request(tmp_path: Path) -> IPCCSourceDownloadExecutionRequest:
    return create_ipcc_source_download_execution_request(
        _downloadable_candidate(),
        target_root=str(tmp_path),
        target_relative_path="ipcc/efdb.xlsx",
        allow_download_execution=True,
        allow_file_write=True,
    )


def _fixture_request(
    tmp_path: Path,
    fixture: dict[str, object],
) -> IPCCSourceDownloadExecutionRequest:
    candidate = replace(
        _downloadable_candidate(),
        candidate_id=str(fixture["candidate_id"]),
        title=str(fixture["candidate_title"]),
        reference_uri=str(fixture["source_reference_uri"]),
        artifact_kind=str(fixture["artifact_kind"]),
        content_type=str(fixture["content_type"]),
        extension=str(fixture["extension"]),
        document_year=int(fixture["document_year"]),
        reporting_year=int(fixture["reporting_year"]),
        version_label=str(fixture["version_label"]),
    )
    return create_ipcc_source_download_execution_request(
        candidate,
        target_root=str(tmp_path),
        target_relative_path=str(fixture["target_relative_path"]),
        allow_download_execution=True,
        allow_file_write=True,
    )


def _load_parity_fixture() -> dict[str, object]:
    with PARITY_FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def _unexpected_transport(
    source_reference_uri: str,
) -> IPCCSourceDownloadTransportResponse:
    raise AssertionError(f"unexpected transport call for {source_reference_uri}")


def _create_directory_symlink(target: Path, link: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"directory symlink unavailable: {error}")


def _issue_codes(
    issues: tuple[IPCCSourceDownloadExecutionIssue, ...],
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
