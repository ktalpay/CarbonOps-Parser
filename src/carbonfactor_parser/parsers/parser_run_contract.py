"""Runtime-passive parser run request/result metadata contract."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.parsers.adapter_registry_contract import (
    Phase1ParserAdapterRegistry,
    get_phase1_parser_adapter_by_source_family,
)
from carbonfactor_parser.parsers.input_artifact_contract import ParserInputArtifact
from carbonfactor_parser.parsers.normalized_output_row_contract import (
    ParserNormalizedOutputRow,
    validate_parser_normalized_output_row,
)
from carbonfactor_parser.parsers.validation_issue_contract import (
    ParserValidationIssue,
    ParserValidationIssueSeverity,
    validate_parser_validation_issue,
)


class ParserRunStatus(str, Enum):
    """Deterministic parser run result status values."""

    DECLARED = "declared"
    COMPLETED = "completed"
    COMPLETED_WITH_ISSUES = "completed_with_issues"
    FAILED = "failed"


@dataclass(frozen=True)
class ParserRunRequest:
    """Metadata-only parser run request for one Phase 1 parser adapter."""

    source_family: str
    source_key: str
    parser_key: str
    artifacts: tuple[ParserInputArtifact, ...]
    run_id: str | None = None
    correlation_id: str | None = None
    requested_reporting_year: int | None = None
    run_metadata: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ParserRunSummary:
    """Deterministic metadata-only parser run counts."""

    artifact_count: int
    row_count: int
    issue_count: int
    info_count: int
    warning_count: int
    error_count: int


@dataclass(frozen=True)
class ParserRunResult:
    """Metadata-only parser run result boundary for future parser adapters."""

    source_family: str
    source_key: str
    parser_key: str
    status: ParserRunStatus
    rows: tuple[ParserNormalizedOutputRow, ...]
    issues: tuple[ParserValidationIssue, ...]
    summary: ParserRunSummary
    artifact_references: tuple[str, ...] = ()
    run_id: str | None = None
    correlation_id: str | None = None
    artifact_metadata: tuple[tuple[str, str], ...] = ()
    run_metadata: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ParserRunContractValidationIssue:
    """Validation issue for parser run request/result metadata."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class ParserRunContractValidationResult:
    """Structural validation result for parser run request/result metadata."""

    issues: tuple[ParserRunContractValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def create_parser_run_request(
    *,
    source_family: str,
    artifacts: Sequence[ParserInputArtifact],
    run_id: str | None = None,
    correlation_id: str | None = None,
    requested_reporting_year: int | None = None,
    run_metadata: Mapping[str, str] | None = None,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> ParserRunRequest:
    """Create a parser run request from registered adapter metadata."""

    descriptor = get_phase1_parser_adapter_by_source_family(
        source_family,
        registry,
    )
    if descriptor is None:
        raise ValueError(
            "source_family is not registered for a Phase 1 parser adapter."
        )

    return ParserRunRequest(
        source_family=descriptor.source_family,
        source_key=descriptor.source_family,
        parser_key=descriptor.parser_key,
        artifacts=tuple(artifacts),
        run_id=run_id,
        correlation_id=correlation_id,
        requested_reporting_year=requested_reporting_year,
        run_metadata=_metadata_items(run_metadata),
    )


def create_parser_run_result(
    *,
    request: ParserRunRequest,
    status: ParserRunStatus,
    rows: Sequence[ParserNormalizedOutputRow] = (),
    issues: Sequence[ParserValidationIssue] = (),
    artifact_metadata: Mapping[str, str] | None = None,
    run_metadata: Mapping[str, str] | None = None,
) -> ParserRunResult:
    """Create a parser run result without executing parsers or persistence."""

    row_items = tuple(rows)
    issue_items = tuple(issues)
    return ParserRunResult(
        source_family=request.source_family,
        source_key=request.source_key,
        parser_key=request.parser_key,
        status=status,
        rows=row_items,
        issues=issue_items,
        summary=_summary(
            artifact_count=len(request.artifacts),
            row_count=len(row_items),
            issues=issue_items,
        ),
        artifact_references=tuple(
            artifact.artifact_reference for artifact in request.artifacts
        ),
        run_id=request.run_id,
        correlation_id=request.correlation_id,
        artifact_metadata=_metadata_items(artifact_metadata),
        run_metadata=_metadata_items(run_metadata),
    )


def validate_parser_run_request(
    request: ParserRunRequest,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> ParserRunContractValidationResult:
    """Validate parser run request metadata without runtime side effects."""

    issues: list[ParserRunContractValidationIssue] = []
    _validate_common_identity(request, "request", issues, registry)
    _validate_optional_text(
        request.run_id,
        "request.run_id",
        "PARSER_RUN_REQUEST_BLANK_RUN_ID",
        "run_id must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        request.correlation_id,
        "request.correlation_id",
        "PARSER_RUN_REQUEST_BLANK_CORRELATION_ID",
        "correlation_id must be non-empty when provided.",
        issues,
    )
    _validate_positive_int(
        request.requested_reporting_year,
        "request.requested_reporting_year",
        "PARSER_RUN_REQUEST_INVALID_REPORTING_YEAR",
        "requested_reporting_year must be a positive integer when provided.",
        issues,
    )
    _validate_metadata(
        request.run_metadata,
        "request.run_metadata",
        "PARSER_RUN_REQUEST_INVALID_RUN_METADATA",
        issues,
    )
    _validate_request_artifacts(request, issues)

    return ParserRunContractValidationResult(issues=tuple(issues))


def validate_parser_run_result(
    result: ParserRunResult,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> ParserRunContractValidationResult:
    """Validate parser run result metadata without parser execution."""

    issues: list[ParserRunContractValidationIssue] = []
    _validate_common_identity(result, "result", issues, registry)
    if not isinstance(result.status, ParserRunStatus):
        issues.append(
            ParserRunContractValidationIssue(
                code="PARSER_RUN_RESULT_INVALID_STATUS",
                message="status must be a ParserRunStatus value.",
                field_name="result.status",
            )
        )
    _validate_optional_text(
        result.run_id,
        "result.run_id",
        "PARSER_RUN_RESULT_BLANK_RUN_ID",
        "run_id must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        result.correlation_id,
        "result.correlation_id",
        "PARSER_RUN_RESULT_BLANK_CORRELATION_ID",
        "correlation_id must be non-empty when provided.",
        issues,
    )
    _validate_metadata(
        result.artifact_metadata,
        "result.artifact_metadata",
        "PARSER_RUN_RESULT_INVALID_ARTIFACT_METADATA",
        issues,
    )
    _validate_metadata(
        result.run_metadata,
        "result.run_metadata",
        "PARSER_RUN_RESULT_INVALID_RUN_METADATA",
        issues,
    )
    _validate_result_artifact_references(result, issues)
    _validate_result_rows(result, issues, registry)
    _validate_result_issues(result, issues, registry)
    _validate_summary_counts(result, issues)

    return ParserRunContractValidationResult(issues=tuple(issues))


def _summary(
    *,
    artifact_count: int,
    row_count: int,
    issues: tuple[ParserValidationIssue, ...],
) -> ParserRunSummary:
    info_count = sum(
        issue.severity is ParserValidationIssueSeverity.INFO for issue in issues
    )
    warning_count = sum(
        issue.severity is ParserValidationIssueSeverity.WARNING for issue in issues
    )
    error_count = sum(
        issue.severity is ParserValidationIssueSeverity.ERROR for issue in issues
    )
    return ParserRunSummary(
        artifact_count=artifact_count,
        row_count=row_count,
        issue_count=len(issues),
        info_count=info_count,
        warning_count=warning_count,
        error_count=error_count,
    )


def _validate_common_identity(
    obj: ParserRunRequest | ParserRunResult,
    prefix: str,
    issues: list[ParserRunContractValidationIssue],
    registry: Phase1ParserAdapterRegistry | None,
) -> None:
    _validate_required_text(
        obj.source_family,
        f"{prefix}.source_family",
        f"PARSER_RUN_{prefix.upper()}_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        obj.source_key,
        f"{prefix}.source_key",
        f"PARSER_RUN_{prefix.upper()}_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        obj.parser_key,
        f"{prefix}.parser_key",
        f"PARSER_RUN_{prefix.upper()}_MISSING_PARSER_KEY",
        "parser_key must be a non-empty string.",
        issues,
    )

    descriptor = get_phase1_parser_adapter_by_source_family(
        obj.source_family,
        registry,
    )
    if descriptor is None:
        issues.append(
            ParserRunContractValidationIssue(
                code=f"PARSER_RUN_{prefix.upper()}_UNKNOWN_SOURCE_FAMILY",
                message="source_family must match a registered Phase 1 parser adapter.",
                field_name=f"{prefix}.source_family",
            )
        )
        return

    if obj.source_key != descriptor.source_family:
        issues.append(
            ParserRunContractValidationIssue(
                code=f"PARSER_RUN_{prefix.upper()}_SOURCE_KEY_MISMATCH",
                message="source_key must match the registered source_family.",
                field_name=f"{prefix}.source_key",
            )
        )
    if obj.parser_key != descriptor.parser_key:
        issues.append(
            ParserRunContractValidationIssue(
                code=f"PARSER_RUN_{prefix.upper()}_PARSER_KEY_MISMATCH",
                message="parser_key must match the registered parser adapter.",
                field_name=f"{prefix}.parser_key",
            )
        )


def _validate_request_artifacts(
    request: ParserRunRequest,
    issues: list[ParserRunContractValidationIssue],
) -> None:
    if not isinstance(request.artifacts, tuple) or not request.artifacts:
        issues.append(
            ParserRunContractValidationIssue(
                code="PARSER_RUN_REQUEST_MISSING_ARTIFACTS",
                message="artifacts must be a non-empty tuple.",
                field_name="request.artifacts",
            )
        )
        return

    for position, artifact in enumerate(request.artifacts, start=1):
        _validate_artifact_alignment(
            artifact,
            request.source_family,
            request.source_key,
            request.parser_key,
            f"request.artifacts[{position}]",
            issues,
        )


def _validate_artifact_alignment(
    artifact: ParserInputArtifact,
    source_family: str,
    source_key: str,
    parser_key: str,
    field_prefix: str,
    issues: list[ParserRunContractValidationIssue],
) -> None:
    if artifact.source_family != source_family:
        issues.append(
            ParserRunContractValidationIssue(
                code="PARSER_RUN_REQUEST_ARTIFACT_SOURCE_FAMILY_MISMATCH",
                message="artifact source_family must match request source_family.",
                field_name=f"{field_prefix}.source_family",
            )
        )
    if artifact.source_key != source_key:
        issues.append(
            ParserRunContractValidationIssue(
                code="PARSER_RUN_REQUEST_ARTIFACT_SOURCE_KEY_MISMATCH",
                message="artifact source_key must match request source_key.",
                field_name=f"{field_prefix}.source_key",
            )
        )
    if artifact.parser_key != parser_key:
        issues.append(
            ParserRunContractValidationIssue(
                code="PARSER_RUN_REQUEST_ARTIFACT_PARSER_KEY_MISMATCH",
                message="artifact parser_key must match request parser_key.",
                field_name=f"{field_prefix}.parser_key",
            )
        )


def _validate_result_rows(
    result: ParserRunResult,
    issues: list[ParserRunContractValidationIssue],
    registry: Phase1ParserAdapterRegistry | None,
) -> None:
    if not isinstance(result.rows, tuple):
        issues.append(
            ParserRunContractValidationIssue(
                code="PARSER_RUN_RESULT_INVALID_ROWS",
                message="rows must be a tuple.",
                field_name="result.rows",
            )
        )
        return

    for position, row in enumerate(result.rows, start=1):
        for row_issue in validate_parser_normalized_output_row(row, registry).issues:
            issues.append(
                ParserRunContractValidationIssue(
                    code=row_issue.code,
                    message=row_issue.message,
                    field_name=f"result.rows[{position}].{row_issue.field_name}",
                )
            )
        if row.source_family != result.source_family:
            issues.append(
                ParserRunContractValidationIssue(
                    code="PARSER_RUN_RESULT_ROW_SOURCE_FAMILY_MISMATCH",
                    message="row source_family must match result source_family.",
                    field_name=f"result.rows[{position}].source_family",
                )
            )
        if row.source_key != result.source_key:
            issues.append(
                ParserRunContractValidationIssue(
                    code="PARSER_RUN_RESULT_ROW_SOURCE_KEY_MISMATCH",
                    message="row source_key must match result source_key.",
                    field_name=f"result.rows[{position}].source_key",
                )
            )
        if row.parser_key != result.parser_key:
            issues.append(
                ParserRunContractValidationIssue(
                    code="PARSER_RUN_RESULT_ROW_PARSER_KEY_MISMATCH",
                    message="row parser_key must match result parser_key.",
                    field_name=f"result.rows[{position}].parser_key",
                )
            )


def _validate_result_artifact_references(
    result: ParserRunResult,
    issues: list[ParserRunContractValidationIssue],
) -> None:
    if not isinstance(result.artifact_references, tuple):
        issues.append(
            ParserRunContractValidationIssue(
                code="PARSER_RUN_RESULT_INVALID_ARTIFACT_REFERENCES",
                message="artifact_references must be a tuple.",
                field_name="result.artifact_references",
            )
        )
        return

    for position, artifact_reference in enumerate(
        result.artifact_references,
        start=1,
    ):
        _validate_required_text(
            artifact_reference,
            f"result.artifact_references[{position}]",
            "PARSER_RUN_RESULT_BLANK_ARTIFACT_REFERENCE",
            "artifact references must contain only non-empty strings.",
            issues,
        )


def _validate_result_issues(
    result: ParserRunResult,
    issues: list[ParserRunContractValidationIssue],
    registry: Phase1ParserAdapterRegistry | None,
) -> None:
    if not isinstance(result.issues, tuple):
        issues.append(
            ParserRunContractValidationIssue(
                code="PARSER_RUN_RESULT_INVALID_ISSUES",
                message="issues must be a tuple.",
                field_name="result.issues",
            )
        )
        return

    for position, issue in enumerate(result.issues, start=1):
        for validation_issue in validate_parser_validation_issue(
            issue,
            registry,
        ).issues:
            issues.append(
                ParserRunContractValidationIssue(
                    code=validation_issue.code,
                    message=validation_issue.message,
                    field_name=(
                        f"result.issues[{position}]."
                        f"{validation_issue.field_name}"
                    ),
                )
            )
        if issue.source_family != result.source_family:
            issues.append(
                ParserRunContractValidationIssue(
                    code="PARSER_RUN_RESULT_ISSUE_SOURCE_FAMILY_MISMATCH",
                    message="issue source_family must match result source_family.",
                    field_name=f"result.issues[{position}].source_family",
                )
            )
        if issue.source_key != result.source_key:
            issues.append(
                ParserRunContractValidationIssue(
                    code="PARSER_RUN_RESULT_ISSUE_SOURCE_KEY_MISMATCH",
                    message="issue source_key must match result source_key.",
                    field_name=f"result.issues[{position}].source_key",
                )
            )
        if issue.parser_key != result.parser_key:
            issues.append(
                ParserRunContractValidationIssue(
                    code="PARSER_RUN_RESULT_ISSUE_PARSER_KEY_MISMATCH",
                    message="issue parser_key must match result parser_key.",
                    field_name=f"result.issues[{position}].parser_key",
                )
            )


def _validate_summary_counts(
    result: ParserRunResult,
    issues: list[ParserRunContractValidationIssue],
) -> None:
    summary = result.summary
    expected = _summary(
        artifact_count=len(result.artifact_references),
        row_count=len(result.rows),
        issues=result.issues,
    )
    for field_name in (
        "artifact_count",
        "row_count",
        "issue_count",
        "info_count",
        "warning_count",
        "error_count",
    ):
        if getattr(summary, field_name) < 0:
            issues.append(
                ParserRunContractValidationIssue(
                    code="PARSER_RUN_RESULT_NEGATIVE_SUMMARY_COUNT",
                    message="summary counts must be non-negative.",
                    field_name=f"result.summary.{field_name}",
                )
            )

    if summary.row_count != expected.row_count:
        issues.append(
            ParserRunContractValidationIssue(
                code="PARSER_RUN_RESULT_SUMMARY_ROW_COUNT_MISMATCH",
                message="row_count must match result rows.",
                field_name="result.summary.row_count",
            )
        )
    if summary.artifact_count != expected.artifact_count:
        issues.append(
            ParserRunContractValidationIssue(
                code="PARSER_RUN_RESULT_SUMMARY_ARTIFACT_COUNT_MISMATCH",
                message="artifact_count must match result artifact references.",
                field_name="result.summary.artifact_count",
            )
        )
    for field_name in ("issue_count", "info_count", "warning_count", "error_count"):
        if getattr(summary, field_name) != getattr(expected, field_name):
            issues.append(
                ParserRunContractValidationIssue(
                    code="PARSER_RUN_RESULT_SUMMARY_ISSUE_COUNT_MISMATCH",
                    message="issue summary counts must match result issues.",
                    field_name=f"result.summary.{field_name}",
                )
            )


def _metadata_items(
    metadata: Mapping[str, str] | None,
) -> tuple[tuple[str, str], ...]:
    if metadata is None:
        return ()
    return tuple(sorted(dict(metadata).items(), key=lambda item: item[0]))


def _validate_metadata(
    metadata: tuple[tuple[str, str], ...],
    field_name: str,
    code: str,
    issues: list[ParserRunContractValidationIssue],
) -> None:
    if not isinstance(metadata, tuple):
        issues.append(
            ParserRunContractValidationIssue(
                code=code,
                message="metadata must be a tuple of string key-value pairs.",
                field_name=field_name,
            )
        )
        return

    for position, item in enumerate(metadata, start=1):
        if not isinstance(item, tuple) or len(item) != 2:
            issues.append(
                ParserRunContractValidationIssue(
                    code=code,
                    message="metadata must contain two-item tuples.",
                    field_name=f"{field_name}[{position}]",
                )
            )
            continue
        key, value = item
        if not isinstance(key, str) or not key.strip():
            issues.append(
                ParserRunContractValidationIssue(
                    code=code,
                    message="metadata keys must be non-empty strings.",
                    field_name=f"{field_name}[{position}].key",
                )
            )
        if not isinstance(value, str):
            issues.append(
                ParserRunContractValidationIssue(
                    code=code,
                    message="metadata values must be strings.",
                    field_name=f"{field_name}[{position}].value",
                )
            )


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[ParserRunContractValidationIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            ParserRunContractValidationIssue(
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
    issues: list[ParserRunContractValidationIssue],
) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        issues.append(
            ParserRunContractValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )


def _validate_positive_int(
    value: int | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[ParserRunContractValidationIssue],
) -> None:
    if value is not None and (not isinstance(value, int) or value <= 0):
        issues.append(
            ParserRunContractValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )
