"""Runtime-passive parser input artifact metadata contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from carbonfactor_parser.parsers.adapter_registry_contract import (
    Phase1ParserAdapterRegistry,
    get_phase1_parser_adapter_by_source_family,
)
from carbonfactor_parser.parsers.source_format_contract import ParserSourceFormat


@dataclass(frozen=True)
class ParserInputArtifact:
    """Metadata-only artifact input prepared for a Phase 1 parser adapter."""

    source_family: str
    source_key: str
    parser_key: str
    parser_source_format: ParserSourceFormat
    format_hint: str
    artifact_reference: str
    original_filename: str | None = None
    display_name: str | None = None
    checksum_sha256: str | None = None
    content_type: str | None = None
    extension: str | None = None
    reporting_year: int | None = None


@dataclass(frozen=True)
class ParserInputArtifactValidationIssue:
    """Validation issue for parser input artifact metadata."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class ParserInputArtifactValidationResult:
    """Structural validation result for parser input artifact metadata."""

    issues: tuple[ParserInputArtifactValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def create_phase1_parser_input_artifact(
    *,
    source_family: str,
    artifact_reference: str,
    original_filename: str | None = None,
    display_name: str | None = None,
    checksum_sha256: str | None = None,
    content_type: str | None = None,
    extension: str | None = None,
    reporting_year: int | None = None,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> ParserInputArtifact:
    """Create parser input artifact metadata from the adapter registry."""

    descriptor = get_phase1_parser_adapter_by_source_family(
        source_family,
        registry,
    )
    if descriptor is None:
        raise ValueError(
            "source_family is not registered for a Phase 1 parser adapter."
        )

    return ParserInputArtifact(
        source_family=descriptor.source_family,
        source_key=descriptor.source_family,
        parser_key=descriptor.parser_key,
        parser_source_format=descriptor.capability.parser_source_format,
        format_hint=descriptor.capability.format_hint,
        artifact_reference=artifact_reference,
        original_filename=original_filename,
        display_name=display_name,
        checksum_sha256=checksum_sha256,
        content_type=content_type,
        extension=extension,
        reporting_year=reporting_year,
    )


def validate_parser_input_artifact(
    artifact: ParserInputArtifact,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> ParserInputArtifactValidationResult:
    """Validate parser input artifact metadata without touching contents."""

    issues: list[ParserInputArtifactValidationIssue] = []

    _validate_required_text(
        artifact.source_family,
        "source_family",
        "PARSER_INPUT_ARTIFACT_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        artifact.source_key,
        "source_key",
        "PARSER_INPUT_ARTIFACT_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        artifact.parser_key,
        "parser_key",
        "PARSER_INPUT_ARTIFACT_MISSING_PARSER_KEY",
        "parser_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        _metadata_value(artifact.parser_source_format),
        "parser_source_format",
        "PARSER_INPUT_ARTIFACT_MISSING_SOURCE_FORMAT",
        "parser_source_format must be provided.",
        issues,
    )
    _validate_required_text(
        artifact.format_hint,
        "format_hint",
        "PARSER_INPUT_ARTIFACT_MISSING_FORMAT_HINT",
        "format_hint must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        artifact.artifact_reference,
        "artifact_reference",
        "PARSER_INPUT_ARTIFACT_MISSING_REFERENCE",
        "artifact_reference must be a non-empty string.",
        issues,
    )

    _validate_optional_text(
        artifact.original_filename,
        "original_filename",
        "PARSER_INPUT_ARTIFACT_BLANK_ORIGINAL_FILENAME",
        "original_filename must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        artifact.display_name,
        "display_name",
        "PARSER_INPUT_ARTIFACT_BLANK_DISPLAY_NAME",
        "display_name must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        artifact.checksum_sha256,
        "checksum_sha256",
        "PARSER_INPUT_ARTIFACT_BLANK_CHECKSUM_SHA256",
        "checksum_sha256 must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        artifact.content_type,
        "content_type",
        "PARSER_INPUT_ARTIFACT_BLANK_CONTENT_TYPE",
        "content_type must be non-empty when provided.",
        issues,
    )
    _validate_optional_text(
        artifact.extension,
        "extension",
        "PARSER_INPUT_ARTIFACT_BLANK_EXTENSION",
        "extension must be non-empty when provided.",
        issues,
    )
    if artifact.reporting_year is not None and (
        not isinstance(artifact.reporting_year, int)
        or artifact.reporting_year <= 0
    ):
        issues.append(
            ParserInputArtifactValidationIssue(
                code="PARSER_INPUT_ARTIFACT_INVALID_REPORTING_YEAR",
                message="reporting_year must be a positive integer when provided.",
                field_name="reporting_year",
            )
        )

    descriptor = get_phase1_parser_adapter_by_source_family(
        artifact.source_family,
        registry,
    )
    if descriptor is None:
        issues.append(
            ParserInputArtifactValidationIssue(
                code="PARSER_INPUT_ARTIFACT_UNKNOWN_SOURCE_FAMILY",
                message="source_family must match a registered Phase 1 parser adapter.",
                field_name="source_family",
            )
        )
    else:
        _validate_registry_alignment(artifact, descriptor, issues)

    return ParserInputArtifactValidationResult(issues=tuple(issues))


def _validate_registry_alignment(
    artifact: ParserInputArtifact,
    descriptor: Any,
    issues: list[ParserInputArtifactValidationIssue],
) -> None:
    if artifact.source_key != descriptor.source_family:
        issues.append(
            ParserInputArtifactValidationIssue(
                code="PARSER_INPUT_ARTIFACT_SOURCE_KEY_MISMATCH",
                message="source_key must match the registered source_family.",
                field_name="source_key",
            )
        )
    if artifact.parser_key != descriptor.parser_key:
        issues.append(
            ParserInputArtifactValidationIssue(
                code="PARSER_INPUT_ARTIFACT_PARSER_KEY_MISMATCH",
                message="parser_key must match the registered parser adapter.",
                field_name="parser_key",
            )
        )
    if artifact.parser_source_format is not descriptor.capability.parser_source_format:
        issues.append(
            ParserInputArtifactValidationIssue(
                code="PARSER_INPUT_ARTIFACT_SOURCE_FORMAT_MISMATCH",
                message=(
                    "parser_source_format must match the registered parser "
                    "adapter capability."
                ),
                field_name="parser_source_format",
            )
        )
    if artifact.format_hint != descriptor.capability.format_hint:
        issues.append(
            ParserInputArtifactValidationIssue(
                code="PARSER_INPUT_ARTIFACT_FORMAT_HINT_MISMATCH",
                message="format_hint must match the registered parser adapter capability.",
                field_name="format_hint",
            )
        )


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[ParserInputArtifactValidationIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            ParserInputArtifactValidationIssue(
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
    issues: list[ParserInputArtifactValidationIssue],
) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        issues.append(
            ParserInputArtifactValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )


def _metadata_value(value: Any) -> str | None:
    if value is None:
        return None
    enum_value = getattr(value, "value", value)
    return str(enum_value)
