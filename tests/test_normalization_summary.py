import pytest

from carbonfactor_parser.normalization import NormalizationResultSummary


def test_normalization_result_summary_can_be_constructed_with_valid_values() -> None:
    summary = NormalizationResultSummary(
        record_count=2,
        issue_count=1,
        source_family="artificial",
        source_id="fixture-source",
        metadata={"example": "true"},
    )

    assert summary.record_count == 2
    assert summary.issue_count == 1
    assert summary.source_family == "artificial"
    assert summary.source_id == "fixture-source"
    assert summary.is_artificial is True
    assert summary.metadata == {"example": "true"}


def test_normalization_result_summary_rejects_negative_record_count() -> None:
    with pytest.raises(ValueError, match="record_count"):
        NormalizationResultSummary(record_count=-1, issue_count=0)


def test_normalization_result_summary_rejects_negative_issue_count() -> None:
    with pytest.raises(ValueError, match="issue_count"):
        NormalizationResultSummary(record_count=0, issue_count=-1)


def test_normalization_result_summary_metadata_is_isolated_from_caller_mutation() -> None:
    metadata = {"source": "artificial"}
    summary = NormalizationResultSummary(
        record_count=1,
        issue_count=0,
        metadata=metadata,
    )

    metadata["source"] = "changed"

    assert summary.metadata == {"source": "artificial"}
    with pytest.raises(TypeError):
        summary.metadata["source"] = "changed"


def test_normalization_result_summary_supports_existing_count_aliases() -> None:
    summary = NormalizationResultSummary(
        normalized_record_count=1,
        warning_count=1,
        error_count=0,
    )

    assert summary.record_count == 1
    assert summary.issue_count == 1
    assert summary.normalized_record_count == 1
    assert summary.has_normalized_records is True
    assert summary.has_warnings is True
    assert summary.has_errors is False
    assert summary.is_clean is False


def test_normalization_result_summary_does_not_require_file_io(tmp_path) -> None:
    missing_path = tmp_path / "missing.csv"

    summary = NormalizationResultSummary(
        record_count=1,
        issue_count=0,
        source_id=str(missing_path),
    )

    assert summary.source_id == str(missing_path)
    assert not missing_path.exists()
