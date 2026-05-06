"""Parser input contract for acquired artifacts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class ParserInputContract:
    """Source acquisition output prepared for future parser execution."""

    source_family: str
    source_id: str
    acquisition_status: str
    artifact_reference: str | None = None
    checksum_sha256: str | None = None
    content_type: str | None = None
    format_hint: str | None = None
    acquisition_run_id: str | None = None
    run_metadata: Mapping[str, object] | None = None
    manifest_metadata: Mapping[str, object] | None = None


@dataclass(frozen=True)
class ParserInputValidationIssue:
    """Validation issue for parser input contract shape."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class ParserInputValidationResult:
    """Validation result for parser input contract shape."""

    issues: tuple[ParserInputValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def create_parser_input_contract(
    *,
    source_family: str,
    source_id: str,
    acquisition_status: str,
    artifact_reference: str | None = None,
    checksum_sha256: str | None = None,
    content_type: str | None = None,
    format_hint: str | None = None,
    acquisition_run_id: str | None = None,
    run_metadata: Mapping[str, object] | None = None,
    manifest_metadata: Mapping[str, object] | None = None,
) -> ParserInputContract:
    """Create a parser input contract without touching artifact contents."""

    return ParserInputContract(
        source_family=source_family,
        source_id=source_id,
        acquisition_status=acquisition_status,
        artifact_reference=artifact_reference,
        checksum_sha256=checksum_sha256,
        content_type=content_type,
        format_hint=format_hint,
        acquisition_run_id=acquisition_run_id,
        run_metadata=dict(run_metadata) if run_metadata is not None else None,
        manifest_metadata=(
            dict(manifest_metadata) if manifest_metadata is not None else None
        ),
    )


def validate_parser_input_contract(
    parser_input: ParserInputContract,
) -> ParserInputValidationResult:
    """Validate parser input metadata without touching artifact contents."""

    issues: list[ParserInputValidationIssue] = []

    _validate_required_text(
        parser_input.source_family,
        "source_family",
        "PARSER_INPUT_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        parser_input.source_id,
        "source_id",
        "PARSER_INPUT_MISSING_SOURCE_ID",
        "source_id must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        parser_input.artifact_reference,
        "artifact_reference",
        "PARSER_INPUT_MISSING_ARTIFACT_REFERENCE",
        "artifact_reference must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        parser_input.acquisition_status,
        "acquisition_status",
        "PARSER_INPUT_MISSING_ACQUISITION_STATUS",
        "acquisition_status must be a non-empty string.",
        issues,
    )
    _validate_optional_text(
        parser_input.checksum_sha256,
        "checksum_sha256",
        "PARSER_INPUT_BLANK_CHECKSUM_SHA256",
        "checksum_sha256 must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        parser_input.content_type,
        "content_type",
        "PARSER_INPUT_BLANK_CONTENT_TYPE",
        "content_type must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        parser_input.format_hint,
        "format_hint",
        "PARSER_INPUT_BLANK_FORMAT_HINT",
        "format_hint must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        parser_input.acquisition_run_id,
        "acquisition_run_id",
        "PARSER_INPUT_BLANK_ACQUISITION_RUN_ID",
        "acquisition_run_id must be non-empty when provided.",
        issues,
    )
    _validate_optional_mapping(
        parser_input.run_metadata,
        "run_metadata",
        "PARSER_INPUT_EMPTY_RUN_METADATA",
        "run_metadata must be a non-empty mapping when provided.",
        issues,
    )
    _validate_optional_mapping(
        parser_input.manifest_metadata,
        "manifest_metadata",
        "PARSER_INPUT_EMPTY_MANIFEST_METADATA",
        "manifest_metadata must be a non-empty mapping when provided.",
        issues,
    )

    return ParserInputValidationResult(issues=tuple(issues))


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[ParserInputValidationIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            ParserInputValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            ),
        )


def _validate_optional_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[ParserInputValidationIssue],
) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        issues.append(
            ParserInputValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            ),
        )


def _validate_optional_mapping(
    value: Mapping[str, object] | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[ParserInputValidationIssue],
) -> None:
    if value is not None and (not isinstance(value, Mapping) or not value):
        issues.append(
            ParserInputValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            ),
        )
