"""Runtime-passive source acquisition run metadata contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.source_acquisition.discovery_candidate_contract import (
    SourceDiscoveryCandidate,
    SourceDiscoveryCandidateResult,
    create_phase1_source_discovery_candidates,
    validate_source_discovery_candidate,
)
from carbonfactor_parser.source_acquisition.download_artifact_contract import (
    SourceDownloadArtifact,
    SourceDownloadArtifactResult,
    create_phase1_source_download_artifacts,
    validate_source_download_artifact,
)
from carbonfactor_parser.source_acquisition.registry import (
    create_default_source_acquisition_registry,
)


class SourceAcquisitionRunStatus(str, Enum):
    """Runtime-passive source acquisition run status values."""

    DECLARED = "declared"
    COMPLETED = "completed"
    COMPLETED_WITH_ISSUES = "completed_with_issues"
    FAILED = "failed"


@dataclass(frozen=True)
class SourceAcquisitionRunRequest:
    """Metadata-only source acquisition run request."""

    source_family: str
    source_key: str
    candidates: tuple[SourceDiscoveryCandidate, ...]
    run_id: str | None = None
    requested_document_year: int | None = None
    requested_reporting_year: int | None = None
    version_label: str | None = None


@dataclass(frozen=True)
class SourceAcquisitionRunSummary:
    """Deterministic metadata-only source acquisition run counts."""

    candidate_count: int
    artifact_count: int
    issue_count: int
    info_count: int
    warning_count: int
    error_count: int


@dataclass(frozen=True)
class SourceAcquisitionRunIssue:
    """Metadata-only source acquisition run issue."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class SourceAcquisitionRunResult:
    """Metadata-only source acquisition run result."""

    source_family: str
    source_key: str
    status: SourceAcquisitionRunStatus
    candidates: tuple[SourceDiscoveryCandidate, ...]
    artifacts: tuple[SourceDownloadArtifact, ...]
    issues: tuple[SourceAcquisitionRunIssue, ...]
    summary: SourceAcquisitionRunSummary
    run_id: str | None = None
    version_label: str | None = None

    @property
    def candidate_ids(self) -> tuple[str, ...]:
        return tuple(candidate.candidate_id for candidate in self.candidates)

    @property
    def artifact_ids(self) -> tuple[str, ...]:
        return tuple(artifact.artifact_id for artifact in self.artifacts)


@dataclass(frozen=True)
class SourceAcquisitionRunValidationResult:
    """Structural validation result for source acquisition run metadata."""

    issues: tuple[SourceAcquisitionRunIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def create_source_acquisition_run_request(
    *,
    source_key: str,
    candidates: SourceDiscoveryCandidateResult | None = None,
    run_id: str | None = None,
    requested_document_year: int | None = None,
    requested_reporting_year: int | None = None,
    version_label: str | None = None,
) -> SourceAcquisitionRunRequest:
    """Create metadata-only acquisition run request for one Phase 1 source."""

    descriptor = _descriptor_by_source_key(source_key)
    if descriptor is None:
        raise ValueError("source_key is not registered for a Phase 1 source.")

    active_candidates = (
        create_phase1_source_discovery_candidates()
        if candidates is None
        else candidates
    )
    selected_candidates = tuple(
        candidate
        for candidate in active_candidates.candidates
        if candidate.source_key == source_key
    )

    return SourceAcquisitionRunRequest(
        source_family=descriptor.source_family,
        source_key=descriptor.source_id,
        candidates=selected_candidates,
        run_id=run_id,
        requested_document_year=requested_document_year,
        requested_reporting_year=requested_reporting_year,
        version_label=version_label,
    )


def create_source_acquisition_run_result(
    request: SourceAcquisitionRunRequest,
    *,
    status: SourceAcquisitionRunStatus = SourceAcquisitionRunStatus.DECLARED,
    artifacts: SourceDownloadArtifactResult | None = None,
    issues: tuple[SourceAcquisitionRunIssue, ...] = (),
) -> SourceAcquisitionRunResult:
    """Create metadata-only acquisition run result from request metadata."""

    active_artifacts = (
        create_phase1_source_download_artifacts(
            SourceDiscoveryCandidateResult(candidates=request.candidates),
        )
        if artifacts is None
        else artifacts
    )

    return SourceAcquisitionRunResult(
        source_family=request.source_family,
        source_key=request.source_key,
        status=status,
        candidates=request.candidates,
        artifacts=active_artifacts.artifacts,
        issues=issues,
        summary=_create_summary(
            candidates=request.candidates,
            artifacts=active_artifacts.artifacts,
            issues=issues,
        ),
        run_id=request.run_id,
        version_label=request.version_label,
    )


def create_phase1_source_acquisition_run_requests(
    candidates: SourceDiscoveryCandidateResult | None = None,
) -> tuple[SourceAcquisitionRunRequest, ...]:
    """Create deterministic metadata-only acquisition requests for Phase 1."""

    active_candidates = (
        create_phase1_source_discovery_candidates()
        if candidates is None
        else candidates
    )
    return tuple(
        create_source_acquisition_run_request(
            source_key=descriptor.source_id,
            candidates=active_candidates,
        )
        for descriptor in create_default_source_acquisition_registry()
    )


def create_phase1_source_acquisition_run_results(
    candidates: SourceDiscoveryCandidateResult | None = None,
) -> tuple[SourceAcquisitionRunResult, ...]:
    """Create deterministic metadata-only acquisition results for Phase 1."""

    return tuple(
        create_source_acquisition_run_result(request)
        for request in create_phase1_source_acquisition_run_requests(candidates)
    )


def validate_source_acquisition_run_request(
    request: SourceAcquisitionRunRequest,
) -> SourceAcquisitionRunValidationResult:
    """Validate acquisition run request metadata without runtime side effects."""

    issues: list[SourceAcquisitionRunIssue] = []

    _validate_required_text(
        request.source_family,
        "source_family",
        "SOURCE_ACQUISITION_RUN_REQUEST_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.source_key,
        "source_key",
        "SOURCE_ACQUISITION_RUN_REQUEST_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_optional_text(
        request.run_id,
        "run_id",
        "SOURCE_ACQUISITION_RUN_REQUEST_BLANK_RUN_ID",
        "run_id must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        request.version_label,
        "version_label",
        "SOURCE_ACQUISITION_RUN_REQUEST_BLANK_VERSION_LABEL",
        "version_label must be non-empty when provided.",
        issues,
    )
    _validate_optional_positive_int(
        request.requested_document_year,
        "requested_document_year",
        "SOURCE_ACQUISITION_RUN_REQUEST_INVALID_DOCUMENT_YEAR",
        "requested_document_year must be a positive integer when provided.",
        issues,
    )
    _validate_optional_positive_int(
        request.requested_reporting_year,
        "requested_reporting_year",
        "SOURCE_ACQUISITION_RUN_REQUEST_INVALID_REPORTING_YEAR",
        "requested_reporting_year must be a positive integer when provided.",
        issues,
    )
    _validate_registry_alignment(
        source_family=request.source_family,
        source_key=request.source_key,
        field_prefix="",
        missing_code="SOURCE_ACQUISITION_RUN_REQUEST_UNKNOWN_SOURCE_KEY",
        mismatch_code="SOURCE_ACQUISITION_RUN_REQUEST_SOURCE_FAMILY_MISMATCH",
        issues=issues,
    )
    _validate_request_candidates(request, issues)

    return SourceAcquisitionRunValidationResult(issues=tuple(issues))


def validate_source_acquisition_run_result(
    result: SourceAcquisitionRunResult,
) -> SourceAcquisitionRunValidationResult:
    """Validate acquisition run result metadata without runtime side effects."""

    issues: list[SourceAcquisitionRunIssue] = []

    _validate_required_text(
        result.source_family,
        "source_family",
        "SOURCE_ACQUISITION_RUN_RESULT_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        result.source_key,
        "source_key",
        "SOURCE_ACQUISITION_RUN_RESULT_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_optional_text(
        result.run_id,
        "run_id",
        "SOURCE_ACQUISITION_RUN_RESULT_BLANK_RUN_ID",
        "run_id must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        result.version_label,
        "version_label",
        "SOURCE_ACQUISITION_RUN_RESULT_BLANK_VERSION_LABEL",
        "version_label must be non-empty when provided.",
        issues,
    )
    if not isinstance(result.status, SourceAcquisitionRunStatus):
        issues.append(
            SourceAcquisitionRunIssue(
                code="SOURCE_ACQUISITION_RUN_RESULT_INVALID_STATUS",
                message="status must be a defined source acquisition run status.",
                field_name="status",
            )
        )
    _validate_registry_alignment(
        source_family=result.source_family,
        source_key=result.source_key,
        field_prefix="",
        missing_code="SOURCE_ACQUISITION_RUN_RESULT_UNKNOWN_SOURCE_KEY",
        mismatch_code="SOURCE_ACQUISITION_RUN_RESULT_SOURCE_FAMILY_MISMATCH",
        issues=issues,
    )
    _validate_result_candidates(result, issues)
    _validate_result_artifacts(result, issues)
    _validate_result_issues(result.issues, issues)
    _validate_summary(result, issues)

    return SourceAcquisitionRunValidationResult(issues=tuple(issues))


def _create_summary(
    *,
    candidates: tuple[SourceDiscoveryCandidate, ...],
    artifacts: tuple[SourceDownloadArtifact, ...],
    issues: tuple[SourceAcquisitionRunIssue, ...],
) -> SourceAcquisitionRunSummary:
    return SourceAcquisitionRunSummary(
        candidate_count=len(candidates),
        artifact_count=len(artifacts),
        issue_count=len(issues),
        info_count=sum(1 for issue in issues if issue.severity == "info"),
        warning_count=sum(1 for issue in issues if issue.severity == "warning"),
        error_count=sum(1 for issue in issues if issue.severity == "error"),
    )


def _validate_request_candidates(
    request: SourceAcquisitionRunRequest,
    issues: list[SourceAcquisitionRunIssue],
) -> None:
    if not request.candidates:
        issues.append(
            SourceAcquisitionRunIssue(
                code="SOURCE_ACQUISITION_RUN_REQUEST_MISSING_CANDIDATES",
                message="candidates must include at least one discovery candidate.",
                field_name="candidates",
            )
        )

    for position, candidate in enumerate(request.candidates, start=1):
        _append_candidate_validation_issues(candidate, f"candidates[{position}]", issues)
        _validate_candidate_alignment(
            candidate,
            source_family=request.source_family,
            source_key=request.source_key,
            field_prefix=f"candidates[{position}]",
            family_code=(
                "SOURCE_ACQUISITION_RUN_REQUEST_CANDIDATE_SOURCE_FAMILY_MISMATCH"
            ),
            key_code="SOURCE_ACQUISITION_RUN_REQUEST_CANDIDATE_SOURCE_KEY_MISMATCH",
            issues=issues,
        )


def _validate_result_candidates(
    result: SourceAcquisitionRunResult,
    issues: list[SourceAcquisitionRunIssue],
) -> None:
    for position, candidate in enumerate(result.candidates, start=1):
        _append_candidate_validation_issues(candidate, f"candidates[{position}]", issues)
        _validate_candidate_alignment(
            candidate,
            source_family=result.source_family,
            source_key=result.source_key,
            field_prefix=f"candidates[{position}]",
            family_code=(
                "SOURCE_ACQUISITION_RUN_RESULT_CANDIDATE_SOURCE_FAMILY_MISMATCH"
            ),
            key_code="SOURCE_ACQUISITION_RUN_RESULT_CANDIDATE_SOURCE_KEY_MISMATCH",
            issues=issues,
        )


def _validate_result_artifacts(
    result: SourceAcquisitionRunResult,
    issues: list[SourceAcquisitionRunIssue],
) -> None:
    candidate_ids = set(result.candidate_ids)
    for position, artifact in enumerate(result.artifacts, start=1):
        _append_artifact_validation_issues(artifact, f"artifacts[{position}]", issues)
        if artifact.source_family != result.source_family:
            issues.append(
                SourceAcquisitionRunIssue(
                    code=(
                        "SOURCE_ACQUISITION_RUN_RESULT_ARTIFACT_SOURCE_FAMILY_MISMATCH"
                    ),
                    message="artifact source_family must match the run source_family.",
                    field_name=f"artifacts[{position}].source_family",
                )
            )
        if artifact.source_key != result.source_key:
            issues.append(
                SourceAcquisitionRunIssue(
                    code="SOURCE_ACQUISITION_RUN_RESULT_ARTIFACT_SOURCE_KEY_MISMATCH",
                    message="artifact source_key must match the run source_key.",
                    field_name=f"artifacts[{position}].source_key",
                )
            )
        if artifact.candidate_id not in candidate_ids:
            issues.append(
                SourceAcquisitionRunIssue(
                    code="SOURCE_ACQUISITION_RUN_RESULT_ARTIFACT_CANDIDATE_ID_MISMATCH",
                    message="artifact candidate_id must match a run candidate.",
                    field_name=f"artifacts[{position}].candidate_id",
                )
            )


def _validate_result_issues(
    run_issues: tuple[SourceAcquisitionRunIssue, ...],
    issues: list[SourceAcquisitionRunIssue],
) -> None:
    for position, run_issue in enumerate(run_issues, start=1):
        _validate_required_text(
            run_issue.code,
            f"issues[{position}].code",
            "SOURCE_ACQUISITION_RUN_RESULT_ISSUE_MISSING_CODE",
            "issue code must be a non-empty string.",
            issues,
        )
        _validate_required_text(
            run_issue.message,
            f"issues[{position}].message",
            "SOURCE_ACQUISITION_RUN_RESULT_ISSUE_MISSING_MESSAGE",
            "issue message must be a non-empty string.",
            issues,
        )
        _validate_required_text(
            run_issue.field_name,
            f"issues[{position}].field_name",
            "SOURCE_ACQUISITION_RUN_RESULT_ISSUE_MISSING_FIELD_NAME",
            "issue field_name must be a non-empty string.",
            issues,
        )
        if run_issue.severity not in ("info", "warning", "error"):
            issues.append(
                SourceAcquisitionRunIssue(
                    code="SOURCE_ACQUISITION_RUN_RESULT_ISSUE_INVALID_SEVERITY",
                    message="issue severity must be info, warning, or error.",
                    field_name=f"issues[{position}].severity",
                )
            )


def _validate_summary(
    result: SourceAcquisitionRunResult,
    issues: list[SourceAcquisitionRunIssue],
) -> None:
    summary = result.summary
    expected_summary = _create_summary(
        candidates=result.candidates,
        artifacts=result.artifacts,
        issues=result.issues,
    )

    for field_name, value in (
        ("summary.candidate_count", summary.candidate_count),
        ("summary.artifact_count", summary.artifact_count),
        ("summary.issue_count", summary.issue_count),
        ("summary.info_count", summary.info_count),
        ("summary.warning_count", summary.warning_count),
        ("summary.error_count", summary.error_count),
    ):
        if not isinstance(value, int) or value < 0:
            issues.append(
                SourceAcquisitionRunIssue(
                    code="SOURCE_ACQUISITION_RUN_RESULT_NEGATIVE_SUMMARY_COUNT",
                    message="summary counts must be non-negative integers.",
                    field_name=field_name,
                )
            )

    if summary.candidate_count != expected_summary.candidate_count:
        issues.append(
            SourceAcquisitionRunIssue(
                code="SOURCE_ACQUISITION_RUN_RESULT_SUMMARY_CANDIDATE_COUNT_MISMATCH",
                message="summary candidate_count must match candidate count.",
                field_name="summary.candidate_count",
            )
        )
    if summary.artifact_count != expected_summary.artifact_count:
        issues.append(
            SourceAcquisitionRunIssue(
                code="SOURCE_ACQUISITION_RUN_RESULT_SUMMARY_ARTIFACT_COUNT_MISMATCH",
                message="summary artifact_count must match artifact count.",
                field_name="summary.artifact_count",
            )
        )
    if summary.issue_count != expected_summary.issue_count:
        issues.append(
            SourceAcquisitionRunIssue(
                code="SOURCE_ACQUISITION_RUN_RESULT_SUMMARY_ISSUE_COUNT_MISMATCH",
                message="summary issue_count must match issue count.",
                field_name="summary.issue_count",
            )
        )
    if summary.info_count != expected_summary.info_count:
        issues.append(
            SourceAcquisitionRunIssue(
                code="SOURCE_ACQUISITION_RUN_RESULT_SUMMARY_INFO_COUNT_MISMATCH",
                message="summary info_count must match info issue count.",
                field_name="summary.info_count",
            )
        )
    if summary.warning_count != expected_summary.warning_count:
        issues.append(
            SourceAcquisitionRunIssue(
                code="SOURCE_ACQUISITION_RUN_RESULT_SUMMARY_WARNING_COUNT_MISMATCH",
                message="summary warning_count must match warning issue count.",
                field_name="summary.warning_count",
            )
        )
    if summary.error_count != expected_summary.error_count:
        issues.append(
            SourceAcquisitionRunIssue(
                code="SOURCE_ACQUISITION_RUN_RESULT_SUMMARY_ERROR_COUNT_MISMATCH",
                message="summary error_count must match error issue count.",
                field_name="summary.error_count",
            )
        )


def _append_candidate_validation_issues(
    candidate: SourceDiscoveryCandidate,
    field_prefix: str,
    issues: list[SourceAcquisitionRunIssue],
) -> None:
    for issue in validate_source_discovery_candidate(candidate).issues:
        issues.append(
            SourceAcquisitionRunIssue(
                code=issue.code,
                message=issue.message,
                field_name=f"{field_prefix}.{issue.field_name}",
                severity=issue.severity,
            )
        )


def _append_artifact_validation_issues(
    artifact: SourceDownloadArtifact,
    field_prefix: str,
    issues: list[SourceAcquisitionRunIssue],
) -> None:
    for issue in validate_source_download_artifact(artifact).issues:
        issues.append(
            SourceAcquisitionRunIssue(
                code=issue.code,
                message=issue.message,
                field_name=f"{field_prefix}.{issue.field_name}",
                severity=issue.severity,
            )
        )


def _validate_candidate_alignment(
    candidate: SourceDiscoveryCandidate,
    *,
    source_family: str,
    source_key: str,
    field_prefix: str,
    family_code: str,
    key_code: str,
    issues: list[SourceAcquisitionRunIssue],
) -> None:
    if candidate.source_family != source_family:
        issues.append(
            SourceAcquisitionRunIssue(
                code=family_code,
                message="candidate source_family must match the run source_family.",
                field_name=f"{field_prefix}.source_family",
            )
        )
    if candidate.source_key != source_key:
        issues.append(
            SourceAcquisitionRunIssue(
                code=key_code,
                message="candidate source_key must match the run source_key.",
                field_name=f"{field_prefix}.source_key",
            )
        )


def _validate_registry_alignment(
    *,
    source_family: str,
    source_key: str,
    field_prefix: str,
    missing_code: str,
    mismatch_code: str,
    issues: list[SourceAcquisitionRunIssue],
) -> None:
    descriptor = _descriptor_by_source_key(source_key)
    if descriptor is None:
        issues.append(
            SourceAcquisitionRunIssue(
                code=missing_code,
                message="source_key must match a registered Phase 1 source.",
                field_name=f"{field_prefix}source_key",
            )
        )
        return

    if source_family != descriptor.source_family:
        issues.append(
            SourceAcquisitionRunIssue(
                code=mismatch_code,
                message="source_family must match the registered source family.",
                field_name=f"{field_prefix}source_family",
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
    issues: list[SourceAcquisitionRunIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            SourceAcquisitionRunIssue(
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
    issues: list[SourceAcquisitionRunIssue],
) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        issues.append(
            SourceAcquisitionRunIssue(
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
    issues: list[SourceAcquisitionRunIssue],
) -> None:
    if value is not None and (not isinstance(value, int) or value <= 0):
        issues.append(
            SourceAcquisitionRunIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )
