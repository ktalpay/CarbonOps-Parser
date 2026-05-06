"""Raw parsed record payload boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ParsedRawRecord:
    """One parser-output raw record before normalization."""

    source_family: str
    source_id: str
    record_index: int
    raw_fields: Mapping[str, object]
    row_number: int | None = None
    parser_metadata: Mapping[str, object] | None = None
    source_context: Mapping[str, object] | None = None


@dataclass(frozen=True)
class ParsedRawRecordPayload:
    """Collection of raw parser records before normalization."""

    source_family: str
    source_id: str
    records: tuple[ParsedRawRecord, ...]
    parser_metadata: Mapping[str, object] | None = None
    source_context: Mapping[str, object] | None = None


@dataclass(frozen=True)
class ParsedRawRecordValidationIssue:
    """Validation issue for raw parsed record payload shape."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class ParsedRawRecordValidationResult:
    """Validation result for raw parsed record payload shape."""

    issues: tuple[ParsedRawRecordValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def create_parsed_raw_record(
    *,
    source_family: str,
    source_id: str,
    record_index: int,
    raw_fields: Mapping[str, object],
    row_number: int | None = None,
    parser_metadata: Mapping[str, object] | None = None,
    source_context: Mapping[str, object] | None = None,
) -> ParsedRawRecord:
    """Create a raw parser record without normalizing values."""

    return ParsedRawRecord(
        source_family=source_family,
        source_id=source_id,
        record_index=record_index,
        raw_fields=dict(raw_fields),
        row_number=row_number,
        parser_metadata=dict(parser_metadata) if parser_metadata is not None else None,
        source_context=dict(source_context) if source_context is not None else None,
    )


def create_parsed_raw_record_payload(
    *,
    source_family: str,
    source_id: str,
    records: tuple[ParsedRawRecord, ...] | list[ParsedRawRecord],
    parser_metadata: Mapping[str, object] | None = None,
    source_context: Mapping[str, object] | None = None,
) -> ParsedRawRecordPayload:
    """Create a raw parser payload without normalization or persistence."""

    return ParsedRawRecordPayload(
        source_family=source_family,
        source_id=source_id,
        records=tuple(records),
        parser_metadata=dict(parser_metadata) if parser_metadata is not None else None,
        source_context=dict(source_context) if source_context is not None else None,
    )


def validate_parsed_raw_record(
    record: ParsedRawRecord,
) -> ParsedRawRecordValidationResult:
    """Validate raw parser record shape without interpreting values."""

    issues: list[ParsedRawRecordValidationIssue] = []

    _validate_required_text(
        record.source_family,
        "source_family",
        "PARSED_RAW_RECORD_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        record.source_id,
        "source_id",
        "PARSED_RAW_RECORD_MISSING_SOURCE_ID",
        "source_id must be a non-empty string.",
        issues,
    )
    if not isinstance(record.record_index, int) or record.record_index < 1:
        issues.append(
            ParsedRawRecordValidationIssue(
                code="PARSED_RAW_RECORD_INVALID_RECORD_INDEX",
                message="record_index must be a positive integer.",
                field_name="record_index",
            ),
        )
    if not isinstance(record.raw_fields, Mapping) or not record.raw_fields:
        issues.append(
            ParsedRawRecordValidationIssue(
                code="PARSED_RAW_RECORD_MISSING_RAW_FIELDS",
                message="raw_fields must be a non-empty mapping.",
                field_name="raw_fields",
            ),
        )

    return ParsedRawRecordValidationResult(issues=tuple(issues))


def validate_parsed_raw_record_payload(
    payload: ParsedRawRecordPayload,
) -> ParsedRawRecordValidationResult:
    """Validate raw parser payload shape without interpreting values."""

    issues: list[ParsedRawRecordValidationIssue] = []
    _validate_required_text(
        payload.source_family,
        "source_family",
        "PARSED_RAW_RECORD_PAYLOAD_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        payload.source_id,
        "source_id",
        "PARSED_RAW_RECORD_PAYLOAD_MISSING_SOURCE_ID",
        "source_id must be a non-empty string.",
        issues,
    )

    for position, record in enumerate(payload.records, start=1):
        for issue in validate_parsed_raw_record(record).issues:
            issues.append(
                ParsedRawRecordValidationIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=f"records[{position}].{issue.field_name}",
                ),
            )

    return ParsedRawRecordValidationResult(issues=tuple(issues))


def _validate_required_text(
    value: str,
    field_name: str,
    code: str,
    message: str,
    issues: list[ParsedRawRecordValidationIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            ParsedRawRecordValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            ),
        )
