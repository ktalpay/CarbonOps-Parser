"""Runtime-passive IPCC source discovery boundary contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.source_acquisition.registry import (
    create_default_source_acquisition_registry,
)

IPCC_SOURCE_FAMILY = "ipcc_efdb"
IPCC_SOURCE_KEY = "ipcc_efdb"


class IPCCSourceDiscoveryMode(str, Enum):
    """Supported IPCC source discovery boundary modes."""

    RUNTIME_PASSIVE = "runtime_passive"


class IPCCSourceDiscoveryStatus(str, Enum):
    """Status values for IPCC source discovery boundary results."""

    DECLARED = "declared"
    INVALID = "invalid"


@dataclass(frozen=True)
class IPCCSourceDiscoveryRequest:
    """Runtime-passive request metadata for future IPCC source discovery."""

    source_family: str
    source_key: str
    discovery_reference_uri: str
    mode: IPCCSourceDiscoveryMode = IPCCSourceDiscoveryMode.RUNTIME_PASSIVE
    allow_network: bool = False
    allow_download: bool = False
    allow_parse: bool = False
    allow_database_writes: bool = False
    allow_scheduler: bool = False


@dataclass(frozen=True)
class IPCCSourceDocumentCandidate:
    """Metadata-only IPCC source document candidate."""

    source_family: str
    source_key: str
    candidate_id: str
    title: str
    reference_uri: str
    artifact_kind: str
    status: IPCCSourceDiscoveryStatus = IPCCSourceDiscoveryStatus.DECLARED
    document_year: int | None = None
    reporting_year: int | None = None
    content_type: str | None = None
    extension: str | None = None
    checksum_sha256: str | None = None
    version_label: str | None = None
    discovered_at_label: str | None = None
    download_allowed: bool = False


@dataclass(frozen=True)
class IPCCSourceDiscoveryIssue:
    """Validation issue for IPCC source discovery boundary metadata."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class IPCCSourceDiscoveryValidationResult:
    """Structural validation result for IPCC source discovery metadata."""

    issues: tuple[IPCCSourceDiscoveryIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


@dataclass(frozen=True)
class IPCCSourceDiscoveryResult:
    """Runtime-passive IPCC source discovery result."""

    status: IPCCSourceDiscoveryStatus
    request: IPCCSourceDiscoveryRequest
    candidates: tuple[IPCCSourceDocumentCandidate, ...]
    issues: tuple[IPCCSourceDiscoveryIssue, ...] = ()
    no_network: bool = True
    no_download: bool = True
    no_parse: bool = True
    no_database_writes: bool = True
    no_sql: bool = True
    no_scheduler: bool = True

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)

    @property
    def candidate_ids(self) -> tuple[str, ...]:
        return tuple(candidate.candidate_id for candidate in self.candidates)


def create_ipcc_source_discovery_request() -> IPCCSourceDiscoveryRequest:
    """Create deterministic IPCC discovery request metadata without execution."""

    descriptor = _ipcc_descriptor()
    return IPCCSourceDiscoveryRequest(
        source_family=descriptor.source_family,
        source_key=descriptor.source_id,
        discovery_reference_uri=descriptor.acquisition_url,
    )


def create_ipcc_source_discovery_result(
    request: IPCCSourceDiscoveryRequest | None = None,
) -> IPCCSourceDiscoveryResult:
    """Create deterministic IPCC source discovery metadata without downloads."""

    active_request = (
        create_ipcc_source_discovery_request() if request is None else request
    )
    validation = validate_ipcc_source_discovery_request(active_request)
    if not validation.is_valid:
        return IPCCSourceDiscoveryResult(
            status=IPCCSourceDiscoveryStatus.INVALID,
            request=active_request,
            candidates=(),
            issues=validation.issues,
        )

    descriptor = _ipcc_descriptor()
    candidate = IPCCSourceDocumentCandidate(
        source_family=descriptor.source_family,
        source_key=descriptor.source_id,
        candidate_id="ipcc_source_discovery_candidate_001_ipcc_efdb",
        title=descriptor.display_name,
        reference_uri=active_request.discovery_reference_uri,
        artifact_kind=descriptor.expected_format,
        version_label="py049_ipcc_discovery_boundary",
        discovered_at_label="runtime_passive_discovery_unavailable",
    )
    candidate_validation = validate_ipcc_source_document_candidate(candidate)
    return IPCCSourceDiscoveryResult(
        status=(
            IPCCSourceDiscoveryStatus.DECLARED
            if candidate_validation.is_valid
            else IPCCSourceDiscoveryStatus.INVALID
        ),
        request=active_request,
        candidates=(candidate,) if candidate_validation.is_valid else (),
        issues=candidate_validation.issues,
    )


def validate_ipcc_source_discovery_request(
    request: IPCCSourceDiscoveryRequest,
) -> IPCCSourceDiscoveryValidationResult:
    """Validate IPCC discovery request metadata without side effects."""

    issues: list[IPCCSourceDiscoveryIssue] = []

    _validate_required_text(
        request.source_family,
        "source_family",
        "IPCC_SOURCE_DISCOVERY_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.source_key,
        "source_key",
        "IPCC_SOURCE_DISCOVERY_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.discovery_reference_uri,
        "discovery_reference_uri",
        "IPCC_SOURCE_DISCOVERY_MISSING_REFERENCE_URI",
        "discovery_reference_uri must be a non-empty string.",
        issues,
    )

    if request.source_family != IPCC_SOURCE_FAMILY:
        issues.append(
            IPCCSourceDiscoveryIssue(
                code="IPCC_SOURCE_DISCOVERY_SOURCE_FAMILY_MISMATCH",
                message="source_family must be ipcc_efdb.",
                field_name="source_family",
            )
        )
    if request.source_key != IPCC_SOURCE_KEY:
        issues.append(
            IPCCSourceDiscoveryIssue(
                code="IPCC_SOURCE_DISCOVERY_SOURCE_KEY_MISMATCH",
                message="source_key must be ipcc_efdb.",
                field_name="source_key",
            )
        )
    if request.mode is not IPCCSourceDiscoveryMode.RUNTIME_PASSIVE:
        issues.append(
            IPCCSourceDiscoveryIssue(
                code="IPCC_SOURCE_DISCOVERY_UNSUPPORTED_MODE",
                message="mode must remain runtime_passive.",
                field_name="mode",
            )
        )
    _validate_false(
        request.allow_network,
        "allow_network",
        "IPCC_SOURCE_DISCOVERY_NETWORK_NOT_ALLOWED",
        "allow_network must be False for this boundary.",
        issues,
    )
    _validate_false(
        request.allow_download,
        "allow_download",
        "IPCC_SOURCE_DISCOVERY_DOWNLOAD_NOT_ALLOWED",
        "allow_download must be False for this boundary.",
        issues,
    )
    _validate_false(
        request.allow_parse,
        "allow_parse",
        "IPCC_SOURCE_DISCOVERY_PARSE_NOT_ALLOWED",
        "allow_parse must be False for this boundary.",
        issues,
    )
    _validate_false(
        request.allow_database_writes,
        "allow_database_writes",
        "IPCC_SOURCE_DISCOVERY_DATABASE_WRITES_NOT_ALLOWED",
        "allow_database_writes must be False for this boundary.",
        issues,
    )
    _validate_false(
        request.allow_scheduler,
        "allow_scheduler",
        "IPCC_SOURCE_DISCOVERY_SCHEDULER_NOT_ALLOWED",
        "allow_scheduler must be False for this boundary.",
        issues,
    )

    return IPCCSourceDiscoveryValidationResult(issues=tuple(issues))


def validate_ipcc_source_document_candidate(
    candidate: IPCCSourceDocumentCandidate,
) -> IPCCSourceDiscoveryValidationResult:
    """Validate IPCC candidate metadata without dereferencing references."""

    issues: list[IPCCSourceDiscoveryIssue] = []

    _validate_required_text(
        candidate.source_family,
        "source_family",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        candidate.source_key,
        "source_key",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        candidate.candidate_id,
        "candidate_id",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_CANDIDATE_ID",
        "candidate_id must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        candidate.title,
        "title",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_TITLE",
        "title must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        candidate.reference_uri,
        "reference_uri",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_REFERENCE_URI",
        "reference_uri must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        candidate.artifact_kind,
        "artifact_kind",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_ARTIFACT_KIND",
        "artifact_kind must be a non-empty string.",
        issues,
    )
    _validate_optional_text(
        candidate.content_type,
        "content_type",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_BLANK_CONTENT_TYPE",
        "content_type must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        candidate.extension,
        "extension",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_BLANK_EXTENSION",
        "extension must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        candidate.checksum_sha256,
        "checksum_sha256",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_BLANK_CHECKSUM_SHA256",
        "checksum_sha256 must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        candidate.version_label,
        "version_label",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_BLANK_VERSION_LABEL",
        "version_label must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        candidate.discovered_at_label,
        "discovered_at_label",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_BLANK_DISCOVERED_AT_LABEL",
        "discovered_at_label must be non-empty when provided.",
        issues,
    )
    _validate_optional_positive_int(
        candidate.document_year,
        "document_year",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_INVALID_DOCUMENT_YEAR",
        "document_year must be a positive integer when provided.",
        issues,
    )
    _validate_optional_positive_int(
        candidate.reporting_year,
        "reporting_year",
        "IPCC_SOURCE_DISCOVERY_CANDIDATE_INVALID_REPORTING_YEAR",
        "reporting_year must be a positive integer when provided.",
        issues,
    )

    descriptor = _ipcc_descriptor()
    if candidate.source_family != descriptor.source_family:
        issues.append(
            IPCCSourceDiscoveryIssue(
                code="IPCC_SOURCE_DISCOVERY_CANDIDATE_SOURCE_FAMILY_MISMATCH",
                message="source_family must match the IPCC source family.",
                field_name="source_family",
            )
        )
    if candidate.source_key != descriptor.source_id:
        issues.append(
            IPCCSourceDiscoveryIssue(
                code="IPCC_SOURCE_DISCOVERY_CANDIDATE_SOURCE_KEY_MISMATCH",
                message="source_key must match the IPCC source key.",
                field_name="source_key",
            )
        )
    if candidate.artifact_kind != descriptor.expected_format:
        issues.append(
            IPCCSourceDiscoveryIssue(
                code="IPCC_SOURCE_DISCOVERY_CANDIDATE_ARTIFACT_KIND_MISMATCH",
                message="artifact_kind must match the IPCC expected format.",
                field_name="artifact_kind",
            )
        )
    if candidate.status is not IPCCSourceDiscoveryStatus.DECLARED:
        issues.append(
            IPCCSourceDiscoveryIssue(
                code="IPCC_SOURCE_DISCOVERY_CANDIDATE_UNSUPPORTED_STATUS",
                message="candidate status must remain declared.",
                field_name="status",
            )
        )
    if candidate.download_allowed:
        issues.append(
            IPCCSourceDiscoveryIssue(
                code="IPCC_SOURCE_DISCOVERY_CANDIDATE_DOWNLOAD_NOT_ALLOWED",
                message="download_allowed must be False for this boundary.",
                field_name="download_allowed",
            )
        )

    return IPCCSourceDiscoveryValidationResult(issues=tuple(issues))


def validate_ipcc_source_discovery_result(
    result: IPCCSourceDiscoveryResult,
) -> IPCCSourceDiscoveryValidationResult:
    """Validate IPCC discovery result metadata without runtime behavior."""

    issues: list[IPCCSourceDiscoveryIssue] = []
    issues.extend(validate_ipcc_source_discovery_request(result.request).issues)

    for field_name, value in (
        ("no_network", result.no_network),
        ("no_download", result.no_download),
        ("no_parse", result.no_parse),
        ("no_database_writes", result.no_database_writes),
        ("no_sql", result.no_sql),
        ("no_scheduler", result.no_scheduler),
    ):
        if value is not True:
            issues.append(
                IPCCSourceDiscoveryIssue(
                    code="IPCC_SOURCE_DISCOVERY_RESULT_SIDE_EFFECT_FLAG_ENABLED",
                    message=f"{field_name} must remain True.",
                    field_name=field_name,
                )
            )

    for position, candidate in enumerate(result.candidates, start=1):
        for issue in validate_ipcc_source_document_candidate(candidate).issues:
            issues.append(
                IPCCSourceDiscoveryIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=f"candidates[{position}].{issue.field_name}",
                    severity=issue.severity,
                )
            )

    if result.status is IPCCSourceDiscoveryStatus.DECLARED and issues:
        issues.append(
            IPCCSourceDiscoveryIssue(
                code="IPCC_SOURCE_DISCOVERY_RESULT_STATUS_MISMATCH",
                message="declared result status requires valid metadata.",
                field_name="status",
            )
        )
    if result.status is IPCCSourceDiscoveryStatus.INVALID and not result.issues:
        issues.append(
            IPCCSourceDiscoveryIssue(
                code="IPCC_SOURCE_DISCOVERY_RESULT_MISSING_INVALID_ISSUES",
                message="invalid result status requires issue metadata.",
                field_name="issues",
            )
        )

    return IPCCSourceDiscoveryValidationResult(issues=tuple(issues))


def _ipcc_descriptor() -> object:
    for descriptor in create_default_source_acquisition_registry():
        if descriptor.source_id == IPCC_SOURCE_KEY:
            return descriptor
    raise ValueError("IPCC source descriptor is not registered.")


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[IPCCSourceDiscoveryIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            IPCCSourceDiscoveryIssue(
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
    issues: list[IPCCSourceDiscoveryIssue],
) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        issues.append(
            IPCCSourceDiscoveryIssue(
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
    issues: list[IPCCSourceDiscoveryIssue],
) -> None:
    if value is not None and (
        not isinstance(value, int) or isinstance(value, bool) or value <= 0
    ):
        issues.append(
            IPCCSourceDiscoveryIssue(
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
    issues: list[IPCCSourceDiscoveryIssue],
) -> None:
    if value is not False:
        issues.append(
            IPCCSourceDiscoveryIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )
