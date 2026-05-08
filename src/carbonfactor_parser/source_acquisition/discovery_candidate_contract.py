"""Runtime-passive source discovery candidate metadata contract."""

from __future__ import annotations

from dataclasses import dataclass

from carbonfactor_parser.source_acquisition.registry import (
    create_default_source_acquisition_registry,
)


@dataclass(frozen=True)
class SourceDiscoveryCandidate:
    """Metadata-only future source discovery candidate."""

    source_family: str
    source_key: str
    candidate_id: str
    title: str
    reference_uri: str
    artifact_kind: str
    document_year: int | None = None
    reporting_year: int | None = None
    content_type: str | None = None
    extension: str | None = None
    checksum_sha256: str | None = None
    version_label: str | None = None
    discovered_at_label: str | None = None


@dataclass(frozen=True)
class SourceDiscoveryCandidateResult:
    """Deterministic collection of source discovery candidates."""

    candidates: tuple[SourceDiscoveryCandidate, ...]

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)

    @property
    def source_keys(self) -> tuple[str, ...]:
        return tuple(candidate.source_key for candidate in self.candidates)


@dataclass(frozen=True)
class SourceDiscoveryCandidateValidationIssue:
    """Validation issue for source discovery candidate metadata."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class SourceDiscoveryCandidateValidationResult:
    """Structural validation result for source discovery candidate metadata."""

    issues: tuple[SourceDiscoveryCandidateValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def create_phase1_source_discovery_candidates(
) -> SourceDiscoveryCandidateResult:
    """Create deterministic Phase 1 source candidates from descriptor metadata."""

    candidates = tuple(
        SourceDiscoveryCandidate(
            source_family=descriptor.source_family,
            source_key=descriptor.source_id,
            candidate_id=f"phase1_candidate_{index:03d}_{descriptor.source_id}",
            title=descriptor.display_name,
            reference_uri=descriptor.acquisition_url,
            artifact_kind=descriptor.expected_format,
            version_label="phase1_discovery_contract",
            discovered_at_label="runtime_passive_discovery_unavailable",
        )
        for index, descriptor in enumerate(
            create_default_source_acquisition_registry(),
            start=1,
        )
    )
    return SourceDiscoveryCandidateResult(candidates=candidates)


def validate_source_discovery_candidate(
    candidate: SourceDiscoveryCandidate,
) -> SourceDiscoveryCandidateValidationResult:
    """Validate source discovery candidate metadata without dereferencing it."""

    issues: list[SourceDiscoveryCandidateValidationIssue] = []

    _validate_required_text(
        candidate.source_family,
        "source_family",
        "SOURCE_DISCOVERY_CANDIDATE_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        candidate.source_key,
        "source_key",
        "SOURCE_DISCOVERY_CANDIDATE_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        candidate.candidate_id,
        "candidate_id",
        "SOURCE_DISCOVERY_CANDIDATE_MISSING_CANDIDATE_ID",
        "candidate_id must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        candidate.title,
        "title",
        "SOURCE_DISCOVERY_CANDIDATE_MISSING_TITLE",
        "title must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        candidate.reference_uri,
        "reference_uri",
        "SOURCE_DISCOVERY_CANDIDATE_MISSING_REFERENCE_URI",
        "reference_uri must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        candidate.artifact_kind,
        "artifact_kind",
        "SOURCE_DISCOVERY_CANDIDATE_MISSING_ARTIFACT_KIND",
        "artifact_kind must be a non-empty string.",
        issues,
    )
    _validate_optional_text(
        candidate.content_type,
        "content_type",
        "SOURCE_DISCOVERY_CANDIDATE_BLANK_CONTENT_TYPE",
        "content_type must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        candidate.extension,
        "extension",
        "SOURCE_DISCOVERY_CANDIDATE_BLANK_EXTENSION",
        "extension must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        candidate.checksum_sha256,
        "checksum_sha256",
        "SOURCE_DISCOVERY_CANDIDATE_BLANK_CHECKSUM_SHA256",
        "checksum_sha256 must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        candidate.version_label,
        "version_label",
        "SOURCE_DISCOVERY_CANDIDATE_BLANK_VERSION_LABEL",
        "version_label must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        candidate.discovered_at_label,
        "discovered_at_label",
        "SOURCE_DISCOVERY_CANDIDATE_BLANK_DISCOVERED_AT_LABEL",
        "discovered_at_label must be non-empty when provided.",
        issues,
    )
    _validate_optional_positive_int(
        candidate.document_year,
        "document_year",
        "SOURCE_DISCOVERY_CANDIDATE_INVALID_DOCUMENT_YEAR",
        "document_year must be a positive integer when provided.",
        issues,
    )
    _validate_optional_positive_int(
        candidate.reporting_year,
        "reporting_year",
        "SOURCE_DISCOVERY_CANDIDATE_INVALID_REPORTING_YEAR",
        "reporting_year must be a positive integer when provided.",
        issues,
    )
    _validate_candidate_registry_alignment(candidate, issues)

    return SourceDiscoveryCandidateValidationResult(issues=tuple(issues))


def validate_source_discovery_candidate_result(
    result: SourceDiscoveryCandidateResult,
) -> SourceDiscoveryCandidateValidationResult:
    """Validate source discovery candidate batches without runtime side effects."""

    issues: list[SourceDiscoveryCandidateValidationIssue] = []
    for position, candidate in enumerate(result.candidates, start=1):
        for issue in validate_source_discovery_candidate(candidate).issues:
            issues.append(
                SourceDiscoveryCandidateValidationIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=f"candidates[{position}].{issue.field_name}",
                )
            )

    return SourceDiscoveryCandidateValidationResult(issues=tuple(issues))


def _validate_candidate_registry_alignment(
    candidate: SourceDiscoveryCandidate,
    issues: list[SourceDiscoveryCandidateValidationIssue],
) -> None:
    descriptor = _descriptor_by_source_key(candidate.source_key)
    if descriptor is None:
        issues.append(
            SourceDiscoveryCandidateValidationIssue(
                code="SOURCE_DISCOVERY_CANDIDATE_UNKNOWN_SOURCE_KEY",
                message="source_key must match a registered Phase 1 source.",
                field_name="source_key",
            )
        )
        return

    if candidate.source_family != descriptor.source_family:
        issues.append(
            SourceDiscoveryCandidateValidationIssue(
                code="SOURCE_DISCOVERY_CANDIDATE_SOURCE_FAMILY_MISMATCH",
                message="source_family must match the registered source family.",
                field_name="source_family",
            )
        )
    if candidate.artifact_kind != descriptor.expected_format:
        issues.append(
            SourceDiscoveryCandidateValidationIssue(
                code="SOURCE_DISCOVERY_CANDIDATE_ARTIFACT_KIND_MISMATCH",
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
    issues: list[SourceDiscoveryCandidateValidationIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            SourceDiscoveryCandidateValidationIssue(
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
    issues: list[SourceDiscoveryCandidateValidationIssue],
) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        issues.append(
            SourceDiscoveryCandidateValidationIssue(
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
    issues: list[SourceDiscoveryCandidateValidationIssue],
) -> None:
    if value is not None and (not isinstance(value, int) or value <= 0):
        issues.append(
            SourceDiscoveryCandidateValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )
