"""Persistence input boundary for normalized results."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from carbonfactor_parser.normalization import (
    NormalizationIssueSeverity,
    NormalizationResult,
    NormalizedRecord,
)


class PersistenceInputBuildStatus(str, Enum):
    """Status for building future persistence input."""

    READY = "ready"
    NOT_READY = "not_ready"
    NO_RECORDS = "no_records"
    FAILED = "failed"


@dataclass(frozen=True)
class PersistenceInputIssue:
    """Issue explaining why persistence input is not ready."""

    code: str
    message: str
    field_name: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class PersistenceInputRecord:
    """One normalized record prepared for a future persistence boundary."""

    source_family: str
    source_id: str
    record_id: str
    normalized_fields: tuple[tuple[str, object], ...]
    record_index: object | None = None
    row_number: object | None = None
    source_reference: str | None = None
    parser_metadata: Mapping[str, object] | None = None
    normalization_metadata: Mapping[str, object] | None = None


@dataclass(frozen=True)
class PersistenceInput:
    """Normalized records prepared for a future persistence boundary."""

    source_family: str
    source_id: str
    records: tuple[PersistenceInputRecord, ...]
    parser_metadata: Mapping[str, object] | None = None
    normalization_metadata: Mapping[str, object] | None = None


@dataclass(frozen=True)
class PersistenceInputBuildResult:
    """Structured result for building persistence input."""

    status: PersistenceInputBuildStatus
    persistence_input: PersistenceInput | None = None
    issues: tuple[PersistenceInputIssue, ...] = ()


def build_persistence_input_from_normalization_result(
    normalization_result: NormalizationResult,
    *,
    parser_metadata: Mapping[str, object] | None = None,
    normalization_metadata: Mapping[str, object] | None = None,
) -> PersistenceInputBuildResult:
    """Build persistence input without connecting to or writing to a database."""

    error_issues = _normalization_error_issues(normalization_result)
    if error_issues:
        return PersistenceInputBuildResult(
            status=PersistenceInputBuildStatus.FAILED,
            issues=tuple(
                PersistenceInputIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=issue.location,
                )
                for issue in error_issues
            ),
        )

    if not normalization_result.records:
        return PersistenceInputBuildResult(
            status=PersistenceInputBuildStatus.NO_RECORDS,
            issues=(
                PersistenceInputIssue(
                    code="PERSISTENCE_INPUT_NO_NORMALIZED_RECORDS",
                    message=(
                        "NormalizationResult must include normalized records "
                        "before persistence input can be ready."
                    ),
                    field_name="records",
                    severity="warning",
                ),
            ),
        )

    issues = _record_shape_issues(normalization_result.records)
    if issues:
        return PersistenceInputBuildResult(
            status=PersistenceInputBuildStatus.FAILED,
            issues=tuple(issues),
        )

    first_fields = dict(normalization_result.records[0].fields)
    source_family = _required_field_text(first_fields, "source_family")
    source_id = _required_field_text(first_fields, "source_id")
    if source_family is None or source_id is None:
        return PersistenceInputBuildResult(
            status=PersistenceInputBuildStatus.NOT_READY,
            issues=(
                PersistenceInputIssue(
                    code="PERSISTENCE_INPUT_SOURCE_IDENTITY_NOT_READY",
                    message=(
                        "Normalized records must include source_family and "
                        "source_id before persistence input can be ready."
                    ),
                    field_name="records",
                ),
            ),
        )

    parser_metadata_copy = (
        dict(parser_metadata) if parser_metadata is not None else None
    )
    normalization_metadata_copy = (
        dict(normalization_metadata)
        if normalization_metadata is not None
        else None
    )

    return PersistenceInputBuildResult(
        status=PersistenceInputBuildStatus.READY,
        persistence_input=PersistenceInput(
            source_family=source_family,
            source_id=source_id,
            records=tuple(
                _persistence_record(
                    record,
                    parser_metadata=parser_metadata_copy,
                    normalization_metadata=normalization_metadata_copy,
                )
                for record in normalization_result.records
            ),
            parser_metadata=parser_metadata_copy,
            normalization_metadata=normalization_metadata_copy,
        ),
    )


def _normalization_error_issues(normalization_result: NormalizationResult):
    return tuple(
        issue
        for issue in normalization_result.issues
        if issue.severity == NormalizationIssueSeverity.ERROR
    )


def _record_shape_issues(
    records: tuple[NormalizedRecord, ...],
) -> list[PersistenceInputIssue]:
    issues: list[PersistenceInputIssue] = []
    expected_source_family: str | None = None
    expected_source_id: str | None = None

    for position, record in enumerate(records, start=1):
        fields = dict(record.fields)
        source_family = _required_field_text(fields, "source_family")
        source_id = _required_field_text(fields, "source_id")

        if source_family is None:
            issues.append(
                _missing_record_field_issue(
                    position,
                    "source_family",
                ),
            )
        if source_id is None:
            issues.append(
                _missing_record_field_issue(
                    position,
                    "source_id",
                ),
            )

        if source_family is not None and source_id is not None:
            if expected_source_family is None:
                expected_source_family = source_family
                expected_source_id = source_id
            elif (
                source_family != expected_source_family
                or source_id != expected_source_id
            ):
                issues.append(
                    PersistenceInputIssue(
                        code="PERSISTENCE_INPUT_MIXED_SOURCE_IDENTITY",
                        message=(
                            "Normalized records must share one source_family "
                            "and source_id for a single persistence input."
                        ),
                        field_name=f"records[{position}]",
                    ),
                )

    return issues


def _persistence_record(
    record: NormalizedRecord,
    *,
    parser_metadata: Mapping[str, object] | None,
    normalization_metadata: Mapping[str, object] | None,
) -> PersistenceInputRecord:
    fields = dict(record.fields)
    source_family = _required_field_text(fields, "source_family")
    source_id = _required_field_text(fields, "source_id")

    return PersistenceInputRecord(
        source_family=source_family or "",
        source_id=source_id or "",
        record_id=record.record_id,
        normalized_fields=tuple(record.fields),
        record_index=fields.get("record_index"),
        row_number=fields.get("row_number"),
        source_reference=record.source_reference,
        parser_metadata=dict(parser_metadata) if parser_metadata is not None else None,
        normalization_metadata=(
            dict(normalization_metadata)
            if normalization_metadata is not None
            else None
        ),
    )


def _missing_record_field_issue(
    position: int,
    field_name: str,
) -> PersistenceInputIssue:
    return PersistenceInputIssue(
        code="PERSISTENCE_INPUT_MISSING_SOURCE_IDENTITY",
        message=(
            "Normalized records must include non-empty source_family and source_id "
            "fields before persistence input can be ready."
        ),
        field_name=f"records[{position}].fields.{field_name}",
    )


def _required_field_text(
    fields: Mapping[str, object],
    field_name: str,
) -> str | None:
    value = fields.get(field_name)
    if isinstance(value, str) and value.strip():
        return value
    return None
