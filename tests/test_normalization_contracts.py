from dataclasses import FrozenInstanceError

import pytest

from carbonfactor_parser.normalization import (
    NormalizationIssue,
    NormalizationIssueSeverity,
    NormalizationResult,
    NormalizationResultSummary,
    NormalizedRecord,
)


def test_normalization_issue_can_represent_warning_and_error() -> None:
    warning = NormalizationIssue(
        code="fixture_warning",
        message="Fixture warning",
        severity=NormalizationIssueSeverity.WARNING,
    )
    error = NormalizationIssue(
        code="fixture_error",
        message="Fixture error",
        severity=NormalizationIssueSeverity.ERROR,
        location="record 1",
    )

    assert warning.severity == NormalizationIssueSeverity.WARNING
    assert error.severity == NormalizationIssueSeverity.ERROR
    assert error.location == "record 1"


def test_normalized_record_can_be_created_with_generic_fields() -> None:
    record = NormalizedRecord(
        record_id="record-001",
        fields=(
            ("category_label", "sample"),
            ("value_label", "example"),
        ),
        source_reference="fixture:source.csv",
    )

    assert record.record_id == "record-001"
    assert record.fields == (
        ("category_label", "sample"),
        ("value_label", "example"),
    )
    assert record.source_reference == "fixture:source.csv"
    assert record.is_artificial is True


def test_normalization_result_can_be_created_with_no_records_or_issues() -> None:
    result = NormalizationResult()

    assert result.records == ()
    assert result.issues == ()
    assert isinstance(result.summary, NormalizationResultSummary)


def test_normalization_result_summary_counts_records_warnings_and_errors() -> None:
    result = NormalizationResult(
        records=(
            NormalizedRecord(record_id="record-001"),
            NormalizedRecord(record_id="record-002"),
        ),
        issues=(
            NormalizationIssue(
                code="fixture_warning",
                message="Fixture warning",
                severity=NormalizationIssueSeverity.WARNING,
            ),
            NormalizationIssue(
                code="fixture_error",
                message="Fixture error",
                severity=NormalizationIssueSeverity.ERROR,
            ),
        ),
    )

    summary = result.summary

    assert summary.normalized_record_count == 2
    assert summary.warning_count == 1
    assert summary.error_count == 1


def test_normalization_result_summary_boolean_flags_for_clean_result() -> None:
    summary = NormalizationResult().summary

    assert summary.has_normalized_records is False
    assert summary.has_warnings is False
    assert summary.has_errors is False
    assert summary.is_clean is True


def test_normalization_result_summary_boolean_flags_for_non_clean_result() -> None:
    result = NormalizationResult(
        records=(NormalizedRecord(record_id="record-001"),),
        issues=(
            NormalizationIssue(
                code="fixture_warning",
                message="Fixture warning",
                severity=NormalizationIssueSeverity.WARNING,
            ),
        ),
    )

    summary = result.summary

    assert summary.has_normalized_records is True
    assert summary.has_warnings is True
    assert summary.has_errors is False
    assert summary.is_clean is False


def test_normalization_result_records_and_issues_are_tuple_based() -> None:
    issue = NormalizationIssue(
        code="fixture_warning",
        message="Fixture warning",
        severity=NormalizationIssueSeverity.WARNING,
    )
    record = NormalizedRecord(record_id="record-001")
    result = NormalizationResult(records=(record,), issues=(issue,))

    assert isinstance(record.fields, tuple)
    assert isinstance(result.records, tuple)
    assert isinstance(result.issues, tuple)


def test_normalization_contract_dataclasses_are_frozen() -> None:
    issue = NormalizationIssue(
        code="fixture_warning",
        message="Fixture warning",
        severity=NormalizationIssueSeverity.WARNING,
    )
    record = NormalizedRecord(record_id="record-001")
    result = NormalizationResult()

    with pytest.raises(FrozenInstanceError):
        issue.code = "changed"
    with pytest.raises(FrozenInstanceError):
        record.record_id = "changed"
    with pytest.raises(FrozenInstanceError):
        result.records = ()


def test_normalization_contracts_do_not_require_file_io(tmp_path) -> None:
    missing_path = tmp_path / "missing.csv"
    result = NormalizationResult(
        records=(
            NormalizedRecord(
                record_id="record-001",
                source_reference=str(missing_path),
            ),
        )
    )

    assert result.summary.normalized_record_count == 1
    assert not missing_path.exists()
