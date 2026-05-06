"""Local parser file content loader boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from carbonfactor_parser.parsers.file_content_input import (
    ParserFileContentInput,
    create_parser_file_content_input,
    validate_parser_file_content_input,
)


DEFAULT_PARSER_FILE_CONTENT_MAX_BYTES = 5_000_000


class ParserFileContentLoadStatus(str, Enum):
    """Status values for loading local parser file content."""

    SUCCESS = "success"
    FAILED = "failed"
    NOT_FOUND = "not_found"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ParserFileContentLoadIssue:
    """Structured issue for local parser file content loading."""

    code: str
    message: str
    field_name: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class ParserFileContentLoadResult:
    """Result for explicitly loading local content into parser input."""

    status: ParserFileContentLoadStatus
    content_input: ParserFileContentInput | None = None
    local_path: str | None = None
    issues: tuple[ParserFileContentLoadIssue, ...] = ()

    @property
    def is_success(self) -> bool:
        return self.status == ParserFileContentLoadStatus.SUCCESS


def load_parser_file_content_from_local_path(
    *,
    source_family: str,
    source_id: str,
    local_path: str | Path | None,
    content_type: str | None = None,
    format_hint: str | None = None,
    artifact_reference: str | None = None,
    checksum_sha256: str | None = None,
    max_bytes: int = DEFAULT_PARSER_FILE_CONTENT_MAX_BYTES,
) -> ParserFileContentLoadResult:
    """Load explicit local UTF-8 text content without parsing it."""

    metadata_issue = _metadata_issue(
        source_family=source_family,
        source_id=source_id,
        local_path=local_path,
        content_type=content_type,
        format_hint=format_hint,
        artifact_reference=artifact_reference,
        checksum_sha256=checksum_sha256,
        max_bytes=max_bytes,
    )
    if metadata_issue is not None:
        return ParserFileContentLoadResult(
            status=ParserFileContentLoadStatus.FAILED,
            local_path=_string_path(local_path),
            issues=(metadata_issue,),
        )

    path = Path(str(local_path))
    path_text = str(path)

    if not path.exists():
        return ParserFileContentLoadResult(
            status=ParserFileContentLoadStatus.NOT_FOUND,
            local_path=path_text,
            issues=(
                ParserFileContentLoadIssue(
                    code="PARSER_FILE_CONTENT_LOAD_NOT_FOUND",
                    message="local_path must point to an existing local file.",
                    field_name="local_path",
                ),
            ),
        )

    if path.is_dir():
        return ParserFileContentLoadResult(
            status=ParserFileContentLoadStatus.FAILED,
            local_path=path_text,
            issues=(
                ParserFileContentLoadIssue(
                    code="PARSER_FILE_CONTENT_LOAD_DIRECTORY",
                    message="local_path must point to a file, not a directory.",
                    field_name="local_path",
                ),
            ),
        )

    if not path.is_file():
        return ParserFileContentLoadResult(
            status=ParserFileContentLoadStatus.FAILED,
            local_path=path_text,
            issues=(
                ParserFileContentLoadIssue(
                    code="PARSER_FILE_CONTENT_LOAD_NOT_FILE",
                    message="local_path must point to a regular local file.",
                    field_name="local_path",
                ),
            ),
        )

    try:
        if path.stat().st_size > max_bytes:
            return ParserFileContentLoadResult(
                status=ParserFileContentLoadStatus.UNSUPPORTED,
                local_path=path_text,
                issues=(
                    ParserFileContentLoadIssue(
                        code="PARSER_FILE_CONTENT_LOAD_TOO_LARGE",
                        message="local file exceeds the configured max_bytes guard.",
                        field_name="local_path",
                    ),
                ),
            )

        raw_content = path.read_bytes()
    except OSError as exc:
        return ParserFileContentLoadResult(
            status=ParserFileContentLoadStatus.FAILED,
            local_path=path_text,
            issues=(
                ParserFileContentLoadIssue(
                    code="PARSER_FILE_CONTENT_LOAD_IO_ERROR",
                    message=f"local file could not be loaded: {exc}",
                    field_name="local_path",
                ),
            ),
        )

    try:
        text_content = raw_content.decode("utf-8")
    except UnicodeDecodeError:
        return ParserFileContentLoadResult(
            status=ParserFileContentLoadStatus.UNSUPPORTED,
            local_path=path_text,
            issues=(
                ParserFileContentLoadIssue(
                    code="PARSER_FILE_CONTENT_LOAD_UNSUPPORTED_ENCODING",
                    message="local file content must be valid UTF-8 text.",
                    field_name="local_path",
                ),
            ),
        )

    if "\x00" in text_content:
        return ParserFileContentLoadResult(
            status=ParserFileContentLoadStatus.UNSUPPORTED,
            local_path=path_text,
            issues=(
                ParserFileContentLoadIssue(
                    code="PARSER_FILE_CONTENT_LOAD_BINARY_CONTENT",
                    message="local file content must be UTF-8 text without NUL bytes.",
                    field_name="local_path",
                ),
            ),
        )

    content_input = create_parser_file_content_input(
        source_family=source_family,
        source_id=source_id,
        content=text_content,
        content_type=content_type,
        format_hint=format_hint,
        artifact_reference=artifact_reference or path_text,
        checksum_sha256=checksum_sha256,
    )
    validation_result = validate_parser_file_content_input(content_input)
    if not validation_result.is_valid:
        return ParserFileContentLoadResult(
            status=ParserFileContentLoadStatus.FAILED,
            local_path=path_text,
            issues=tuple(
                ParserFileContentLoadIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=issue.field_name,
                    severity=issue.severity,
                )
                for issue in validation_result.issues
            ),
        )

    return ParserFileContentLoadResult(
        status=ParserFileContentLoadStatus.SUCCESS,
        content_input=content_input,
        local_path=path_text,
    )


def _metadata_issue(
    *,
    source_family: str,
    source_id: str,
    local_path: str | Path | None,
    content_type: str | None,
    format_hint: str | None,
    artifact_reference: str | None,
    checksum_sha256: str | None,
    max_bytes: int,
) -> ParserFileContentLoadIssue | None:
    required_fields = (
        ("source_family", source_family),
        ("source_id", source_id),
        ("local_path", _string_path(local_path)),
    )
    for field_name, value in required_fields:
        if not isinstance(value, str) or not value.strip():
            return ParserFileContentLoadIssue(
                code="PARSER_FILE_CONTENT_LOAD_MISSING_REQUIRED_FIELD",
                message=f"{field_name} must be a non-empty value.",
                field_name=field_name,
            )

    optional_fields = (
        ("content_type", content_type),
        ("format_hint", format_hint),
        ("artifact_reference", artifact_reference),
        ("checksum_sha256", checksum_sha256),
    )
    for field_name, value in optional_fields:
        if value is not None and (not isinstance(value, str) or not value.strip()):
            return ParserFileContentLoadIssue(
                code="PARSER_FILE_CONTENT_LOAD_BLANK_OPTIONAL_FIELD",
                message=f"{field_name} must be non-empty when provided.",
                field_name=field_name,
            )

    if max_bytes <= 0:
        return ParserFileContentLoadIssue(
            code="PARSER_FILE_CONTENT_LOAD_INVALID_MAX_BYTES",
            message="max_bytes must be greater than zero.",
            field_name="max_bytes",
        )

    return None


def _string_path(local_path: str | Path | None) -> str | None:
    if local_path is None:
        return None
    return str(local_path)
