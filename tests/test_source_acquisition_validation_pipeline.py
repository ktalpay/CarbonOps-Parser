from dataclasses import replace

from carbonfactor_parser.source_acquisition import (
    ArtificialSourceAcquisitionMetadata,
    ArtificialSourceAcquisitionValidationPipelineResult,
    SourceAcquisitionValidationCount,
    create_artificial_source_acquisition_metadata,
    summarize_source_acquisition_validation_result,
    validate_and_summarize_artificial_source_acquisition_metadata,
    validate_artificial_source_acquisition_metadata,
)


VALID_CHECKSUM = "d" * 64


def valid_metadata() -> ArtificialSourceAcquisitionMetadata:
    return create_artificial_source_acquisition_metadata(
        source_family="artificial_family",
        logical_source_name="artificial-logical-source",
        declared_content_type="text/csv",
        checksum_sha256=VALID_CHECKSUM,
        acquired_at_label="static-artificial-acquisition-label",
    )


def test_valid_metadata_produces_valid_result_and_summary() -> None:
    pipeline_result = validate_and_summarize_artificial_source_acquisition_metadata(
        valid_metadata(),
    )

    assert isinstance(
        pipeline_result,
        ArtificialSourceAcquisitionValidationPipelineResult,
    )
    assert pipeline_result.validation_result.is_valid is True
    assert pipeline_result.summary.is_valid is True
    assert pipeline_result.summary.total_issue_count == 0


def test_invalid_artificial_shape_produces_invalid_result_and_summary() -> None:
    metadata = replace(valid_metadata(), checksum_sha256="not-a-checksum")

    pipeline_result = validate_and_summarize_artificial_source_acquisition_metadata(
        metadata,
    )

    assert pipeline_result.validation_result.is_valid is False
    assert pipeline_result.summary.is_valid is False
    assert pipeline_result.summary.severity_counts == (
        SourceAcquisitionValidationCount(name="error", count=1),
    )
    assert pipeline_result.summary.category_counts == (
        SourceAcquisitionValidationCount(name="metadata_shape", count=1),
    )


def test_pipeline_summary_total_issue_count_matches_validation_result() -> None:
    metadata = ArtificialSourceAcquisitionMetadata(
        source_family=" ",
        logical_source_name=" ",
        declared_content_type="text/csv",
        checksum_sha256="not-a-checksum",
        acquired_at_label="static-artificial-acquisition-label",
    )

    pipeline_result = validate_and_summarize_artificial_source_acquisition_metadata(
        metadata,
    )

    assert pipeline_result.summary.total_issue_count == len(
        pipeline_result.validation_result.issues,
    )


def test_pipeline_does_not_mutate_metadata() -> None:
    metadata = valid_metadata()
    expected_metadata = valid_metadata()

    validate_and_summarize_artificial_source_acquisition_metadata(metadata)

    assert metadata == expected_metadata


def test_pipeline_uses_existing_helper_outputs_consistently() -> None:
    metadata = replace(valid_metadata(), parser_hint=" ")

    pipeline_result = validate_and_summarize_artificial_source_acquisition_metadata(
        metadata,
    )
    expected_validation_result = validate_artificial_source_acquisition_metadata(
        metadata,
    )
    expected_summary = summarize_source_acquisition_validation_result(
        expected_validation_result,
    )

    assert pipeline_result.validation_result == expected_validation_result
    assert pipeline_result.summary == expected_summary
