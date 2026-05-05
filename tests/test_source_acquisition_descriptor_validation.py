from __future__ import annotations

import json

from carbonfactor_parser.source_acquisition.descriptor_validation import (
    serialize_descriptor_validation_report,
    validate_source_descriptors,
)
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor
from carbonfactor_parser.source_acquisition.registry import create_default_source_acquisition_registry


def test_default_registry_validation_report_is_deterministic() -> None:
    report = validate_source_descriptors(create_default_source_acquisition_registry())
    assert report.issue_count == 2
    assert report.warning_count == 2
    assert report.error_count == 0
    assert [issue.source_id for issue in report.issues] == ["defra_desnz", "ipcc_efdb"]


def test_duplicate_source_id_is_reported_as_error() -> None:
    descriptors = (
        SourceAcquisitionDescriptor("dup", "a", "A", "h1", "u1", "csv", "a", True),
        SourceAcquisitionDescriptor("dup", "b", "B", "h2", "u2", "csv", "b", True),
    )
    report = validate_source_descriptors(descriptors)
    assert report.error_count == 1
    assert any(issue.field == "source_id" and issue.severity == "error" for issue in report.issues)


def test_missing_required_fields_and_non_bool_enabled_are_errors() -> None:
    descriptors = (
        SourceAcquisitionDescriptor("", "", "", "", "", "", "desc", "yes"),  # type: ignore[arg-type]
    )
    report = validate_source_descriptors(descriptors)
    assert report.error_count == 7
    assert sorted(issue.field for issue in report.issues if issue.severity == "error") == [
        "acquisition_url",
        "display_name",
        "enabled",
        "expected_format",
        "homepage_url",
        "source_family",
        "source_id",
    ]


def test_equal_acquisition_and_homepage_url_adds_warning() -> None:
    descriptors = (
        SourceAcquisitionDescriptor("same", "fam", "Same", "x", "x", "csv", "desc", True),
    )
    report = validate_source_descriptors(descriptors)
    assert report.warning_count == 1
    assert report.issues[0].severity == "warning"


def test_report_json_serialization_is_deterministic() -> None:
    report = validate_source_descriptors(create_default_source_acquisition_registry())
    first = serialize_descriptor_validation_report(report)
    second = serialize_descriptor_validation_report(report)
    assert first == second
    payload = json.loads(first)
    assert payload["issue_count"] == 2
    assert payload["warning_count"] == 2
    assert payload["error_count"] == 0
