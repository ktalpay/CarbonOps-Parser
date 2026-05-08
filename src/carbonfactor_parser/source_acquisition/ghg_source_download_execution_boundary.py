"""Explicit GHG-only source download execution boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import errno
from hashlib import sha256
import os
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

from carbonfactor_parser.source_acquisition.ghg_source_discovery_boundary import (
    GHG_SOURCE_FAMILY,
    GHG_SOURCE_KEY,
    GHGSourceDocumentCandidate,
)


class GHGSourceDownloadExecutionStatus(str, Enum):
    """Status values for GHG source download execution."""

    BLOCKED = "blocked"
    DOWNLOADED = "downloaded"
    FAILED = "failed"


@dataclass(frozen=True)
class GHGSourceDownloadExecutionRequest:
    """Explicit opt-in request to download one GHG source candidate."""

    source_family: str
    source_key: str
    candidate_id: str
    candidate_title: str
    source_reference_uri: str
    artifact_kind: str
    target_root: str
    target_relative_path: str
    candidate_download_allowed: bool = False
    allow_download_execution: bool = False
    allow_file_write: bool = False
    allow_network: bool = False
    allow_overwrite: bool = False
    allow_parse: bool = False
    allow_database_writes: bool = False
    allow_scheduler: bool = False
    content_type: str | None = None
    extension: str | None = None
    expected_checksum_sha256: str | None = None
    document_year: int | None = None
    reporting_year: int | None = None
    version_label: str | None = None


@dataclass(frozen=True)
class GHGSourceDownloadTransportResponse:
    """Downloaded payload returned by a caller-provided transport."""

    content: bytes
    content_type: str | None = None
    final_uri: str | None = None


class GHGSourceDownloadTransport(Protocol):
    """Caller-provided transport for explicit GHG source download execution."""

    def __call__(
        self,
        source_reference_uri: str,
    ) -> GHGSourceDownloadTransportResponse:
        """Return downloaded content for the provided source reference."""


@dataclass(frozen=True)
class GHGSourceDownloadedArtifact:
    """Local artifact produced by explicit GHG source download execution."""

    source_family: str
    source_key: str
    candidate_id: str
    artifact_id: str
    artifact_kind: str
    source_reference_uri: str
    local_path: str
    original_filename: str
    checksum_sha256: str
    size_bytes: int
    content_type: str | None = None
    extension: str | None = None
    final_uri: str | None = None
    document_year: int | None = None
    reporting_year: int | None = None
    version_label: str | None = None


@dataclass(frozen=True)
class GHGSourceDownloadExecutionIssue:
    """Validation or execution issue for GHG source downloads."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class GHGSourceDownloadExecutionValidationResult:
    """Structural validation result for GHG source download requests."""

    issues: tuple[GHGSourceDownloadExecutionIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


@dataclass(frozen=True)
class GHGSourceDownloadExecutionResult:
    """Result of explicit GHG source download execution."""

    status: GHGSourceDownloadExecutionStatus
    request: GHGSourceDownloadExecutionRequest
    artifact: GHGSourceDownloadedArtifact | None = None
    issues: tuple[GHGSourceDownloadExecutionIssue, ...] = ()
    no_parse: bool = True
    no_database_writes: bool = True
    no_sql: bool = True
    no_scheduler: bool = True

    @property
    def downloaded(self) -> bool:
        return self.status is GHGSourceDownloadExecutionStatus.DOWNLOADED


@dataclass(frozen=True)
class _SafeTargetPath:
    target_path: Path
    resolved_root: Path
    resolved_parent: Path
    resolved_target_path: Path


def create_ghg_source_download_execution_request(
    candidate: GHGSourceDocumentCandidate,
    *,
    target_root: str,
    target_relative_path: str,
    allow_download_execution: bool = False,
    allow_file_write: bool = False,
    allow_network: bool = False,
    allow_overwrite: bool = False,
) -> GHGSourceDownloadExecutionRequest:
    """Create an explicit GHG download request from candidate metadata."""

    return GHGSourceDownloadExecutionRequest(
        source_family=candidate.source_family,
        source_key=candidate.source_key,
        candidate_id=candidate.candidate_id,
        candidate_title=candidate.title,
        source_reference_uri=candidate.reference_uri,
        artifact_kind=candidate.artifact_kind,
        target_root=target_root,
        target_relative_path=target_relative_path,
        candidate_download_allowed=candidate.download_allowed,
        allow_download_execution=allow_download_execution,
        allow_file_write=allow_file_write,
        allow_network=allow_network,
        allow_overwrite=allow_overwrite,
        content_type=candidate.content_type,
        extension=candidate.extension,
        expected_checksum_sha256=candidate.checksum_sha256,
        document_year=candidate.document_year,
        reporting_year=candidate.reporting_year,
        version_label=candidate.version_label,
    )


def validate_ghg_source_download_execution_request(
    request: GHGSourceDownloadExecutionRequest,
) -> GHGSourceDownloadExecutionValidationResult:
    """Validate a GHG source download request without executing it."""

    issues: list[GHGSourceDownloadExecutionIssue] = []

    _validate_required_text(
        request.source_family,
        "source_family",
        "GHG_SOURCE_DOWNLOAD_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.source_key,
        "source_key",
        "GHG_SOURCE_DOWNLOAD_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.candidate_id,
        "candidate_id",
        "GHG_SOURCE_DOWNLOAD_MISSING_CANDIDATE_ID",
        "candidate_id must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.candidate_title,
        "candidate_title",
        "GHG_SOURCE_DOWNLOAD_MISSING_CANDIDATE_TITLE",
        "candidate_title must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.source_reference_uri,
        "source_reference_uri",
        "GHG_SOURCE_DOWNLOAD_MISSING_SOURCE_REFERENCE_URI",
        "source_reference_uri must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.artifact_kind,
        "artifact_kind",
        "GHG_SOURCE_DOWNLOAD_MISSING_ARTIFACT_KIND",
        "artifact_kind must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.target_root,
        "target_root",
        "GHG_SOURCE_DOWNLOAD_MISSING_TARGET_ROOT",
        "target_root must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.target_relative_path,
        "target_relative_path",
        "GHG_SOURCE_DOWNLOAD_MISSING_TARGET_RELATIVE_PATH",
        "target_relative_path must be a non-empty string.",
        issues,
    )
    _validate_optional_text(
        request.content_type,
        "content_type",
        "GHG_SOURCE_DOWNLOAD_BLANK_CONTENT_TYPE",
        "content_type must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        request.extension,
        "extension",
        "GHG_SOURCE_DOWNLOAD_BLANK_EXTENSION",
        "extension must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        request.expected_checksum_sha256,
        "expected_checksum_sha256",
        "GHG_SOURCE_DOWNLOAD_BLANK_EXPECTED_CHECKSUM_SHA256",
        "expected_checksum_sha256 must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        request.version_label,
        "version_label",
        "GHG_SOURCE_DOWNLOAD_BLANK_VERSION_LABEL",
        "version_label must be non-empty when provided.",
        issues,
    )
    _validate_optional_positive_int(
        request.document_year,
        "document_year",
        "GHG_SOURCE_DOWNLOAD_INVALID_DOCUMENT_YEAR",
        "document_year must be a positive integer when provided.",
        issues,
    )
    _validate_optional_positive_int(
        request.reporting_year,
        "reporting_year",
        "GHG_SOURCE_DOWNLOAD_INVALID_REPORTING_YEAR",
        "reporting_year must be a positive integer when provided.",
        issues,
    )

    if request.source_family != GHG_SOURCE_FAMILY:
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_SOURCE_FAMILY_MISMATCH",
                message="source_family must be ghg_protocol.",
                field_name="source_family",
            )
        )
    if request.source_key != GHG_SOURCE_KEY:
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_SOURCE_KEY_MISMATCH",
                message="source_key must be ghg_protocol.",
                field_name="source_key",
            )
        )
    _validate_true(
        request.candidate_download_allowed,
        "candidate_download_allowed",
        "GHG_SOURCE_DOWNLOAD_CANDIDATE_NOT_DOWNLOADABLE",
        "candidate metadata must explicitly allow download execution.",
        issues,
    )
    _validate_true(
        request.allow_download_execution,
        "allow_download_execution",
        "GHG_SOURCE_DOWNLOAD_EXECUTION_NOT_ALLOWED",
        "allow_download_execution must be True.",
        issues,
    )
    _validate_true(
        request.allow_file_write,
        "allow_file_write",
        "GHG_SOURCE_DOWNLOAD_FILE_WRITE_NOT_ALLOWED",
        "allow_file_write must be True.",
        issues,
    )
    _validate_false(
        request.allow_parse,
        "allow_parse",
        "GHG_SOURCE_DOWNLOAD_PARSE_NOT_ALLOWED",
        "allow_parse must be False for this boundary.",
        issues,
    )
    _validate_false(
        request.allow_database_writes,
        "allow_database_writes",
        "GHG_SOURCE_DOWNLOAD_DATABASE_WRITES_NOT_ALLOWED",
        "allow_database_writes must be False for this boundary.",
        issues,
    )
    _validate_false(
        request.allow_scheduler,
        "allow_scheduler",
        "GHG_SOURCE_DOWNLOAD_SCHEDULER_NOT_ALLOWED",
        "allow_scheduler must be False for this boundary.",
        issues,
    )

    _validate_source_reference_uri(request, issues)
    _validate_target_paths(request, issues)

    return GHGSourceDownloadExecutionValidationResult(issues=tuple(issues))


def execute_ghg_source_download(
    request: GHGSourceDownloadExecutionRequest,
    transport: GHGSourceDownloadTransport,
) -> GHGSourceDownloadExecutionResult:
    """Execute one explicit GHG source download using a provided transport."""

    validation = validate_ghg_source_download_execution_request(request)
    if not validation.is_valid:
        return GHGSourceDownloadExecutionResult(
            status=GHGSourceDownloadExecutionStatus.BLOCKED,
            request=request,
            issues=validation.issues,
        )

    safe_target, target_issues = _prepare_safe_target_path(request)
    if target_issues:
        return GHGSourceDownloadExecutionResult(
            status=GHGSourceDownloadExecutionStatus.BLOCKED,
            request=request,
            issues=target_issues,
        )
    if safe_target is None:
        return GHGSourceDownloadExecutionResult(
            status=GHGSourceDownloadExecutionStatus.BLOCKED,
            request=request,
            issues=(
                GHGSourceDownloadExecutionIssue(
                    code="GHG_SOURCE_DOWNLOAD_TARGET_PATH_UNRESOLVED",
                    message="target path could not be resolved safely.",
                    field_name="target_relative_path",
                ),
            ),
        )

    try:
        response = transport(request.source_reference_uri)
    except Exception as error:  # noqa: BLE001
        return GHGSourceDownloadExecutionResult(
            status=GHGSourceDownloadExecutionStatus.FAILED,
            request=request,
            issues=(
                GHGSourceDownloadExecutionIssue(
                    code="GHG_SOURCE_DOWNLOAD_TRANSPORT_FAILED",
                    message=f"transport failed: {error}",
                    field_name="source_reference_uri",
                ),
            ),
        )

    response_validation = _validate_transport_response(response)
    if not response_validation.is_valid:
        return GHGSourceDownloadExecutionResult(
            status=GHGSourceDownloadExecutionStatus.FAILED,
            request=request,
            issues=response_validation.issues,
        )

    content = bytes(response.content)
    checksum_sha256 = sha256(content).hexdigest()
    if (
        request.expected_checksum_sha256 is not None
        and checksum_sha256.lower() != request.expected_checksum_sha256.lower()
    ):
        return GHGSourceDownloadExecutionResult(
            status=GHGSourceDownloadExecutionStatus.FAILED,
            request=request,
            issues=(
                GHGSourceDownloadExecutionIssue(
                    code="GHG_SOURCE_DOWNLOAD_CHECKSUM_MISMATCH",
                    message="downloaded content checksum did not match expected value.",
                    field_name="expected_checksum_sha256",
                ),
            ),
        )

    try:
        _write_content_to_safe_target(
            safe_target,
            content,
            allow_overwrite=request.allow_overwrite,
        )
    except Exception as error:  # noqa: BLE001
        issue_code = "GHG_SOURCE_DOWNLOAD_WRITE_FAILED"
        if isinstance(error, FileExistsError):
            issue_code = "GHG_SOURCE_DOWNLOAD_TARGET_EXISTS"
        elif isinstance(error, OSError) and error.errno == errno.ELOOP:
            issue_code = "GHG_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE"
        return GHGSourceDownloadExecutionResult(
            status=GHGSourceDownloadExecutionStatus.FAILED,
            request=request,
            issues=(
                GHGSourceDownloadExecutionIssue(
                    code=issue_code,
                    message=f"target write failed: {error}",
                    field_name="target_relative_path",
                ),
            ),
        )

    artifact = GHGSourceDownloadedArtifact(
        source_family=request.source_family,
        source_key=request.source_key,
        candidate_id=request.candidate_id,
        artifact_id=f"ghg_source_download_artifact_{request.candidate_id}",
        artifact_kind=request.artifact_kind,
        source_reference_uri=request.source_reference_uri,
        local_path=str(safe_target.resolved_target_path),
        original_filename=safe_target.resolved_target_path.name,
        checksum_sha256=checksum_sha256,
        size_bytes=len(content),
        content_type=response.content_type or request.content_type,
        extension=request.extension,
        final_uri=response.final_uri,
        document_year=request.document_year,
        reporting_year=request.reporting_year,
        version_label=request.version_label,
    )
    return GHGSourceDownloadExecutionResult(
        status=GHGSourceDownloadExecutionStatus.DOWNLOADED,
        request=request,
        artifact=artifact,
    )


def validate_ghg_source_download_execution_result(
    result: GHGSourceDownloadExecutionResult,
) -> GHGSourceDownloadExecutionValidationResult:
    """Validate a GHG source download execution result."""

    issues: list[GHGSourceDownloadExecutionIssue] = []
    issues.extend(validate_ghg_source_download_execution_request(result.request).issues)

    for field_name, value in (
        ("no_parse", result.no_parse),
        ("no_database_writes", result.no_database_writes),
        ("no_sql", result.no_sql),
        ("no_scheduler", result.no_scheduler),
    ):
        if value is not True:
            issues.append(
                GHGSourceDownloadExecutionIssue(
                    code="GHG_SOURCE_DOWNLOAD_RESULT_SIDE_EFFECT_FLAG_ENABLED",
                    message=f"{field_name} must remain True.",
                    field_name=field_name,
                )
            )

    if result.status is GHGSourceDownloadExecutionStatus.DOWNLOADED:
        if result.artifact is None:
            issues.append(
                GHGSourceDownloadExecutionIssue(
                    code="GHG_SOURCE_DOWNLOAD_RESULT_MISSING_ARTIFACT",
                    message="downloaded results require artifact metadata.",
                    field_name="artifact",
                )
            )
    elif result.artifact is not None:
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_RESULT_UNEXPECTED_ARTIFACT",
                message="non-downloaded results must not include artifact metadata.",
                field_name="artifact",
            )
        )

    if (
        result.status is not GHGSourceDownloadExecutionStatus.DOWNLOADED
        and not result.issues
    ):
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_RESULT_MISSING_ISSUES",
                message="blocked or failed results require issue metadata.",
                field_name="issues",
            )
        )

    if result.artifact is not None:
        issues.extend(_validate_artifact(result.artifact).issues)

    return GHGSourceDownloadExecutionValidationResult(issues=tuple(issues))


def _validate_source_reference_uri(
    request: GHGSourceDownloadExecutionRequest,
    issues: list[GHGSourceDownloadExecutionIssue],
) -> None:
    parsed = urlparse(request.source_reference_uri)
    scheme = parsed.scheme
    if not scheme:
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_SOURCE_REFERENCE_URI_MISSING_SCHEME",
                message="source_reference_uri must include a URI scheme.",
                field_name="source_reference_uri",
            )
        )
        return
    if scheme == "discovery":
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_DISCOVERY_REFERENCE_NOT_DOWNLOADABLE",
                message="discovery references are not direct download references.",
                field_name="source_reference_uri",
            )
        )
        return
    if scheme == "http":
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_INSECURE_HTTP_NOT_ALLOWED",
                message="source_reference_uri must not use insecure HTTP.",
                field_name="source_reference_uri",
            )
        )
        return
    if scheme == "https" and not request.allow_network:
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_NETWORK_NOT_ALLOWED",
                message="allow_network must be True for HTTPS references.",
                field_name="allow_network",
            )
        )
    if scheme not in {"https", "memory", "mock"}:
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_UNSAFE_SOURCE_REFERENCE_URI",
                message="source_reference_uri scheme is not allowed.",
                field_name="source_reference_uri",
            )
        )


def _validate_target_paths(
    request: GHGSourceDownloadExecutionRequest,
    issues: list[GHGSourceDownloadExecutionIssue],
) -> None:
    target_root = Path(request.target_root)
    target_relative_path = Path(request.target_relative_path)

    if not target_root.is_absolute():
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_TARGET_ROOT_NOT_ABSOLUTE",
                message="target_root must be an absolute path.",
                field_name="target_root",
            )
        )
    if target_relative_path.is_absolute():
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_ABSOLUTE",
                message="target_relative_path must be relative.",
                field_name="target_relative_path",
            )
        )
    if "://" in request.target_relative_path:
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_URI",
                message="target_relative_path must not be a URI.",
                field_name="target_relative_path",
            )
        )
    if any(part in {"", ".", ".."} for part in target_relative_path.parts):
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_UNSAFE",
                message=(
                    "target_relative_path must not contain empty, current, or "
                    "parent segments."
                ),
                field_name="target_relative_path",
            )
        )


def _prepare_safe_target_path(
    request: GHGSourceDownloadExecutionRequest,
) -> tuple[_SafeTargetPath | None, tuple[GHGSourceDownloadExecutionIssue, ...]]:
    issues: list[GHGSourceDownloadExecutionIssue] = []
    target_root = Path(request.target_root)
    target_relative_path = Path(request.target_relative_path)

    try:
        target_root.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        return None, (
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_TARGET_ROOT_CREATE_FAILED",
                message=f"target_root could not be created: {error}",
                field_name="target_root",
            ),
        )

    if not target_root.is_dir():
        return None, (
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_TARGET_ROOT_NOT_DIRECTORY",
                message="target_root must resolve to a directory.",
                field_name="target_root",
            ),
        )

    try:
        resolved_root = target_root.resolve(strict=True)
    except OSError as error:
        return None, (
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_TARGET_ROOT_RESOLVE_FAILED",
                message=f"target_root could not be resolved: {error}",
                field_name="target_root",
            ),
        )

    current_path = target_root
    resolved_parent = resolved_root
    for part in target_relative_path.parts[:-1]:
        current_path = current_path / part
        if current_path.is_symlink():
            issues.append(
                GHGSourceDownloadExecutionIssue(
                    code="GHG_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE",
                    message="target parent path must not contain symlinks.",
                    field_name="target_relative_path",
                )
            )
            continue
        try:
            if current_path.exists():
                if not current_path.is_dir():
                    issues.append(
                        GHGSourceDownloadExecutionIssue(
                            code="GHG_SOURCE_DOWNLOAD_TARGET_PARENT_NOT_DIRECTORY",
                            message="target parent path must be a directory.",
                            field_name="target_relative_path",
                        )
                    )
                    continue
            else:
                current_path.mkdir()
        except OSError as error:
            issues.append(
                GHGSourceDownloadExecutionIssue(
                    code="GHG_SOURCE_DOWNLOAD_TARGET_PARENT_CREATE_FAILED",
                    message=f"target parent path could not be prepared: {error}",
                    field_name="target_relative_path",
                )
            )
            continue

        try:
            resolved_parent = current_path.resolve(strict=True)
        except OSError as error:
            issues.append(
                GHGSourceDownloadExecutionIssue(
                    code="GHG_SOURCE_DOWNLOAD_TARGET_PARENT_RESOLVE_FAILED",
                    message=f"target parent path could not be resolved: {error}",
                    field_name="target_relative_path",
                )
            )
            continue
        if not _is_relative_to(resolved_parent, resolved_root):
            issues.append(
                GHGSourceDownloadExecutionIssue(
                    code="GHG_SOURCE_DOWNLOAD_TARGET_CONTAINMENT_UNSAFE",
                    message="resolved target parent escapes target_root.",
                    field_name="target_relative_path",
                )
            )

    target_path = target_root / target_relative_path
    if target_path.is_symlink():
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE",
                message="target path must not be an existing symlink.",
                field_name="target_relative_path",
            )
        )
    elif target_path.exists():
        if target_path.is_dir():
            issues.append(
                GHGSourceDownloadExecutionIssue(
                    code="GHG_SOURCE_DOWNLOAD_TARGET_NOT_FILE",
                    message="target path must not be a directory.",
                    field_name="target_relative_path",
                )
            )
        elif not request.allow_overwrite:
            issues.append(
                GHGSourceDownloadExecutionIssue(
                    code="GHG_SOURCE_DOWNLOAD_TARGET_EXISTS",
                    message="target path already exists and overwrite is disabled.",
                    field_name="target_relative_path",
                )
            )

    resolved_target_path = resolved_parent / target_relative_path.name
    if not _is_relative_to(resolved_target_path, resolved_root):
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_TARGET_CONTAINMENT_UNSAFE",
                message="resolved target path escapes target_root.",
                field_name="target_relative_path",
            )
        )

    if issues:
        return None, tuple(issues)

    return (
        _SafeTargetPath(
            target_path=target_path,
            resolved_root=resolved_root,
            resolved_parent=resolved_parent,
            resolved_target_path=resolved_target_path,
        ),
        (),
    )


def _write_content_to_safe_target(
    safe_target: _SafeTargetPath,
    content: bytes,
    *,
    allow_overwrite: bool,
) -> None:
    flags = os.O_WRONLY | os.O_CREAT
    flags |= os.O_TRUNC if allow_overwrite else os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)

    directory_fd = os.open(safe_target.resolved_parent, directory_flags)
    try:
        file_fd = os.open(
            safe_target.resolved_target_path.name,
            flags,
            0o600,
            dir_fd=directory_fd,
        )
        try:
            target_file = os.fdopen(file_fd, "wb")
        except Exception:
            os.close(file_fd)
            raise
        with target_file:
            target_file.write(content)
    finally:
        os.close(directory_fd)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _validate_transport_response(
    response: GHGSourceDownloadTransportResponse,
) -> GHGSourceDownloadExecutionValidationResult:
    issues: list[GHGSourceDownloadExecutionIssue] = []
    content = getattr(response, "content", None)
    if not isinstance(content, bytes):
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_RESPONSE_CONTENT_NOT_BYTES",
                message="transport response content must be bytes.",
                field_name="transport.content",
            )
        )
    elif len(content) == 0:
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_RESPONSE_EMPTY_CONTENT",
                message="transport response content must not be empty.",
                field_name="transport.content",
            )
        )

    return GHGSourceDownloadExecutionValidationResult(issues=tuple(issues))


def _validate_artifact(
    artifact: GHGSourceDownloadedArtifact,
) -> GHGSourceDownloadExecutionValidationResult:
    issues: list[GHGSourceDownloadExecutionIssue] = []
    _validate_required_text(
        artifact.local_path,
        "artifact.local_path",
        "GHG_SOURCE_DOWNLOAD_ARTIFACT_MISSING_LOCAL_PATH",
        "artifact local_path must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        artifact.checksum_sha256,
        "artifact.checksum_sha256",
        "GHG_SOURCE_DOWNLOAD_ARTIFACT_MISSING_CHECKSUM_SHA256",
        "artifact checksum_sha256 must be a non-empty string.",
        issues,
    )
    _validate_optional_positive_int(
        artifact.size_bytes,
        "artifact.size_bytes",
        "GHG_SOURCE_DOWNLOAD_ARTIFACT_INVALID_SIZE_BYTES",
        "artifact size_bytes must be a positive integer.",
        issues,
    )
    if artifact.source_family != GHG_SOURCE_FAMILY:
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_ARTIFACT_SOURCE_FAMILY_MISMATCH",
                message="artifact source_family must be ghg_protocol.",
                field_name="artifact.source_family",
            )
        )
    if artifact.source_key != GHG_SOURCE_KEY:
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code="GHG_SOURCE_DOWNLOAD_ARTIFACT_SOURCE_KEY_MISMATCH",
                message="artifact source_key must be ghg_protocol.",
                field_name="artifact.source_key",
            )
        )

    return GHGSourceDownloadExecutionValidationResult(issues=tuple(issues))


def _target_path(request: GHGSourceDownloadExecutionRequest) -> Path:
    return Path(request.target_root) / request.target_relative_path


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[GHGSourceDownloadExecutionIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )


def _validate_optional_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[GHGSourceDownloadExecutionIssue],
) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )


def _validate_optional_positive_int(
    value: int | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[GHGSourceDownloadExecutionIssue],
) -> None:
    if value is not None and (
        not isinstance(value, int) or isinstance(value, bool) or value <= 0
    ):
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )


def _validate_true(
    value: bool,
    field_name: str,
    code: str,
    message: str,
    issues: list[GHGSourceDownloadExecutionIssue],
) -> None:
    if value is not True:
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )


def _validate_false(
    value: bool,
    field_name: str,
    code: str,
    message: str,
    issues: list[GHGSourceDownloadExecutionIssue],
) -> None:
    if value is not False:
        issues.append(
            GHGSourceDownloadExecutionIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )
