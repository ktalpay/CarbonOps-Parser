"""Runtime-passive Phase 1 orchestration executor boundary skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.parsers.adapter_registry_contract import (
    Phase1ParserAdapterRegistry,
)
from carbonfactor_parser.source_acquisition.phase1_orchestration_plan_contract import (
    Phase1OrchestrationPlan,
    create_phase1_orchestration_plans,
    validate_phase1_orchestration_plan,
)


class Phase1OrchestrationExecutorStatus(str, Enum):
    """Deterministic Phase 1 orchestration executor boundary statuses."""

    PLANNED = "planned"
    NOT_EXECUTABLE = "not_executable"
    NOT_IMPLEMENTED = "not_implemented"


@dataclass(frozen=True)
class Phase1OrchestrationExecutorRequest:
    """Metadata-only request for a future Phase 1 orchestration executor."""

    source_family: str
    source_key: str
    orchestration_plan: Phase1OrchestrationPlan
    executor_id: str | None = None
    correlation_id: str | None = None


@dataclass(frozen=True)
class Phase1OrchestrationExecutorReadiness:
    """Metadata-only executor readiness declaration."""

    source_family: str
    source_key: str
    is_executable: bool
    reason: str
    plan_status: str


@dataclass(frozen=True)
class Phase1OrchestrationExecutorSummary:
    """Deterministic metadata-only executor boundary counts."""

    acquisition_candidate_count: int
    acquisition_artifact_count: int
    parser_run_request_count: int
    dry_run_boundary_count: int
    dry_run_eligible_count: int
    plan_issue_count: int
    executor_issue_count: int


@dataclass(frozen=True)
class Phase1OrchestrationExecutorIssue:
    """Structural issue for Phase 1 orchestration executor metadata."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class Phase1OrchestrationExecutorResult:
    """Metadata-only result for the future executor boundary."""

    source_family: str
    source_key: str
    status: Phase1OrchestrationExecutorStatus
    request: Phase1OrchestrationExecutorRequest
    readiness: Phase1OrchestrationExecutorReadiness
    summary: Phase1OrchestrationExecutorSummary
    issues: tuple[Phase1OrchestrationExecutorIssue, ...] = ()
    executor_id: str | None = None
    correlation_id: str | None = None


@dataclass(frozen=True)
class Phase1OrchestrationExecutorValidationResult:
    """Structural validation result for executor boundary metadata."""

    issues: tuple[Phase1OrchestrationExecutorIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def create_phase1_orchestration_executor_request(
    orchestration_plan: Phase1OrchestrationPlan,
    *,
    executor_id: str | None = None,
    correlation_id: str | None = None,
) -> Phase1OrchestrationExecutorRequest:
    """Create an executor boundary request without executing anything."""

    return Phase1OrchestrationExecutorRequest(
        source_family=orchestration_plan.source_family,
        source_key=orchestration_plan.source_key,
        orchestration_plan=orchestration_plan,
        executor_id=executor_id,
        correlation_id=correlation_id,
    )


def plan_phase1_orchestration_executor_boundary(
    request: Phase1OrchestrationExecutorRequest,
    *,
    status: Phase1OrchestrationExecutorStatus = (
        Phase1OrchestrationExecutorStatus.NOT_IMPLEMENTED
    ),
    issues: tuple[Phase1OrchestrationExecutorIssue, ...] = (),
    registry: Phase1ParserAdapterRegistry | None = None,
) -> Phase1OrchestrationExecutorResult:
    """Plan the future executor boundary without runtime execution."""

    plan_validation = validate_phase1_orchestration_plan(
        request.orchestration_plan,
        registry,
    )
    readiness = _create_readiness(request, plan_validation.is_valid)
    return Phase1OrchestrationExecutorResult(
        source_family=request.source_family,
        source_key=request.source_key,
        status=status,
        request=request,
        readiness=readiness,
        summary=_create_summary(
            plan=request.orchestration_plan,
            issues=issues,
        ),
        issues=issues,
        executor_id=request.executor_id,
        correlation_id=request.correlation_id,
    )


def create_phase1_orchestration_executor_boundaries(
    plans: tuple[Phase1OrchestrationPlan, ...] | None = None,
    *,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> tuple[Phase1OrchestrationExecutorResult, ...]:
    """Create deterministic executor boundary skeletons for Phase 1 plans."""

    active_plans = create_phase1_orchestration_plans(registry=registry) if plans is None else plans
    return tuple(
        plan_phase1_orchestration_executor_boundary(
            create_phase1_orchestration_executor_request(plan),
            registry=registry,
        )
        for plan in active_plans
    )


def validate_phase1_orchestration_executor_request(
    request: Phase1OrchestrationExecutorRequest,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> Phase1OrchestrationExecutorValidationResult:
    """Validate executor request metadata without runtime side effects."""

    issues: list[Phase1OrchestrationExecutorIssue] = []
    _validate_common_request_fields(request, issues)
    _append_plan_validation_issues(request.orchestration_plan, issues, registry)
    _validate_request_plan_alignment(request, issues)
    return Phase1OrchestrationExecutorValidationResult(issues=tuple(issues))


def validate_phase1_orchestration_executor_result(
    result: Phase1OrchestrationExecutorResult,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> Phase1OrchestrationExecutorValidationResult:
    """Validate executor result metadata without runtime side effects."""

    issues: list[Phase1OrchestrationExecutorIssue] = []
    _validate_required_text(
        result.source_family,
        "source_family",
        "PHASE1_ORCHESTRATION_EXECUTOR_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        result.source_key,
        "source_key",
        "PHASE1_ORCHESTRATION_EXECUTOR_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_optional_text(
        result.executor_id,
        "executor_id",
        "PHASE1_ORCHESTRATION_EXECUTOR_BLANK_EXECUTOR_ID",
        "executor_id must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        result.correlation_id,
        "correlation_id",
        "PHASE1_ORCHESTRATION_EXECUTOR_BLANK_CORRELATION_ID",
        "correlation_id must be non-empty when provided.",
        issues,
    )
    if not isinstance(result.status, Phase1OrchestrationExecutorStatus):
        issues.append(
            Phase1OrchestrationExecutorIssue(
                code="PHASE1_ORCHESTRATION_EXECUTOR_INVALID_STATUS",
                message="status must be a defined executor boundary status.",
                field_name="status",
            )
        )

    _validate_common_request_fields(result.request, issues)
    _append_plan_validation_issues(result.request.orchestration_plan, issues, registry)
    _validate_result_request_alignment(result, issues)
    _validate_readiness(result, issues)
    _validate_executor_issues(result.issues, issues)
    _validate_summary(result, issues)

    return Phase1OrchestrationExecutorValidationResult(issues=tuple(issues))


def validate_phase1_orchestration_executor_results(
    results: tuple[Phase1OrchestrationExecutorResult, ...],
    registry: Phase1ParserAdapterRegistry | None = None,
) -> Phase1OrchestrationExecutorValidationResult:
    """Validate executor boundary batches without runtime side effects."""

    issues: list[Phase1OrchestrationExecutorIssue] = []
    for position, result in enumerate(results, start=1):
        for issue in validate_phase1_orchestration_executor_result(
            result,
            registry,
        ).issues:
            issues.append(
                Phase1OrchestrationExecutorIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=f"results[{position}].{issue.field_name}",
                    severity=issue.severity,
                )
            )
    return Phase1OrchestrationExecutorValidationResult(issues=tuple(issues))


def _create_readiness(
    request: Phase1OrchestrationExecutorRequest,
    plan_is_valid: bool,
) -> Phase1OrchestrationExecutorReadiness:
    return Phase1OrchestrationExecutorReadiness(
        source_family=request.source_family,
        source_key=request.source_key,
        is_executable=False,
        reason=(
            "runtime_execution_not_implemented"
            if plan_is_valid
            else "orchestration_plan_structurally_invalid"
        ),
        plan_status=request.orchestration_plan.status.value,
    )


def _create_summary(
    *,
    plan: Phase1OrchestrationPlan,
    issues: tuple[Phase1OrchestrationExecutorIssue, ...],
) -> Phase1OrchestrationExecutorSummary:
    return Phase1OrchestrationExecutorSummary(
        acquisition_candidate_count=plan.summary.acquisition_candidate_count,
        acquisition_artifact_count=plan.summary.acquisition_artifact_count,
        parser_run_request_count=plan.summary.parser_run_request_count,
        dry_run_boundary_count=plan.summary.dry_run_boundary_count,
        dry_run_eligible_count=plan.summary.dry_run_eligible_count,
        plan_issue_count=plan.summary.issue_count,
        executor_issue_count=len(issues),
    )


def _validate_common_request_fields(
    request: Phase1OrchestrationExecutorRequest,
    issues: list[Phase1OrchestrationExecutorIssue],
) -> None:
    _validate_required_text(
        request.source_family,
        "request.source_family",
        "PHASE1_ORCHESTRATION_EXECUTOR_REQUEST_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        request.source_key,
        "request.source_key",
        "PHASE1_ORCHESTRATION_EXECUTOR_REQUEST_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_optional_text(
        request.executor_id,
        "request.executor_id",
        "PHASE1_ORCHESTRATION_EXECUTOR_REQUEST_BLANK_EXECUTOR_ID",
        "executor_id must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        request.correlation_id,
        "request.correlation_id",
        "PHASE1_ORCHESTRATION_EXECUTOR_REQUEST_BLANK_CORRELATION_ID",
        "correlation_id must be non-empty when provided.",
        issues,
    )
    _validate_request_plan_alignment(request, issues)


def _append_plan_validation_issues(
    plan: Phase1OrchestrationPlan,
    issues: list[Phase1OrchestrationExecutorIssue],
    registry: Phase1ParserAdapterRegistry | None,
) -> None:
    for issue in validate_phase1_orchestration_plan(plan, registry).issues:
        issues.append(
            Phase1OrchestrationExecutorIssue(
                code=issue.code,
                message=issue.message,
                field_name=f"request.orchestration_plan.{issue.field_name}",
                severity=issue.severity,
            )
        )


def _validate_request_plan_alignment(
    request: Phase1OrchestrationExecutorRequest,
    issues: list[Phase1OrchestrationExecutorIssue],
) -> None:
    plan = request.orchestration_plan
    if plan.source_family != request.source_family:
        issues.append(
            Phase1OrchestrationExecutorIssue(
                code="PHASE1_ORCHESTRATION_EXECUTOR_REQUEST_PLAN_SOURCE_FAMILY_MISMATCH",
                message="request source_family must match the orchestration plan.",
                field_name="request.orchestration_plan.source_family",
            )
        )
    if plan.source_key != request.source_key:
        issues.append(
            Phase1OrchestrationExecutorIssue(
                code="PHASE1_ORCHESTRATION_EXECUTOR_REQUEST_PLAN_SOURCE_KEY_MISMATCH",
                message="request source_key must match the orchestration plan.",
                field_name="request.orchestration_plan.source_key",
            )
        )


def _validate_result_request_alignment(
    result: Phase1OrchestrationExecutorResult,
    issues: list[Phase1OrchestrationExecutorIssue],
) -> None:
    if result.request.source_family != result.source_family:
        issues.append(
            Phase1OrchestrationExecutorIssue(
                code="PHASE1_ORCHESTRATION_EXECUTOR_RESULT_REQUEST_SOURCE_FAMILY_MISMATCH",
                message="result source_family must match request source_family.",
                field_name="request.source_family",
            )
        )
    if result.request.source_key != result.source_key:
        issues.append(
            Phase1OrchestrationExecutorIssue(
                code="PHASE1_ORCHESTRATION_EXECUTOR_RESULT_REQUEST_SOURCE_KEY_MISMATCH",
                message="result source_key must match request source_key.",
                field_name="request.source_key",
            )
        )
    if result.executor_id != result.request.executor_id:
        issues.append(
            Phase1OrchestrationExecutorIssue(
                code="PHASE1_ORCHESTRATION_EXECUTOR_ID_MISMATCH",
                message="executor_id must match the executor request.",
                field_name="executor_id",
            )
        )
    if result.correlation_id != result.request.correlation_id:
        issues.append(
            Phase1OrchestrationExecutorIssue(
                code="PHASE1_ORCHESTRATION_EXECUTOR_CORRELATION_ID_MISMATCH",
                message="correlation_id must match the executor request.",
                field_name="correlation_id",
            )
        )


def _validate_readiness(
    result: Phase1OrchestrationExecutorResult,
    issues: list[Phase1OrchestrationExecutorIssue],
) -> None:
    readiness = result.readiness
    _validate_required_text(
        readiness.source_family,
        "readiness.source_family",
        "PHASE1_ORCHESTRATION_EXECUTOR_READINESS_MISSING_SOURCE_FAMILY",
        "readiness source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        readiness.source_key,
        "readiness.source_key",
        "PHASE1_ORCHESTRATION_EXECUTOR_READINESS_MISSING_SOURCE_KEY",
        "readiness source_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        readiness.reason,
        "readiness.reason",
        "PHASE1_ORCHESTRATION_EXECUTOR_READINESS_MISSING_REASON",
        "readiness reason must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        readiness.plan_status,
        "readiness.plan_status",
        "PHASE1_ORCHESTRATION_EXECUTOR_READINESS_MISSING_PLAN_STATUS",
        "readiness plan_status must be a non-empty string.",
        issues,
    )
    if readiness.source_family != result.source_family:
        issues.append(
            Phase1OrchestrationExecutorIssue(
                code="PHASE1_ORCHESTRATION_EXECUTOR_READINESS_SOURCE_FAMILY_MISMATCH",
                message="readiness source_family must match the result.",
                field_name="readiness.source_family",
            )
        )
    if readiness.source_key != result.source_key:
        issues.append(
            Phase1OrchestrationExecutorIssue(
                code="PHASE1_ORCHESTRATION_EXECUTOR_READINESS_SOURCE_KEY_MISMATCH",
                message="readiness source_key must match the result.",
                field_name="readiness.source_key",
            )
        )
    if readiness.is_executable:
        issues.append(
            Phase1OrchestrationExecutorIssue(
                code="PHASE1_ORCHESTRATION_EXECUTOR_UNEXPECTED_EXECUTABLE_READINESS",
                message="executor boundary must remain runtime-passive.",
                field_name="readiness.is_executable",
            )
        )


def _validate_executor_issues(
    executor_issues: tuple[Phase1OrchestrationExecutorIssue, ...],
    issues: list[Phase1OrchestrationExecutorIssue],
) -> None:
    for position, executor_issue in enumerate(executor_issues, start=1):
        _validate_required_text(
            executor_issue.code,
            f"issues[{position}].code",
            "PHASE1_ORCHESTRATION_EXECUTOR_ISSUE_MISSING_CODE",
            "issue code must be a non-empty string.",
            issues,
        )
        _validate_required_text(
            executor_issue.message,
            f"issues[{position}].message",
            "PHASE1_ORCHESTRATION_EXECUTOR_ISSUE_MISSING_MESSAGE",
            "issue message must be a non-empty string.",
            issues,
        )
        _validate_required_text(
            executor_issue.field_name,
            f"issues[{position}].field_name",
            "PHASE1_ORCHESTRATION_EXECUTOR_ISSUE_MISSING_FIELD_NAME",
            "issue field_name must be a non-empty string.",
            issues,
        )
        if executor_issue.severity not in ("info", "warning", "error"):
            issues.append(
                Phase1OrchestrationExecutorIssue(
                    code="PHASE1_ORCHESTRATION_EXECUTOR_ISSUE_INVALID_SEVERITY",
                    message="issue severity must be info, warning, or error.",
                    field_name=f"issues[{position}].severity",
                )
            )


def _validate_summary(
    result: Phase1OrchestrationExecutorResult,
    issues: list[Phase1OrchestrationExecutorIssue],
) -> None:
    expected_summary = _create_summary(
        plan=result.request.orchestration_plan,
        issues=result.issues,
    )
    for field_name, value in (
        (
            "summary.acquisition_candidate_count",
            result.summary.acquisition_candidate_count,
        ),
        ("summary.acquisition_artifact_count", result.summary.acquisition_artifact_count),
        ("summary.parser_run_request_count", result.summary.parser_run_request_count),
        ("summary.dry_run_boundary_count", result.summary.dry_run_boundary_count),
        ("summary.dry_run_eligible_count", result.summary.dry_run_eligible_count),
        ("summary.plan_issue_count", result.summary.plan_issue_count),
        ("summary.executor_issue_count", result.summary.executor_issue_count),
    ):
        if not isinstance(value, int) or value < 0:
            issues.append(
                Phase1OrchestrationExecutorIssue(
                    code="PHASE1_ORCHESTRATION_EXECUTOR_NEGATIVE_SUMMARY_COUNT",
                    message="summary counts must be non-negative integers.",
                    field_name=field_name,
                )
            )

    _append_summary_mismatch(
        result.summary.acquisition_candidate_count,
        expected_summary.acquisition_candidate_count,
        "PHASE1_ORCHESTRATION_EXECUTOR_SUMMARY_CANDIDATE_COUNT_MISMATCH",
        "summary.acquisition_candidate_count",
        issues,
    )
    _append_summary_mismatch(
        result.summary.acquisition_artifact_count,
        expected_summary.acquisition_artifact_count,
        "PHASE1_ORCHESTRATION_EXECUTOR_SUMMARY_ARTIFACT_COUNT_MISMATCH",
        "summary.acquisition_artifact_count",
        issues,
    )
    _append_summary_mismatch(
        result.summary.parser_run_request_count,
        expected_summary.parser_run_request_count,
        "PHASE1_ORCHESTRATION_EXECUTOR_SUMMARY_REQUEST_COUNT_MISMATCH",
        "summary.parser_run_request_count",
        issues,
    )
    _append_summary_mismatch(
        result.summary.dry_run_boundary_count,
        expected_summary.dry_run_boundary_count,
        "PHASE1_ORCHESTRATION_EXECUTOR_SUMMARY_DRY_RUN_COUNT_MISMATCH",
        "summary.dry_run_boundary_count",
        issues,
    )
    _append_summary_mismatch(
        result.summary.dry_run_eligible_count,
        expected_summary.dry_run_eligible_count,
        "PHASE1_ORCHESTRATION_EXECUTOR_SUMMARY_ELIGIBLE_COUNT_MISMATCH",
        "summary.dry_run_eligible_count",
        issues,
    )
    _append_summary_mismatch(
        result.summary.plan_issue_count,
        expected_summary.plan_issue_count,
        "PHASE1_ORCHESTRATION_EXECUTOR_SUMMARY_PLAN_ISSUE_COUNT_MISMATCH",
        "summary.plan_issue_count",
        issues,
    )
    _append_summary_mismatch(
        result.summary.executor_issue_count,
        expected_summary.executor_issue_count,
        "PHASE1_ORCHESTRATION_EXECUTOR_SUMMARY_EXECUTOR_ISSUE_COUNT_MISMATCH",
        "summary.executor_issue_count",
        issues,
    )


def _append_summary_mismatch(
    actual: int,
    expected: int,
    code: str,
    field_name: str,
    issues: list[Phase1OrchestrationExecutorIssue],
) -> None:
    if actual != expected:
        issues.append(
            Phase1OrchestrationExecutorIssue(
                code=code,
                message="summary count must match executor boundary metadata.",
                field_name=field_name,
            )
        )


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[Phase1OrchestrationExecutorIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            Phase1OrchestrationExecutorIssue(
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
    issues: list[Phase1OrchestrationExecutorIssue],
) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        issues.append(
            Phase1OrchestrationExecutorIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )
