import pytest

from carbonfactor_parser.source_acquisition import (
    SourceAcquisitionValidationCount,
    SourceAcquisitionValidationIssue,
    SourceAcquisitionValidationSummary,
    create_source_acquisition_validation_issue,
    create_source_acquisition_validation_result,
    summarize_source_acquisition_validation_result,
)


def issue(
    *,
    code: str,
    category: str,
    severity: str,
) -> SourceAcquisitionValidationIssue:
    return create_source_acquisition_validation_issue(
        code=code,
        message=f"{code} artificial shape issue.",
        category=category,
        severity=severity,
    )


def test_empty_validation_result_summary_is_valid() -> None:
    result = create_source_acquisition_validation_result()

    summary = summarize_source_acquisition_validation_result(result)

    assert summary == SourceAcquisitionValidationSummary(
        total_issue_count=0,
        severity_counts=(),
        category_counts=(),
        is_valid=True,
    )


def test_validation_result_with_issues_is_invalid() -> None:
    result = create_source_acquisition_validation_result(
        [
            issue(
                code="SOURCE_ACQUISITION_REQUIRED_FIELD",
                category="metadata_shape",
                severity="error",
            ),
        ],
    )

    summary = summarize_source_acquisition_validation_result(result)

    assert summary.is_valid is False


def test_total_issue_count_is_correct() -> None:
    result = create_source_acquisition_validation_result(
        [
            issue(
                code="SOURCE_ACQUISITION_REQUIRED_FIELD",
                category="metadata_shape",
                severity="error",
            ),
            issue(
                code="SOURCE_ACQUISITION_OPTIONAL_FIELD",
                category="hint_shape",
                severity="warning",
            ),
        ],
    )

    summary = summarize_source_acquisition_validation_result(result)

    assert summary.total_issue_count == 2


def test_severity_counts_are_correct_and_deterministic() -> None:
    result = create_source_acquisition_validation_result(
        [
            issue(
                code="SOURCE_ACQUISITION_OPTIONAL_FIELD",
                category="hint_shape",
                severity="warning",
            ),
            issue(
                code="SOURCE_ACQUISITION_REQUIRED_FIELD",
                category="metadata_shape",
                severity="error",
            ),
            issue(
                code="SOURCE_ACQUISITION_INVALID_CHECKSUM_SHA256",
                category="metadata_shape",
                severity="error",
            ),
        ],
    )

    summary = summarize_source_acquisition_validation_result(result)

    assert summary.severity_counts == (
        SourceAcquisitionValidationCount(name="error", count=2),
        SourceAcquisitionValidationCount(name="warning", count=1),
    )


def test_category_counts_are_correct_and_deterministic() -> None:
    result = create_source_acquisition_validation_result(
        [
            issue(
                code="SOURCE_ACQUISITION_OPTIONAL_FIELD",
                category="hint_shape",
                severity="warning",
            ),
            issue(
                code="SOURCE_ACQUISITION_REQUIRED_FIELD",
                category="metadata_shape",
                severity="error",
            ),
            issue(
                code="SOURCE_ACQUISITION_INVALID_CHECKSUM_SHA256",
                category="metadata_shape",
                severity="error",
            ),
        ],
    )

    summary = summarize_source_acquisition_validation_result(result)

    assert summary.category_counts == (
        SourceAcquisitionValidationCount(name="hint_shape", count=1),
        SourceAcquisitionValidationCount(name="metadata_shape", count=2),
    )


def test_summary_does_not_mutate_original_result() -> None:
    issues = (
        create_source_acquisition_validation_issue(
            code="SOURCE_ACQUISITION_REQUIRED_FIELD",
            message="Artificial source metadata field is required.",
            category="metadata_shape",
            severity="error",
        ),
    )
    result = create_source_acquisition_validation_result(issues)

    summarize_source_acquisition_validation_result(result)

    assert result.issues is issues
    assert result.issues == issues


def test_non_result_input_raises_type_error() -> None:
    with pytest.raises(
        TypeError,
        match="result must be a SourceAcquisitionValidationResult.",
    ):
        summarize_source_acquisition_validation_result(object())  # type: ignore[arg-type]
