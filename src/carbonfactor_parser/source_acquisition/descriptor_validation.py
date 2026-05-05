"""Deterministic descriptor validation and reporting helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Literal

from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor

ValidationSeverity = Literal["warning", "error"]


@dataclass(frozen=True)
class SourceDescriptorValidationIssue:
    """One deterministic descriptor validation issue."""

    source_id: str
    field: str
    severity: ValidationSeverity
    message: str


@dataclass(frozen=True)
class SourceDescriptorValidationReport:
    """Deterministic descriptor validation report for descriptor metadata."""

    issues: tuple[SourceDescriptorValidationIssue, ...]
    issue_count: int
    warning_count: int
    error_count: int


def validate_source_descriptors(
    descriptors: tuple[SourceAcquisitionDescriptor, ...] | list[SourceAcquisitionDescriptor],
) -> SourceDescriptorValidationReport:
    """Validate descriptor metadata using local deterministic rules only."""

    normalized = tuple(descriptors)
    issues: list[SourceDescriptorValidationIssue] = []
    seen_source_ids: dict[str, int] = {}

    for index, descriptor in enumerate(normalized):
        source_id = descriptor.source_id
        display_source_id = source_id if source_id.strip() else f"<index:{index}>"

        _append_required_string_issue(issues, source_id, "source_id", display_source_id)
        _append_required_string_issue(issues, descriptor.source_family, "source_family", display_source_id)
        _append_required_string_issue(issues, descriptor.display_name, "display_name", display_source_id)
        _append_required_string_issue(issues, descriptor.homepage_url, "homepage_url", display_source_id)
        _append_required_string_issue(issues, descriptor.acquisition_url, "acquisition_url", display_source_id)
        _append_required_string_issue(issues, descriptor.expected_format, "expected_format", display_source_id)

        if not isinstance(descriptor.enabled, bool):
            issues.append(
                SourceDescriptorValidationIssue(
                    source_id=display_source_id,
                    field="enabled",
                    severity="error",
                    message="enabled must be a bool.",
                )
            )

        if descriptor.acquisition_url == descriptor.homepage_url:
            issues.append(
                SourceDescriptorValidationIssue(
                    source_id=display_source_id,
                    field="acquisition_url",
                    severity="warning",
                    message=(
                        "acquisition_url matches homepage_url; this may be a discovery URL "
                        "instead of a direct acquisition endpoint."
                    ),
                )
            )

        if source_id in seen_source_ids:
            first_index = seen_source_ids[source_id]
            issues.append(
                SourceDescriptorValidationIssue(
                    source_id=display_source_id,
                    field="source_id",
                    severity="error",
                    message=(
                        "duplicate source_id found in descriptor registry "
                        f"(first index {first_index}, duplicate index {index})."
                    ),
                )
            )
        else:
            seen_source_ids[source_id] = index

    return create_source_descriptor_validation_report(tuple(issues))


def create_source_descriptor_validation_report(
    issues: tuple[SourceDescriptorValidationIssue, ...],
) -> SourceDescriptorValidationReport:
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    error_count = sum(1 for issue in issues if issue.severity == "error")
    return SourceDescriptorValidationReport(
        issues=issues,
        issue_count=len(issues),
        warning_count=warning_count,
        error_count=error_count,
    )


def serialize_descriptor_validation_report(report: SourceDescriptorValidationReport) -> str:
    """Serialize validation report into deterministic JSON."""

    payload = {
        "issue_count": report.issue_count,
        "warning_count": report.warning_count,
        "error_count": report.error_count,
        "issues": [
            {
                "source_id": issue.source_id,
                "field": issue.field,
                "severity": issue.severity,
                "message": issue.message,
            }
            for issue in report.issues
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=False)


def _append_required_string_issue(
    issues: list[SourceDescriptorValidationIssue],
    value: str,
    field: str,
    source_id: str,
) -> None:
    if not value.strip():
        issues.append(
            SourceDescriptorValidationIssue(
                source_id=source_id,
                field=field,
                severity="error",
                message=f"{field} must be a non-empty string.",
            )
        )
