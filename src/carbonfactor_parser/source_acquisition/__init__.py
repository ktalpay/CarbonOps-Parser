"""Artificial-only source acquisition metadata shape."""

from __future__ import annotations

from dataclasses import dataclass
import re

from carbonfactor_parser.source_acquisition.checksum import compute_sha256_hex
from carbonfactor_parser.source_acquisition.file_store import write_acquired_content
from carbonfactor_parser.source_acquisition.descriptor_validation import (
    SourceDescriptorValidationIssue,
    SourceDescriptorValidationReport,
    serialize_descriptor_validation_report,
    validate_source_descriptors,
)

from carbonfactor_parser.source_acquisition.client import (
    NoopSourceAcquisitionClient,
    SourceAcquisitionClient,
    SourceAcquisitionResult,
    acquire_all_sources,
)
from carbonfactor_parser.source_acquisition.http_client import (
    HttpAcquisitionTransport,
    HttpAcquisitionTransportResponse,
    HttpSourceAcquisitionClient,
)
from carbonfactor_parser.source_acquisition.http_transport import (
    StandardLibraryHttpAcquisitionTransport,
)
from carbonfactor_parser.source_acquisition.manifest import (
    SourceAcquisitionManifestEntry,
    create_manifest_entry,
    serialize_manifest_entries,
    write_acquisition_manifest,
)
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor
from carbonfactor_parser.source_acquisition.registry import (
    create_default_source_acquisition_registry,
    validate_source_acquisition_registry,
)
from carbonfactor_parser.source_acquisition.run import (
    SourceAcquisitionRunResult,
    run_source_acquisition,
)
from carbonfactor_parser.source_acquisition.status import (
    ACQUISITION_FAILED_STATUSES,
    ACQUISITION_KNOWN_STATUSES,
    ACQUISITION_SKIPPED_STATUSES,
    ACQUISITION_STATUS_ACQUIRED,
    ACQUISITION_STATUS_FAILED,
    ACQUISITION_STATUS_NOT_IMPLEMENTED,
    ACQUISITION_STATUS_SKIPPED,
    ACQUISITION_SUCCESS_STATUSES,
    count_acquisition_statuses,
    is_acquired_status,
    is_failed_status,
    is_skipped_status,
)
from carbonfactor_parser.source_acquisition.targets import (
    SourceAcquisitionTarget,
    plan_source_acquisition_target,
    plan_source_acquisition_targets,
)


_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class ArtificialSourceAcquisitionMetadata:
    """Static artificial metadata for source acquisition boundary tests.

    logical_source_name is an artificial label, not a filesystem path.
    acquired_at_label is a static label, not runtime clock behavior.
    checksum_sha256 is deterministic artificial metadata only.
    parser_hint and adapter_hint are non-authoritative hints.
    """

    source_family: str
    logical_source_name: str
    declared_content_type: str
    checksum_sha256: str
    acquired_at_label: str
    parser_hint: str | None = None
    adapter_hint: str | None = None


@dataclass(frozen=True)
class SourceAcquisitionValidationIssue:
    """Artificial-only source acquisition validation issue shape."""

    code: str
    message: str
    category: str
    severity: str
    field_name: str | None = None


@dataclass(frozen=True)
class SourceAcquisitionValidationResult:
    """Artificial-only source acquisition validation result shape."""

    issues: tuple[SourceAcquisitionValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


@dataclass(frozen=True)
class SourceAcquisitionValidationCount:
    """Deterministic count item for artificial validation summaries."""

    name: str
    count: int


@dataclass(frozen=True)
class SourceAcquisitionValidationSummary:
    """Artificial-only source acquisition validation summary shape."""

    total_issue_count: int
    severity_counts: tuple[SourceAcquisitionValidationCount, ...]
    category_counts: tuple[SourceAcquisitionValidationCount, ...]
    is_valid: bool


@dataclass(frozen=True)
class ArtificialSourceAcquisitionValidationPipelineResult:
    """Artificial-only composition of validation result and summary."""

    validation_result: SourceAcquisitionValidationResult
    summary: SourceAcquisitionValidationSummary


def create_artificial_source_acquisition_metadata(
    *,
    source_family: str,
    logical_source_name: str,
    declared_content_type: str,
    checksum_sha256: str,
    acquired_at_label: str,
    parser_hint: str | None = None,
    adapter_hint: str | None = None,
) -> ArtificialSourceAcquisitionMetadata:
    """Create artificial metadata without reading files or external state."""

    metadata = ArtificialSourceAcquisitionMetadata(
        source_family=source_family,
        logical_source_name=logical_source_name,
        declared_content_type=declared_content_type,
        checksum_sha256=checksum_sha256,
        acquired_at_label=acquired_at_label,
        parser_hint=parser_hint,
        adapter_hint=adapter_hint,
    )

    result = validate_artificial_source_acquisition_metadata(metadata)
    if not result.is_valid:
        raise ValueError("; ".join(issue.message for issue in result.issues))

    return metadata


def create_source_acquisition_validation_issue(
    *,
    code: str,
    message: str,
    category: str,
    severity: str,
    field_name: str | None = None,
) -> SourceAcquisitionValidationIssue:
    """Create an artificial validation issue without source validation."""

    issue = SourceAcquisitionValidationIssue(
        code=code,
        message=message,
        category=category,
        severity=severity,
        field_name=field_name,
    )

    issues = _validate_source_acquisition_validation_issue(issue)
    if issues:
        raise ValueError("; ".join(issues))

    return issue


def create_source_acquisition_validation_result(
    issues: (
        tuple[SourceAcquisitionValidationIssue, ...]
        | list[SourceAcquisitionValidationIssue]
    ) = (),
) -> SourceAcquisitionValidationResult:
    """Create an artificial validation result without running validation."""

    normalized_issues = tuple(issues)
    for index, issue in enumerate(normalized_issues):
        if not isinstance(issue, SourceAcquisitionValidationIssue):
            raise TypeError(
                f"issues[{index}] must be a SourceAcquisitionValidationIssue.",
            )

    return SourceAcquisitionValidationResult(issues=normalized_issues)


def validate_artificial_source_acquisition_metadata(
    metadata: ArtificialSourceAcquisitionMetadata,
) -> SourceAcquisitionValidationResult:
    """Validate artificial metadata shape without source correctness claims."""

    if not isinstance(metadata, ArtificialSourceAcquisitionMetadata):
        raise TypeError(
            "metadata must be an ArtificialSourceAcquisitionMetadata.",
        )

    issues: list[SourceAcquisitionValidationIssue] = []

    _validate_required_metadata_field(metadata.source_family, "source_family", issues)
    _validate_required_metadata_field(
        metadata.logical_source_name,
        "logical_source_name",
        issues,
    )
    _validate_required_metadata_field(
        metadata.declared_content_type,
        "declared_content_type",
        issues,
    )
    _validate_required_metadata_field(
        metadata.checksum_sha256,
        "checksum_sha256",
        issues,
    )
    _validate_required_metadata_field(
        metadata.acquired_at_label,
        "acquired_at_label",
        issues,
    )
    _validate_optional_metadata_field(metadata.parser_hint, "parser_hint", issues)
    _validate_optional_metadata_field(metadata.adapter_hint, "adapter_hint", issues)

    if isinstance(metadata.checksum_sha256, str) and metadata.checksum_sha256.strip():
        if _SHA256_HEX_PATTERN.fullmatch(metadata.checksum_sha256) is None:
            issues.append(
                create_source_acquisition_validation_issue(
                    code="SOURCE_ACQUISITION_INVALID_CHECKSUM_SHA256",
                    message="checksum_sha256 must look like 64 hex characters.",
                    category="metadata_shape",
                    severity="error",
                    field_name="checksum_sha256",
                ),
            )

    return create_source_acquisition_validation_result(issues)


def summarize_source_acquisition_validation_result(
    result: SourceAcquisitionValidationResult,
) -> SourceAcquisitionValidationSummary:
    """Summarize artificial validation result issues without validation work."""

    if not isinstance(result, SourceAcquisitionValidationResult):
        raise TypeError("result must be a SourceAcquisitionValidationResult.")

    return SourceAcquisitionValidationSummary(
        total_issue_count=len(result.issues),
        severity_counts=_count_issue_attribute(result.issues, "severity"),
        category_counts=_count_issue_attribute(result.issues, "category"),
        is_valid=result.is_valid,
    )


def validate_and_summarize_artificial_source_acquisition_metadata(
    metadata: ArtificialSourceAcquisitionMetadata,
) -> ArtificialSourceAcquisitionValidationPipelineResult:
    """Compose artificial metadata validation and summary helpers."""

    validation_result = validate_artificial_source_acquisition_metadata(metadata)
    summary = summarize_source_acquisition_validation_result(validation_result)

    return ArtificialSourceAcquisitionValidationPipelineResult(
        validation_result=validation_result,
        summary=summary,
    )


def _validate_required_metadata_field(
    value: object,
    field_name: str,
    issues: list[SourceAcquisitionValidationIssue],
) -> None:
    if isinstance(value, str) and value.strip():
        return

    issues.append(
        create_source_acquisition_validation_issue(
            code="SOURCE_ACQUISITION_REQUIRED_FIELD",
            message=f"{field_name} must be a non-empty string.",
            category="metadata_shape",
            severity="error",
            field_name=field_name,
        ),
    )


def _validate_optional_metadata_field(
    value: object,
    field_name: str,
    issues: list[SourceAcquisitionValidationIssue],
) -> None:
    if value is None:
        return

    if isinstance(value, str) and value.strip():
        return

    issues.append(
        create_source_acquisition_validation_issue(
            code="SOURCE_ACQUISITION_OPTIONAL_FIELD",
            message=f"{field_name} must be None or a non-empty string.",
            category="metadata_shape",
            severity="error",
            field_name=field_name,
        ),
    )


def _count_issue_attribute(
    issues: tuple[SourceAcquisitionValidationIssue, ...],
    attribute_name: str,
) -> tuple[SourceAcquisitionValidationCount, ...]:
    counts: dict[str, int] = {}
    for issue in issues:
        attribute_value = getattr(issue, attribute_name)
        counts[attribute_value] = counts.get(attribute_value, 0) + 1

    return tuple(
        SourceAcquisitionValidationCount(name=name, count=counts[name])
        for name in sorted(counts)
    )


def _validate_source_acquisition_validation_issue(
    issue: SourceAcquisitionValidationIssue,
) -> list[str]:
    issues: list[str] = []

    _validate_required_string(issue.code, "code", issues)
    _validate_required_string(issue.message, "message", issues)
    _validate_required_string(issue.category, "category", issues)
    _validate_required_string(issue.severity, "severity", issues)
    _validate_optional_string(issue.field_name, "field_name", issues)

    return issues


def _validate_required_string(
    value: object,
    field_name: str,
    issues: list[str],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{field_name} must be a non-empty string.")


def _validate_optional_string(
    value: object,
    field_name: str,
    issues: list[str],
) -> None:
    if value is None:
        return

    if not isinstance(value, str) or not value.strip():
        issues.append(f"{field_name} must be None or a non-empty string.")


__all__ = (
    "ArtificialSourceAcquisitionMetadata",
    "ArtificialSourceAcquisitionValidationPipelineResult",
    "NoopSourceAcquisitionClient",
    "HttpAcquisitionTransport",
    "HttpAcquisitionTransportResponse",
    "HttpSourceAcquisitionClient",
    "SourceAcquisitionClient",
    "SourceAcquisitionDescriptor",
    "SourceDescriptorValidationIssue",
    "SourceDescriptorValidationReport",
    "SourceAcquisitionManifestEntry",
    "SourceAcquisitionResult",
    "SourceAcquisitionRunResult",
    "SourceAcquisitionValidationCount",
    "SourceAcquisitionValidationIssue",
    "SourceAcquisitionValidationResult",
    "SourceAcquisitionValidationSummary",
    "acquire_all_sources",
    "run_source_acquisition",
    "create_manifest_entry",
    "create_artificial_source_acquisition_metadata",
    "create_default_source_acquisition_registry",
    "create_source_acquisition_validation_issue",
    "create_source_acquisition_validation_result",
    "summarize_source_acquisition_validation_result",
    "validate_and_summarize_artificial_source_acquisition_metadata",
    "validate_artificial_source_acquisition_metadata",
    "validate_source_acquisition_registry",
    "validate_source_descriptors",
    "serialize_descriptor_validation_report",
    "SourceAcquisitionTarget",
    "plan_source_acquisition_target",
    "plan_source_acquisition_targets",
    "serialize_manifest_entries",
    "write_acquisition_manifest",
    "ACQUISITION_STATUS_ACQUIRED",
    "ACQUISITION_STATUS_FAILED",
    "ACQUISITION_STATUS_SKIPPED",
    "ACQUISITION_STATUS_NOT_IMPLEMENTED",
    "ACQUISITION_SUCCESS_STATUSES",
    "ACQUISITION_FAILED_STATUSES",
    "ACQUISITION_SKIPPED_STATUSES",
    "ACQUISITION_KNOWN_STATUSES",
    "is_acquired_status",
    "is_failed_status",
    "is_skipped_status",
    "count_acquisition_statuses",
)
