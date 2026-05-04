import carbonfactor_parser
from carbonfactor_parser import (
    ArtificialSourceAcquisitionMetadata,
    SourceAcquisitionValidationIssue,
    SourceAcquisitionValidationResult,
    create_artificial_source_acquisition_metadata,
    create_source_acquisition_validation_issue,
    create_source_acquisition_validation_result,
)
from carbonfactor_parser import source_acquisition


VALID_CHECKSUM = "b" * 64


def test_artificial_metadata_model_imports_from_root_package() -> None:
    assert (
        ArtificialSourceAcquisitionMetadata
        is source_acquisition.ArtificialSourceAcquisitionMetadata
    )
    assert (
        carbonfactor_parser.ArtificialSourceAcquisitionMetadata
        is source_acquisition.ArtificialSourceAcquisitionMetadata
    )


def test_artificial_metadata_factory_imports_from_root_package() -> None:
    assert (
        create_artificial_source_acquisition_metadata
        is source_acquisition.create_artificial_source_acquisition_metadata
    )
    assert (
        carbonfactor_parser.create_artificial_source_acquisition_metadata
        is source_acquisition.create_artificial_source_acquisition_metadata
    )


def test_exported_factory_creates_artificial_metadata_shape() -> None:
    metadata = create_artificial_source_acquisition_metadata(
        source_family="artificial_family",
        logical_source_name="artificial-logical-source",
        declared_content_type="text/csv",
        checksum_sha256=VALID_CHECKSUM,
        acquired_at_label="static-artificial-acquisition-label",
        parser_hint="non-authoritative-parser-hint",
        adapter_hint="non-authoritative-adapter-hint",
    )

    assert metadata == ArtificialSourceAcquisitionMetadata(
        source_family="artificial_family",
        logical_source_name="artificial-logical-source",
        declared_content_type="text/csv",
        checksum_sha256=VALID_CHECKSUM,
        acquired_at_label="static-artificial-acquisition-label",
        parser_hint="non-authoritative-parser-hint",
        adapter_hint="non-authoritative-adapter-hint",
    )


def test_validation_issue_shape_imports_from_root_package() -> None:
    assert (
        SourceAcquisitionValidationIssue
        is source_acquisition.SourceAcquisitionValidationIssue
    )
    assert (
        carbonfactor_parser.SourceAcquisitionValidationIssue
        is source_acquisition.SourceAcquisitionValidationIssue
    )


def test_validation_result_shape_imports_from_root_package() -> None:
    assert (
        SourceAcquisitionValidationResult
        is source_acquisition.SourceAcquisitionValidationResult
    )
    assert (
        carbonfactor_parser.SourceAcquisitionValidationResult
        is source_acquisition.SourceAcquisitionValidationResult
    )


def test_exported_validation_result_factory_creates_artificial_result_shape() -> None:
    issue = create_source_acquisition_validation_issue(
        code="ARTIFICIAL_SOURCE_REQUIRED",
        message="Artificial source metadata field is required.",
        category="metadata_shape",
        severity="error",
        field_name="logical_source_name",
    )
    result = create_source_acquisition_validation_result([issue])

    assert issue == SourceAcquisitionValidationIssue(
        code="ARTIFICIAL_SOURCE_REQUIRED",
        message="Artificial source metadata field is required.",
        category="metadata_shape",
        severity="error",
        field_name="logical_source_name",
    )
    assert result == SourceAcquisitionValidationResult(issues=(issue,))
    assert result.is_valid is False


def test_root_all_lists_source_acquisition_public_symbols_only() -> None:
    assert carbonfactor_parser.__all__ == (
        "ArtificialSourceAcquisitionMetadata",
        "SourceAcquisitionValidationIssue",
        "SourceAcquisitionValidationResult",
        "create_artificial_source_acquisition_metadata",
        "create_source_acquisition_validation_issue",
        "create_source_acquisition_validation_result",
    )
