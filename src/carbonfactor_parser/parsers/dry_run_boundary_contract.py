"""Runtime-passive parser dry-run execution boundary contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.parsers.adapter_registry_contract import (
    Phase1ParserAdapterRegistry,
)
from carbonfactor_parser.parsers.parser_adapter_readiness_report_contract import (
    ParserAdapterReadinessReportEntry,
    build_phase1_parser_adapter_readiness_report,
)
from carbonfactor_parser.parsers.parser_run_contract import (
    ParserRunRequest,
    validate_parser_run_request,
)
from carbonfactor_parser.parsers.validation_issue_contract import (
    ParserValidationIssue,
    ParserValidationIssueSeverity,
    create_parser_validation_issue,
)


class ParserDryRunBoundaryStatus(str, Enum):
    """Deterministic parser dry-run boundary status values."""

    PLANNED = "planned"
    STRUCTURALLY_INVALID = "structurally_invalid"
    ADAPTER_UNREGISTERED = "adapter_unregistered"


@dataclass(frozen=True)
class ParserDryRunEligibility:
    """Readiness metadata used by the parser dry-run boundary."""

    source_family: str
    source_key: str
    parser_key: str
    readiness: str
    execution_mode: str
    supports_parser_execution: bool
    supports_file_reads: bool
    supports_content_inspection: bool
    is_structurally_eligible: bool


@dataclass(frozen=True)
class ParserDryRunSummary:
    """Deterministic metadata-only parser dry-run counts."""

    artifact_count: int
    issue_count: int
    info_count: int
    warning_count: int
    error_count: int


@dataclass(frozen=True)
class ParserDryRunBoundaryResult:
    """Metadata-only parser dry-run boundary result."""

    source_family: str
    source_key: str
    parser_key: str
    request: ParserRunRequest
    status: ParserDryRunBoundaryStatus
    eligibility: ParserDryRunEligibility
    issues: tuple[ParserValidationIssue, ...]
    summary: ParserDryRunSummary
    run_id: str | None = None
    correlation_id: str | None = None


@dataclass(frozen=True)
class ParserDryRunBoundaryValidationIssue:
    """Validation issue for parser dry-run boundary metadata."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class ParserDryRunBoundaryValidationResult:
    """Structural validation result for parser dry-run boundary metadata."""

    issues: tuple[ParserDryRunBoundaryValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def plan_parser_dry_run_boundary(
    request: ParserRunRequest,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> ParserDryRunBoundaryResult:
    """Plan parser dry-run eligibility without executing parser code."""

    readiness_entry = _readiness_entry_for_request(request, registry)
    request_validation = validate_parser_run_request(request, registry)
    issues = (
        _validation_issues_from_request_validation(
            request,
            request_validation.issues,
            registry,
        )
        if readiness_entry is not None
        else ()
    )
    status = _status_for_request(readiness_entry, request_validation.is_valid)
    eligibility = _eligibility_from_request(
        request,
        readiness_entry,
        request_validation.is_valid,
    )

    return ParserDryRunBoundaryResult(
        source_family=request.source_family,
        source_key=request.source_key,
        parser_key=request.parser_key,
        request=request,
        status=status,
        eligibility=eligibility,
        issues=issues,
        summary=_summary(request.artifacts, issues),
        run_id=request.run_id,
        correlation_id=request.correlation_id,
    )


def validate_parser_dry_run_boundary_result(
    result: ParserDryRunBoundaryResult,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> ParserDryRunBoundaryValidationResult:
    """Validate dry-run boundary metadata without executing parsers."""

    issues: list[ParserDryRunBoundaryValidationIssue] = []

    _validate_required_text(
        result.source_family,
        "result.source_family",
        "PARSER_DRY_RUN_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        result.source_key,
        "result.source_key",
        "PARSER_DRY_RUN_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        result.parser_key,
        "result.parser_key",
        "PARSER_DRY_RUN_MISSING_PARSER_KEY",
        "parser_key must be a non-empty string.",
        issues,
    )
    if not isinstance(result.status, ParserDryRunBoundaryStatus):
        issues.append(
            ParserDryRunBoundaryValidationIssue(
                code="PARSER_DRY_RUN_INVALID_STATUS",
                message="status must be a ParserDryRunBoundaryStatus value.",
                field_name="result.status",
            )
        )
    _validate_identity_alignment(result, issues, registry)
    _validate_request_alignment(result, issues)
    _validate_eligibility(result, issues)
    _validate_issue_alignment(result, issues)
    _validate_summary(result, issues)

    return ParserDryRunBoundaryValidationResult(issues=tuple(issues))


def _readiness_entry_for_request(
    request: ParserRunRequest,
    registry: Phase1ParserAdapterRegistry | None,
) -> ParserAdapterReadinessReportEntry | None:
    report = build_phase1_parser_adapter_readiness_report(registry)
    for entry in report.entries:
        if entry.source_family == request.source_family:
            return entry
    return None


def _status_for_request(
    readiness_entry: ParserAdapterReadinessReportEntry | None,
    request_is_valid: bool,
) -> ParserDryRunBoundaryStatus:
    if readiness_entry is None:
        return ParserDryRunBoundaryStatus.ADAPTER_UNREGISTERED
    if not request_is_valid:
        return ParserDryRunBoundaryStatus.STRUCTURALLY_INVALID
    return ParserDryRunBoundaryStatus.PLANNED


def _eligibility_from_request(
    request: ParserRunRequest,
    readiness_entry: ParserAdapterReadinessReportEntry | None,
    request_is_valid: bool,
) -> ParserDryRunEligibility:
    if readiness_entry is None:
        return ParserDryRunEligibility(
            source_family=request.source_family,
            source_key=request.source_key,
            parser_key=request.parser_key,
            readiness="unregistered",
            execution_mode="unregistered",
            supports_parser_execution=False,
            supports_file_reads=False,
            supports_content_inspection=False,
            is_structurally_eligible=False,
        )

    return ParserDryRunEligibility(
        source_family=readiness_entry.source_family,
        source_key=readiness_entry.source_key,
        parser_key=readiness_entry.parser_key,
        readiness=readiness_entry.readiness,
        execution_mode=readiness_entry.execution_mode,
        supports_parser_execution=(
            readiness_entry.capability.supports_parser_execution
        ),
        supports_file_reads=readiness_entry.capability.supports_file_reads,
        supports_content_inspection=(
            readiness_entry.capability.supports_content_inspection
        ),
        is_structurally_eligible=request_is_valid,
    )


def _validation_issues_from_request_validation(
    request: ParserRunRequest,
    validation_issues: tuple[object, ...],
    registry: Phase1ParserAdapterRegistry | None,
) -> tuple[ParserValidationIssue, ...]:
    artifact_reference = (
        request.artifacts[0].artifact_reference if request.artifacts else None
    )
    return tuple(
        create_parser_validation_issue(
            source_family=request.source_family,
            severity=ParserValidationIssueSeverity.ERROR,
            code=issue.code,
            message=issue.message,
            artifact_reference=artifact_reference,
            context={"field_name": issue.field_name},
            registry=registry,
        )
        for issue in validation_issues
    )


def _summary(
    artifacts: tuple[object, ...],
    issues: tuple[ParserValidationIssue, ...],
) -> ParserDryRunSummary:
    info_count = sum(
        issue.severity is ParserValidationIssueSeverity.INFO for issue in issues
    )
    warning_count = sum(
        issue.severity is ParserValidationIssueSeverity.WARNING for issue in issues
    )
    error_count = sum(
        issue.severity is ParserValidationIssueSeverity.ERROR for issue in issues
    )
    return ParserDryRunSummary(
        artifact_count=len(artifacts),
        issue_count=len(issues),
        info_count=info_count,
        warning_count=warning_count,
        error_count=error_count,
    )


def _validate_identity_alignment(
    result: ParserDryRunBoundaryResult,
    issues: list[ParserDryRunBoundaryValidationIssue],
    registry: Phase1ParserAdapterRegistry | None,
) -> None:
    readiness_entry = _readiness_entry_for_request(result.request, registry)
    if readiness_entry is None:
        issues.append(
            ParserDryRunBoundaryValidationIssue(
                code="PARSER_DRY_RUN_UNKNOWN_SOURCE_FAMILY",
                message="source_family must match a registered Phase 1 parser adapter.",
                field_name="result.source_family",
            )
        )
        return

    if result.source_key != readiness_entry.source_key:
        issues.append(
            ParserDryRunBoundaryValidationIssue(
                code="PARSER_DRY_RUN_SOURCE_KEY_MISMATCH",
                message="source_key must match the registered source_family.",
                field_name="result.source_key",
            )
        )
    if result.parser_key != readiness_entry.parser_key:
        issues.append(
            ParserDryRunBoundaryValidationIssue(
                code="PARSER_DRY_RUN_PARSER_KEY_MISMATCH",
                message="parser_key must match the registered parser adapter.",
                field_name="result.parser_key",
            )
        )


def _validate_request_alignment(
    result: ParserDryRunBoundaryResult,
    issues: list[ParserDryRunBoundaryValidationIssue],
) -> None:
    if result.request.source_family != result.source_family:
        issues.append(
            ParserDryRunBoundaryValidationIssue(
                code="PARSER_DRY_RUN_REQUEST_SOURCE_FAMILY_MISMATCH",
                message="request source_family must match result source_family.",
                field_name="result.request.source_family",
            )
        )
    if result.request.source_key != result.source_key:
        issues.append(
            ParserDryRunBoundaryValidationIssue(
                code="PARSER_DRY_RUN_REQUEST_SOURCE_KEY_MISMATCH",
                message="request source_key must match result source_key.",
                field_name="result.request.source_key",
            )
        )
    if result.request.parser_key != result.parser_key:
        issues.append(
            ParserDryRunBoundaryValidationIssue(
                code="PARSER_DRY_RUN_REQUEST_PARSER_KEY_MISMATCH",
                message="request parser_key must match result parser_key.",
                field_name="result.request.parser_key",
            )
        )


def _validate_eligibility(
    result: ParserDryRunBoundaryResult,
    issues: list[ParserDryRunBoundaryValidationIssue],
) -> None:
    eligibility = result.eligibility
    for field_name, value in (
        ("source_family", eligibility.source_family),
        ("source_key", eligibility.source_key),
        ("parser_key", eligibility.parser_key),
        ("readiness", eligibility.readiness),
        ("execution_mode", eligibility.execution_mode),
    ):
        _validate_required_text(
            value,
            f"result.eligibility.{field_name}",
            "PARSER_DRY_RUN_INVALID_ELIGIBILITY",
            f"eligibility {field_name} must be a non-empty string.",
            issues,
        )
    if eligibility.source_family != result.source_family:
        issues.append(
            ParserDryRunBoundaryValidationIssue(
                code="PARSER_DRY_RUN_ELIGIBILITY_SOURCE_FAMILY_MISMATCH",
                message="eligibility source_family must match result source_family.",
                field_name="result.eligibility.source_family",
            )
        )
    if eligibility.source_key != result.source_key:
        issues.append(
            ParserDryRunBoundaryValidationIssue(
                code="PARSER_DRY_RUN_ELIGIBILITY_SOURCE_KEY_MISMATCH",
                message="eligibility source_key must match result source_key.",
                field_name="result.eligibility.source_key",
            )
        )
    if eligibility.parser_key != result.parser_key:
        issues.append(
            ParserDryRunBoundaryValidationIssue(
                code="PARSER_DRY_RUN_ELIGIBILITY_PARSER_KEY_MISMATCH",
                message="eligibility parser_key must match result parser_key.",
                field_name="result.eligibility.parser_key",
            )
        )


def _validate_issue_alignment(
    result: ParserDryRunBoundaryResult,
    issues: list[ParserDryRunBoundaryValidationIssue],
) -> None:
    for position, issue in enumerate(result.issues, start=1):
        if issue.source_family != result.source_family:
            issues.append(
                ParserDryRunBoundaryValidationIssue(
                    code="PARSER_DRY_RUN_ISSUE_SOURCE_FAMILY_MISMATCH",
                    message="issue source_family must match result source_family.",
                    field_name=f"result.issues[{position}].source_family",
                )
            )
        if issue.source_key != result.source_key:
            issues.append(
                ParserDryRunBoundaryValidationIssue(
                    code="PARSER_DRY_RUN_ISSUE_SOURCE_KEY_MISMATCH",
                    message="issue source_key must match result source_key.",
                    field_name=f"result.issues[{position}].source_key",
                )
            )
        if issue.parser_key != result.parser_key:
            issues.append(
                ParserDryRunBoundaryValidationIssue(
                    code="PARSER_DRY_RUN_ISSUE_PARSER_KEY_MISMATCH",
                    message="issue parser_key must match result parser_key.",
                    field_name=f"result.issues[{position}].parser_key",
                )
            )


def _validate_summary(
    result: ParserDryRunBoundaryResult,
    issues: list[ParserDryRunBoundaryValidationIssue],
) -> None:
    expected = _summary(result.request.artifacts, result.issues)
    for field_name in (
        "artifact_count",
        "issue_count",
        "info_count",
        "warning_count",
        "error_count",
    ):
        if getattr(result.summary, field_name) < 0:
            issues.append(
                ParserDryRunBoundaryValidationIssue(
                    code="PARSER_DRY_RUN_NEGATIVE_SUMMARY_COUNT",
                    message="summary counts must be non-negative.",
                    field_name=f"result.summary.{field_name}",
                )
            )
        if getattr(result.summary, field_name) != getattr(expected, field_name):
            issues.append(
                ParserDryRunBoundaryValidationIssue(
                    code="PARSER_DRY_RUN_SUMMARY_COUNT_MISMATCH",
                    message="summary counts must match dry-run metadata.",
                    field_name=f"result.summary.{field_name}",
                )
            )


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[ParserDryRunBoundaryValidationIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            ParserDryRunBoundaryValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )
