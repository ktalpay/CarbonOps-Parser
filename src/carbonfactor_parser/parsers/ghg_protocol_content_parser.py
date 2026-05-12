"""GHG Protocol content parser for deterministic normalized factor rows."""

from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
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


GHG_PROTOCOL_NORMALIZED_CONTENT_HEADER = (
    "record_type",
    "source_year",
    "source_version",
    "factor_id",
    "factor_name",
    "factor_value",
    "unit",
    "category",
    "subcategory",
    "scope",
    "gas",
    "provenance_note",
)

_REQUIRED_FIELDS = (
    "source_year",
    "source_version",
    "factor_id",
    "factor_name",
    "factor_value",
    "unit",
    "category",
)


def parse_ghg_protocol_file_content(
    content_input: ParserFileContentInput,
) -> ParserExecutionResult:
    """Parse already-loaded GHG Protocol normalized CSV fixture content."""

    parser_input = _parser_input_from_content_input(content_input)
    validation_result = validate_parser_file_content_input(content_input)
    if not validation_result.is_valid:
        if _only_missing_content(validation_result):
            return create_parser_execution_result(
                status=ParserExecutionResultStatus.NO_RECORDS,
                parser_input=parser_input,
                issues=(
                    ParserExecutionIssue(
                        code="GHG_PROTOCOL_CONTENT_EMPTY",
                        message="GHG Protocol content input did not include parseable content.",
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

    if content_input.source_family != "ghg_protocol":
        return create_parser_execution_result(
            status=ParserExecutionResultStatus.FAILED,
            parser_input=parser_input,
            issues=(
                ParserExecutionIssue(
                    code="GHG_PROTOCOL_CONTENT_SOURCE_FAMILY_MISMATCH",
                    message="GHG Protocol content parser only accepts ghg_protocol source_family.",
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
                    code="GHG_PROTOCOL_CONTENT_BYTES_DECODE_FAILED",
                    message="GHG Protocol bytes content must be UTF-8 CSV text.",
                    severity=ParserExecutionIssueSeverity.ERROR,
                    location="content",
                ),
            ),
            parser_metadata=_parser_metadata(),
        )

    return _parse_normalized_csv(content_text, parser_input)


def _parse_normalized_csv(content_text: str, parser_input) -> ParserExecutionResult:
    reader = csv.DictReader(StringIO(content_text))
    if tuple(reader.fieldnames or ()) != GHG_PROTOCOL_NORMALIZED_CONTENT_HEADER:
        return create_parser_execution_result(
            status=ParserExecutionResultStatus.FAILED,
            parser_input=parser_input,
            issues=(
                ParserExecutionIssue(
                    code="GHG_PROTOCOL_CONTENT_INVALID_HEADER",
                    message=(
                        "GHG Protocol normalized content header must match the "
                        "declared parser contract."
                    ),
                    severity=ParserExecutionIssueSeverity.ERROR,
                    location="header",
                    context={
                        "expected_header": GHG_PROTOCOL_NORMALIZED_CONTENT_HEADER,
                    },
                ),
            ),
            parser_metadata=_parser_metadata(),
        )

    issues: list[ParserExecutionIssue] = []
    raw_records = []
    parsed_record_count = 0
    skipped_record_count = 0

    for row_number, row in enumerate(reader, start=2):
        if None in row:
            issues.append(
                ParserExecutionIssue(
                    code="GHG_PROTOCOL_CONTENT_INVALID_ROW",
                    message="GHG Protocol content row has an unexpected column count.",
                    severity=ParserExecutionIssueSeverity.ERROR,
                    location=f"row[{row_number}]",
                    context={"row_number": row_number},
                ),
            )
            continue

        normalized_row = _trim_row(row)
        if not any(normalized_row.values()):
            continue

        if normalized_row["record_type"] != "emission_factor":
            skipped_record_count += 1
            issues.append(
                ParserExecutionIssue(
                    code="GHG_PROTOCOL_CONTENT_UNSUPPORTED_ROW_SKIPPED",
                    message="GHG Protocol content row was skipped because record_type is unsupported.",
                    severity=ParserExecutionIssueSeverity.WARNING,
                    location=f"row[{row_number}].record_type",
                    context={
                        "row_number": row_number,
                        "record_type": normalized_row["record_type"],
                    },
                ),
            )
            continue

        row_issues = _row_issues(normalized_row, row_number)
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
                raw_fields=_normalized_raw_fields(
                    normalized_row,
                    parser_input,
                    row_number,
                ),
                parser_metadata=_parser_metadata(skipped_record_count),
                source_context=_source_context(parser_input, row_number),
            ),
        )

    if any(issue.severity == ParserExecutionIssueSeverity.ERROR for issue in issues):
        return create_parser_execution_result(
            status=ParserExecutionResultStatus.FAILED,
            parser_input=parser_input,
            issues=tuple(issues),
            parser_metadata=_parser_metadata(skipped_record_count),
        )

    if parsed_record_count == 0:
        return create_parser_execution_result(
            status=ParserExecutionResultStatus.NO_RECORDS,
            parser_input=parser_input,
            issues=(
                *tuple(issues),
                ParserExecutionIssue(
                    code="GHG_PROTOCOL_CONTENT_NO_RECORDS",
                    message="GHG Protocol normalized content included no parseable emission factor rows.",
                    severity=ParserExecutionIssueSeverity.WARNING,
                    location="content",
                ),
            ),
            parser_metadata=_parser_metadata(skipped_record_count),
        )

    return create_parser_execution_result(
        status=ParserExecutionResultStatus.SUCCESS,
        parser_input=parser_input,
        parsed_record_count=parsed_record_count,
        issues=tuple(issues),
        parser_metadata=_parser_metadata(skipped_record_count),
        raw_record_payload=create_parsed_raw_record_payload(
            source_family=parser_input.source_family,
            source_id=parser_input.source_id,
            records=tuple(raw_records),
            parser_metadata=_parser_metadata(skipped_record_count),
            source_context={
                "artifact_reference": parser_input.artifact_reference,
                "checksum_sha256": parser_input.checksum_sha256,
            },
        ),
    )


def _trim_row(row: dict[str | None, str | None]) -> dict[str, str]:
    return {
        field_name: (row.get(field_name) or "").strip()
        for field_name in GHG_PROTOCOL_NORMALIZED_CONTENT_HEADER
    }


def _row_issues(row: dict[str, str], row_number: int) -> tuple[ParserExecutionIssue, ...]:
    issues: list[ParserExecutionIssue] = []
    for field_name in _REQUIRED_FIELDS:
        if not row[field_name]:
            issues.append(
                ParserExecutionIssue(
                    code="GHG_PROTOCOL_CONTENT_MISSING_REQUIRED_FIELD",
                    message=(
                        "GHG Protocol emission factor row is missing required "
                        f"field: {field_name}."
                    ),
                    severity=ParserExecutionIssueSeverity.ERROR,
                    location=f"row[{row_number}].{field_name}",
                    context={"row_number": row_number, "field_name": field_name},
                ),
            )

    try:
        source_year = int(row["source_year"])
    except ValueError:
        source_year = 0
    if source_year < 1:
        issues.append(
            ParserExecutionIssue(
                code="GHG_PROTOCOL_CONTENT_INVALID_SOURCE_YEAR",
                message="GHG Protocol source_year must be a positive integer.",
                severity=ParserExecutionIssueSeverity.ERROR,
                location=f"row[{row_number}].source_year",
                context={"row_number": row_number},
            ),
        )

    try:
        Decimal(row["factor_value"])
    except InvalidOperation:
        issues.append(
            ParserExecutionIssue(
                code="GHG_PROTOCOL_CONTENT_INVALID_FACTOR_VALUE",
                message="GHG Protocol factor_value must be a decimal number.",
                severity=ParserExecutionIssueSeverity.ERROR,
                location=f"row[{row_number}].factor_value",
                context={"row_number": row_number},
            ),
        )

    return tuple(issues)


def _normalized_raw_fields(
    row: dict[str, str],
    parser_input,
    row_number: int,
) -> dict[str, object]:
    master_id = f"ghg_master_{row['source_year']}_{row['source_version']}_{row['factor_id']}"
    detail_id = f"ghg_detail_{row['source_year']}_{row['source_version']}_{row['factor_id']}"

    return {
        "source_family": parser_input.source_family,
        "source_id": parser_input.source_id,
        "source_year": int(row["source_year"]),
        "source_version": row["source_version"],
        "factor_id": row["factor_id"],
        "factor_name": row["factor_name"],
        "factor_value": Decimal(row["factor_value"]),
        "unit": row["unit"],
        "category": row["category"],
        "subcategory": row["subcategory"] or None,
        "scope": row["scope"] or None,
        "gas": row["gas"] or None,
        "provenance_note": row["provenance_note"] or None,
        "provenance_artifact_reference": parser_input.artifact_reference,
        "provenance_checksum_algorithm": "sha256"
        if parser_input.checksum_sha256
        else None,
        "provenance_checksum_value": parser_input.checksum_sha256,
        "provenance_row_number": row_number,
        "source_family_master_id": master_id,
        "source_family_detail_id": detail_id,
        "master_external_key": (
            f"{row['source_year']}:{row['source_version']}:{row['factor_id']}"
        ),
        "detail_external_key": f"{row['factor_id']}:{row['unit']}",
    }


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


def _source_context(parser_input, row_number: int) -> dict[str, object]:
    return {
        "artifact_reference": parser_input.artifact_reference,
        "checksum_sha256": parser_input.checksum_sha256,
        "row_number": row_number,
    }


def _parser_metadata(skipped_record_count: int = 0) -> dict[str, object]:
    return {
        "parser_kind": "ghg_protocol_normalized_content",
        "is_real_source_parser": True,
        "normalization_executed": True,
        "skipped_record_count": skipped_record_count,
    }
