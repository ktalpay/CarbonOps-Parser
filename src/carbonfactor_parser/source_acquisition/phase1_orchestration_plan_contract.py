"""Runtime-passive Phase 1 source-to-parser orchestration plan contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.parsers.adapter_registry_contract import (
    Phase1ParserAdapterRegistry,
)
from carbonfactor_parser.parsers.dry_run_boundary_contract import (
    ParserDryRunBoundaryResult,
    ParserDryRunBoundaryStatus,
    plan_parser_dry_run_boundary,
    validate_parser_dry_run_boundary_result,
)
from carbonfactor_parser.parsers.parser_run_contract import ParserRunRequest
from carbonfactor_parser.source_acquisition.acquisition_to_parser_plan_contract import (
    AcquisitionToParserPlanResult,
    create_acquisition_to_parser_plan,
    validate_acquisition_to_parser_plan,
)
from carbonfactor_parser.source_acquisition.discovery_candidate_contract import (
    SourceDiscoveryCandidateResult,
)
from carbonfactor_parser.source_acquisition.run_contract import (
    SourceAcquisitionRunRequest,
    SourceAcquisitionRunResult,
    create_phase1_source_acquisition_run_results,
    create_source_acquisition_run_request,
    validate_source_acquisition_run_request,
    validate_source_acquisition_run_result,
)


class Phase1OrchestrationPlanStatus(str, Enum):
    """Deterministic Phase 1 orchestration plan status values."""

    DECLARED = "declared"
    PLANNED = "planned"
    PLANNED_WITH_ISSUES = "planned_with_issues"
    FAILED = "failed"


@dataclass(frozen=True)
class Phase1OrchestrationPlanSummary:
    """Deterministic metadata-only orchestration plan counts."""

    acquisition_candidate_count: int
    acquisition_artifact_count: int
    parser_plan_artifact_count: int
    parser_input_artifact_count: int
    parser_run_request_count: int
    dry_run_boundary_count: int
    dry_run_eligible_count: int
    issue_count: int


@dataclass(frozen=True)
class Phase1OrchestrationPlanIssue:
    """Structural issue for Phase 1 orchestration plan metadata."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class Phase1OrchestrationPlan:
    """Metadata-only Phase 1 source-to-parser orchestration plan."""

    source_family: str
    source_key: str
    status: Phase1OrchestrationPlanStatus
    acquisition_request: SourceAcquisitionRunRequest
    acquisition_result: SourceAcquisitionRunResult
    acquisition_to_parser_plan: AcquisitionToParserPlanResult
    parser_run_requests: tuple[ParserRunRequest, ...]
    dry_run_boundaries: tuple[ParserDryRunBoundaryResult, ...]
    issues: tuple[Phase1OrchestrationPlanIssue, ...]
    summary: Phase1OrchestrationPlanSummary
    plan_id: str | None = None
    correlation_id: str | None = None

    @property
    def parser_keys(self) -> tuple[str, ...]:
        return tuple(request.parser_key for request in self.parser_run_requests)

    @property
    def dry_run_statuses(self) -> tuple[ParserDryRunBoundaryStatus, ...]:
        return tuple(boundary.status for boundary in self.dry_run_boundaries)


@dataclass(frozen=True)
class Phase1OrchestrationPlanValidationResult:
    """Structural validation result for Phase 1 orchestration plans."""

    issues: tuple[Phase1OrchestrationPlanIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def create_phase1_orchestration_plan(
    acquisition_result: SourceAcquisitionRunResult,
    *,
    status: Phase1OrchestrationPlanStatus = Phase1OrchestrationPlanStatus.PLANNED,
    plan_id: str | None = None,
    correlation_id: str | None = None,
    issues: tuple[Phase1OrchestrationPlanIssue, ...] = (),
    registry: Phase1ParserAdapterRegistry | None = None,
) -> Phase1OrchestrationPlan:
    """Create a Phase 1 orchestration plan without executing runtime behavior."""

    acquisition_request = create_source_acquisition_run_request(
        source_key=acquisition_result.source_key,
        candidates=SourceDiscoveryCandidateResult(
            candidates=acquisition_result.candidates,
        ),
        run_id=acquisition_result.run_id,
        version_label=acquisition_result.version_label,
    )
    parser_plan = create_acquisition_to_parser_plan(
        acquisition_result,
        registry=registry,
    )
    parser_run_requests = parser_plan.parser_run_requests
    dry_run_boundaries = tuple(
        plan_parser_dry_run_boundary(request, registry)
        for request in parser_run_requests
    )

    return Phase1OrchestrationPlan(
        source_family=acquisition_result.source_family,
        source_key=acquisition_result.source_key,
        status=status,
        acquisition_request=acquisition_request,
        acquisition_result=acquisition_result,
        acquisition_to_parser_plan=parser_plan,
        parser_run_requests=parser_run_requests,
        dry_run_boundaries=dry_run_boundaries,
        issues=issues,
        summary=_create_summary(
            acquisition_request=acquisition_request,
            acquisition_result=acquisition_result,
            acquisition_to_parser_plan=parser_plan,
            parser_run_requests=parser_run_requests,
            dry_run_boundaries=dry_run_boundaries,
            issues=issues,
        ),
        plan_id=plan_id,
        correlation_id=correlation_id,
    )


def create_phase1_orchestration_plans(
    acquisition_results: tuple[SourceAcquisitionRunResult, ...] | None = None,
    *,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> tuple[Phase1OrchestrationPlan, ...]:
    """Create deterministic Phase 1 orchestration plans for all sources."""

    active_results = (
        create_phase1_source_acquisition_run_results()
        if acquisition_results is None
        else acquisition_results
    )
    return tuple(
        create_phase1_orchestration_plan(result, registry=registry)
        for result in active_results
    )


def validate_phase1_orchestration_plan(
    plan: Phase1OrchestrationPlan,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> Phase1OrchestrationPlanValidationResult:
    """Validate orchestration metadata without executing external behavior."""

    issues: list[Phase1OrchestrationPlanIssue] = []

    _validate_required_text(
        plan.source_family,
        "source_family",
        "PHASE1_ORCHESTRATION_PLAN_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        plan.source_key,
        "source_key",
        "PHASE1_ORCHESTRATION_PLAN_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_optional_text(
        plan.plan_id,
        "plan_id",
        "PHASE1_ORCHESTRATION_PLAN_BLANK_PLAN_ID",
        "plan_id must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        plan.correlation_id,
        "correlation_id",
        "PHASE1_ORCHESTRATION_PLAN_BLANK_CORRELATION_ID",
        "correlation_id must be non-empty when provided.",
        issues,
    )
    if not isinstance(plan.status, Phase1OrchestrationPlanStatus):
        issues.append(
            Phase1OrchestrationPlanIssue(
                code="PHASE1_ORCHESTRATION_PLAN_INVALID_STATUS",
                message="status must be a defined Phase 1 orchestration status.",
                field_name="status",
            )
        )

    _append_acquisition_request_issues(plan, issues)
    _append_acquisition_result_issues(plan, issues)
    _append_parser_plan_issues(plan, issues, registry)
    _append_dry_run_issues(plan, issues, registry)
    _validate_acquisition_alignment(plan, issues)
    _validate_parser_plan_alignment(plan, issues)
    _validate_parser_request_alignment(plan, issues)
    _validate_dry_run_alignment(plan, issues)
    _validate_plan_issues(plan.issues, issues)
    _validate_summary(plan, issues)

    return Phase1OrchestrationPlanValidationResult(issues=tuple(issues))


def validate_phase1_orchestration_plans(
    plans: tuple[Phase1OrchestrationPlan, ...],
    registry: Phase1ParserAdapterRegistry | None = None,
) -> Phase1OrchestrationPlanValidationResult:
    """Validate Phase 1 orchestration plan batches without side effects."""

    issues: list[Phase1OrchestrationPlanIssue] = []
    for position, plan in enumerate(plans, start=1):
        for issue in validate_phase1_orchestration_plan(plan, registry).issues:
            issues.append(
                Phase1OrchestrationPlanIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=f"plans[{position}].{issue.field_name}",
                    severity=issue.severity,
                )
            )
    return Phase1OrchestrationPlanValidationResult(issues=tuple(issues))


def _create_summary(
    *,
    acquisition_request: SourceAcquisitionRunRequest,
    acquisition_result: SourceAcquisitionRunResult,
    acquisition_to_parser_plan: AcquisitionToParserPlanResult,
    parser_run_requests: tuple[ParserRunRequest, ...],
    dry_run_boundaries: tuple[ParserDryRunBoundaryResult, ...],
    issues: tuple[Phase1OrchestrationPlanIssue, ...],
) -> Phase1OrchestrationPlanSummary:
    return Phase1OrchestrationPlanSummary(
        acquisition_candidate_count=len(acquisition_request.candidates),
        acquisition_artifact_count=len(acquisition_result.artifacts),
        parser_plan_artifact_count=(
            acquisition_to_parser_plan.summary.downloaded_artifact_count
        ),
        parser_input_artifact_count=(
            acquisition_to_parser_plan.summary.parser_input_artifact_count
        ),
        parser_run_request_count=len(parser_run_requests),
        dry_run_boundary_count=len(dry_run_boundaries),
        dry_run_eligible_count=sum(
            1
            for boundary in dry_run_boundaries
            if boundary.eligibility.is_structurally_eligible
        ),
        issue_count=len(issues),
    )


def _append_acquisition_request_issues(
    plan: Phase1OrchestrationPlan,
    issues: list[Phase1OrchestrationPlanIssue],
) -> None:
    for issue in validate_source_acquisition_run_request(
        plan.acquisition_request,
    ).issues:
        issues.append(
            Phase1OrchestrationPlanIssue(
                code=issue.code,
                message=issue.message,
                field_name=f"acquisition_request.{issue.field_name}",
                severity=issue.severity,
            )
        )


def _append_acquisition_result_issues(
    plan: Phase1OrchestrationPlan,
    issues: list[Phase1OrchestrationPlanIssue],
) -> None:
    for issue in validate_source_acquisition_run_result(
        plan.acquisition_result,
    ).issues:
        issues.append(
            Phase1OrchestrationPlanIssue(
                code=issue.code,
                message=issue.message,
                field_name=f"acquisition_result.{issue.field_name}",
                severity=issue.severity,
            )
        )


def _append_parser_plan_issues(
    plan: Phase1OrchestrationPlan,
    issues: list[Phase1OrchestrationPlanIssue],
    registry: Phase1ParserAdapterRegistry | None,
) -> None:
    for issue in validate_acquisition_to_parser_plan(
        plan.acquisition_to_parser_plan,
        registry,
    ).issues:
        issues.append(
            Phase1OrchestrationPlanIssue(
                code=issue.code,
                message=issue.message,
                field_name=f"acquisition_to_parser_plan.{issue.field_name}",
                severity=issue.severity,
            )
        )


def _append_dry_run_issues(
    plan: Phase1OrchestrationPlan,
    issues: list[Phase1OrchestrationPlanIssue],
    registry: Phase1ParserAdapterRegistry | None,
) -> None:
    for position, boundary in enumerate(plan.dry_run_boundaries, start=1):
        for issue in validate_parser_dry_run_boundary_result(
            boundary,
            registry,
        ).issues:
            issues.append(
                Phase1OrchestrationPlanIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=f"dry_run_boundaries[{position}].{issue.field_name}",
                    severity=issue.severity,
                )
            )


def _validate_acquisition_alignment(
    plan: Phase1OrchestrationPlan,
    issues: list[Phase1OrchestrationPlanIssue],
) -> None:
    for field_name, value in (
        ("source_family", plan.source_family),
        ("source_key", plan.source_key),
    ):
        if getattr(plan.acquisition_request, field_name) != value:
            issues.append(
                Phase1OrchestrationPlanIssue(
                    code=(
                        "PHASE1_ORCHESTRATION_PLAN_ACQUISITION_REQUEST_SOURCE_MISMATCH"
                    ),
                    message="acquisition request source metadata must match the plan.",
                    field_name=f"acquisition_request.{field_name}",
                )
            )
        if getattr(plan.acquisition_result, field_name) != value:
            issues.append(
                Phase1OrchestrationPlanIssue(
                    code=(
                        "PHASE1_ORCHESTRATION_PLAN_ACQUISITION_RESULT_SOURCE_MISMATCH"
                    ),
                    message="acquisition result source metadata must match the plan.",
                    field_name=f"acquisition_result.{field_name}",
                )
            )


def _validate_parser_plan_alignment(
    plan: Phase1OrchestrationPlan,
    issues: list[Phase1OrchestrationPlanIssue],
) -> None:
    parser_plan = plan.acquisition_to_parser_plan
    if parser_plan.source_family != plan.source_family:
        issues.append(
            Phase1OrchestrationPlanIssue(
                code="PHASE1_ORCHESTRATION_PLAN_PARSER_PLAN_SOURCE_FAMILY_MISMATCH",
                message="acquisition-to-parser plan source_family must match.",
                field_name="acquisition_to_parser_plan.source_family",
            )
        )
    if parser_plan.source_key != plan.source_key:
        issues.append(
            Phase1OrchestrationPlanIssue(
                code="PHASE1_ORCHESTRATION_PLAN_PARSER_PLAN_SOURCE_KEY_MISMATCH",
                message="acquisition-to-parser plan source_key must match.",
                field_name="acquisition_to_parser_plan.source_key",
            )
        )
    if parser_plan.parser_run_requests != plan.parser_run_requests:
        issues.append(
            Phase1OrchestrationPlanIssue(
                code="PHASE1_ORCHESTRATION_PLAN_PARSER_REQUESTS_MISMATCH",
                message="parser run requests must match acquisition-to-parser plan.",
                field_name="parser_run_requests",
            )
        )


def _validate_parser_request_alignment(
    plan: Phase1OrchestrationPlan,
    issues: list[Phase1OrchestrationPlanIssue],
) -> None:
    for position, request in enumerate(plan.parser_run_requests, start=1):
        if request.source_family != plan.source_family:
            issues.append(
                Phase1OrchestrationPlanIssue(
                    code="PHASE1_ORCHESTRATION_PLAN_REQUEST_SOURCE_FAMILY_MISMATCH",
                    message="parser request source_family must match the plan.",
                    field_name=f"parser_run_requests[{position}].source_family",
                )
            )
        if request.source_key != plan.source_key:
            issues.append(
                Phase1OrchestrationPlanIssue(
                    code="PHASE1_ORCHESTRATION_PLAN_REQUEST_SOURCE_KEY_MISMATCH",
                    message="parser request source_key must match the plan.",
                    field_name=f"parser_run_requests[{position}].source_key",
                )
            )


def _validate_dry_run_alignment(
    plan: Phase1OrchestrationPlan,
    issues: list[Phase1OrchestrationPlanIssue],
) -> None:
    dry_run_requests = tuple(boundary.request for boundary in plan.dry_run_boundaries)
    if dry_run_requests != plan.parser_run_requests:
        issues.append(
            Phase1OrchestrationPlanIssue(
                code="PHASE1_ORCHESTRATION_PLAN_DRY_RUN_REQUESTS_MISMATCH",
                message="dry-run boundary requests must match parser run requests.",
                field_name="dry_run_boundaries",
            )
        )

    for position, boundary in enumerate(plan.dry_run_boundaries, start=1):
        if boundary.source_family != plan.source_family:
            issues.append(
                Phase1OrchestrationPlanIssue(
                    code="PHASE1_ORCHESTRATION_PLAN_DRY_RUN_SOURCE_FAMILY_MISMATCH",
                    message="dry-run boundary source_family must match the plan.",
                    field_name=f"dry_run_boundaries[{position}].source_family",
                )
            )
        if boundary.source_key != plan.source_key:
            issues.append(
                Phase1OrchestrationPlanIssue(
                    code="PHASE1_ORCHESTRATION_PLAN_DRY_RUN_SOURCE_KEY_MISMATCH",
                    message="dry-run boundary source_key must match the plan.",
                    field_name=f"dry_run_boundaries[{position}].source_key",
                )
            )


def _validate_plan_issues(
    plan_issues: tuple[Phase1OrchestrationPlanIssue, ...],
    issues: list[Phase1OrchestrationPlanIssue],
) -> None:
    for position, plan_issue in enumerate(plan_issues, start=1):
        _validate_required_text(
            plan_issue.code,
            f"issues[{position}].code",
            "PHASE1_ORCHESTRATION_PLAN_ISSUE_MISSING_CODE",
            "issue code must be a non-empty string.",
            issues,
        )
        _validate_required_text(
            plan_issue.message,
            f"issues[{position}].message",
            "PHASE1_ORCHESTRATION_PLAN_ISSUE_MISSING_MESSAGE",
            "issue message must be a non-empty string.",
            issues,
        )
        _validate_required_text(
            plan_issue.field_name,
            f"issues[{position}].field_name",
            "PHASE1_ORCHESTRATION_PLAN_ISSUE_MISSING_FIELD_NAME",
            "issue field_name must be a non-empty string.",
            issues,
        )
        if plan_issue.severity not in ("info", "warning", "error"):
            issues.append(
                Phase1OrchestrationPlanIssue(
                    code="PHASE1_ORCHESTRATION_PLAN_ISSUE_INVALID_SEVERITY",
                    message="issue severity must be info, warning, or error.",
                    field_name=f"issues[{position}].severity",
                )
            )


def _validate_summary(
    plan: Phase1OrchestrationPlan,
    issues: list[Phase1OrchestrationPlanIssue],
) -> None:
    expected_summary = _create_summary(
        acquisition_request=plan.acquisition_request,
        acquisition_result=plan.acquisition_result,
        acquisition_to_parser_plan=plan.acquisition_to_parser_plan,
        parser_run_requests=plan.parser_run_requests,
        dry_run_boundaries=plan.dry_run_boundaries,
        issues=plan.issues,
    )
    for field_name, value in (
        ("summary.acquisition_candidate_count", plan.summary.acquisition_candidate_count),
        ("summary.acquisition_artifact_count", plan.summary.acquisition_artifact_count),
        ("summary.parser_plan_artifact_count", plan.summary.parser_plan_artifact_count),
        ("summary.parser_input_artifact_count", plan.summary.parser_input_artifact_count),
        ("summary.parser_run_request_count", plan.summary.parser_run_request_count),
        ("summary.dry_run_boundary_count", plan.summary.dry_run_boundary_count),
        ("summary.dry_run_eligible_count", plan.summary.dry_run_eligible_count),
        ("summary.issue_count", plan.summary.issue_count),
    ):
        if not isinstance(value, int) or value < 0:
            issues.append(
                Phase1OrchestrationPlanIssue(
                    code="PHASE1_ORCHESTRATION_PLAN_NEGATIVE_SUMMARY_COUNT",
                    message="summary counts must be non-negative integers.",
                    field_name=field_name,
                )
            )

    _append_summary_mismatch(
        plan.summary.acquisition_candidate_count,
        expected_summary.acquisition_candidate_count,
        "PHASE1_ORCHESTRATION_PLAN_SUMMARY_CANDIDATE_COUNT_MISMATCH",
        "summary.acquisition_candidate_count",
        issues,
    )
    _append_summary_mismatch(
        plan.summary.acquisition_artifact_count,
        expected_summary.acquisition_artifact_count,
        "PHASE1_ORCHESTRATION_PLAN_SUMMARY_ARTIFACT_COUNT_MISMATCH",
        "summary.acquisition_artifact_count",
        issues,
    )
    _append_summary_mismatch(
        plan.summary.parser_plan_artifact_count,
        expected_summary.parser_plan_artifact_count,
        "PHASE1_ORCHESTRATION_PLAN_SUMMARY_PARSER_PLAN_COUNT_MISMATCH",
        "summary.parser_plan_artifact_count",
        issues,
    )
    _append_summary_mismatch(
        plan.summary.parser_input_artifact_count,
        expected_summary.parser_input_artifact_count,
        "PHASE1_ORCHESTRATION_PLAN_SUMMARY_INPUT_COUNT_MISMATCH",
        "summary.parser_input_artifact_count",
        issues,
    )
    _append_summary_mismatch(
        plan.summary.parser_run_request_count,
        expected_summary.parser_run_request_count,
        "PHASE1_ORCHESTRATION_PLAN_SUMMARY_REQUEST_COUNT_MISMATCH",
        "summary.parser_run_request_count",
        issues,
    )
    _append_summary_mismatch(
        plan.summary.dry_run_boundary_count,
        expected_summary.dry_run_boundary_count,
        "PHASE1_ORCHESTRATION_PLAN_SUMMARY_DRY_RUN_COUNT_MISMATCH",
        "summary.dry_run_boundary_count",
        issues,
    )
    _append_summary_mismatch(
        plan.summary.dry_run_eligible_count,
        expected_summary.dry_run_eligible_count,
        "PHASE1_ORCHESTRATION_PLAN_SUMMARY_ELIGIBLE_COUNT_MISMATCH",
        "summary.dry_run_eligible_count",
        issues,
    )
    _append_summary_mismatch(
        plan.summary.issue_count,
        expected_summary.issue_count,
        "PHASE1_ORCHESTRATION_PLAN_SUMMARY_ISSUE_COUNT_MISMATCH",
        "summary.issue_count",
        issues,
    )


def _append_summary_mismatch(
    actual: int,
    expected: int,
    code: str,
    field_name: str,
    issues: list[Phase1OrchestrationPlanIssue],
) -> None:
    if actual != expected:
        issues.append(
            Phase1OrchestrationPlanIssue(
                code=code,
                message="summary count must match plan metadata.",
                field_name=field_name,
            )
        )


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[Phase1OrchestrationPlanIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            Phase1OrchestrationPlanIssue(
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
    issues: list[Phase1OrchestrationPlanIssue],
) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        issues.append(
            Phase1OrchestrationPlanIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )
