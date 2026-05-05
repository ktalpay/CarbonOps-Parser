from dataclasses import FrozenInstanceError, replace

import pytest

from carbonfactor_parser.source_acquisition import (
    ArtificialSourceAcquisitionMetadata,
    SourceAcquisitionValidationResult,
    create_artificial_source_acquisition_metadata,
    validate_artificial_source_acquisition_metadata,
)


VALID_CHECKSUM = "a" * 64


def valid_metadata() -> ArtificialSourceAcquisitionMetadata:
    return create_artificial_source_acquisition_metadata(
        source_family="artificial_family",
        logical_source_name="artificial-logical-source",
        declared_content_type="text/csv",
        checksum_sha256=VALID_CHECKSUM,
        acquired_at_label="static-artificial-acquisition-label",
        parser_hint="artificial-parser-hint",
        adapter_hint="artificial-adapter-hint",
    )


def test_valid_artificial_metadata_can_be_created() -> None:
    metadata = valid_metadata()

    assert metadata == ArtificialSourceAcquisitionMetadata(
        source_family="artificial_family",
        logical_source_name="artificial-logical-source",
        declared_content_type="text/csv",
        checksum_sha256=VALID_CHECKSUM,
        acquired_at_label="static-artificial-acquisition-label",
        parser_hint="artificial-parser-hint",
        adapter_hint="artificial-adapter-hint",
    )
    assert validate_artificial_source_acquisition_metadata(
        metadata,
    ) == SourceAcquisitionValidationResult()


def test_metadata_is_immutable() -> None:
    metadata = valid_metadata()

    with pytest.raises(FrozenInstanceError):
        metadata.source_family = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field_name", "expected_issue"),
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
def test_blank_required_fields_are_rejected(
    field_name: str,
    expected_issue: str,
) -> None:
    metadata = replace(valid_metadata(), **{field_name: " "})

    result = validate_artificial_source_acquisition_metadata(metadata)

    assert [issue.message for issue in result.issues] == [expected_issue]


@pytest.mark.parametrize(
    "checksum",
    [
        "a" * 63,
        "a" * 65,
        "g" * 64,
        "not-a-checksum",
    ],
)
def test_invalid_checksum_shape_is_rejected(checksum: str) -> None:
    metadata = replace(valid_metadata(), checksum_sha256=checksum)

    result = validate_artificial_source_acquisition_metadata(metadata)

    assert [issue.message for issue in result.issues] == [
        "checksum_sha256 must look like 64 hex characters.",
    ]


def test_checksum_shape_accepts_uppercase_hex_characters() -> None:
    metadata = replace(valid_metadata(), checksum_sha256="A" * 64)

    assert validate_artificial_source_acquisition_metadata(
        metadata,
    ) == SourceAcquisitionValidationResult()


def test_parser_hint_and_adapter_hint_are_optional() -> None:
    metadata = create_artificial_source_acquisition_metadata(
        source_family="artificial_family",
        logical_source_name="artificial-logical-source",
        declared_content_type="text/csv",
        checksum_sha256=VALID_CHECKSUM,
        acquired_at_label="static-artificial-acquisition-label",
    )

    assert metadata.parser_hint is None
    assert metadata.adapter_hint is None
    assert validate_artificial_source_acquisition_metadata(
        metadata,
    ) == SourceAcquisitionValidationResult()


@pytest.mark.parametrize(
    ("field_name", "expected_issue"),
    [
        ("parser_hint", "parser_hint must be None or a non-empty string."),
        ("adapter_hint", "adapter_hint must be None or a non-empty string."),
    ],
)
def test_blank_parser_hint_and_adapter_hint_are_rejected_when_provided(
    field_name: str,
    expected_issue: str,
) -> None:
    metadata = replace(valid_metadata(), **{field_name: " "})

    result = validate_artificial_source_acquisition_metadata(metadata)

    assert [issue.message for issue in result.issues] == [expected_issue]


def test_factory_rejects_invalid_artificial_metadata_shape() -> None:
    with pytest.raises(
        ValueError,
        match="source_family must be a non-empty string.",
    ):
        create_artificial_source_acquisition_metadata(
            source_family=" ",
            logical_source_name="artificial-logical-source",
            declared_content_type="text/csv",
            checksum_sha256=VALID_CHECKSUM,
            acquired_at_label="static-artificial-acquisition-label",
        )


def test_non_metadata_input_raises_type_error() -> None:
    with pytest.raises(
        TypeError,
        match="metadata must be an ArtificialSourceAcquisitionMetadata.",
    ):
        validate_artificial_source_acquisition_metadata(object())  # type: ignore[arg-type]


def test_logical_source_name_is_label_only() -> None:
    metadata = create_artificial_source_acquisition_metadata(
        source_family="artificial_family",
        logical_source_name="not/a/filesystem/path.csv",
        declared_content_type="text/csv",
        checksum_sha256=VALID_CHECKSUM,
        acquired_at_label="static-artificial-acquisition-label",
    )

    assert metadata.logical_source_name == "not/a/filesystem/path.csv"
    assert validate_artificial_source_acquisition_metadata(
        metadata,
    ) == SourceAcquisitionValidationResult()


def test_module_public_symbols_include_artificial_source_acquisition_shapes() -> None:
    from carbonfactor_parser import source_acquisition

    assert source_acquisition.__all__ == (
        "ArtificialSourceAcquisitionMetadata",
        "ArtificialSourceAcquisitionValidationPipelineResult",
        "NoopSourceAcquisitionClient",
        "HttpAcquisitionTransport",
        "HttpAcquisitionTransportResponse",
        "HttpSourceAcquisitionClient",
        "SourceAcquisitionClient",
        "SourceAcquisitionDescriptor",
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
