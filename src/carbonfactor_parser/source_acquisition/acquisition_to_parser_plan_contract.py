"""Runtime-passive acquisition-to-parser plan metadata contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.parsers.adapter_registry_contract import (
    Phase1ParserAdapterRegistry,
)
from carbonfactor_parser.parsers.parser_run_contract import (
    ParserRunRequest,
    create_parser_run_request,
    validate_parser_run_request,
)
from carbonfactor_parser.source_acquisition.download_artifact_contract import (
    SourceDownloadArtifactResult,
)
from carbonfactor_parser.source_acquisition.run_contract import (
    SourceAcquisitionRunResult,
    create_phase1_source_acquisition_run_results,
    validate_source_acquisition_run_result,
)
from carbonfactor_parser.source_acquisition.source_artifact_parser_input_bridge_contract import (
    SourceArtifactParserInputBridgeResult,
    create_phase1_source_artifact_parser_input_bridge,
    validate_source_artifact_parser_input_bridge_result,
)


class AcquisitionToParserPlanStatus(str, Enum):
    """Deterministic acquisition-to-parser plan status values."""

    DECLARED = "declared"
    PLANNED = "planned"
    PLANNED_WITH_ISSUES = "planned_with_issues"
    FAILED = "failed"


@dataclass(frozen=True)
class AcquisitionToParserPlanSummary:
    """Deterministic metadata-only acquisition-to-parser plan counts."""

    downloaded_artifact_count: int
    bridge_entry_count: int
    parser_input_artifact_count: int
    parser_run_request_count: int
    issue_count: int


@dataclass(frozen=True)
class AcquisitionToParserPlanIssue:
    """Validation or structural issue for acquisition-to-parser plans."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class AcquisitionToParserPlanResult:
    """Metadata-only plan from acquisition output to parser run requests."""

    source_family: str
    source_key: str
    status: AcquisitionToParserPlanStatus
    acquisition_result: SourceAcquisitionRunResult
    bridge_result: SourceArtifactParserInputBridgeResult
    parser_run_requests: tuple[ParserRunRequest, ...]
    issues: tuple[AcquisitionToParserPlanIssue, ...]
    summary: AcquisitionToParserPlanSummary
    acquisition_run_id: str | None = None

    @property
    def parser_keys(self) -> tuple[str, ...]:
        return tuple(request.parser_key for request in self.parser_run_requests)

    @property
    def artifact_references(self) -> tuple[str, ...]:
        return tuple(
            artifact.artifact_reference
            for request in self.parser_run_requests
            for artifact in request.artifacts
        )


@dataclass(frozen=True)
class AcquisitionToParserPlanValidationResult:
    """Structural validation result for acquisition-to-parser plan metadata."""

    issues: tuple[AcquisitionToParserPlanIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def create_acquisition_to_parser_plan(
    acquisition_result: SourceAcquisitionRunResult,
    *,
    status: AcquisitionToParserPlanStatus = AcquisitionToParserPlanStatus.PLANNED,
    issues: tuple[AcquisitionToParserPlanIssue, ...] = (),
    registry: Phase1ParserAdapterRegistry | None = None,
) -> AcquisitionToParserPlanResult:
    """Create parser run request metadata from acquisition result metadata."""

    bridge_result = create_phase1_source_artifact_parser_input_bridge(
        SourceDownloadArtifactResult(artifacts=acquisition_result.artifacts),
        registry=registry,
    )
    parser_run_request = create_parser_run_request(
        source_family=acquisition_result.source_family,
        artifacts=bridge_result.parser_input_artifacts,
        correlation_id=acquisition_result.run_id,
        run_metadata=_run_metadata(acquisition_result),
        registry=registry,
    )
    parser_run_requests = (parser_run_request,)

    return AcquisitionToParserPlanResult(
        source_family=acquisition_result.source_family,
        source_key=acquisition_result.source_key,
        status=status,
        acquisition_result=acquisition_result,
        bridge_result=bridge_result,
        parser_run_requests=parser_run_requests,
        issues=issues,
        summary=_create_summary(
            acquisition_result=acquisition_result,
            bridge_result=bridge_result,
            parser_run_requests=parser_run_requests,
            issues=issues,
        ),
        acquisition_run_id=acquisition_result.run_id,
    )


def create_phase1_acquisition_to_parser_plans(
    acquisition_results: tuple[SourceAcquisitionRunResult, ...] | None = None,
    *,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> tuple[AcquisitionToParserPlanResult, ...]:
    """Create deterministic acquisition-to-parser plans for Phase 1 sources."""

    active_results = (
        create_phase1_source_acquisition_run_results()
        if acquisition_results is None
        else acquisition_results
    )
    return tuple(
        create_acquisition_to_parser_plan(
            acquisition_result,
            registry=registry,
        )
        for acquisition_result in active_results
    )


def validate_acquisition_to_parser_plan(
    plan: AcquisitionToParserPlanResult,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> AcquisitionToParserPlanValidationResult:
    """Validate plan metadata without executing acquisition or parsers."""

    issues: list[AcquisitionToParserPlanIssue] = []

    _validate_required_text(
        plan.source_family,
        "source_family",
        "ACQUISITION_TO_PARSER_PLAN_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        plan.source_key,
        "source_key",
        "ACQUISITION_TO_PARSER_PLAN_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_optional_text(
        plan.acquisition_run_id,
        "acquisition_run_id",
        "ACQUISITION_TO_PARSER_PLAN_BLANK_ACQUISITION_RUN_ID",
        "acquisition_run_id must be non-empty when provided.",
        issues,
    )
    if not isinstance(plan.status, AcquisitionToParserPlanStatus):
        issues.append(
            AcquisitionToParserPlanIssue(
                code="ACQUISITION_TO_PARSER_PLAN_INVALID_STATUS",
                message="status must be a defined acquisition-to-parser plan status.",
                field_name="status",
            )
        )

    _append_acquisition_validation_issues(plan, issues)
    _append_bridge_validation_issues(plan, issues, registry)
    _append_parser_request_validation_issues(plan, issues, registry)
    _validate_acquisition_alignment(plan, issues)
    _validate_bridge_alignment(plan, issues)
    _validate_parser_request_alignment(plan, issues)
    _validate_plan_issues(plan.issues, issues)
    _validate_summary(plan, issues)

    return AcquisitionToParserPlanValidationResult(issues=tuple(issues))


def validate_acquisition_to_parser_plans(
    plans: tuple[AcquisitionToParserPlanResult, ...],
    registry: Phase1ParserAdapterRegistry | None = None,
) -> AcquisitionToParserPlanValidationResult:
    """Validate plan batches without runtime side effects."""

    issues: list[AcquisitionToParserPlanIssue] = []
    for position, plan in enumerate(plans, start=1):
        for issue in validate_acquisition_to_parser_plan(plan, registry).issues:
            issues.append(
                AcquisitionToParserPlanIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=f"plans[{position}].{issue.field_name}",
                    severity=issue.severity,
                )
            )

    return AcquisitionToParserPlanValidationResult(issues=tuple(issues))


def _run_metadata(
    acquisition_result: SourceAcquisitionRunResult,
) -> dict[str, str]:
    metadata = {"source_acquisition_source_key": acquisition_result.source_key}
    if acquisition_result.run_id is not None:
        metadata["source_acquisition_run_id"] = acquisition_result.run_id
    return metadata


def _create_summary(
    *,
    acquisition_result: SourceAcquisitionRunResult,
    bridge_result: SourceArtifactParserInputBridgeResult,
    parser_run_requests: tuple[ParserRunRequest, ...],
    issues: tuple[AcquisitionToParserPlanIssue, ...],
) -> AcquisitionToParserPlanSummary:
    return AcquisitionToParserPlanSummary(
        downloaded_artifact_count=len(acquisition_result.artifacts),
        bridge_entry_count=len(bridge_result.entries),
        parser_input_artifact_count=len(bridge_result.parser_input_artifacts),
        parser_run_request_count=len(parser_run_requests),
        issue_count=len(issues),
    )


def _append_acquisition_validation_issues(
    plan: AcquisitionToParserPlanResult,
    issues: list[AcquisitionToParserPlanIssue],
) -> None:
    for issue in validate_source_acquisition_run_result(
        plan.acquisition_result,
    ).issues:
        issues.append(
            AcquisitionToParserPlanIssue(
                code=issue.code,
                message=issue.message,
                field_name=f"acquisition_result.{issue.field_name}",
                severity=issue.severity,
            )
        )


def _append_bridge_validation_issues(
    plan: AcquisitionToParserPlanResult,
    issues: list[AcquisitionToParserPlanIssue],
    registry: Phase1ParserAdapterRegistry | None,
) -> None:
    for issue in validate_source_artifact_parser_input_bridge_result(
        plan.bridge_result,
        registry,
    ).issues:
        issues.append(
            AcquisitionToParserPlanIssue(
                code=issue.code,
                message=issue.message,
                field_name=f"bridge_result.{issue.field_name}",
                severity=issue.severity,
            )
        )


def _append_parser_request_validation_issues(
    plan: AcquisitionToParserPlanResult,
    issues: list[AcquisitionToParserPlanIssue],
    registry: Phase1ParserAdapterRegistry | None,
) -> None:
    for position, request in enumerate(plan.parser_run_requests, start=1):
        for issue in validate_parser_run_request(request, registry).issues:
            issues.append(
                AcquisitionToParserPlanIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=f"parser_run_requests[{position}].{issue.field_name}",
                    severity=issue.severity,
                )
            )


def _validate_acquisition_alignment(
    plan: AcquisitionToParserPlanResult,
    issues: list[AcquisitionToParserPlanIssue],
) -> None:
    if plan.acquisition_result.source_family != plan.source_family:
        issues.append(
            AcquisitionToParserPlanIssue(
                code="ACQUISITION_TO_PARSER_PLAN_ACQUISITION_SOURCE_FAMILY_MISMATCH",
                message="acquisition_result source_family must match the plan.",
                field_name="acquisition_result.source_family",
            )
        )
    if plan.acquisition_result.source_key != plan.source_key:
        issues.append(
            AcquisitionToParserPlanIssue(
                code="ACQUISITION_TO_PARSER_PLAN_ACQUISITION_SOURCE_KEY_MISMATCH",
                message="acquisition_result source_key must match the plan.",
                field_name="acquisition_result.source_key",
            )
        )
    if plan.acquisition_result.run_id != plan.acquisition_run_id:
        issues.append(
            AcquisitionToParserPlanIssue(
                code="ACQUISITION_TO_PARSER_PLAN_ACQUISITION_RUN_ID_MISMATCH",
                message="acquisition_run_id must match acquisition_result run_id.",
                field_name="acquisition_run_id",
            )
        )


def _validate_bridge_alignment(
    plan: AcquisitionToParserPlanResult,
    issues: list[AcquisitionToParserPlanIssue],
) -> None:
    acquisition_artifact_ids = plan.acquisition_result.artifact_ids
    bridge_artifact_ids = tuple(
        entry.source_artifact_id for entry in plan.bridge_result.entries
    )
    if bridge_artifact_ids != acquisition_artifact_ids:
        issues.append(
            AcquisitionToParserPlanIssue(
                code="ACQUISITION_TO_PARSER_PLAN_BRIDGE_ARTIFACT_ORDER_MISMATCH",
                message="bridge artifact ids must match acquisition artifacts in order.",
                field_name="bridge_result.entries",
            )
        )

    for position, entry in enumerate(plan.bridge_result.entries, start=1):
        if entry.source_family != plan.source_family:
            issues.append(
                AcquisitionToParserPlanIssue(
                    code="ACQUISITION_TO_PARSER_PLAN_BRIDGE_SOURCE_FAMILY_MISMATCH",
                    message="bridge source_family must match the plan.",
                    field_name=f"bridge_result.entries[{position}].source_family",
                )
            )
        if entry.source_key != plan.source_key:
            issues.append(
                AcquisitionToParserPlanIssue(
                    code="ACQUISITION_TO_PARSER_PLAN_BRIDGE_SOURCE_KEY_MISMATCH",
                    message="bridge source_key must match the plan.",
                    field_name=f"bridge_result.entries[{position}].source_key",
                )
            )


def _validate_parser_request_alignment(
    plan: AcquisitionToParserPlanResult,
    issues: list[AcquisitionToParserPlanIssue],
) -> None:
    bridge_artifacts = plan.bridge_result.parser_input_artifacts
    for position, request in enumerate(plan.parser_run_requests, start=1):
        if request.source_family != plan.source_family:
            issues.append(
                AcquisitionToParserPlanIssue(
                    code="ACQUISITION_TO_PARSER_PLAN_REQUEST_SOURCE_FAMILY_MISMATCH",
                    message="parser run request source_family must match the plan.",
                    field_name=f"parser_run_requests[{position}].source_family",
                )
            )
        if request.source_key != plan.source_key:
            issues.append(
                AcquisitionToParserPlanIssue(
                    code="ACQUISITION_TO_PARSER_PLAN_REQUEST_SOURCE_KEY_MISMATCH",
                    message="parser run request source_key must match the plan.",
                    field_name=f"parser_run_requests[{position}].source_key",
                )
            )
        if request.artifacts != bridge_artifacts:
            issues.append(
                AcquisitionToParserPlanIssue(
                    code="ACQUISITION_TO_PARSER_PLAN_REQUEST_ARTIFACTS_MISMATCH",
                    message="parser run request artifacts must match bridge output.",
                    field_name=f"parser_run_requests[{position}].artifacts",
                )
            )
        for artifact_position, artifact in enumerate(request.artifacts, start=1):
            if artifact.source_key != request.source_key:
                issues.append(
                    AcquisitionToParserPlanIssue(
                        code=(
                            "ACQUISITION_TO_PARSER_PLAN_REQUEST_ARTIFACT_SOURCE_KEY_MISMATCH"
                        ),
                        message=(
                            "parser run request artifacts must match request source_key."
                        ),
                        field_name=(
                            f"parser_run_requests[{position}]."
                            f"artifacts[{artifact_position}].source_key"
                        ),
                    )
                )
            if artifact.parser_key != request.parser_key:
                issues.append(
                    AcquisitionToParserPlanIssue(
                        code=(
                            "ACQUISITION_TO_PARSER_PLAN_REQUEST_ARTIFACT_PARSER_KEY_MISMATCH"
                        ),
                        message=(
                            "parser run request artifacts must match request parser_key."
                        ),
                        field_name=(
                            f"parser_run_requests[{position}]."
                            f"artifacts[{artifact_position}].parser_key"
                        ),
                    )
                )


def _validate_plan_issues(
    plan_issues: tuple[AcquisitionToParserPlanIssue, ...],
    issues: list[AcquisitionToParserPlanIssue],
) -> None:
    for position, plan_issue in enumerate(plan_issues, start=1):
        _validate_required_text(
            plan_issue.code,
            f"issues[{position}].code",
            "ACQUISITION_TO_PARSER_PLAN_ISSUE_MISSING_CODE",
            "issue code must be a non-empty string.",
            issues,
        )
        _validate_required_text(
            plan_issue.message,
            f"issues[{position}].message",
            "ACQUISITION_TO_PARSER_PLAN_ISSUE_MISSING_MESSAGE",
            "issue message must be a non-empty string.",
            issues,
        )
        _validate_required_text(
            plan_issue.field_name,
            f"issues[{position}].field_name",
            "ACQUISITION_TO_PARSER_PLAN_ISSUE_MISSING_FIELD_NAME",
            "issue field_name must be a non-empty string.",
            issues,
        )
        if plan_issue.severity not in ("info", "warning", "error"):
            issues.append(
                AcquisitionToParserPlanIssue(
                    code="ACQUISITION_TO_PARSER_PLAN_ISSUE_INVALID_SEVERITY",
                    message="issue severity must be info, warning, or error.",
                    field_name=f"issues[{position}].severity",
                )
            )


def _validate_summary(
    plan: AcquisitionToParserPlanResult,
    issues: list[AcquisitionToParserPlanIssue],
) -> None:
    expected_summary = _create_summary(
        acquisition_result=plan.acquisition_result,
        bridge_result=plan.bridge_result,
        parser_run_requests=plan.parser_run_requests,
        issues=plan.issues,
    )
    for field_name, value in (
        ("summary.downloaded_artifact_count", plan.summary.downloaded_artifact_count),
        ("summary.bridge_entry_count", plan.summary.bridge_entry_count),
        (
            "summary.parser_input_artifact_count",
            plan.summary.parser_input_artifact_count,
        ),
        ("summary.parser_run_request_count", plan.summary.parser_run_request_count),
        ("summary.issue_count", plan.summary.issue_count),
    ):
        if not isinstance(value, int) or value < 0:
            issues.append(
                AcquisitionToParserPlanIssue(
                    code="ACQUISITION_TO_PARSER_PLAN_NEGATIVE_SUMMARY_COUNT",
                    message="summary counts must be non-negative integers.",
                    field_name=field_name,
                )
            )

    if plan.summary.downloaded_artifact_count != expected_summary.downloaded_artifact_count:
        issues.append(
            AcquisitionToParserPlanIssue(
                code="ACQUISITION_TO_PARSER_PLAN_SUMMARY_ARTIFACT_COUNT_MISMATCH",
                message="downloaded_artifact_count must match acquisition artifacts.",
                field_name="summary.downloaded_artifact_count",
            )
        )
    if plan.summary.bridge_entry_count != expected_summary.bridge_entry_count:
        issues.append(
            AcquisitionToParserPlanIssue(
                code="ACQUISITION_TO_PARSER_PLAN_SUMMARY_BRIDGE_COUNT_MISMATCH",
                message="bridge_entry_count must match bridge entries.",
                field_name="summary.bridge_entry_count",
            )
        )
    if (
        plan.summary.parser_input_artifact_count
        != expected_summary.parser_input_artifact_count
    ):
        issues.append(
            AcquisitionToParserPlanIssue(
                code="ACQUISITION_TO_PARSER_PLAN_SUMMARY_INPUT_COUNT_MISMATCH",
                message="parser_input_artifact_count must match bridge parser inputs.",
                field_name="summary.parser_input_artifact_count",
            )
        )
    if (
        plan.summary.parser_run_request_count
        != expected_summary.parser_run_request_count
    ):
        issues.append(
            AcquisitionToParserPlanIssue(
                code="ACQUISITION_TO_PARSER_PLAN_SUMMARY_REQUEST_COUNT_MISMATCH",
                message="parser_run_request_count must match parser run requests.",
                field_name="summary.parser_run_request_count",
            )
        )
    if plan.summary.issue_count != expected_summary.issue_count:
        issues.append(
            AcquisitionToParserPlanIssue(
                code="ACQUISITION_TO_PARSER_PLAN_SUMMARY_ISSUE_COUNT_MISMATCH",
                message="issue_count must match plan issues.",
                field_name="summary.issue_count",
            )
        )


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[AcquisitionToParserPlanIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            AcquisitionToParserPlanIssue(
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
    issues: list[AcquisitionToParserPlanIssue],
) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        issues.append(
            AcquisitionToParserPlanIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )
