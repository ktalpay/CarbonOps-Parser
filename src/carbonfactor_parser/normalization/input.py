"""Normalization input boundary built from parser raw payloads."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from carbonfactor_parser.normalization.handoff import (
    ParserExecutionNormalizationHandoffResult,
    ParserExecutionNormalizationHandoffStatus,
)
from carbonfactor_parser.parsers.raw_record import (
    ParsedRawRecord,
    ParsedRawRecordPayload,
)


class NormalizationInputBuildStatus(str, Enum):
    """Status for building future normalization input."""

    READY = "ready"
    NOT_READY = "not_ready"


@dataclass(frozen=True)
class NormalizationInputIssue:
    """Issue explaining why normalization input is not ready."""

    code: str
    message: str
    field_name: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class NormalizationInputRecord:
    """One raw parser record prepared for future normalization."""

    source_family: str
    source_id: str
    record_index: int
    raw_fields: Mapping[str, object]
    row_number: int | None = None
    parser_metadata: Mapping[str, object] | None = None
    source_context: Mapping[str, object] | None = None


@dataclass(frozen=True)
class NormalizationInput:
    """Raw parser records prepared for a future normalization boundary."""

    source_family: str
    source_id: str
    records: tuple[NormalizationInputRecord, ...]
    parser_metadata: Mapping[str, object] | None = None
    source_context: Mapping[str, object] | None = None


@dataclass(frozen=True)
class NormalizationInputBuildResult:
    """Structured result for building normalization input."""

    status: NormalizationInputBuildStatus
    normalization_input: NormalizationInput | None = None
    issues: tuple[NormalizationInputIssue, ...] = ()


@dataclass(frozen=True)
class NormalizationInputValidationResult:
    """Validation result for normalization input shape."""

    issues: tuple[NormalizationInputIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def create_normalization_input_record_from_raw_record(
    raw_record: ParsedRawRecord,
) -> NormalizationInputRecord:
    """Copy a raw parser record into normalization input without transforming it."""

    return NormalizationInputRecord(
        source_family=raw_record.source_family,
        source_id=raw_record.source_id,
        record_index=raw_record.record_index,
        row_number=raw_record.row_number,
        raw_fields=dict(raw_record.raw_fields),
        parser_metadata=(
            dict(raw_record.parser_metadata)
            if raw_record.parser_metadata is not None
            else None
        ),
        source_context=(
            dict(raw_record.source_context)
            if raw_record.source_context is not None
            else None
        ),
    )


def create_normalization_input_from_raw_payload(
    raw_payload: ParsedRawRecordPayload,
) -> NormalizationInput:
    """Copy parser raw payload into normalization input without normalization."""

    return NormalizationInput(
        source_family=raw_payload.source_family,
        source_id=raw_payload.source_id,
        records=tuple(
            create_normalization_input_record_from_raw_record(record)
            for record in raw_payload.records
        ),
        parser_metadata=(
            dict(raw_payload.parser_metadata)
            if raw_payload.parser_metadata is not None
            else None
        ),
        source_context=(
            dict(raw_payload.source_context)
            if raw_payload.source_context is not None
            else None
        ),
    )


def build_normalization_input_from_raw_payload(
    raw_payload: ParsedRawRecordPayload,
) -> NormalizationInputBuildResult:
    """Build normalization input from raw payload without executing normalization."""

    normalization_input = create_normalization_input_from_raw_payload(raw_payload)
    validation_result = validate_normalization_input(normalization_input)
    if not validation_result.is_valid:
        return NormalizationInputBuildResult(
            status=NormalizationInputBuildStatus.NOT_READY,
            issues=validation_result.issues,
        )

    return NormalizationInputBuildResult(
        status=NormalizationInputBuildStatus.READY,
        normalization_input=normalization_input,
    )


def build_normalization_input_from_parser_execution_handoff(
    handoff_result: ParserExecutionNormalizationHandoffResult,
) -> NormalizationInputBuildResult:
    """Build normalization input from a ready parser execution handoff."""

    if (
        handoff_result.status != ParserExecutionNormalizationHandoffStatus.READY
        or handoff_result.handoff is None
    ):
        return NormalizationInputBuildResult(
            status=NormalizationInputBuildStatus.NOT_READY,
            issues=(
                NormalizationInputIssue(
                    code="NORMALIZATION_INPUT_HANDOFF_NOT_READY",
                    message=(
                        "Parser execution handoff must be ready before "
                        "normalization input can be built."
                    ),
                    field_name="handoff",
                ),
            ),
        )

    raw_payload = handoff_result.handoff.raw_record_payload
    if raw_payload is None:
        return NormalizationInputBuildResult(
            status=NormalizationInputBuildStatus.NOT_READY,
            issues=(
                NormalizationInputIssue(
                    code="NORMALIZATION_INPUT_RAW_PAYLOAD_MISSING",
                    message=(
                        "Parser execution handoff must include raw record "
                        "payload before normalization input can be built."
                    ),
                    field_name="raw_record_payload",
                ),
            ),
        )

    return build_normalization_input_from_raw_payload(raw_payload)


def validate_normalization_input_record(
    record: NormalizationInputRecord,
) -> NormalizationInputValidationResult:
    """Validate normalization input record shape without interpreting values."""

    issues: list[NormalizationInputIssue] = []
    _validate_required_text(
        record.source_family,
        "source_family",
        "NORMALIZATION_INPUT_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        record.source_id,
        "source_id",
        "NORMALIZATION_INPUT_MISSING_SOURCE_ID",
        "source_id must be a non-empty string.",
        issues,
    )
    if not isinstance(record.record_index, int) or record.record_index < 1:
        issues.append(
            NormalizationInputIssue(
                code="NORMALIZATION_INPUT_INVALID_RECORD_INDEX",
                message="record_index must be a positive integer.",
                field_name="record_index",
            ),
        )
    if not isinstance(record.raw_fields, Mapping) or not record.raw_fields:
        issues.append(
            NormalizationInputIssue(
                code="NORMALIZATION_INPUT_MISSING_RAW_FIELDS",
                message="raw_fields must be a non-empty mapping.",
                field_name="raw_fields",
            ),
        )

    return NormalizationInputValidationResult(issues=tuple(issues))


def validate_normalization_input(
    normalization_input: NormalizationInput,
) -> NormalizationInputValidationResult:
    """Validate normalization input shape without normalizing records."""

    issues: list[NormalizationInputIssue] = []
    _validate_required_text(
        normalization_input.source_family,
        "source_family",
        "NORMALIZATION_INPUT_PAYLOAD_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        normalization_input.source_id,
        "source_id",
        "NORMALIZATION_INPUT_PAYLOAD_MISSING_SOURCE_ID",
        "source_id must be a non-empty string.",
        issues,
    )
    if not normalization_input.records:
        issues.append(
            NormalizationInputIssue(
                code="NORMALIZATION_INPUT_PAYLOAD_MISSING_RECORDS",
                message="records must include at least one input record.",
                field_name="records",
            ),
        )

    for position, record in enumerate(normalization_input.records, start=1):
        for issue in validate_normalization_input_record(record).issues:
            issues.append(
                NormalizationInputIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=f"records[{position}].{issue.field_name}",
                ),
            )

    return NormalizationInputValidationResult(issues=tuple(issues))


def _validate_required_text(
    value: str,
    field_name: str,
    code: str,
    message: str,
    issues: list[NormalizationInputIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            NormalizationInputIssue(
                code=code,
                message=message,
                field_name=field_name,
            ),
        )
