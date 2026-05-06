"""Parser file content input boundary."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParserFileContentInput:
    """Already-loaded parser content prepared for future parsing."""

    source_family: str
    source_id: str
    content: str | bytes
    content_type: str | None = None
    format_hint: str | None = None
    artifact_reference: str | None = None
    checksum_sha256: str | None = None


@dataclass(frozen=True)
class ParserFileContentValidationIssue:
    """Validation issue for parser file content input shape."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class ParserFileContentValidationResult:
    """Validation result for parser file content input shape."""

    issues: tuple[ParserFileContentValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def create_parser_file_content_input(
    *,
    source_family: str,
    source_id: str,
    content: str | bytes,
    content_type: str | None = None,
    format_hint: str | None = None,
    artifact_reference: str | None = None,
    checksum_sha256: str | None = None,
) -> ParserFileContentInput:
    """Create a parser content input without loading files or parsing content."""

    return ParserFileContentInput(
        source_family=source_family,
        source_id=source_id,
        content=content,
        content_type=content_type,
        format_hint=format_hint,
        artifact_reference=artifact_reference,
        checksum_sha256=checksum_sha256,
    )


def validate_parser_file_content_input(
    content_input: ParserFileContentInput,
) -> ParserFileContentValidationResult:
    """Validate already-loaded parser content without parsing it."""

    issues: list[ParserFileContentValidationIssue] = []

    _validate_required_text(
        content_input.source_family,
        "source_family",
        "PARSER_FILE_CONTENT_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        content_input.source_id,
        "source_id",
        "PARSER_FILE_CONTENT_MISSING_SOURCE_ID",
        "source_id must be a non-empty string.",
        issues,
    )
    _validate_required_content(content_input.content, issues)
    _validate_optional_text(
        content_input.content_type,
        "content_type",
        "PARSER_FILE_CONTENT_BLANK_CONTENT_TYPE",
        "content_type must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        content_input.format_hint,
        "format_hint",
        "PARSER_FILE_CONTENT_BLANK_FORMAT_HINT",
        "format_hint must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        content_input.artifact_reference,
        "artifact_reference",
        "PARSER_FILE_CONTENT_BLANK_ARTIFACT_REFERENCE",
        "artifact_reference must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        content_input.checksum_sha256,
        "checksum_sha256",
        "PARSER_FILE_CONTENT_BLANK_CHECKSUM_SHA256",
        "checksum_sha256 must be non-empty when provided.",
        issues,
    )

    return ParserFileContentValidationResult(issues=tuple(issues))


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[ParserFileContentValidationIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            ParserFileContentValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            ),
        )


def _validate_required_content(
    value: str | bytes,
    issues: list[ParserFileContentValidationIssue],
) -> None:
    if isinstance(value, str) and value.strip():
        return
    if isinstance(value, bytes) and value:
        return

    issues.append(
        ParserFileContentValidationIssue(
            code="PARSER_FILE_CONTENT_MISSING_CONTENT",
            message="content must be non-empty already-loaded text or bytes.",
            field_name="content",
        ),
    )


def _validate_optional_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[ParserFileContentValidationIssue],
) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        issues.append(
            ParserFileContentValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            ),
        )
