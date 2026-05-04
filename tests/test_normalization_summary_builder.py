from dataclasses import FrozenInstanceError

import pytest

from carbonfactor_parser.normalization import (
    ArtificialNormalizationSummaryBuilder,
    NormalizationIssue,
    NormalizationIssueSeverity,
    NormalizationResult,
    NormalizationResultSummary,
    NormalizedRecord,
)


def _normalization_result() -> NormalizationResult:
    return NormalizationResult(
        records=(
            NormalizedRecord(
                record_id="record-001",
                source_reference="fixture:artificial-normalization",
            ),
            NormalizedRecord(
                record_id="record-002",
                source_reference="fixture:artificial-normalization",
            ),
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


def test_artificial_normalization_summary_builder_is_importable() -> None:
    builder = ArtificialNormalizationSummaryBuilder()

    assert isinstance(builder, ArtificialNormalizationSummaryBuilder)


def test_builder_accepts_normalization_result_and_returns_summary() -> None:
    summary = ArtificialNormalizationSummaryBuilder().build(_normalization_result())

    assert isinstance(summary, NormalizationResultSummary)


def test_builder_counts_records_from_normalized_records_only() -> None:
    result = NormalizationResult(
        records=(
            NormalizedRecord(record_id="record-001"),
            NormalizedRecord(record_id="record-002"),
            NormalizedRecord(record_id="record-003"),
        ),
        issues=(
            NormalizationIssue(
                code="fixture_warning",
                message="Fixture warning",
                severity=NormalizationIssueSeverity.WARNING,
            ),
        ),
    )

    summary = ArtificialNormalizationSummaryBuilder().build(result)

    assert summary.record_count == 3
    assert summary.normalized_record_count == 3


def test_builder_counts_issues_from_normalization_issues_only() -> None:
    summary = ArtificialNormalizationSummaryBuilder().build(_normalization_result())

    assert summary.issue_count == 2
    assert summary.warning_count == 1
    assert summary.error_count == 1
    assert summary.is_clean is False


def test_builder_output_is_deterministic() -> None:
    builder = ArtificialNormalizationSummaryBuilder()
    result = _normalization_result()

    first = builder.build(result)
    second = builder.build(result)

    assert first == second
    assert first.metadata == second.metadata


def test_builder_does_not_mutate_input_result() -> None:
    result = _normalization_result()
    original_records = result.records
    original_issues = result.issues

    ArtificialNormalizationSummaryBuilder().build(result)

    assert result.records == original_records
    assert result.issues == original_issues
    with pytest.raises(FrozenInstanceError):
        result.records = ()


def test_builder_marks_summary_as_artificial_and_preserves_shared_source_reference() -> None:
    summary = ArtificialNormalizationSummaryBuilder().build(_normalization_result())

    assert summary.is_artificial is True
    assert summary.source_family is None
    assert summary.source_id == "fixture:artificial-normalization"
    assert summary.metadata == {
        "source_reference": "fixture:artificial-normalization",
    }


def test_builder_omits_source_reference_when_records_disagree() -> None:
    result = NormalizationResult(
        records=(
            NormalizedRecord(
                record_id="record-001",
                source_reference="fixture:first",
            ),
            NormalizedRecord(
                record_id="record-002",
                source_reference="fixture:second",
            ),
        )
    )

    summary = ArtificialNormalizationSummaryBuilder().build(result)

    assert summary.source_id is None
    assert summary.metadata == {}


def test_builder_handles_empty_normalization_result() -> None:
    summary = ArtificialNormalizationSummaryBuilder().build(NormalizationResult())

    assert summary.record_count == 0
    assert summary.issue_count == 0
    assert summary.has_normalized_records is False
    assert summary.has_warnings is False
    assert summary.has_errors is False
    assert summary.is_clean is True


def test_builder_does_not_require_files_network_config_db_or_scheduler(tmp_path) -> None:
    missing_path = tmp_path / "missing.csv"
    result = NormalizationResult(
        records=(
            NormalizedRecord(
                record_id="record-001",
                source_reference=str(missing_path),
            ),
        )
    )

    summary = ArtificialNormalizationSummaryBuilder().build(result)
    summary_text = str(summary).lower()

    assert summary.record_count == 1
    assert not missing_path.exists()
    assert "://" not in summary_text
    assert "config" not in summary_text
    assert "database" not in summary_text
    assert "credential" not in summary_text
    assert "schedule" not in summary_text
