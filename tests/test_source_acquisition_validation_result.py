import pytest

from carbonfactor_parser.source_acquisition import (
    SourceAcquisitionValidationIssue,
    SourceAcquisitionValidationResult,
    create_source_acquisition_validation_issue,
    create_source_acquisition_validation_result,
)


def valid_issue() -> SourceAcquisitionValidationIssue:
    return create_source_acquisition_validation_issue(
        code="ARTIFICIAL_SOURCE_REQUIRED",
        message="Artificial source metadata field is required.",
        category="metadata_shape",
        severity="error",
        field_name="logical_source_name",
    )


def test_issue_creation_with_required_fields() -> None:
    issue = valid_issue()

    assert issue == SourceAcquisitionValidationIssue(
        code="ARTIFICIAL_SOURCE_REQUIRED",
        message="Artificial source metadata field is required.",
        category="metadata_shape",
        severity="error",
        field_name="logical_source_name",
    )


@pytest.mark.parametrize(
    ("field_name", "expected_message"),
    [
        ("code", "code must be a non-empty string."),
        ("message", "message must be a non-empty string."),
        ("category", "category must be a non-empty string."),
        ("severity", "severity must be a non-empty string."),
    ],
)
def test_blank_required_issue_fields_are_rejected(
    field_name: str,
    expected_message: str,
) -> None:
    kwargs = {
        "code": "ARTIFICIAL_SOURCE_REQUIRED",
        "message": "Artificial source metadata field is required.",
        "category": "metadata_shape",
        "severity": "error",
    }
    kwargs[field_name] = " "

    with pytest.raises(ValueError, match=expected_message):
        create_source_acquisition_validation_issue(**kwargs)


def test_field_name_is_optional() -> None:
    issue = create_source_acquisition_validation_issue(
        code="ARTIFICIAL_SOURCE_SHAPE",
        message="Artificial source metadata shape issue.",
        category="metadata_shape",
        severity="warning",
    )

    assert issue.field_name is None


def test_blank_field_name_is_rejected_when_provided() -> None:
    with pytest.raises(
        ValueError,
        match="field_name must be None or a non-empty string.",
    ):
        create_source_acquisition_validation_issue(
            code="ARTIFICIAL_SOURCE_SHAPE",
            message="Artificial source metadata shape issue.",
            category="metadata_shape",
            severity="warning",
            field_name=" ",
        )


def test_result_with_no_issues_is_valid() -> None:
    result = create_source_acquisition_validation_result()

    assert result == SourceAcquisitionValidationResult(issues=())
    assert result.is_valid is True


def test_result_with_issues_is_invalid() -> None:
    result = create_source_acquisition_validation_result([valid_issue()])

    assert result.is_valid is False


def test_result_issues_are_stored_as_tuple() -> None:
    issue = valid_issue()
    result = create_source_acquisition_validation_result([issue])

    assert result.issues == (issue,)


def test_tuple_issues_are_preserved() -> None:
    issues = (valid_issue(),)
    result = create_source_acquisition_validation_result(issues)

    assert result.issues is issues


def test_issue_list_mutation_after_creation_does_not_mutate_result() -> None:
    issues = [valid_issue()]
    result = create_source_acquisition_validation_result(issues)
    issues.append(
        create_source_acquisition_validation_issue(
            code="ARTIFICIAL_SOURCE_EXTRA",
            message="Additional artificial shape issue.",
            category="metadata_shape",
            severity="warning",
        ),
    )

    assert result.issues == (issues[0],)


def test_result_rejects_non_issue_entries() -> None:
    with pytest.raises(
        TypeError,
        match=r"issues\[0\] must be a SourceAcquisitionValidationIssue.",
    ):
        create_source_acquisition_validation_result(["not an issue"])  # type: ignore[list-item]
