"""Runtime-passive parser validation issue metadata contract."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.parsers.adapter_registry_contract import (
    Phase1ParserAdapterRegistry,
    get_phase1_parser_adapter_by_source_family,
)


class ParserValidationIssueSeverity(str, Enum):
    """Deterministic parser validation issue severity values."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ParserValidationIssue:
    """Metadata-only parser validation issue for Phase 1 parser adapters."""

    source_family: str
    source_key: str
    parser_key: str
    severity: ParserValidationIssueSeverity
    code: str
    message: str
    artifact_reference: str | None = None
    row_id: str | None = None
    source_row_number: int | None = None
    field_key: str | None = None
    context: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ParserValidationIssueCollection:
    """Deterministic collection of parser validation issues."""

    issues: tuple[ParserValidationIssue, ...]

    @property
    def issue_count(self) -> int:
        return len(self.issues)


@dataclass(frozen=True)
class ParserValidationIssueValidationIssue:
    """Validation issue for parser validation issue metadata."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class ParserValidationIssueValidationResult:
    """Structural validation result for parser validation issue metadata."""

    issues: tuple[ParserValidationIssueValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def create_parser_validation_issue(
    *,
    source_family: str,
    severity: ParserValidationIssueSeverity,
    code: str,
    message: str,
    artifact_reference: str | None = None,
    row_id: str | None = None,
    source_row_number: int | None = None,
    field_key: str | None = None,
    context: Mapping[str, str] | None = None,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> ParserValidationIssue:
    """Create parser diagnostic metadata from the adapter registry."""

    descriptor = get_phase1_parser_adapter_by_source_family(
        source_family,
        registry,
    )
    if descriptor is None:
        raise ValueError(
            "source_family is not registered for a Phase 1 parser adapter."
        )

    return ParserValidationIssue(
        source_family=descriptor.source_family,
        source_key=descriptor.source_family,
        parser_key=descriptor.parser_key,
        severity=severity,
        code=code,
        message=message,
        artifact_reference=artifact_reference,
        row_id=row_id,
        source_row_number=source_row_number,
        field_key=field_key,
        context=_context_items(context),
    )


def create_parser_validation_issue_collection(
    issues: Sequence[ParserValidationIssue],
) -> ParserValidationIssueCollection:
    """Create a parser validation issue collection preserving issue order."""

    return ParserValidationIssueCollection(issues=tuple(issues))


def validate_parser_validation_issue(
    issue: ParserValidationIssue,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> ParserValidationIssueValidationResult:
    """Validate parser diagnostic metadata without source content inspection."""

    issues: list[ParserValidationIssueValidationIssue] = []

    _validate_required_text(
        issue.source_family,
        "source_family",
        "PARSER_VALIDATION_ISSUE_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        issue.source_key,
        "source_key",
        "PARSER_VALIDATION_ISSUE_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        issue.parser_key,
        "parser_key",
        "PARSER_VALIDATION_ISSUE_MISSING_PARSER_KEY",
        "parser_key must be a non-empty string.",
        issues,
    )
    _validate_severity(issue.severity, issues)
    _validate_required_text(
        issue.code,
        "code",
        "PARSER_VALIDATION_ISSUE_MISSING_CODE",
        "code must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        issue.message,
        "message",
        "PARSER_VALIDATION_ISSUE_MISSING_MESSAGE",
        "message must be a non-empty string.",
        issues,
    )
    _validate_optional_text(
        issue.artifact_reference,
        "artifact_reference",
        "PARSER_VALIDATION_ISSUE_BLANK_ARTIFACT_REFERENCE",
        "artifact_reference must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        issue.row_id,
        "row_id",
        "PARSER_VALIDATION_ISSUE_BLANK_ROW_ID",
        "row_id must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        issue.field_key,
        "field_key",
        "PARSER_VALIDATION_ISSUE_BLANK_FIELD_KEY",
        "field_key must be non-empty when provided.",
        issues,
    )
    if issue.source_row_number is not None and (
        not isinstance(issue.source_row_number, int)
        or issue.source_row_number <= 0
    ):
        issues.append(
            ParserValidationIssueValidationIssue(
                code="PARSER_VALIDATION_ISSUE_INVALID_SOURCE_ROW_NUMBER",
                message="source_row_number must be a positive integer when provided.",
                field_name="source_row_number",
            )
        )
    _validate_context(issue.context, issues)

    descriptor = get_phase1_parser_adapter_by_source_family(
        issue.source_family,
        registry,
    )
    if descriptor is None:
        issues.append(
            ParserValidationIssueValidationIssue(
                code="PARSER_VALIDATION_ISSUE_UNKNOWN_SOURCE_FAMILY",
                message="source_family must match a registered Phase 1 parser adapter.",
                field_name="source_family",
            )
        )
    else:
        if issue.source_key != descriptor.source_family:
            issues.append(
                ParserValidationIssueValidationIssue(
                    code="PARSER_VALIDATION_ISSUE_SOURCE_KEY_MISMATCH",
                    message="source_key must match the registered source_family.",
                    field_name="source_key",
                )
            )
        if issue.parser_key != descriptor.parser_key:
            issues.append(
                ParserValidationIssueValidationIssue(
                    code="PARSER_VALIDATION_ISSUE_PARSER_KEY_MISMATCH",
                    message="parser_key must match the registered parser adapter.",
                    field_name="parser_key",
                )
            )

    return ParserValidationIssueValidationResult(issues=tuple(issues))


def validate_parser_validation_issue_collection(
    collection: ParserValidationIssueCollection,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> ParserValidationIssueValidationResult:
    """Validate a parser diagnostic collection without runtime side effects."""

    issues: list[ParserValidationIssueValidationIssue] = []
    for position, issue in enumerate(collection.issues, start=1):
        for validation_issue in validate_parser_validation_issue(
            issue,
            registry,
        ).issues:
            issues.append(
                ParserValidationIssueValidationIssue(
                    code=validation_issue.code,
                    message=validation_issue.message,
                    field_name=f"issues[{position}].{validation_issue.field_name}",
                )
            )

    return ParserValidationIssueValidationResult(issues=tuple(issues))


def _context_items(
    context: Mapping[str, str] | None,
) -> tuple[tuple[str, str], ...]:
    if context is None:
        return ()
    return tuple(sorted(dict(context).items(), key=lambda item: item[0]))


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[ParserValidationIssueValidationIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            ParserValidationIssueValidationIssue(
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
    issues: list[ParserValidationIssueValidationIssue],
) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        issues.append(
            ParserValidationIssueValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )


def _validate_severity(
    severity: ParserValidationIssueSeverity,
    issues: list[ParserValidationIssueValidationIssue],
) -> None:
    if not isinstance(severity, ParserValidationIssueSeverity):
        issues.append(
            ParserValidationIssueValidationIssue(
                code="PARSER_VALIDATION_ISSUE_INVALID_SEVERITY",
                message="severity must be a ParserValidationIssueSeverity value.",
                field_name="severity",
            )
        )


def _validate_context(
    context: tuple[tuple[str, str], ...],
    issues: list[ParserValidationIssueValidationIssue],
) -> None:
    if not isinstance(context, tuple):
        issues.append(
            ParserValidationIssueValidationIssue(
                code="PARSER_VALIDATION_ISSUE_INVALID_CONTEXT",
                message="context must be a tuple of string key-value pairs.",
                field_name="context",
            )
        )
        return

    for position, item in enumerate(context, start=1):
        if not isinstance(item, tuple) or len(item) != 2:
            issues.append(
                ParserValidationIssueValidationIssue(
                    code="PARSER_VALIDATION_ISSUE_INVALID_CONTEXT_ITEM",
                    message="context must contain two-item tuples.",
                    field_name=f"context[{position}]",
                )
            )
            continue

        key, value = item
        if not isinstance(key, str) or not key.strip():
            issues.append(
                ParserValidationIssueValidationIssue(
                    code="PARSER_VALIDATION_ISSUE_BLANK_CONTEXT_KEY",
                    message="context keys must be non-empty strings.",
                    field_name=f"context[{position}].key",
                )
            )
        if not isinstance(value, str):
            issues.append(
                ParserValidationIssueValidationIssue(
                    code="PARSER_VALIDATION_ISSUE_INVALID_CONTEXT_VALUE",
                    message="context values must be strings.",
                    field_name=f"context[{position}].value",
                )
            )
