from dataclasses import replace

import pytest

from carbonfactor_parser.source_acquisition import (
    ArtificialSourceAcquisitionMetadata,
    SourceAcquisitionValidationResult,
    create_artificial_source_acquisition_metadata,
    validate_artificial_source_acquisition_metadata,
)


VALID_CHECKSUM = "c" * 64


def valid_metadata() -> ArtificialSourceAcquisitionMetadata:
    return create_artificial_source_acquisition_metadata(
        source_family="artificial_family",
        logical_source_name="artificial-logical-source",
        declared_content_type="text/csv",
        checksum_sha256=VALID_CHECKSUM,
        acquired_at_label="static-artificial-acquisition-label",
    )


def test_valid_metadata_returns_valid_result() -> None:
    result = validate_artificial_source_acquisition_metadata(valid_metadata())

    assert result == SourceAcquisitionValidationResult(issues=())
    assert result.is_valid is True


def test_unsupported_input_raises_type_error() -> None:
    with pytest.raises(
        TypeError,
        match="metadata must be an ArtificialSourceAcquisitionMetadata.",
    ):
        validate_artificial_source_acquisition_metadata(object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "expected_message"),
    [
        ("source_family", "source_family must be a non-empty string."),
        (
            "logical_source_name",
            "logical_source_name must be a non-empty string.",
        ),
        (
            "declared_content_type",
            "declared_content_type must be a non-empty string.",
        ),
        ("checksum_sha256", "checksum_sha256 must be a non-empty string."),
        ("acquired_at_label", "acquired_at_label must be a non-empty string."),
    ],
)
def test_blank_required_fields_are_reported(
    field_name: str,
    expected_message: str,
) -> None:
    result = validate_artificial_source_acquisition_metadata(
        replace(valid_metadata(), **{field_name: " "}),
    )

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].code == "SOURCE_ACQUISITION_REQUIRED_FIELD"
    assert result.issues[0].message == expected_message
    assert result.issues[0].category == "metadata_shape"
    assert result.issues[0].severity == "error"
    assert result.issues[0].field_name == field_name


@pytest.mark.parametrize("checksum", ["c" * 63, "c" * 65, "g" * 64])
def test_invalid_checksum_shape_is_reported(checksum: str) -> None:
    result = validate_artificial_source_acquisition_metadata(
        replace(valid_metadata(), checksum_sha256=checksum),
    )

    assert result.is_valid is False
    assert result.issues[0].code == "SOURCE_ACQUISITION_INVALID_CHECKSUM_SHA256"
    assert result.issues[0].message == (
        "checksum_sha256 must look like 64 hex characters."
    )
    assert result.issues[0].category == "metadata_shape"
    assert result.issues[0].severity == "error"
    assert result.issues[0].field_name == "checksum_sha256"


def test_optional_hints_are_accepted_when_none() -> None:
    metadata = replace(valid_metadata(), parser_hint=None, adapter_hint=None)

    result = validate_artificial_source_acquisition_metadata(metadata)

    assert result.is_valid is True


@pytest.mark.parametrize("field_name", ["parser_hint", "adapter_hint"])
def test_blank_hints_are_reported_when_provided(field_name: str) -> None:
    result = validate_artificial_source_acquisition_metadata(
        replace(valid_metadata(), **{field_name: " "}),
    )

    assert result.is_valid is False
    assert result.issues[0].code == "SOURCE_ACQUISITION_OPTIONAL_FIELD"
    assert result.issues[0].message == (
        f"{field_name} must be None or a non-empty string."
    )
    assert result.issues[0].category == "metadata_shape"
    assert result.issues[0].severity == "error"
    assert result.issues[0].field_name == field_name


def test_multiple_shape_issues_are_returned_in_field_order() -> None:
    metadata = ArtificialSourceAcquisitionMetadata(
        source_family=" ",
        logical_source_name=" ",
        declared_content_type=" ",
        checksum_sha256="not-a-checksum",
        acquired_at_label=" ",
        parser_hint=" ",
        adapter_hint=" ",
    )

    result = validate_artificial_source_acquisition_metadata(metadata)

    assert [issue.field_name for issue in result.issues] == [
        "source_family",
        "logical_source_name",
        "declared_content_type",
        "acquired_at_label",
        "parser_hint",
        "adapter_hint",
        "checksum_sha256",
    ]
