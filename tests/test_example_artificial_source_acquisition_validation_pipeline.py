import inspect

from carbonfactor_parser import (
    create_artificial_source_acquisition_metadata,
    validate_and_summarize_artificial_source_acquisition_metadata,
)
from examples import example_artificial_source_acquisition_validation_pipeline as example
from examples.example_artificial_source_acquisition_validation_pipeline import (
    run_example,
)


def test_artificial_source_acquisition_validation_pipeline_example_is_callable() -> None:
    result = run_example()

    assert isinstance(result, dict)


def test_artificial_source_acquisition_validation_pipeline_example_is_deterministic() -> None:
    first = run_example()
    second = run_example()

    assert first == second
    assert tuple(first) == (
        "source_family",
        "logical_source_name",
        "declared_content_type",
        "acquired_at_label",
        "parser_hint",
        "adapter_hint",
        "validation_is_valid",
        "summary_is_valid",
        "total_issue_count",
        "severity_counts",
        "category_counts",
    )


def test_artificial_source_acquisition_validation_pipeline_example_uses_pipeline() -> None:
    source = inspect.getsource(example.run_example)

    assert (
        example.create_artificial_source_acquisition_metadata
        is create_artificial_source_acquisition_metadata
    )
    assert (
        example.validate_and_summarize_artificial_source_acquisition_metadata
        is validate_and_summarize_artificial_source_acquisition_metadata
    )
    assert "validate_and_summarize_artificial_source_acquisition_metadata(" in source
    assert "validate_artificial_source_acquisition_metadata(" not in source
    assert "summarize_source_acquisition_validation_result(" not in source


def test_artificial_source_acquisition_validation_pipeline_example_returns_valid_result() -> None:
    result = run_example()

    assert result["source_family"] == "artificial_source_acquisition"
    assert result["logical_source_name"] == "artificial-in-memory-source"
    assert result["declared_content_type"] == "text/csv"
    assert result["acquired_at_label"] == "static-artificial-acquisition-label"
    assert result["parser_hint"] == "artificial-parser-hint"
    assert result["adapter_hint"] == "artificial-adapter-hint"
    assert result["validation_is_valid"] is True
    assert result["summary_is_valid"] is True
    assert result["total_issue_count"] == 0


def test_artificial_source_acquisition_validation_pipeline_example_returns_empty_counts() -> None:
    result = run_example()

    assert result["severity_counts"] == ()
    assert result["category_counts"] == ()


def test_artificial_source_acquisition_validation_pipeline_example_does_not_open_files(
    monkeypatch,
) -> None:
    def fail_open(*args, **kwargs):
        raise AssertionError("example should not open files")

    monkeypatch.setattr("builtins.open", fail_open)

    result = run_example()

    assert result["total_issue_count"] == 0


def test_artificial_source_acquisition_validation_pipeline_example_does_not_use_runtime_services() -> None:
    result = run_example()
    result_text = str(result).lower()

    assert "://" not in result_text
    assert "config" not in result_text
    assert "database" not in result_text
    assert "credential" not in result_text
    assert "schedule" not in result_text


def test_artificial_source_acquisition_validation_pipeline_example_does_not_apply_conversion_or_factor_logic() -> None:
    result = run_example()
    result_text = str(result).lower()

    assert "converted" not in result_text
    assert "factor" not in result_text
    assert "kgco2e" not in result_text
