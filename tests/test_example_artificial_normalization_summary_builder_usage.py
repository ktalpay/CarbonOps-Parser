import inspect

from carbonfactor_parser.normalization import ArtificialNormalizationSummaryBuilder
from examples import example_artificial_normalization_summary_builder_usage as example
from examples.example_artificial_normalization_summary_builder_usage import run_example


def test_artificial_normalization_summary_builder_usage_is_importable_and_callable() -> None:
    result = run_example()

    assert isinstance(result, dict)


def test_artificial_normalization_summary_builder_usage_returns_deterministic_output() -> None:
    first = run_example()
    second = run_example()

    assert first == second
    assert tuple(first) == (
        "record_count",
        "issue_count",
        "source_family",
        "source_id",
        "is_artificial",
        "metadata",
        "warning_count",
        "error_count",
        "has_normalized_records",
        "has_warnings",
        "has_errors",
        "is_clean",
    )


def test_artificial_normalization_summary_builder_usage_constructs_result_directly() -> None:
    source = inspect.getsource(example.run_example)

    assert "NormalizationResult(" in source
    assert "NormalizedRecord(" in source
    assert "NormalizationIssue(" in source


def test_artificial_normalization_summary_builder_usage_uses_builder() -> None:
    source = inspect.getsource(example.run_example)

    assert example.ArtificialNormalizationSummaryBuilder is ArtificialNormalizationSummaryBuilder
    assert "ArtificialNormalizationSummaryBuilder().build(result)" in source
    assert "ArtificialNormalizationExecutor" not in source


def test_artificial_normalization_summary_builder_usage_returns_summary_fields() -> None:
    result = run_example()

    assert result["record_count"] == 2
    assert result["issue_count"] == 1
    assert result["source_family"] is None
    assert result["source_id"] == "fixture:artificial-normalization-summary"
    assert result["is_artificial"] is True
    assert result["metadata"] == (
        ("source_reference", "fixture:artificial-normalization-summary"),
    )


def test_artificial_normalization_summary_builder_usage_returns_issue_counts() -> None:
    result = run_example()

    assert result["warning_count"] == 1
    assert result["error_count"] == 0
    assert result["has_normalized_records"] is True
    assert result["has_warnings"] is True
    assert result["has_errors"] is False
    assert result["is_clean"] is False


def test_artificial_normalization_summary_builder_usage_does_not_require_files(tmp_path) -> None:
    result = run_example()
    missing_path = tmp_path / "artificial-normalization-summary.txt"

    assert result["source_id"] == "fixture:artificial-normalization-summary"
    assert not missing_path.exists()


def test_artificial_normalization_summary_builder_usage_does_not_use_runtime_services() -> None:
    result = run_example()
    result_text = str(result).lower()

    assert "://" not in result_text
    assert "config" not in result_text
    assert "database" not in result_text
    assert "credential" not in result_text
    assert "schedule" not in result_text


def test_artificial_normalization_summary_builder_usage_does_not_apply_conversion_or_correctness() -> None:
    result = run_example()
    result_text = str(result).lower()

    assert "converted" not in result_text
    assert "correct" not in result_text
    assert "factor" not in result_text
    assert "kgco2e" not in result_text
