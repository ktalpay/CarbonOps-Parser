"""Runtime-passive source download artifact metadata contract."""

from __future__ import annotations

from dataclasses import dataclass

from carbonfactor_parser.source_acquisition.discovery_candidate_contract import (
    SourceDiscoveryCandidate,
    SourceDiscoveryCandidateResult,
    create_phase1_source_discovery_candidates,
)
from carbonfactor_parser.source_acquisition.registry import (
    create_default_source_acquisition_registry,
)


@dataclass(frozen=True)
class SourceDownloadArtifact:
    """Metadata-only future downloaded source artifact."""

    source_family: str
    source_key: str
    candidate_id: str
    artifact_id: str
    artifact_kind: str
    source_reference_uri: str
    local_reference: str
    original_filename: str | None = None
    display_name: str | None = None
    content_type: str | None = None
    extension: str | None = None
    checksum_sha256: str | None = None
    size_bytes: int | None = None
    document_year: int | None = None
    reporting_year: int | None = None
    version_label: str | None = None


@dataclass(frozen=True)
class SourceDownloadArtifactResult:
    """Deterministic collection of source download artifact metadata."""

    artifacts: tuple[SourceDownloadArtifact, ...]

    @property
    def artifact_count(self) -> int:
        return len(self.artifacts)

    @property
    def source_keys(self) -> tuple[str, ...]:
        return tuple(artifact.source_key for artifact in self.artifacts)


@dataclass(frozen=True)
class SourceDownloadArtifactValidationIssue:
    """Validation issue for source download artifact metadata."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class SourceDownloadArtifactValidationResult:
    """Structural validation result for source download artifact metadata."""

    issues: tuple[SourceDownloadArtifactValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def create_source_download_artifact_from_candidate(
    candidate: SourceDiscoveryCandidate,
    *,
    artifact_id: str,
    local_reference: str,
    original_filename: str | None = None,
    display_name: str | None = None,
    content_type: str | None = None,
    extension: str | None = None,
    checksum_sha256: str | None = None,
    size_bytes: int | None = None,
) -> SourceDownloadArtifact:
    """Create download artifact metadata from discovery candidate metadata."""

    return SourceDownloadArtifact(
        source_family=candidate.source_family,
        source_key=candidate.source_key,
        candidate_id=candidate.candidate_id,
        artifact_id=artifact_id,
        artifact_kind=candidate.artifact_kind,
        source_reference_uri=candidate.reference_uri,
        local_reference=local_reference,
        original_filename=original_filename,
        display_name=display_name if display_name is not None else candidate.title,
        content_type=content_type if content_type is not None else candidate.content_type,
        extension=extension if extension is not None else candidate.extension,
        checksum_sha256=(
            checksum_sha256
            if checksum_sha256 is not None
            else candidate.checksum_sha256
        ),
        size_bytes=size_bytes,
        document_year=candidate.document_year,
        reporting_year=candidate.reporting_year,
        version_label=candidate.version_label,
    )


def create_phase1_source_download_artifacts(
    candidates: SourceDiscoveryCandidateResult | None = None,
) -> SourceDownloadArtifactResult:
    """Create deterministic Phase 1 source download artifact metadata."""

    active_candidates = (
        create_phase1_source_discovery_candidates()
        if candidates is None
        else candidates
    )
    artifacts = tuple(
        create_source_download_artifact_from_candidate(
            candidate,
            artifact_id=f"phase1_download_artifact_{index:03d}_{candidate.source_key}",
            local_reference=f"download://phase1/{candidate.source_key}/artifact",
            original_filename=f"{candidate.source_key}.discovery",
        )
        for index, candidate in enumerate(active_candidates.candidates, start=1)
    )
    return SourceDownloadArtifactResult(artifacts=artifacts)


def validate_source_download_artifact(
    artifact: SourceDownloadArtifact,
) -> SourceDownloadArtifactValidationResult:
    """Validate download artifact metadata without touching external systems."""

    issues: list[SourceDownloadArtifactValidationIssue] = []

    _validate_required_text(
        artifact.source_family,
        "source_family",
        "SOURCE_DOWNLOAD_ARTIFACT_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        artifact.source_key,
        "source_key",
        "SOURCE_DOWNLOAD_ARTIFACT_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        artifact.candidate_id,
        "candidate_id",
        "SOURCE_DOWNLOAD_ARTIFACT_MISSING_CANDIDATE_ID",
        "candidate_id must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        artifact.artifact_id,
        "artifact_id",
        "SOURCE_DOWNLOAD_ARTIFACT_MISSING_ARTIFACT_ID",
        "artifact_id must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        artifact.artifact_kind,
        "artifact_kind",
        "SOURCE_DOWNLOAD_ARTIFACT_MISSING_ARTIFACT_KIND",
        "artifact_kind must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        artifact.source_reference_uri,
        "source_reference_uri",
        "SOURCE_DOWNLOAD_ARTIFACT_MISSING_SOURCE_REFERENCE_URI",
        "source_reference_uri must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        artifact.local_reference,
        "local_reference",
        "SOURCE_DOWNLOAD_ARTIFACT_MISSING_LOCAL_REFERENCE",
        "local_reference must be a non-empty string.",
        issues,
    )
    _validate_optional_text(
        artifact.original_filename,
        "original_filename",
        "SOURCE_DOWNLOAD_ARTIFACT_BLANK_ORIGINAL_FILENAME",
        "original_filename must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        artifact.display_name,
        "display_name",
        "SOURCE_DOWNLOAD_ARTIFACT_BLANK_DISPLAY_NAME",
        "display_name must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        artifact.content_type,
        "content_type",
        "SOURCE_DOWNLOAD_ARTIFACT_BLANK_CONTENT_TYPE",
        "content_type must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        artifact.extension,
        "extension",
        "SOURCE_DOWNLOAD_ARTIFACT_BLANK_EXTENSION",
        "extension must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        artifact.checksum_sha256,
        "checksum_sha256",
        "SOURCE_DOWNLOAD_ARTIFACT_BLANK_CHECKSUM_SHA256",
        "checksum_sha256 must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        artifact.version_label,
        "version_label",
        "SOURCE_DOWNLOAD_ARTIFACT_BLANK_VERSION_LABEL",
        "version_label must be non-empty when provided.",
        issues,
    )
    _validate_optional_positive_int(
        artifact.size_bytes,
        "size_bytes",
        "SOURCE_DOWNLOAD_ARTIFACT_INVALID_SIZE_BYTES",
        "size_bytes must be a positive integer when provided.",
        issues,
    )
    _validate_optional_positive_int(
        artifact.document_year,
        "document_year",
        "SOURCE_DOWNLOAD_ARTIFACT_INVALID_DOCUMENT_YEAR",
        "document_year must be a positive integer when provided.",
        issues,
    )
    _validate_optional_positive_int(
        artifact.reporting_year,
        "reporting_year",
        "SOURCE_DOWNLOAD_ARTIFACT_INVALID_REPORTING_YEAR",
        "reporting_year must be a positive integer when provided.",
        issues,
    )
    _validate_artifact_registry_alignment(artifact, issues)

    return SourceDownloadArtifactValidationResult(issues=tuple(issues))


def validate_source_download_artifact_result(
    result: SourceDownloadArtifactResult,
) -> SourceDownloadArtifactValidationResult:
    """Validate download artifact batches without runtime side effects."""

    issues: list[SourceDownloadArtifactValidationIssue] = []
    for position, artifact in enumerate(result.artifacts, start=1):
        for issue in validate_source_download_artifact(artifact).issues:
            issues.append(
                SourceDownloadArtifactValidationIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=f"artifacts[{position}].{issue.field_name}",
                )
            )

    return SourceDownloadArtifactValidationResult(issues=tuple(issues))


def _validate_artifact_registry_alignment(
    artifact: SourceDownloadArtifact,
    issues: list[SourceDownloadArtifactValidationIssue],
) -> None:
    descriptor = _descriptor_by_source_key(artifact.source_key)
    if descriptor is None:
        issues.append(
            SourceDownloadArtifactValidationIssue(
                code="SOURCE_DOWNLOAD_ARTIFACT_UNKNOWN_SOURCE_KEY",
                message="source_key must match a registered Phase 1 source.",
                field_name="source_key",
            )
        )
        return

    if artifact.source_family != descriptor.source_family:
        issues.append(
            SourceDownloadArtifactValidationIssue(
                code="SOURCE_DOWNLOAD_ARTIFACT_SOURCE_FAMILY_MISMATCH",
                message="source_family must match the registered source family.",
                field_name="source_family",
            )
        )
    if artifact.artifact_kind != descriptor.expected_format:
        issues.append(
            SourceDownloadArtifactValidationIssue(
                code="SOURCE_DOWNLOAD_ARTIFACT_KIND_MISMATCH",
                message="artifact_kind must match the registered expected format.",
                field_name="artifact_kind",
            )
        )


def _descriptor_by_source_key(source_key: str) -> object | None:
    for descriptor in create_default_source_acquisition_registry():
        if descriptor.source_id == source_key:
            return descriptor
    return None


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[SourceDownloadArtifactValidationIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            SourceDownloadArtifactValidationIssue(
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
    issues: list[SourceDownloadArtifactValidationIssue],
) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        issues.append(
            SourceDownloadArtifactValidationIssue(
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
    issues: list[SourceDownloadArtifactValidationIssue],
) -> None:
    if value is not None and (not isinstance(value, int) or value <= 0):
        issues.append(
            SourceDownloadArtifactValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )
