"""Explicit IPCC-only source download execution boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import errno
from hashlib import sha256
import os
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

from carbonfactor_parser.source_acquisition.ipcc_source_discovery_boundary import (
    IPCC_SOURCE_FAMILY,
    IPCC_SOURCE_KEY,
    IPCCSourceDocumentCandidate,
)


class IPCCSourceDownloadExecutionStatus(str, Enum):
    """Status values for IPCC source download execution."""

    BLOCKED = "blocked"
    DOWNLOADED = "downloaded"
    FAILED = "failed"


@dataclass(frozen=True)
class IPCCSourceDownloadExecutionRequest:
    """Explicit opt-in request to download one IPCC source candidate."""

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
    retrieved_at_label: str = "download_execution_retrieved_at_caller_boundary"


@dataclass(frozen=True)
class IPCCSourceDownloadTransportResponse:
    """Downloaded payload returned by a caller-provided transport."""

    content: bytes
    content_type: str | None = None
    final_uri: str | None = None


class IPCCSourceDownloadTransport(Protocol):
    """Caller-provided transport for explicit IPCC source download execution."""

    def __call__(
        self,
        source_reference_uri: str,
    ) -> IPCCSourceDownloadTransportResponse:
        """Return downloaded content for the provided source reference."""


@dataclass(frozen=True)
class IPCCSourceDownloadedArtifact:
    """Local artifact produced by explicit IPCC source download execution."""

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
    storage_identity: str | None = None
    document_year: int | None = None
    reporting_year: int | None = None
    version_label: str | None = None
    retrieved_at_label: str | None = None
    reused_existing: bool = False


@dataclass(frozen=True)
class IPCCSourceDownloadExecutionIssue:
    """Validation or execution issue for IPCC source downloads."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class IPCCSourceDownloadExecutionValidationResult:
    """Structural validation result for IPCC source download requests."""

    issues: tuple[IPCCSourceDownloadExecutionIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


@dataclass(frozen=True)
class IPCCSourceDownloadExecutionResult:
    """Result of explicit IPCC source download execution."""

    status: IPCCSourceDownloadExecutionStatus
    request: IPCCSourceDownloadExecutionRequest
    artifact: IPCCSourceDownloadedArtifact | None = None
    issues: tuple[IPCCSourceDownloadExecutionIssue, ...] = ()
    no_parse: bool = True
    no_database_writes: bool = True
    no_sql: bool = True
    no_scheduler: bool = True

    @property
    def downloaded(self) -> bool:
        return self.status is IPCCSourceDownloadExecutionStatus.DOWNLOADED


@dataclass(frozen=True)
class _SafeTargetPath:
    target_path: Path
    resolved_root: Path
    resolved_parent: Path
    resolved_target_path: Path
    parent_fd: int


def create_ipcc_source_download_execution_request(
    candidate: IPCCSourceDocumentCandidate,
    *,
    target_root: str,
    target_relative_path: str,
    allow_download_execution: bool = False,
    allow_file_write: bool = False,
    allow_network: bool = False,
    allow_overwrite: bool = False,
    retrieved_at_label: str = "download_execution_retrieved_at_caller_boundary",
) -> IPCCSourceDownloadExecutionRequest:
    """Create an explicit IPCC download request from candidate metadata."""

    return IPCCSourceDownloadExecutionRequest(
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
        retrieved_at_label=retrieved_at_label,
    )


def validate_ipcc_source_download_execution_request(
    request: IPCCSourceDownloadExecutionRequest,
) -> IPCCSourceDownloadExecutionValidationResult:
    """Validate an IPCC source download request without executing it."""

    issues: list[IPCCSourceDownloadExecutionIssue] = []

    _validate_required_text(
        request.source_family,
        "source_family",
        "IPCC_SOURCE_DOWNLOAD_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.source_key,
        "source_key",
        "IPCC_SOURCE_DOWNLOAD_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.candidate_id,
        "candidate_id",
        "IPCC_SOURCE_DOWNLOAD_MISSING_CANDIDATE_ID",
        "candidate_id must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.candidate_title,
        "candidate_title",
        "IPCC_SOURCE_DOWNLOAD_MISSING_CANDIDATE_TITLE",
        "candidate_title must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.source_reference_uri,
        "source_reference_uri",
        "IPCC_SOURCE_DOWNLOAD_MISSING_SOURCE_REFERENCE_URI",
        "source_reference_uri must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.artifact_kind,
        "artifact_kind",
        "IPCC_SOURCE_DOWNLOAD_MISSING_ARTIFACT_KIND",
        "artifact_kind must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.target_root,
        "target_root",
        "IPCC_SOURCE_DOWNLOAD_MISSING_TARGET_ROOT",
        "target_root must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.target_relative_path,
        "target_relative_path",
        "IPCC_SOURCE_DOWNLOAD_MISSING_TARGET_RELATIVE_PATH",
        "target_relative_path must be a non-empty string.",
        issues,
    )
    _validate_optional_text(
        request.content_type,
        "content_type",
        "IPCC_SOURCE_DOWNLOAD_BLANK_CONTENT_TYPE",
        "content_type must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        request.extension,
        "extension",
        "IPCC_SOURCE_DOWNLOAD_BLANK_EXTENSION",
        "extension must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        request.expected_checksum_sha256,
        "expected_checksum_sha256",
        "IPCC_SOURCE_DOWNLOAD_BLANK_EXPECTED_CHECKSUM_SHA256",
        "expected_checksum_sha256 must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        request.version_label,
        "version_label",
        "IPCC_SOURCE_DOWNLOAD_BLANK_VERSION_LABEL",
        "version_label must be non-empty when provided.",
        issues,
    )
    _validate_required_text(
        request.retrieved_at_label,
        "retrieved_at_label",
        "IPCC_SOURCE_DOWNLOAD_MISSING_RETRIEVED_AT_LABEL",
        "retrieved_at_label must be a non-empty string.",
        issues,
    )
    _validate_optional_positive_int(
        request.document_year,
        "document_year",
        "IPCC_SOURCE_DOWNLOAD_INVALID_DOCUMENT_YEAR",
        "document_year must be a positive integer when provided.",
        issues,
    )
    _validate_optional_positive_int(
        request.reporting_year,
        "reporting_year",
        "IPCC_SOURCE_DOWNLOAD_INVALID_REPORTING_YEAR",
        "reporting_year must be a positive integer when provided.",
        issues,
    )

    if request.source_family != IPCC_SOURCE_FAMILY:
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_SOURCE_FAMILY_MISMATCH",
                message="source_family must be ipcc_efdb.",
                field_name="source_family",
            )
        )
    if request.source_key != IPCC_SOURCE_KEY:
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_SOURCE_KEY_MISMATCH",
                message="source_key must be ipcc_efdb.",
                field_name="source_key",
            )
        )
    _validate_true(
        request.candidate_download_allowed,
        "candidate_download_allowed",
        "IPCC_SOURCE_DOWNLOAD_CANDIDATE_NOT_DOWNLOADABLE",
        "candidate metadata must explicitly allow download execution.",
        issues,
    )
    _validate_true(
        request.allow_download_execution,
        "allow_download_execution",
        "IPCC_SOURCE_DOWNLOAD_EXECUTION_NOT_ALLOWED",
        "allow_download_execution must be True.",
        issues,
    )
    _validate_true(
        request.allow_file_write,
        "allow_file_write",
        "IPCC_SOURCE_DOWNLOAD_FILE_WRITE_NOT_ALLOWED",
        "allow_file_write must be True.",
        issues,
    )
    _validate_false(
        request.allow_parse,
        "allow_parse",
        "IPCC_SOURCE_DOWNLOAD_PARSE_NOT_ALLOWED",
        "allow_parse must be False for this boundary.",
        issues,
    )
    _validate_false(
        request.allow_database_writes,
        "allow_database_writes",
        "IPCC_SOURCE_DOWNLOAD_DATABASE_WRITES_NOT_ALLOWED",
        "allow_database_writes must be False for this boundary.",
        issues,
    )
    _validate_false(
        request.allow_scheduler,
        "allow_scheduler",
        "IPCC_SOURCE_DOWNLOAD_SCHEDULER_NOT_ALLOWED",
        "allow_scheduler must be False for this boundary.",
        issues,
    )

    _validate_source_reference_uri(request, issues)
    _validate_target_paths(request, issues)

    return IPCCSourceDownloadExecutionValidationResult(issues=tuple(issues))


def execute_ipcc_source_download(
    request: IPCCSourceDownloadExecutionRequest,
    transport: IPCCSourceDownloadTransport,
) -> IPCCSourceDownloadExecutionResult:
    """Execute one explicit IPCC source download using a provided transport."""

    validation = validate_ipcc_source_download_execution_request(request)
    if not validation.is_valid:
        return IPCCSourceDownloadExecutionResult(
            status=IPCCSourceDownloadExecutionStatus.BLOCKED,
            request=request,
            issues=validation.issues,
        )

    safe_target, target_issues = _prepare_safe_target_path(request)
    if target_issues:
        return IPCCSourceDownloadExecutionResult(
            status=IPCCSourceDownloadExecutionStatus.BLOCKED,
            request=request,
            issues=target_issues,
        )
    if safe_target is None:
        return IPCCSourceDownloadExecutionResult(
            status=IPCCSourceDownloadExecutionStatus.BLOCKED,
            request=request,
            issues=(
                IPCCSourceDownloadExecutionIssue(
                    code="IPCC_SOURCE_DOWNLOAD_TARGET_PATH_UNRESOLVED",
                    message="target path could not be resolved safely.",
                    field_name="target_relative_path",
                ),
            ),
        )

    try:
        if safe_target.resolved_target_path.exists() and not request.allow_overwrite:
            existing_result = _create_existing_artifact_result(request, safe_target)
            if existing_result is not None:
                return existing_result

        try:
            response = transport(request.source_reference_uri)
        except Exception as error:  # noqa: BLE001
            return IPCCSourceDownloadExecutionResult(
                status=IPCCSourceDownloadExecutionStatus.FAILED,
                request=request,
                issues=(
                    IPCCSourceDownloadExecutionIssue(
                        code="IPCC_SOURCE_DOWNLOAD_TRANSPORT_FAILED",
                        message=f"transport failed: {error}",
                        field_name="source_reference_uri",
                    ),
                ),
            )

        response_validation = _validate_transport_response(response)
        if not response_validation.is_valid:
            return IPCCSourceDownloadExecutionResult(
                status=IPCCSourceDownloadExecutionStatus.FAILED,
                request=request,
                issues=response_validation.issues,
            )

        content = bytes(response.content)
        checksum_sha256 = sha256(content).hexdigest()
        if (
            request.expected_checksum_sha256 is not None
            and checksum_sha256.lower() != request.expected_checksum_sha256.lower()
        ):
            return IPCCSourceDownloadExecutionResult(
                status=IPCCSourceDownloadExecutionStatus.FAILED,
                request=request,
                issues=(
                    IPCCSourceDownloadExecutionIssue(
                        code="IPCC_SOURCE_DOWNLOAD_CHECKSUM_MISMATCH",
                        message=(
                            "downloaded content checksum did not match expected "
                            "value."
                        ),
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
            issue_code = "IPCC_SOURCE_DOWNLOAD_WRITE_FAILED"
            if isinstance(error, FileExistsError):
                issue_code = "IPCC_SOURCE_DOWNLOAD_TARGET_EXISTS"
            elif isinstance(error, OSError) and error.errno == errno.ELOOP:
                issue_code = "IPCC_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE"
            return IPCCSourceDownloadExecutionResult(
                status=IPCCSourceDownloadExecutionStatus.FAILED,
                request=request,
                issues=(
                    IPCCSourceDownloadExecutionIssue(
                        code=issue_code,
                        message=f"target write failed: {error}",
                        field_name="target_relative_path",
                    ),
                ),
            )

        artifact = _create_artifact(
            request,
            safe_target,
            checksum_sha256=checksum_sha256,
            size_bytes=len(content),
            content_type=response.content_type or request.content_type,
            final_uri=response.final_uri,
            reused_existing=False,
        )
        return IPCCSourceDownloadExecutionResult(
            status=IPCCSourceDownloadExecutionStatus.DOWNLOADED,
            request=request,
            artifact=artifact,
        )
    finally:
        _close_safe_target_path(safe_target)


def validate_ipcc_source_download_execution_result(
    result: IPCCSourceDownloadExecutionResult,
) -> IPCCSourceDownloadExecutionValidationResult:
    """Validate an IPCC source download execution result."""

    issues: list[IPCCSourceDownloadExecutionIssue] = []
    issues.extend(
        validate_ipcc_source_download_execution_request(result.request).issues
    )

    if not isinstance(result.status, IPCCSourceDownloadExecutionStatus):
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_RESULT_INVALID_STATUS",
                message=(
                    "status must be a defined IPCC source download execution "
                    "status."
                ),
                field_name="status",
            )
        )

    for field_name, value in (
        ("no_parse", result.no_parse),
        ("no_database_writes", result.no_database_writes),
        ("no_sql", result.no_sql),
        ("no_scheduler", result.no_scheduler),
    ):
        if value is not True:
            issues.append(
                IPCCSourceDownloadExecutionIssue(
                    code="IPCC_SOURCE_DOWNLOAD_RESULT_SIDE_EFFECT_FLAG_ENABLED",
                    message=f"{field_name} must remain True.",
                    field_name=field_name,
                )
            )

    if result.status is IPCCSourceDownloadExecutionStatus.DOWNLOADED:
        if result.artifact is None:
            issues.append(
                IPCCSourceDownloadExecutionIssue(
                    code="IPCC_SOURCE_DOWNLOAD_RESULT_MISSING_ARTIFACT",
                    message="downloaded results require artifact metadata.",
                    field_name="artifact",
                )
            )
    elif result.artifact is not None:
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_RESULT_UNEXPECTED_ARTIFACT",
                message="non-downloaded results must not include artifact metadata.",
                field_name="artifact",
            )
        )

    if (
        result.status is not IPCCSourceDownloadExecutionStatus.DOWNLOADED
        and not result.issues
    ):
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_RESULT_MISSING_ISSUES",
                message="blocked or failed results require issue metadata.",
                field_name="issues",
            )
        )

    if result.artifact is not None:
        issues.extend(_validate_artifact(result.artifact).issues)

    return IPCCSourceDownloadExecutionValidationResult(issues=tuple(issues))


def _validate_source_reference_uri(
    request: IPCCSourceDownloadExecutionRequest,
    issues: list[IPCCSourceDownloadExecutionIssue],
) -> None:
    if not isinstance(request.source_reference_uri, str) or not (
        source_reference_uri := request.source_reference_uri.strip()
    ):
        return

    parsed = urlparse(source_reference_uri)
    scheme = parsed.scheme
    if not scheme:
        if "://" in source_reference_uri:
            issues.append(
                IPCCSourceDownloadExecutionIssue(
                    code="IPCC_SOURCE_DOWNLOAD_MALFORMED_SOURCE_REFERENCE_URI",
                    message="source_reference_uri must be a well-formed URI.",
                    field_name="source_reference_uri",
                )
            )
            return
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_SOURCE_REFERENCE_URI_MISSING_SCHEME",
                message="source_reference_uri must include a URI scheme.",
                field_name="source_reference_uri",
            )
        )
        return
    if scheme == "discovery":
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_DISCOVERY_REFERENCE_NOT_DOWNLOADABLE",
                message="discovery references are not direct download references.",
                field_name="source_reference_uri",
            )
        )
        return
    if scheme in {"http", "https"} and not parsed.netloc:
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_MALFORMED_SOURCE_REFERENCE_URI",
                message="source_reference_uri must be a well-formed URI.",
                field_name="source_reference_uri",
            )
        )
        return
    if scheme == "http":
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_INSECURE_HTTP_NOT_ALLOWED",
                message="source_reference_uri must not use insecure HTTP.",
                field_name="source_reference_uri",
            )
        )
        return
    if scheme == "https" and not request.allow_network:
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_NETWORK_NOT_ALLOWED",
                message="allow_network must be True for HTTPS references.",
                field_name="allow_network",
            )
        )
    if scheme not in {"https", "memory", "mock"}:
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_UNSAFE_SOURCE_REFERENCE_URI",
                message="source_reference_uri scheme is not allowed.",
                field_name="source_reference_uri",
            )
        )


def _validate_target_paths(
    request: IPCCSourceDownloadExecutionRequest,
    issues: list[IPCCSourceDownloadExecutionIssue],
) -> None:
    target_root = Path(request.target_root)
    target_relative_path = Path(request.target_relative_path)

    if not target_root.is_absolute():
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_TARGET_ROOT_NOT_ABSOLUTE",
                message="target_root must be an absolute path.",
                field_name="target_root",
            )
        )
    if target_relative_path.is_absolute():
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_ABSOLUTE",
                message="target_relative_path must be relative.",
                field_name="target_relative_path",
            )
        )
    if "://" in request.target_relative_path:
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_URI",
                message="target_relative_path must not be a URI.",
                field_name="target_relative_path",
            )
        )
    if any(part in {"", ".", ".."} for part in target_relative_path.parts):
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_UNSAFE",
                message=(
                    "target_relative_path must not contain empty, current, or "
                    "parent segments."
                ),
                field_name="target_relative_path",
            )
        )


def _prepare_safe_target_path(
    request: IPCCSourceDownloadExecutionRequest,
) -> tuple[_SafeTargetPath | None, tuple[IPCCSourceDownloadExecutionIssue, ...]]:
    issues: list[IPCCSourceDownloadExecutionIssue] = []
    target_root = Path(request.target_root)
    target_relative_path = Path(request.target_relative_path)

    try:
        target_root.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        return None, (
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_TARGET_ROOT_CREATE_FAILED",
                message=f"target_root could not be created: {error}",
                field_name="target_root",
            ),
        )

    if not target_root.is_dir():
        return None, (
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_TARGET_ROOT_NOT_DIRECTORY",
                message="target_root must resolve to a directory.",
                field_name="target_root",
            ),
        )

    try:
        resolved_root = target_root.resolve(strict=True)
    except OSError as error:
        return None, (
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_TARGET_ROOT_RESOLVE_FAILED",
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
                IPCCSourceDownloadExecutionIssue(
                    code="IPCC_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE",
                    message="target parent path must not contain symlinks.",
                    field_name="target_relative_path",
                )
            )
            continue
        try:
            if current_path.exists():
                if not current_path.is_dir():
                    issues.append(
                        IPCCSourceDownloadExecutionIssue(
                            code="IPCC_SOURCE_DOWNLOAD_TARGET_PARENT_NOT_DIRECTORY",
                            message="target parent path must be a directory.",
                            field_name="target_relative_path",
                        )
                    )
                    continue
            else:
                current_path.mkdir()
        except OSError as error:
            issues.append(
                IPCCSourceDownloadExecutionIssue(
                    code="IPCC_SOURCE_DOWNLOAD_TARGET_PARENT_CREATE_FAILED",
                    message=f"target parent path could not be prepared: {error}",
                    field_name="target_relative_path",
                )
            )
            continue

        try:
            resolved_parent = current_path.resolve(strict=True)
        except OSError as error:
            issues.append(
                IPCCSourceDownloadExecutionIssue(
                    code="IPCC_SOURCE_DOWNLOAD_TARGET_PARENT_RESOLVE_FAILED",
                    message=f"target parent path could not be resolved: {error}",
                    field_name="target_relative_path",
                )
            )
            continue
        if not _is_relative_to(resolved_parent, resolved_root):
            issues.append(
                IPCCSourceDownloadExecutionIssue(
                    code="IPCC_SOURCE_DOWNLOAD_TARGET_CONTAINMENT_UNSAFE",
                    message="resolved target parent escapes target_root.",
                    field_name="target_relative_path",
                )
            )

    target_path = target_root / target_relative_path
    if target_path.is_symlink():
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE",
                message="target path must not be an existing symlink.",
                field_name="target_relative_path",
            )
        )
    elif target_path.exists():
        if target_path.is_dir():
            issues.append(
                IPCCSourceDownloadExecutionIssue(
                    code="IPCC_SOURCE_DOWNLOAD_TARGET_NOT_FILE",
                    message="target path must not be a directory.",
                    field_name="target_relative_path",
                )
            )

    resolved_target_path = resolved_parent / target_relative_path.name
    if not _is_relative_to(resolved_target_path, resolved_root):
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_TARGET_CONTAINMENT_UNSAFE",
                message="resolved target path escapes target_root.",
                field_name="target_relative_path",
            )
        )

    if issues:
        return None, tuple(issues)

    parent_fd, parent_fd_issue = _open_safe_parent_directory_fd(resolved_parent)
    if parent_fd_issue is not None:
        return None, (parent_fd_issue,)

    return (
        _SafeTargetPath(
            target_path=target_path,
            resolved_root=resolved_root,
            resolved_parent=resolved_parent,
            resolved_target_path=resolved_target_path,
            parent_fd=parent_fd,
        ),
        (),
    )


def _open_safe_parent_directory_fd(
    resolved_parent: Path,
) -> tuple[int, IPCCSourceDownloadExecutionIssue | None]:
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        return -1, IPCCSourceDownloadExecutionIssue(
            code="IPCC_SOURCE_DOWNLOAD_TARGET_FD_UNSUPPORTED",
            message="platform does not expose required safe directory flags.",
            field_name="target_relative_path",
        )
    if os.open not in getattr(os, "supports_dir_fd", set()):
        return -1, IPCCSourceDownloadExecutionIssue(
            code="IPCC_SOURCE_DOWNLOAD_TARGET_FD_UNSUPPORTED",
            message="platform does not support directory-relative file opening.",
            field_name="target_relative_path",
        )

    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        return os.open(resolved_parent, directory_flags), None
    except OSError as error:
        issue_code = "IPCC_SOURCE_DOWNLOAD_TARGET_PARENT_OPEN_FAILED"
        if error.errno == errno.ELOOP:
            issue_code = "IPCC_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE"
        return -1, IPCCSourceDownloadExecutionIssue(
            code=issue_code,
            message=f"target parent directory could not be opened safely: {error}",
            field_name="target_relative_path",
        )


def _write_content_to_safe_target(
    safe_target: _SafeTargetPath,
    content: bytes,
    *,
    allow_overwrite: bool,
) -> None:
    _ensure_parent_path_still_matches_open_fd(safe_target)

    flags = os.O_WRONLY | os.O_CREAT
    flags |= os.O_TRUNC if allow_overwrite else os.O_EXCL
    flags |= os.O_NOFOLLOW

    file_fd = os.open(
        safe_target.resolved_target_path.name,
        flags,
        0o600,
        dir_fd=safe_target.parent_fd,
    )
    try:
        target_file = os.fdopen(file_fd, "wb")
    except Exception:
        os.close(file_fd)
        raise
    with target_file:
        target_file.write(content)


def _create_existing_artifact_result(
    request: IPCCSourceDownloadExecutionRequest,
    safe_target: _SafeTargetPath,
) -> IPCCSourceDownloadExecutionResult | None:
    try:
        content = _read_existing_content_from_safe_target(safe_target)
    except Exception as error:  # noqa: BLE001
        issue_code = "IPCC_SOURCE_DOWNLOAD_EXISTING_READ_FAILED"
        if isinstance(error, OSError) and error.errno == errno.ELOOP:
            issue_code = "IPCC_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE"
        return IPCCSourceDownloadExecutionResult(
            status=IPCCSourceDownloadExecutionStatus.BLOCKED,
            request=request,
            issues=(
                IPCCSourceDownloadExecutionIssue(
                    code=issue_code,
                    message=f"existing target could not be read safely: {error}",
                    field_name="target_relative_path",
                ),
            ),
        )

    if len(content) == 0:
        return IPCCSourceDownloadExecutionResult(
            status=IPCCSourceDownloadExecutionStatus.FAILED,
            request=request,
            issues=(
                IPCCSourceDownloadExecutionIssue(
                    code="IPCC_SOURCE_DOWNLOAD_EXISTING_EMPTY_CONTENT",
                    message="existing target content must not be empty.",
                    field_name="target_relative_path",
                ),
            ),
        )

    checksum_sha256 = sha256(content).hexdigest()
    if (
        request.expected_checksum_sha256 is not None
        and checksum_sha256.lower() != request.expected_checksum_sha256.lower()
    ):
        return IPCCSourceDownloadExecutionResult(
            status=IPCCSourceDownloadExecutionStatus.FAILED,
            request=request,
            issues=(
                IPCCSourceDownloadExecutionIssue(
                    code="IPCC_SOURCE_DOWNLOAD_EXISTING_CHECKSUM_MISMATCH",
                    message="existing target checksum did not match expected value.",
                    field_name="expected_checksum_sha256",
                ),
            ),
        )

    return IPCCSourceDownloadExecutionResult(
        status=IPCCSourceDownloadExecutionStatus.DOWNLOADED,
        request=request,
        artifact=_create_artifact(
            request,
            safe_target,
            checksum_sha256=checksum_sha256,
            size_bytes=len(content),
            content_type=request.content_type,
            final_uri=request.source_reference_uri,
            reused_existing=True,
        ),
    )


def _read_existing_content_from_safe_target(safe_target: _SafeTargetPath) -> bytes:
    _ensure_parent_path_still_matches_open_fd(safe_target)

    file_fd = os.open(
        safe_target.resolved_target_path.name,
        os.O_RDONLY | os.O_NOFOLLOW,
        dir_fd=safe_target.parent_fd,
    )
    try:
        target_file = os.fdopen(file_fd, "rb")
    except Exception:
        os.close(file_fd)
        raise
    with target_file:
        return target_file.read()


def _create_artifact(
    request: IPCCSourceDownloadExecutionRequest,
    safe_target: _SafeTargetPath,
    *,
    checksum_sha256: str,
    size_bytes: int,
    content_type: str | None,
    final_uri: str | None,
    reused_existing: bool,
) -> IPCCSourceDownloadedArtifact:
    storage_identity = str(safe_target.resolved_target_path)
    return IPCCSourceDownloadedArtifact(
        source_family=request.source_family,
        source_key=request.source_key,
        candidate_id=request.candidate_id,
        artifact_id=f"ipcc_source_download_artifact_{request.candidate_id}",
        artifact_kind=request.artifact_kind,
        source_reference_uri=request.source_reference_uri,
        local_path=storage_identity,
        original_filename=safe_target.resolved_target_path.name,
        checksum_sha256=checksum_sha256,
        size_bytes=size_bytes,
        content_type=content_type,
        extension=request.extension,
        final_uri=final_uri,
        storage_identity=storage_identity,
        document_year=request.document_year,
        reporting_year=request.reporting_year,
        version_label=request.version_label,
        retrieved_at_label=request.retrieved_at_label,
        reused_existing=reused_existing,
    )


def _close_safe_target_path(safe_target: _SafeTargetPath) -> None:
    os.close(safe_target.parent_fd)


def _ensure_parent_path_still_matches_open_fd(
    safe_target: _SafeTargetPath,
) -> None:
    if safe_target.resolved_parent.is_symlink():
        raise OSError(errno.ELOOP, "target parent path changed to a symlink")

    parent_fd_stat = os.fstat(safe_target.parent_fd)
    parent_path_stat = safe_target.resolved_parent.stat()
    if (
        parent_fd_stat.st_dev != parent_path_stat.st_dev
        or parent_fd_stat.st_ino != parent_path_stat.st_ino
    ):
        raise OSError(
            getattr(errno, "ESTALE", errno.EIO),
            "target parent path changed after validation",
        )


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _validate_transport_response(
    response: IPCCSourceDownloadTransportResponse | object,
) -> IPCCSourceDownloadExecutionValidationResult:
    issues: list[IPCCSourceDownloadExecutionIssue] = []
    if response is None:
        return IPCCSourceDownloadExecutionValidationResult(
            issues=(
                IPCCSourceDownloadExecutionIssue(
                    code="IPCC_SOURCE_DOWNLOAD_RESPONSE_MISSING",
                    message="transport response is required.",
                    field_name="transport",
                ),
            )
        )

    content = getattr(response, "content", None)
    if content is None:
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_RESPONSE_MISSING_CONTENT",
                message="transport response content is required.",
                field_name="transport.content",
            )
        )
    elif not isinstance(content, bytes):
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_RESPONSE_CONTENT_NOT_BYTES",
                message="transport response content must be bytes.",
                field_name="transport.content",
            )
        )
    elif len(content) == 0:
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_RESPONSE_EMPTY_CONTENT",
                message="transport response content must not be empty.",
                field_name="transport.content",
            )
        )

    _validate_optional_text(
        getattr(response, "content_type", None),
        "transport.content_type",
        "IPCC_SOURCE_DOWNLOAD_RESPONSE_BLANK_CONTENT_TYPE",
        "response content_type must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        getattr(response, "final_uri", None),
        "transport.final_uri",
        "IPCC_SOURCE_DOWNLOAD_RESPONSE_BLANK_FINAL_URI",
        "response final_uri must be non-empty when provided.",
        issues,
    )

    return IPCCSourceDownloadExecutionValidationResult(issues=tuple(issues))


def _validate_artifact(
    artifact: IPCCSourceDownloadedArtifact,
) -> IPCCSourceDownloadExecutionValidationResult:
    issues: list[IPCCSourceDownloadExecutionIssue] = []
    _validate_required_text(
        artifact.local_path,
        "artifact.local_path",
        "IPCC_SOURCE_DOWNLOAD_ARTIFACT_MISSING_LOCAL_PATH",
        "artifact local_path must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        artifact.checksum_sha256,
        "artifact.checksum_sha256",
        "IPCC_SOURCE_DOWNLOAD_ARTIFACT_MISSING_CHECKSUM_SHA256",
        "artifact checksum_sha256 must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        artifact.source_reference_uri,
        "artifact.source_reference_uri",
        "IPCC_SOURCE_DOWNLOAD_ARTIFACT_MISSING_SOURCE_REFERENCE_URI",
        "artifact source_reference_uri must be a non-empty string.",
        issues,
    )
    _validate_optional_text(
        artifact.storage_identity,
        "artifact.storage_identity",
        "IPCC_SOURCE_DOWNLOAD_ARTIFACT_BLANK_STORAGE_IDENTITY",
        "artifact storage_identity must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        artifact.version_label,
        "artifact.version_label",
        "IPCC_SOURCE_DOWNLOAD_ARTIFACT_BLANK_VERSION_LABEL",
        "artifact version_label must be non-empty when provided.",
        issues,
    )
    _validate_required_text(
        artifact.retrieved_at_label,
        "artifact.retrieved_at_label",
        "IPCC_SOURCE_DOWNLOAD_ARTIFACT_MISSING_RETRIEVED_AT_LABEL",
        "artifact retrieved_at_label must be a non-empty string.",
        issues,
    )
    _validate_optional_positive_int(
        artifact.size_bytes,
        "artifact.size_bytes",
        "IPCC_SOURCE_DOWNLOAD_ARTIFACT_INVALID_SIZE_BYTES",
        "artifact size_bytes must be a positive integer.",
        issues,
    )
    if artifact.source_family != IPCC_SOURCE_FAMILY:
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_ARTIFACT_SOURCE_FAMILY_MISMATCH",
                message="artifact source_family must be ipcc_efdb.",
                field_name="artifact.source_family",
            )
        )
    if artifact.source_key != IPCC_SOURCE_KEY:
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code="IPCC_SOURCE_DOWNLOAD_ARTIFACT_SOURCE_KEY_MISMATCH",
                message="artifact source_key must be ipcc_efdb.",
                field_name="artifact.source_key",
            )
        )

    return IPCCSourceDownloadExecutionValidationResult(issues=tuple(issues))


def _target_path(request: IPCCSourceDownloadExecutionRequest) -> Path:
    return Path(request.target_root) / request.target_relative_path


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[IPCCSourceDownloadExecutionIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            IPCCSourceDownloadExecutionIssue(
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
    issues: list[IPCCSourceDownloadExecutionIssue],
) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        issues.append(
            IPCCSourceDownloadExecutionIssue(
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
    issues: list[IPCCSourceDownloadExecutionIssue],
) -> None:
    if value is not None and (
        not isinstance(value, int) or isinstance(value, bool) or value <= 0
    ):
        issues.append(
            IPCCSourceDownloadExecutionIssue(
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
    issues: list[IPCCSourceDownloadExecutionIssue],
) -> None:
    if value is not True:
        issues.append(
            IPCCSourceDownloadExecutionIssue(
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
    issues: list[IPCCSourceDownloadExecutionIssue],
) -> None:
    if value is not False:
        issues.append(
            IPCCSourceDownloadExecutionIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )
