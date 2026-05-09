from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
import importlib
from pathlib import Path
import shutil
import sys
import urllib.request

import pytest

from carbonfactor_parser.source_acquisition.ghg_source_discovery_boundary import (
    create_ghg_source_discovery_result,
)
from carbonfactor_parser.source_acquisition.ghg_source_download_execution_boundary import (
    GHGSourceDownloadExecutionIssue,
    GHGSourceDownloadExecutionRequest,
    GHGSourceDownloadExecutionResult,
    GHGSourceDownloadExecutionStatus,
    GHGSourceDownloadExecutionValidationResult,
    GHGSourceDownloadTransportResponse,
    GHGSourceDownloadedArtifact,
    create_ghg_source_download_execution_request,
    execute_ghg_source_download,
    validate_ghg_source_download_execution_request,
    validate_ghg_source_download_execution_result,
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


def test_download_request_from_candidate_is_explicit_opt_in(tmp_path: Path) -> None:
    candidate = _downloadable_candidate()

    request = create_ghg_source_download_execution_request(
        candidate,
        target_root=str(tmp_path),
        target_relative_path="ghg/corporate-standard.pdf",
    )

    assert request == GHGSourceDownloadExecutionRequest(
        source_family="ghg_protocol",
        source_key="ghg_protocol",
        candidate_id="ghg_source_discovery_candidate_001_ghg_protocol",
        candidate_title="GHG Protocol",
        source_reference_uri="mock://ghg_protocol/corporate-standard.pdf",
        artifact_kind="pdf",
        target_root=str(tmp_path),
        target_relative_path="ghg/corporate-standard.pdf",
        candidate_download_allowed=True,
        allow_download_execution=False,
        allow_file_write=False,
        content_type="application/pdf",
        extension=".pdf",
        version_label="py046_mock_download",
    )
    validation = validate_ghg_source_download_execution_request(request)
    assert validation.is_valid is False
    assert _issue_codes(validation.issues) == (
        "GHG_SOURCE_DOWNLOAD_EXECUTION_NOT_ALLOWED",
        "GHG_SOURCE_DOWNLOAD_FILE_WRITE_NOT_ALLOWED",
    )


def test_default_discovery_candidate_is_not_downloadable(tmp_path: Path) -> None:
    candidate = create_ghg_source_discovery_result().candidates[0]
    request = create_ghg_source_download_execution_request(
        candidate,
        target_root=str(tmp_path),
        target_relative_path="ghg/source.discovery",
        allow_download_execution=True,
        allow_file_write=True,
    )

    result = execute_ghg_source_download(request, _unexpected_transport)

    assert result.status is GHGSourceDownloadExecutionStatus.BLOCKED
    assert result.artifact is None
    assert _issue_codes(result.issues) == (
        "GHG_SOURCE_DOWNLOAD_CANDIDATE_NOT_DOWNLOADABLE",
        "GHG_SOURCE_DOWNLOAD_DISCOVERY_REFERENCE_NOT_DOWNLOADABLE",
    )
    assert not (tmp_path / "ghg/source.discovery").exists()


def test_invalid_download_requests_fail_closed_before_transport(
    tmp_path: Path,
) -> None:
    request = replace(
        _valid_request(tmp_path),
        source_family="defra_desnz",
        source_key="defra_desnz",
        allow_parse=True,
        allow_database_writes=True,
        allow_scheduler=True,
    )

    result = execute_ghg_source_download(request, _unexpected_transport)

    assert result.status is GHGSourceDownloadExecutionStatus.BLOCKED
    assert result.downloaded is False
    assert result.artifact is None
    assert result.no_parse is True
    assert result.no_database_writes is True
    assert result.no_sql is True
    assert result.no_scheduler is True
    assert _issue_codes(result.issues) == (
        "GHG_SOURCE_DOWNLOAD_SOURCE_FAMILY_MISMATCH",
        "GHG_SOURCE_DOWNLOAD_SOURCE_KEY_MISMATCH",
        "GHG_SOURCE_DOWNLOAD_PARSE_NOT_ALLOWED",
        "GHG_SOURCE_DOWNLOAD_DATABASE_WRITES_NOT_ALLOWED",
        "GHG_SOURCE_DOWNLOAD_SCHEDULER_NOT_ALLOWED",
    )


@pytest.mark.parametrize(
    ("field_name", "value", "expected_code"),
    (
        (
            "source_reference_uri",
            "https://example.invalid/ghg.pdf",
            "GHG_SOURCE_DOWNLOAD_NETWORK_NOT_ALLOWED",
        ),
        (
            "source_reference_uri",
            "http" + "://example.invalid/ghg.pdf",
            "GHG_SOURCE_DOWNLOAD_INSECURE_HTTP_NOT_ALLOWED",
        ),
        (
            "source_reference_uri",
            "file:///tmp/ghg.pdf",
            "GHG_SOURCE_DOWNLOAD_UNSAFE_SOURCE_REFERENCE_URI",
        ),
        (
            "source_reference_uri",
            "s3://bucket/ghg.pdf",
            "GHG_SOURCE_DOWNLOAD_UNSAFE_SOURCE_REFERENCE_URI",
        ),
        (
            "target_root",
            "relative/root",
            "GHG_SOURCE_DOWNLOAD_TARGET_ROOT_NOT_ABSOLUTE",
        ),
        (
            "target_relative_path",
            "../outside.pdf",
            "GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_UNSAFE",
        ),
        (
            "target_relative_path",
            "/absolute.pdf",
            "GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_ABSOLUTE",
        ),
        (
            "target_relative_path",
            "download://ghg/source.pdf",
            "GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_URI",
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

    validation = validate_ghg_source_download_execution_request(request)

    assert validation.is_valid is False
    assert expected_code in _issue_codes(validation.issues)


def test_successful_download_is_explicit_and_uses_injected_transport(
    tmp_path: Path,
) -> None:
    payload = b"deterministic ghg source bytes"
    calls: list[str] = []

    def transport(source_reference_uri: str) -> GHGSourceDownloadTransportResponse:
        calls.append(source_reference_uri)
        return GHGSourceDownloadTransportResponse(
            content=payload,
            content_type="application/pdf",
            final_uri="mock://ghg_protocol/final.pdf",
        )

    request = _valid_request(tmp_path)
    result = execute_ghg_source_download(request, transport)

    target_path = tmp_path / "ghg/corporate-standard.pdf"
    checksum = sha256(payload).hexdigest()
    assert calls == ["mock://ghg_protocol/corporate-standard.pdf"]
    assert target_path.read_bytes() == payload
    assert result == GHGSourceDownloadExecutionResult(
        status=GHGSourceDownloadExecutionStatus.DOWNLOADED,
        request=request,
        artifact=GHGSourceDownloadedArtifact(
            source_family="ghg_protocol",
            source_key="ghg_protocol",
            candidate_id="ghg_source_discovery_candidate_001_ghg_protocol",
            artifact_id=(
                "ghg_source_download_artifact_"
                "ghg_source_discovery_candidate_001_ghg_protocol"
            ),
            artifact_kind="pdf",
            source_reference_uri="mock://ghg_protocol/corporate-standard.pdf",
            local_path=str(target_path),
            original_filename="corporate-standard.pdf",
            checksum_sha256=checksum,
            size_bytes=len(payload),
            content_type="application/pdf",
            extension=".pdf",
            final_uri="mock://ghg_protocol/final.pdf",
            version_label="py046_mock_download",
        ),
    )
    assert result.downloaded is True
    assert validate_ghg_source_download_execution_result(result).is_valid is True


def test_target_exists_blocks_before_transport_by_default(tmp_path: Path) -> None:
    request = _valid_request(tmp_path)
    target_path = tmp_path / request.target_relative_path
    target_path.parent.mkdir(parents=True)
    target_path.write_bytes(b"existing")

    result = execute_ghg_source_download(request, _unexpected_transport)

    assert result.status is GHGSourceDownloadExecutionStatus.BLOCKED
    assert _issue_codes(result.issues) == ("GHG_SOURCE_DOWNLOAD_TARGET_EXISTS",)
    assert target_path.read_bytes() == b"existing"


def test_symlinked_parent_path_cannot_escape_target_root(tmp_path: Path) -> None:
    target_root = tmp_path / "target-root"
    outside = tmp_path / "outside"
    target_root.mkdir()
    outside.mkdir()
    _create_directory_symlink(outside, target_root / "link")
    request = replace(
        _valid_request(target_root),
        target_relative_path="link/escape.pdf",
    )

    result = execute_ghg_source_download(
        request,
        lambda _: GHGSourceDownloadTransportResponse(content=b"escape"),
    )

    assert result.status is GHGSourceDownloadExecutionStatus.BLOCKED
    assert result.downloaded is False
    assert result.artifact is None
    assert _issue_codes(result.issues) == (
        "GHG_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE",
    )
    assert not (outside / "escape.pdf").exists()
    assert not (target_root / "link/escape.pdf").exists()


def test_existing_final_target_symlink_is_rejected(tmp_path: Path) -> None:
    target_root = tmp_path / "target-root"
    outside = tmp_path / "outside"
    target_parent = target_root / "ghg"
    target_parent.mkdir(parents=True)
    outside.mkdir()
    (target_parent / "escape.pdf").symlink_to(outside / "escape.pdf")
    request = replace(
        _valid_request(target_root),
        target_relative_path="ghg/escape.pdf",
        allow_overwrite=True,
    )

    result = execute_ghg_source_download(
        request,
        lambda _: GHGSourceDownloadTransportResponse(content=b"escape"),
    )

    assert result.status is GHGSourceDownloadExecutionStatus.BLOCKED
    assert result.downloaded is False
    assert result.artifact is None
    assert _issue_codes(result.issues) == (
        "GHG_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE",
    )
    assert not (outside / "escape.pdf").exists()
    assert (target_parent / "escape.pdf").is_symlink()


def test_parent_symlink_swap_during_transport_cannot_escape_target_root(
    tmp_path: Path,
) -> None:
    target_root = tmp_path / "target-root"
    outside = tmp_path / "outside"
    target_parent = target_root / "ghg"
    target_parent.mkdir(parents=True)
    outside.mkdir()
    request = replace(
        _valid_request(target_root),
        target_relative_path="ghg/escape.pdf",
    )

    def swapping_transport(_: str) -> GHGSourceDownloadTransportResponse:
        shutil.rmtree(target_parent)
        _create_directory_symlink(outside, target_parent)
        return GHGSourceDownloadTransportResponse(content=b"escape")

    result = execute_ghg_source_download(request, swapping_transport)

    assert result.status is not GHGSourceDownloadExecutionStatus.DOWNLOADED
    assert result.downloaded is False
    assert result.artifact is None
    assert not (outside / "escape.pdf").exists()
    assert target_parent.is_symlink()


def test_checksum_mismatch_fails_without_writing_file(tmp_path: Path) -> None:
    request = replace(_valid_request(tmp_path), expected_checksum_sha256="a" * 64)

    result = execute_ghg_source_download(
        request,
        lambda _: GHGSourceDownloadTransportResponse(content=b"unexpected"),
    )

    assert result.status is GHGSourceDownloadExecutionStatus.FAILED
    assert result.artifact is None
    assert _issue_codes(result.issues) == (
        "GHG_SOURCE_DOWNLOAD_CHECKSUM_MISMATCH",
    )
    assert not (tmp_path / request.target_relative_path).exists()


def test_transport_errors_and_empty_content_are_failed_results(
    tmp_path: Path,
) -> None:
    failed = execute_ghg_source_download(
        _valid_request(tmp_path),
        lambda _: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    empty = execute_ghg_source_download(
        _valid_request(tmp_path / "other"),
        lambda _: GHGSourceDownloadTransportResponse(content=b""),
    )

    assert failed.status is GHGSourceDownloadExecutionStatus.FAILED
    assert _issue_codes(failed.issues) == ("GHG_SOURCE_DOWNLOAD_TRANSPORT_FAILED",)
    assert empty.status is GHGSourceDownloadExecutionStatus.FAILED
    assert _issue_codes(empty.issues) == (
        "GHG_SOURCE_DOWNLOAD_RESPONSE_EMPTY_CONTENT",
    )


def test_download_execution_dataclasses_are_immutable(tmp_path: Path) -> None:
    request = _valid_request(tmp_path)
    result = execute_ghg_source_download(
        request,
        lambda _: GHGSourceDownloadTransportResponse(content=b"content"),
    )

    with pytest.raises(FrozenInstanceError):
        request.source_key = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.status = GHGSourceDownloadExecutionStatus.FAILED  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.artifact.local_path = "changed"  # type: ignore[union-attr,misc]


def test_validation_result_issue_shape_is_structured(tmp_path: Path) -> None:
    request = replace(_valid_request(tmp_path), candidate_title="")

    issue = validate_ghg_source_download_execution_request(request).issues[0]

    assert isinstance(issue, GHGSourceDownloadExecutionIssue)
    assert issue.code == "GHG_SOURCE_DOWNLOAD_MISSING_CANDIDATE_TITLE"
    assert issue.field_name == "candidate_title"
    assert issue.severity == "error"
    assert issue.message == "candidate_title must be a non-empty string."
    assert GHGSourceDownloadExecutionValidationResult().is_valid is True
    assert GHGSourceDownloadExecutionValidationResult(issues=(issue,)).is_valid is False


def test_result_validation_rejects_side_effect_flags(tmp_path: Path) -> None:
    result = replace(
        execute_ghg_source_download(
            _valid_request(tmp_path),
            lambda _: GHGSourceDownloadTransportResponse(content=b"content"),
        ),
        no_database_writes=False,
        no_sql=False,
    )

    validation = validate_ghg_source_download_execution_result(result)

    assert validation.is_valid is False
    assert _issue_codes(validation.issues) == (
        "GHG_SOURCE_DOWNLOAD_RESULT_SIDE_EFFECT_FLAG_ENABLED",
        "GHG_SOURCE_DOWNLOAD_RESULT_SIDE_EFFECT_FLAG_ENABLED",
    )
    assert tuple(issue.field_name for issue in validation.issues) == (
        "no_database_writes",
        "no_sql",
    )


def test_download_execution_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = (
        "carbonfactor_parser.source_acquisition."
        "ghg_source_download_execution_boundary"
    )
    cleared_modules = _clear_relevant_modules()

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("GHG download execution import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("GHG download execution import read environment")

    def guard_urlopen(*args: object, **kwargs: object) -> object:
        raise AssertionError("GHG download execution import opened network")

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

    assert hasattr(module, "execute_ghg_source_download")
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


def test_ghg_download_execution_boundary_exports_through_contract_api(
    tmp_path: Path,
) -> None:
    from carbonfactor_parser.source_acquisition import contract_api

    request = contract_api.create_ghg_source_download_execution_request(
        _downloadable_candidate(),
        target_root=str(tmp_path),
        target_relative_path="ghg/corporate-standard.pdf",
        allow_download_execution=True,
        allow_file_write=True,
    )

    result = contract_api.execute_ghg_source_download(
        request,
        lambda _: contract_api.GHGSourceDownloadTransportResponse(content=b"content"),
    )

    assert result.status is contract_api.GHGSourceDownloadExecutionStatus.DOWNLOADED
    assert result.artifact is not None
    assert contract_api.validate_ghg_source_download_execution_result(result).is_valid


def _downloadable_candidate():
    return replace(
        create_ghg_source_discovery_result().candidates[0],
        reference_uri="mock://ghg_protocol/corporate-standard.pdf",
        artifact_kind="pdf",
        content_type="application/pdf",
        extension=".pdf",
        version_label="py046_mock_download",
        download_allowed=True,
    )


def _valid_request(tmp_path: Path) -> GHGSourceDownloadExecutionRequest:
    return create_ghg_source_download_execution_request(
        _downloadable_candidate(),
        target_root=str(tmp_path),
        target_relative_path="ghg/corporate-standard.pdf",
        allow_download_execution=True,
        allow_file_write=True,
    )


def _unexpected_transport(
    source_reference_uri: str,
) -> GHGSourceDownloadTransportResponse:
    raise AssertionError(f"unexpected transport call for {source_reference_uri}")


def _create_directory_symlink(target: Path, link: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"directory symlink unavailable: {error}")


def _issue_codes(
    issues: tuple[GHGSourceDownloadExecutionIssue, ...],
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
