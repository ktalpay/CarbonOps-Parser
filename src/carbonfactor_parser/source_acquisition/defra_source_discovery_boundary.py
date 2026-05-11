"""Runtime-passive DEFRA source discovery boundary contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.source_acquisition.registry import (
    create_default_source_acquisition_registry,
)

DEFRA_SOURCE_FAMILY = "defra_desnz"
DEFRA_SOURCE_KEY = "defra_desnz"


class DEFRASourceDiscoveryMode(str, Enum):
    """Supported DEFRA source discovery boundary modes."""

    RUNTIME_PASSIVE = "runtime_passive"


class DEFRASourceDiscoveryStatus(str, Enum):
    """Status values for DEFRA source discovery boundary results."""

    DECLARED = "declared"
    INVALID = "invalid"


@dataclass(frozen=True)
class DEFRASourceDiscoveryRequest:
    """Runtime-passive request metadata for future DEFRA source discovery."""

    source_family: str
    source_key: str
    discovery_reference_uri: str
    mode: DEFRASourceDiscoveryMode = DEFRASourceDiscoveryMode.RUNTIME_PASSIVE
    allow_network: bool = False
    allow_download: bool = False
    allow_parse: bool = False
    allow_database_writes: bool = False
    allow_scheduler: bool = False


@dataclass(frozen=True)
class DEFRASourceDocumentCandidate:
    """Metadata-only DEFRA source document candidate."""

    source_family: str
    source_key: str
    candidate_id: str
    title: str
    reference_uri: str
    artifact_kind: str
    status: DEFRASourceDiscoveryStatus = DEFRASourceDiscoveryStatus.DECLARED
    document_year: int | None = None
    reporting_year: int | None = None
    content_type: str | None = None
    extension: str | None = None
    checksum_sha256: str | None = None
    version_label: str | None = None
    discovered_at_label: str | None = None
    download_allowed: bool = False


@dataclass(frozen=True)
class DEFRASourceDiscoveryIssue:
    """Validation issue for DEFRA source discovery boundary metadata."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class DEFRASourceDiscoveryValidationResult:
    """Structural validation result for DEFRA source discovery metadata."""

    issues: tuple[DEFRASourceDiscoveryIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


@dataclass(frozen=True)
class DEFRASourceDiscoveryResult:
    """Runtime-passive DEFRA source discovery result."""

    status: DEFRASourceDiscoveryStatus
    request: DEFRASourceDiscoveryRequest
    candidates: tuple[DEFRASourceDocumentCandidate, ...]
    issues: tuple[DEFRASourceDiscoveryIssue, ...] = ()
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


def create_defra_source_discovery_request() -> DEFRASourceDiscoveryRequest:
    """Create deterministic DEFRA discovery request metadata without execution."""

    descriptor = _defra_descriptor()
    return DEFRASourceDiscoveryRequest(
        source_family=descriptor.source_family,
        source_key=descriptor.source_id,
        discovery_reference_uri=descriptor.acquisition_url,
    )


def create_defra_source_discovery_result(
    request: DEFRASourceDiscoveryRequest | None = None,
) -> DEFRASourceDiscoveryResult:
    """Create deterministic DEFRA source discovery metadata without downloads."""

    active_request = (
        create_defra_source_discovery_request() if request is None else request
    )
    validation = validate_defra_source_discovery_request(active_request)
    if not validation.is_valid:
        return DEFRASourceDiscoveryResult(
            status=DEFRASourceDiscoveryStatus.INVALID,
            request=active_request,
            candidates=(),
            issues=validation.issues,
        )

    descriptor = _defra_descriptor()
    candidate = DEFRASourceDocumentCandidate(
        source_family=descriptor.source_family,
        source_key=descriptor.source_id,
        candidate_id="defra_source_discovery_candidate_001_defra_desnz",
        title=descriptor.display_name,
        reference_uri=active_request.discovery_reference_uri,
        artifact_kind=descriptor.expected_format,
        version_label="py047_defra_discovery_boundary",
        discovered_at_label="runtime_passive_discovery_unavailable",
    )
    candidate_validation = validate_defra_source_document_candidate(candidate)
    return DEFRASourceDiscoveryResult(
        status=(
            DEFRASourceDiscoveryStatus.DECLARED
            if candidate_validation.is_valid
            else DEFRASourceDiscoveryStatus.INVALID
        ),
        request=active_request,
        candidates=(candidate,) if candidate_validation.is_valid else (),
        issues=candidate_validation.issues,
    )


def validate_defra_source_discovery_request(
    request: DEFRASourceDiscoveryRequest,
) -> DEFRASourceDiscoveryValidationResult:
    """Validate DEFRA discovery request metadata without side effects."""

    issues: list[DEFRASourceDiscoveryIssue] = []

    _validate_required_text(
        request.source_family,
        "source_family",
        "DEFRA_SOURCE_DISCOVERY_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.source_key,
        "source_key",
        "DEFRA_SOURCE_DISCOVERY_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.discovery_reference_uri,
        "discovery_reference_uri",
        "DEFRA_SOURCE_DISCOVERY_MISSING_REFERENCE_URI",
        "discovery_reference_uri must be a non-empty string.",
        issues,
    )

    if request.source_family != DEFRA_SOURCE_FAMILY:
        issues.append(
            DEFRASourceDiscoveryIssue(
                code="DEFRA_SOURCE_DISCOVERY_SOURCE_FAMILY_MISMATCH",
                message="source_family must be defra_desnz.",
                field_name="source_family",
            )
        )
    if request.source_key != DEFRA_SOURCE_KEY:
        issues.append(
            DEFRASourceDiscoveryIssue(
                code="DEFRA_SOURCE_DISCOVERY_SOURCE_KEY_MISMATCH",
                message="source_key must be defra_desnz.",
                field_name="source_key",
            )
        )
    if request.mode is not DEFRASourceDiscoveryMode.RUNTIME_PASSIVE:
        issues.append(
            DEFRASourceDiscoveryIssue(
                code="DEFRA_SOURCE_DISCOVERY_UNSUPPORTED_MODE",
                message="mode must remain runtime_passive.",
                field_name="mode",
            )
        )
    _validate_false(
        request.allow_network,
        "allow_network",
        "DEFRA_SOURCE_DISCOVERY_NETWORK_NOT_ALLOWED",
        "allow_network must be False for this boundary.",
        issues,
    )
    _validate_false(
        request.allow_download,
        "allow_download",
        "DEFRA_SOURCE_DISCOVERY_DOWNLOAD_NOT_ALLOWED",
        "allow_download must be False for this boundary.",
        issues,
    )
    _validate_false(
        request.allow_parse,
        "allow_parse",
        "DEFRA_SOURCE_DISCOVERY_PARSE_NOT_ALLOWED",
        "allow_parse must be False for this boundary.",
        issues,
    )
    _validate_false(
        request.allow_database_writes,
        "allow_database_writes",
        "DEFRA_SOURCE_DISCOVERY_DATABASE_WRITES_NOT_ALLOWED",
        "allow_database_writes must be False for this boundary.",
        issues,
    )
    _validate_false(
        request.allow_scheduler,
        "allow_scheduler",
        "DEFRA_SOURCE_DISCOVERY_SCHEDULER_NOT_ALLOWED",
        "allow_scheduler must be False for this boundary.",
        issues,
    )

    return DEFRASourceDiscoveryValidationResult(issues=tuple(issues))


def validate_defra_source_document_candidate(
    candidate: DEFRASourceDocumentCandidate,
) -> DEFRASourceDiscoveryValidationResult:
    """Validate DEFRA candidate metadata without dereferencing references."""

    issues: list[DEFRASourceDiscoveryIssue] = []

    _validate_required_text(
        candidate.source_family,
        "source_family",
        "DEFRA_SOURCE_DISCOVERY_CANDIDATE_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        candidate.source_key,
        "source_key",
        "DEFRA_SOURCE_DISCOVERY_CANDIDATE_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        candidate.candidate_id,
        "candidate_id",
        "DEFRA_SOURCE_DISCOVERY_CANDIDATE_MISSING_CANDIDATE_ID",
        "candidate_id must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        candidate.title,
        "title",
        "DEFRA_SOURCE_DISCOVERY_CANDIDATE_MISSING_TITLE",
        "title must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        candidate.reference_uri,
        "reference_uri",
        "DEFRA_SOURCE_DISCOVERY_CANDIDATE_MISSING_REFERENCE_URI",
        "reference_uri must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        candidate.artifact_kind,
        "artifact_kind",
        "DEFRA_SOURCE_DISCOVERY_CANDIDATE_MISSING_ARTIFACT_KIND",
        "artifact_kind must be a non-empty string.",
        issues,
    )
    _validate_optional_text(
        candidate.content_type,
        "content_type",
        "DEFRA_SOURCE_DISCOVERY_CANDIDATE_BLANK_CONTENT_TYPE",
        "content_type must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        candidate.extension,
        "extension",
        "DEFRA_SOURCE_DISCOVERY_CANDIDATE_BLANK_EXTENSION",
        "extension must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        candidate.checksum_sha256,
        "checksum_sha256",
        "DEFRA_SOURCE_DISCOVERY_CANDIDATE_BLANK_CHECKSUM_SHA256",
        "checksum_sha256 must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        candidate.version_label,
        "version_label",
        "DEFRA_SOURCE_DISCOVERY_CANDIDATE_BLANK_VERSION_LABEL",
        "version_label must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        candidate.discovered_at_label,
        "discovered_at_label",
        "DEFRA_SOURCE_DISCOVERY_CANDIDATE_BLANK_DISCOVERED_AT_LABEL",
        "discovered_at_label must be non-empty when provided.",
        issues,
    )
    _validate_optional_positive_int(
        candidate.document_year,
        "document_year",
        "DEFRA_SOURCE_DISCOVERY_CANDIDATE_INVALID_DOCUMENT_YEAR",
        "document_year must be a positive integer when provided.",
        issues,
    )
    _validate_optional_positive_int(
        candidate.reporting_year,
        "reporting_year",
        "DEFRA_SOURCE_DISCOVERY_CANDIDATE_INVALID_REPORTING_YEAR",
        "reporting_year must be a positive integer when provided.",
        issues,
    )

    descriptor = _defra_descriptor()
    if candidate.source_family != descriptor.source_family:
        issues.append(
            DEFRASourceDiscoveryIssue(
                code="DEFRA_SOURCE_DISCOVERY_CANDIDATE_SOURCE_FAMILY_MISMATCH",
                message="source_family must match the DEFRA source family.",
                field_name="source_family",
            )
        )
    if candidate.source_key != descriptor.source_id:
        issues.append(
            DEFRASourceDiscoveryIssue(
                code="DEFRA_SOURCE_DISCOVERY_CANDIDATE_SOURCE_KEY_MISMATCH",
                message="source_key must match the DEFRA source key.",
                field_name="source_key",
            )
        )
    if candidate.artifact_kind != descriptor.expected_format:
        issues.append(
            DEFRASourceDiscoveryIssue(
                code="DEFRA_SOURCE_DISCOVERY_CANDIDATE_ARTIFACT_KIND_MISMATCH",
                message="artifact_kind must match the DEFRA expected format.",
                field_name="artifact_kind",
            )
        )
    if candidate.status is not DEFRASourceDiscoveryStatus.DECLARED:
        issues.append(
            DEFRASourceDiscoveryIssue(
                code="DEFRA_SOURCE_DISCOVERY_CANDIDATE_UNSUPPORTED_STATUS",
                message="candidate status must remain declared.",
                field_name="status",
            )
        )
    if candidate.download_allowed:
        issues.append(
            DEFRASourceDiscoveryIssue(
                code="DEFRA_SOURCE_DISCOVERY_CANDIDATE_DOWNLOAD_NOT_ALLOWED",
                message="download_allowed must be False for this boundary.",
                field_name="download_allowed",
            )
        )

    return DEFRASourceDiscoveryValidationResult(issues=tuple(issues))


def validate_defra_source_discovery_result(
    result: DEFRASourceDiscoveryResult,
) -> DEFRASourceDiscoveryValidationResult:
    """Validate DEFRA discovery result metadata without runtime behavior."""

    issues: list[DEFRASourceDiscoveryIssue] = []
    issues.extend(validate_defra_source_discovery_request(result.request).issues)

    if not isinstance(result.status, DEFRASourceDiscoveryStatus):
        issues.append(
            DEFRASourceDiscoveryIssue(
                code="DEFRA_SOURCE_DISCOVERY_RESULT_INVALID_STATUS",
                message="status must be a defined DEFRA source discovery status.",
                field_name="status",
            )
        )

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
                DEFRASourceDiscoveryIssue(
                    code="DEFRA_SOURCE_DISCOVERY_RESULT_SIDE_EFFECT_FLAG_ENABLED",
                    message=f"{field_name} must remain True.",
                    field_name=field_name,
                )
            )

    for position, candidate in enumerate(result.candidates, start=1):
        for issue in validate_defra_source_document_candidate(candidate).issues:
            issues.append(
                DEFRASourceDiscoveryIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=f"candidates[{position}].{issue.field_name}",
                    severity=issue.severity,
                )
            )

    if (
        result.status is DEFRASourceDiscoveryStatus.DECLARED
        and len(result.issues) > 0
    ):
        issues.append(
            DEFRASourceDiscoveryIssue(
                code="DEFRA_SOURCE_DISCOVERY_RESULT_DECLARED_WITH_ISSUES",
                message="declared result status must not include issue metadata.",
                field_name="issues",
            )
        )
    if result.status is DEFRASourceDiscoveryStatus.DECLARED and issues:
        issues.append(
            DEFRASourceDiscoveryIssue(
                code="DEFRA_SOURCE_DISCOVERY_RESULT_STATUS_MISMATCH",
                message="declared result status requires valid metadata.",
                field_name="status",
            )
        )
    if result.status is DEFRASourceDiscoveryStatus.INVALID and not result.issues:
        issues.append(
            DEFRASourceDiscoveryIssue(
                code="DEFRA_SOURCE_DISCOVERY_RESULT_MISSING_INVALID_ISSUES",
                message="invalid result status requires issue metadata.",
                field_name="issues",
            )
        )

    return DEFRASourceDiscoveryValidationResult(issues=tuple(issues))


def _defra_descriptor() -> object:
    for descriptor in create_default_source_acquisition_registry():
        if descriptor.source_id == DEFRA_SOURCE_KEY:
            return descriptor
    raise ValueError("DEFRA source descriptor is not registered.")


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[DEFRASourceDiscoveryIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            DEFRASourceDiscoveryIssue(
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
    issues: list[DEFRASourceDiscoveryIssue],
) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        issues.append(
            DEFRASourceDiscoveryIssue(
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
    issues: list[DEFRASourceDiscoveryIssue],
) -> None:
    if value is not None and (
        not isinstance(value, int) or isinstance(value, bool) or value <= 0
    ):
        issues.append(
            DEFRASourceDiscoveryIssue(
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
    issues: list[DEFRASourceDiscoveryIssue],
) -> None:
    if value is not False:
        issues.append(
            DEFRASourceDiscoveryIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )
