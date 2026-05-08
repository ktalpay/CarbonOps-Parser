"""Runtime-passive parser normalized output row metadata contract."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from carbonfactor_parser.parsers.adapter_registry_contract import (
    Phase1ParserAdapterRegistry,
    get_phase1_parser_adapter_by_source_family,
)
from carbonfactor_parser.parsers.input_artifact_contract import ParserInputArtifact


class ParserNormalizedOutputRowStatus(str, Enum):
    """Runtime-passive normalized parser output row status values."""

    DECLARED = "declared"


@dataclass(frozen=True)
class ParserNormalizedOutputRow:
    """Metadata-only normalized row produced by a future parser adapter."""

    source_family: str
    source_key: str
    parser_key: str
    artifact_reference: str
    row_id: str
    normalized_fields: tuple[tuple[str, Any], ...]
    status: ParserNormalizedOutputRowStatus = ParserNormalizedOutputRowStatus.DECLARED
    source_row_number: int | None = None
    artifact_identifier: str | None = None
    reporting_year: int | None = None
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ParserNormalizedOutputBatch:
    """Deterministic collection of normalized parser output rows."""

    rows: tuple[ParserNormalizedOutputRow, ...]

    @property
    def row_count(self) -> int:
        return len(self.rows)


@dataclass(frozen=True)
class ParserNormalizedOutputRowValidationIssue:
    """Validation issue for normalized parser output row metadata."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class ParserNormalizedOutputRowValidationResult:
    """Structural validation result for normalized parser output row metadata."""

    issues: tuple[ParserNormalizedOutputRowValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def create_parser_normalized_output_row(
    *,
    artifact: ParserInputArtifact,
    row_id: str,
    normalized_fields: Mapping[str, Any],
    source_row_number: int | None = None,
    artifact_identifier: str | None = None,
    status: ParserNormalizedOutputRowStatus = ParserNormalizedOutputRowStatus.DECLARED,
    warnings: Sequence[str] = (),
    errors: Sequence[str] = (),
) -> ParserNormalizedOutputRow:
    """Create normalized row metadata without parser execution or persistence."""

    return ParserNormalizedOutputRow(
        source_family=artifact.source_family,
        source_key=artifact.source_key,
        parser_key=artifact.parser_key,
        artifact_reference=artifact.artifact_reference,
        row_id=row_id,
        normalized_fields=_normalized_field_items(normalized_fields),
        status=status,
        source_row_number=source_row_number,
        artifact_identifier=artifact_identifier,
        reporting_year=artifact.reporting_year,
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def create_parser_normalized_output_batch(
    rows: Sequence[ParserNormalizedOutputRow],
) -> ParserNormalizedOutputBatch:
    """Create a normalized output row batch preserving caller row order."""

    return ParserNormalizedOutputBatch(rows=tuple(rows))


def validate_parser_normalized_output_row(
    row: ParserNormalizedOutputRow,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> ParserNormalizedOutputRowValidationResult:
    """Validate normalized row metadata without interpreting field values."""

    issues: list[ParserNormalizedOutputRowValidationIssue] = []

    _validate_required_text(
        row.source_family,
        "source_family",
        "PARSER_NORMALIZED_ROW_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        row.source_key,
        "source_key",
        "PARSER_NORMALIZED_ROW_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        row.parser_key,
        "parser_key",
        "PARSER_NORMALIZED_ROW_MISSING_PARSER_KEY",
        "parser_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        row.artifact_reference,
        "artifact_reference",
        "PARSER_NORMALIZED_ROW_MISSING_ARTIFACT_REFERENCE",
        "artifact_reference must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        row.row_id,
        "row_id",
        "PARSER_NORMALIZED_ROW_MISSING_ROW_ID",
        "row_id must be a non-empty string.",
        issues,
    )
    _validate_normalized_fields(row.normalized_fields, "normalized_fields", issues)
    _validate_row_status(row.status, issues)
    _validate_positive_int(
        row.source_row_number,
        "source_row_number",
        "PARSER_NORMALIZED_ROW_INVALID_SOURCE_ROW_NUMBER",
        "source_row_number must be a positive integer when provided.",
        issues,
    )
    _validate_positive_int(
        row.reporting_year,
        "reporting_year",
        "PARSER_NORMALIZED_ROW_INVALID_REPORTING_YEAR",
        "reporting_year must be a positive integer when provided.",
        issues,
    )
    _validate_optional_text(
        row.artifact_identifier,
        "artifact_identifier",
        "PARSER_NORMALIZED_ROW_BLANK_ARTIFACT_IDENTIFIER",
        "artifact_identifier must be non-empty when provided.",
        issues,
    )
    _validate_text_collection(
        row.warnings,
        "warnings",
        "PARSER_NORMALIZED_ROW_BLANK_WARNING",
        "warnings must contain only non-empty strings.",
        issues,
    )
    _validate_text_collection(
        row.errors,
        "errors",
        "PARSER_NORMALIZED_ROW_BLANK_ERROR",
        "errors must contain only non-empty strings.",
        issues,
    )

    descriptor = get_phase1_parser_adapter_by_source_family(
        row.source_family,
        registry,
    )
    if descriptor is None:
        issues.append(
            ParserNormalizedOutputRowValidationIssue(
                code="PARSER_NORMALIZED_ROW_UNKNOWN_SOURCE_FAMILY",
                message="source_family must match a registered Phase 1 parser adapter.",
                field_name="source_family",
            )
        )
    else:
        _validate_registry_alignment(row, descriptor, issues)

    return ParserNormalizedOutputRowValidationResult(issues=tuple(issues))


def validate_parser_normalized_output_batch(
    batch: ParserNormalizedOutputBatch,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> ParserNormalizedOutputRowValidationResult:
    """Validate a normalized output row batch without persistence mapping."""

    issues: list[ParserNormalizedOutputRowValidationIssue] = []
    for position, row in enumerate(batch.rows, start=1):
        for issue in validate_parser_normalized_output_row(row, registry).issues:
            issues.append(
                ParserNormalizedOutputRowValidationIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=f"rows[{position}].{issue.field_name}",
                )
            )

    return ParserNormalizedOutputRowValidationResult(issues=tuple(issues))


def _normalized_field_items(
    normalized_fields: Mapping[str, Any],
) -> tuple[tuple[str, Any], ...]:
    return tuple(sorted(dict(normalized_fields).items(), key=lambda item: item[0]))


def _validate_registry_alignment(
    row: ParserNormalizedOutputRow,
    descriptor: Any,
    issues: list[ParserNormalizedOutputRowValidationIssue],
) -> None:
    if row.source_key != descriptor.source_family:
        issues.append(
            ParserNormalizedOutputRowValidationIssue(
                code="PARSER_NORMALIZED_ROW_SOURCE_KEY_MISMATCH",
                message="source_key must match the registered source_family.",
                field_name="source_key",
            )
        )
    if row.parser_key != descriptor.parser_key:
        issues.append(
            ParserNormalizedOutputRowValidationIssue(
                code="PARSER_NORMALIZED_ROW_PARSER_KEY_MISMATCH",
                message="parser_key must match the registered parser adapter.",
                field_name="parser_key",
            )
        )


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[ParserNormalizedOutputRowValidationIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            ParserNormalizedOutputRowValidationIssue(
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
    issues: list[ParserNormalizedOutputRowValidationIssue],
) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        issues.append(
            ParserNormalizedOutputRowValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )


def _validate_normalized_fields(
    normalized_fields: tuple[tuple[str, Any], ...],
    field_name: str,
    issues: list[ParserNormalizedOutputRowValidationIssue],
) -> None:
    if not isinstance(normalized_fields, tuple) or not normalized_fields:
        issues.append(
            ParserNormalizedOutputRowValidationIssue(
                code="PARSER_NORMALIZED_ROW_MISSING_FIELDS",
                message="normalized_fields must be a non-empty tuple of field pairs.",
                field_name=field_name,
            )
        )
        return

    for position, item in enumerate(normalized_fields, start=1):
        if not isinstance(item, tuple) or len(item) != 2:
            issues.append(
                ParserNormalizedOutputRowValidationIssue(
                    code="PARSER_NORMALIZED_ROW_INVALID_FIELD_ITEM",
                    message="normalized_fields must contain two-item tuples.",
                    field_name=f"{field_name}[{position}]",
                )
            )
            continue

        key = item[0]
        if not isinstance(key, str) or not key.strip():
            issues.append(
                ParserNormalizedOutputRowValidationIssue(
                    code="PARSER_NORMALIZED_ROW_BLANK_FIELD_KEY",
                    message="normalized field keys must be non-empty strings.",
                    field_name=f"{field_name}[{position}].key",
                )
            )


def _validate_row_status(
    status: ParserNormalizedOutputRowStatus,
    issues: list[ParserNormalizedOutputRowValidationIssue],
) -> None:
    if not isinstance(status, ParserNormalizedOutputRowStatus):
        issues.append(
            ParserNormalizedOutputRowValidationIssue(
                code="PARSER_NORMALIZED_ROW_INVALID_STATUS",
                message="status must be a ParserNormalizedOutputRowStatus value.",
                field_name="status",
            )
        )


def _validate_positive_int(
    value: int | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[ParserNormalizedOutputRowValidationIssue],
) -> None:
    if value is not None and (not isinstance(value, int) or value <= 0):
        issues.append(
            ParserNormalizedOutputRowValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )


def _validate_text_collection(
    values: tuple[str, ...],
    field_name: str,
    code: str,
    message: str,
    issues: list[ParserNormalizedOutputRowValidationIssue],
) -> None:
    if not isinstance(values, tuple):
        issues.append(
            ParserNormalizedOutputRowValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )
        return

    for position, value in enumerate(values, start=1):
        if not isinstance(value, str) or not value.strip():
            issues.append(
                ParserNormalizedOutputRowValidationIssue(
                    code=code,
                    message=message,
                    field_name=f"{field_name}[{position}]",
                )
            )
