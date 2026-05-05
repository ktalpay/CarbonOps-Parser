import carbonfactor_parser
from carbonfactor_parser import (
    ArtificialSourceAcquisitionMetadata,
    ArtificialSourceAcquisitionValidationPipelineResult,
    ArtificialSourceManifestCollectionValidationSummary,
    ArtificialSourceManifestMetadataCollection,
    SourceAcquisitionValidationCount,
    SourceAcquisitionValidationIssue,
    SourceAcquisitionValidationResult,
    SourceAcquisitionValidationSummary,
    create_artificial_source_acquisition_metadata,
    create_source_acquisition_validation_issue,
    create_source_acquisition_validation_result,
    summarize_source_acquisition_validation_result,
    validate_and_summarize_artificial_source_acquisition_metadata,
    validate_artificial_source_acquisition_metadata,
)
from carbonfactor_parser import source_acquisition
from carbonfactor_parser import source_manifest


VALID_CHECKSUM = "b" * 64

EXPECTED_SOURCE_ACQUISITION_PUBLIC_API = (
    "ArtificialSourceAcquisitionMetadata",
    "ArtificialSourceAcquisitionValidationPipelineResult",
    "NoopSourceAcquisitionClient",
    "SourceAcquisitionClient",
    "SourceAcquisitionDescriptor",
    "SourceAcquisitionResult",
    "SourceAcquisitionValidationCount",
    "SourceAcquisitionValidationIssue",
    "SourceAcquisitionValidationResult",
    "SourceAcquisitionValidationSummary",
    "acquire_all_sources",
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
)

EXPECTED_ROOT_PUBLIC_API = (
    "ArtificialSourceAcquisitionMetadata",
    "ArtificialSourceManifestMetadata",
    "ArtificialSourceManifestMetadataCollection",
    "ArtificialSourceManifestCollectionValidationSummary",
    "ArtificialSourceManifestValidationSummary",
    "ArtificialSourceAcquisitionValidationPipelineResult",
    "SourceAcquisitionValidationCount",
    "SourceAcquisitionValidationIssue",
    "SourceAcquisitionValidationResult",
    "SourceAcquisitionValidationSummary",
    "create_artificial_source_acquisition_metadata",
    "create_source_acquisition_validation_issue",
    "create_source_acquisition_validation_result",
    "summarize_source_acquisition_validation_result",
    "validate_and_summarize_artificial_source_acquisition_metadata",
    "validate_artificial_source_acquisition_metadata",
)


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


def test_validation_summary_shape_imports_from_root_package() -> None:
    assert (
        SourceAcquisitionValidationSummary
        is source_acquisition.SourceAcquisitionValidationSummary
    )
    assert (
        carbonfactor_parser.SourceAcquisitionValidationSummary
        is source_acquisition.SourceAcquisitionValidationSummary
    )


def test_validation_count_shape_imports_from_root_package() -> None:
    assert (
        SourceAcquisitionValidationCount
        is source_acquisition.SourceAcquisitionValidationCount
    )
    assert (
        carbonfactor_parser.SourceAcquisitionValidationCount
        is source_acquisition.SourceAcquisitionValidationCount
    )


def test_validation_pipeline_result_shape_imports_from_root_package() -> None:
    assert (
        ArtificialSourceAcquisitionValidationPipelineResult
        is source_acquisition.ArtificialSourceAcquisitionValidationPipelineResult
    )
    assert (
        carbonfactor_parser.ArtificialSourceAcquisitionValidationPipelineResult
        is source_acquisition.ArtificialSourceAcquisitionValidationPipelineResult
    )


def test_manifest_metadata_collection_imports_from_root_package() -> None:
    assert (
        ArtificialSourceManifestMetadataCollection
        is source_manifest.ArtificialSourceManifestMetadataCollection
    )
    assert carbonfactor_parser.ArtificialSourceManifestMetadataCollection is (
        source_manifest.ArtificialSourceManifestMetadataCollection
    )


def test_manifest_collection_validation_summary_imports_from_root_package() -> None:
    assert (
        ArtificialSourceManifestCollectionValidationSummary
        is source_manifest.ArtificialSourceManifestCollectionValidationSummary
    )
    assert carbonfactor_parser.ArtificialSourceManifestCollectionValidationSummary is (
        source_manifest.ArtificialSourceManifestCollectionValidationSummary
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


def test_exported_summary_helper_creates_artificial_summary_shape() -> None:
    issue = create_source_acquisition_validation_issue(
        code="ARTIFICIAL_SOURCE_REQUIRED",
        message="Artificial source metadata field is required.",
        category="metadata_shape",
        severity="error",
        field_name="logical_source_name",
    )
    result = create_source_acquisition_validation_result([issue])

    summary = summarize_source_acquisition_validation_result(result)

    assert summary == SourceAcquisitionValidationSummary(
        total_issue_count=1,
        severity_counts=(
            SourceAcquisitionValidationCount(name="error", count=1),
        ),
        category_counts=(
            SourceAcquisitionValidationCount(name="metadata_shape", count=1),
        ),
        is_valid=False,
    )


def test_exported_pipeline_helper_composes_artificial_shapes() -> None:
    metadata = create_artificial_source_acquisition_metadata(
        source_family="artificial_family",
        logical_source_name="artificial-logical-source",
        declared_content_type="text/csv",
        checksum_sha256=VALID_CHECKSUM,
        acquired_at_label="static-artificial-acquisition-label",
    )

    pipeline_result = validate_and_summarize_artificial_source_acquisition_metadata(
        metadata,
    )

    assert pipeline_result == ArtificialSourceAcquisitionValidationPipelineResult(
        validation_result=validate_artificial_source_acquisition_metadata(metadata),
        summary=summarize_source_acquisition_validation_result(
            validate_artificial_source_acquisition_metadata(metadata),
        ),
    )


def test_artificial_source_acquisition_public_api_is_stable() -> None:
    assert source_acquisition.__all__ == EXPECTED_SOURCE_ACQUISITION_PUBLIC_API

    for name in EXPECTED_SOURCE_ACQUISITION_PUBLIC_API:
        assert hasattr(source_acquisition, name)


def test_validation_helper_imports_from_root_package() -> None:
    assert (
        validate_artificial_source_acquisition_metadata
        is source_acquisition.validate_artificial_source_acquisition_metadata
    )
    assert (
        carbonfactor_parser.validate_artificial_source_acquisition_metadata
        is source_acquisition.validate_artificial_source_acquisition_metadata
    )


def test_root_all_lists_source_acquisition_public_symbols_only() -> None:
    assert carbonfactor_parser.__all__ == EXPECTED_ROOT_PUBLIC_API
