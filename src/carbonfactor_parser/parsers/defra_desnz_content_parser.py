"""Minimal in-memory DEFRA/DESNZ content parser boundary."""

from __future__ import annotations

import csv
from io import StringIO

from carbonfactor_parser.parsers.execution_result import (
    ParserExecutionIssue,
    ParserExecutionIssueSeverity,
    ParserExecutionResult,
    ParserExecutionResultStatus,
    create_parser_execution_result,
)
from carbonfactor_parser.parsers.file_content_input import (
    ParserFileContentInput,
    validate_parser_file_content_input,
)
from carbonfactor_parser.parsers.input_contract import create_parser_input_contract
from carbonfactor_parser.parsers.raw_record import (
    create_parsed_raw_record,
    create_parsed_raw_record_payload,
)


DEFRA_DESNZ_MINIMAL_CONTENT_HEADER = (
    "factor_id",
    "factor_name",
    "unit",
)

DEFRA_DESNZ_NORMALIZED_CONTENT_HEADER = (
    "source_year",
    "source_version",
    "category",
    "subcategory",
    "activity",
    "factor_id",
    "factor_name",
    "factor_value",
    "unit",
    "greenhouse_gas",
    "provenance",
)

_DEFRA_DESNZ_REQUIRED_NORMALIZED_FIELDS = (
    "source_year",
    "source_version",
    "category",
    "factor_id",
    "factor_name",
    "factor_value",
    "unit",
    "provenance",
)


def parse_defra_desnz_file_content(
    content_input: ParserFileContentInput,
) -> ParserExecutionResult:
    """Parse a tiny already-loaded DEFRA/DESNZ CSV-like fixture format."""

    parser_input = _parser_input_from_content_input(content_input)
    validation_result = validate_parser_file_content_input(content_input)
    if not validation_result.is_valid:
        if _only_missing_content(validation_result):
            return create_parser_execution_result(
                status=ParserExecutionResultStatus.NO_RECORDS,
                parser_input=parser_input,
                issues=(
                    ParserExecutionIssue(
                        code="DEFRA_DESNZ_CONTENT_EMPTY",
                        message="DEFRA/DESNZ content input did not include parseable content.",
                        severity=ParserExecutionIssueSeverity.WARNING,
                        location="content",
                    ),
                ),
                parser_metadata=_parser_metadata(),
            )

        return create_parser_execution_result(
            status=ParserExecutionResultStatus.FAILED,
            parser_input=parser_input,
            issues=tuple(
                ParserExecutionIssue(
                    code=issue.code,
                    message=issue.message,
                    severity=ParserExecutionIssueSeverity.ERROR,
                    location=issue.field_name,
                )
                for issue in validation_result.issues
            ),
            parser_metadata=_parser_metadata(),
        )

    if content_input.source_family != "defra_desnz":
        return create_parser_execution_result(
            status=ParserExecutionResultStatus.FAILED,
            parser_input=parser_input,
            issues=(
                ParserExecutionIssue(
                    code="DEFRA_DESNZ_CONTENT_SOURCE_FAMILY_MISMATCH",
                    message="DEFRA/DESNZ content parser only accepts defra_desnz source_family.",
                    severity=ParserExecutionIssueSeverity.ERROR,
                    location="source_family",
                ),
            ),
            parser_metadata=_parser_metadata(),
        )

    content_text = _content_text(content_input)
    if content_text is None:
        return create_parser_execution_result(
            status=ParserExecutionResultStatus.FAILED,
            parser_input=parser_input,
            issues=(
                ParserExecutionIssue(
                    code="DEFRA_DESNZ_CONTENT_BYTES_DECODE_FAILED",
                    message="DEFRA/DESNZ bytes content must be UTF-8 text for this fixture parser.",
                    severity=ParserExecutionIssueSeverity.ERROR,
                    location="content",
                ),
            ),
            parser_metadata=_parser_metadata(),
        )

    return _parse_minimal_csv(content_text, parser_input)


def _parse_minimal_csv(
    content_text: str,
    parser_input,
) -> ParserExecutionResult:
    reader = csv.DictReader(StringIO(content_text))
    fieldnames = tuple(reader.fieldnames or ())
    if fieldnames == DEFRA_DESNZ_NORMALIZED_CONTENT_HEADER:
        return _parse_normalized_csv(reader, parser_input)
    if fieldnames != DEFRA_DESNZ_MINIMAL_CONTENT_HEADER:
        return create_parser_execution_result(
            status=ParserExecutionResultStatus.FAILED,
            parser_input=parser_input,
            issues=(
                ParserExecutionIssue(
                    code="DEFRA_DESNZ_CONTENT_INVALID_HEADER",
                    message=(
                        "DEFRA/DESNZ content header must match either the "
                        "minimal fixture shape or normalized extraction shape."
                    ),
                    severity=ParserExecutionIssueSeverity.ERROR,
                    location="header",
                ),
            ),
            parser_metadata=_parser_metadata(),
        )

    raw_records = []
    parsed_record_count = 0
    for row_number, row in enumerate(reader, start=2):
        if None in row:
            return create_parser_execution_result(
                status=ParserExecutionResultStatus.FAILED,
                parser_input=parser_input,
                issues=(
                    ParserExecutionIssue(
                        code="DEFRA_DESNZ_CONTENT_INVALID_ROW",
                        message="DEFRA/DESNZ minimal content row has an unexpected column count.",
                        severity=ParserExecutionIssueSeverity.ERROR,
                        location="row",
                    ),
                ),
                parser_metadata=_parser_metadata(),
            )
        if any((value or "").strip() for value in row.values()):
            parsed_record_count += 1
            raw_records.append(
                create_parsed_raw_record(
                    source_family=parser_input.source_family,
                    source_id=parser_input.source_id,
                    record_index=parsed_record_count,
                    row_number=row_number,
                    raw_fields=dict(row),
                    parser_metadata=_parser_metadata(),
                    source_context={
                        "artifact_reference": parser_input.artifact_reference,
                    },
                ),
            )

    if parsed_record_count == 0:
        return create_parser_execution_result(
            status=ParserExecutionResultStatus.NO_RECORDS,
            parser_input=parser_input,
            issues=(
                ParserExecutionIssue(
                    code="DEFRA_DESNZ_CONTENT_NO_RECORDS",
                    message="DEFRA/DESNZ minimal content header was present but no rows were parsed.",
                    severity=ParserExecutionIssueSeverity.WARNING,
                    location="content",
                ),
            ),
            parser_metadata=_parser_metadata(),
        )

    return create_parser_execution_result(
        status=ParserExecutionResultStatus.SUCCESS,
        parser_input=parser_input,
        parsed_record_count=parsed_record_count,
        parser_metadata=_parser_metadata(),
        raw_record_payload=create_parsed_raw_record_payload(
            source_family=parser_input.source_family,
            source_id=parser_input.source_id,
            records=tuple(raw_records),
            parser_metadata=_parser_metadata(),
            source_context={
                "artifact_reference": parser_input.artifact_reference,
            },
        ),
    )


def _parse_normalized_csv(
    reader: csv.DictReader,
    parser_input,
) -> ParserExecutionResult:
    parser_metadata = _parser_metadata(
        parser_kind="defra_desnz_normalized_csv_extraction",
        is_real_source_parser=True,
    )
    issues: list[ParserExecutionIssue] = []
    raw_records = []
    parsed_record_count = 0

    for row_number, row in enumerate(reader, start=2):
        if None in row:
            return create_parser_execution_result(
                status=ParserExecutionResultStatus.FAILED,
                parser_input=parser_input,
                issues=(
                    ParserExecutionIssue(
                        code="DEFRA_DESNZ_CONTENT_INVALID_ROW",
                        message="DEFRA/DESNZ normalized content row has an unexpected column count.",
                        severity=ParserExecutionIssueSeverity.ERROR,
                        location=f"row[{row_number}]",
                    ),
                ),
                parser_metadata=parser_metadata,
            )
        if not any((value or "").strip() for value in row.values()):
            continue

        row_issues = _normalized_row_issues(row, row_number)
        issues.extend(row_issues)
        if row_issues:
            continue

        parsed_record_count += 1
        raw_records.append(
            create_parsed_raw_record(
                source_family=parser_input.source_family,
                source_id=parser_input.source_id,
                record_index=parsed_record_count,
                row_number=row_number,
                raw_fields={key: (value or "").strip() for key, value in row.items()},
                parser_metadata=parser_metadata,
                source_context={
                    "artifact_reference": parser_input.artifact_reference,
                    "source_year": (row.get("source_year") or "").strip(),
                    "source_version": (row.get("source_version") or "").strip(),
                    "provenance": (row.get("provenance") or "").strip(),
                },
            ),
        )

    if issues:
        return create_parser_execution_result(
            status=ParserExecutionResultStatus.FAILED,
            parser_input=parser_input,
            parsed_record_count=parsed_record_count,
            issues=tuple(issues),
            parser_metadata=parser_metadata,
            raw_record_payload=(
                create_parsed_raw_record_payload(
                    source_family=parser_input.source_family,
                    source_id=parser_input.source_id,
                    records=tuple(raw_records),
                    parser_metadata=parser_metadata,
                    source_context={
                        "artifact_reference": parser_input.artifact_reference,
                    },
                )
                if raw_records
                else None
            ),
        )

    if parsed_record_count == 0:
        return create_parser_execution_result(
            status=ParserExecutionResultStatus.NO_RECORDS,
            parser_input=parser_input,
            issues=(
                ParserExecutionIssue(
                    code="DEFRA_DESNZ_CONTENT_NO_RECORDS",
                    message="DEFRA/DESNZ normalized content header was present but no rows were parsed.",
                    severity=ParserExecutionIssueSeverity.WARNING,
                    location="content",
                ),
            ),
            parser_metadata=parser_metadata,
        )

    return create_parser_execution_result(
        status=ParserExecutionResultStatus.SUCCESS,
        parser_input=parser_input,
        parsed_record_count=parsed_record_count,
        parser_metadata=parser_metadata,
        raw_record_payload=create_parsed_raw_record_payload(
            source_family=parser_input.source_family,
            source_id=parser_input.source_id,
            records=tuple(raw_records),
            parser_metadata=parser_metadata,
            source_context={
                "artifact_reference": parser_input.artifact_reference,
            },
        ),
    )


def _normalized_row_issues(
    row: dict[str, str],
    row_number: int,
) -> tuple[ParserExecutionIssue, ...]:
    issues: list[ParserExecutionIssue] = []
    for field_name in _DEFRA_DESNZ_REQUIRED_NORMALIZED_FIELDS:
        if not (row.get(field_name) or "").strip():
            issues.append(
                ParserExecutionIssue(
                    code="DEFRA_DESNZ_CONTENT_MISSING_REQUIRED_FIELD",
                    message=(
                        "DEFRA/DESNZ normalized content row is missing "
                        f"required field: {field_name}."
                    ),
                    severity=ParserExecutionIssueSeverity.ERROR,
                    location=f"row[{row_number}].{field_name}",
                    context={"row_number": row_number, "field_name": field_name},
                ),
            )

    factor_value = (row.get("factor_value") or "").strip()
    if factor_value:
        try:
            float(factor_value)
        except ValueError:
            issues.append(
                ParserExecutionIssue(
                    code="DEFRA_DESNZ_CONTENT_INVALID_FACTOR_VALUE",
                    message="DEFRA/DESNZ normalized factor_value must be numeric.",
                    severity=ParserExecutionIssueSeverity.ERROR,
                    location=f"row[{row_number}].factor_value",
                    context={
                        "row_number": row_number,
                        "field_name": "factor_value",
                        "raw_value": factor_value,
                    },
                ),
            )

    return tuple(issues)


def _content_text(content_input: ParserFileContentInput) -> str | None:
    if isinstance(content_input.content, str):
        return content_input.content
    try:
        return content_input.content.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _only_missing_content(validation_result) -> bool:
    return tuple(issue.code for issue in validation_result.issues) == (
        "PARSER_FILE_CONTENT_MISSING_CONTENT",
    )


def _parser_input_from_content_input(content_input: ParserFileContentInput):
    return create_parser_input_contract(
        source_family=content_input.source_family,
        source_id=content_input.source_id,
        acquisition_status="content_loaded",
        artifact_reference=content_input.artifact_reference or "memory://parser-file-content-input",
        checksum_sha256=content_input.checksum_sha256,
        content_type=content_input.content_type,
        format_hint=content_input.format_hint,
    )


def _parser_metadata(
    *,
    parser_kind: str = "minimal_defra_desnz_content_fixture",
    is_real_source_parser: bool = False,
) -> dict[str, object]:
    return {
        "parser_kind": parser_kind,
        "is_real_source_parser": is_real_source_parser,
        "normalization_executed": False,
    }
