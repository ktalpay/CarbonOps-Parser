from examples.source_adapter_summary_example import (
    FIXTURE_DIRECTORY,
    build_source_adapter_summary_example,
)


def test_summary_example_is_importable_and_callable() -> None:
    summary = build_source_adapter_summary_example()

    assert isinstance(summary, dict)


def test_summary_example_returns_deterministic_fields() -> None:
    first = build_source_adapter_summary_example()
    second = build_source_adapter_summary_example()

    assert first == second
    assert tuple(first) == (
        "document_count",
        "warning_count",
        "error_count",
        "has_documents",
        "has_warnings",
        "has_errors",
        "is_clean",
        "source_families",
        "source_names",
        "file_extensions",
    )


def test_summary_example_includes_expected_document_count() -> None:
    summary = build_source_adapter_summary_example()

    assert summary["document_count"] == 2
    assert summary["has_documents"] is True


def test_summary_example_includes_expected_file_extensions() -> None:
    summary = build_source_adapter_summary_example()

    assert summary["file_extensions"] == (".csv", ".json")


def test_summary_example_reports_warning_and_error_flags() -> None:
    summary = build_source_adapter_summary_example()

    assert summary["warning_count"] == 0
    assert summary["error_count"] == 0
    assert summary["has_warnings"] is False
    assert summary["has_errors"] is False
    assert summary["is_clean"] is True


def test_summary_example_does_not_parse_fixture_contents() -> None:
    summary = build_source_adapter_summary_example(
        allowed_extensions=(".csv", ".json", ".txt")
    )

    assert "factor_id" not in str(summary)
    assert "Example fixture metadata" not in str(summary)
    assert summary["source_names"] == (
        "notes.txt",
        "sample_factors.csv",
        "sample_metadata.json",
    )


def test_summary_example_uses_repository_relative_fixture_path() -> None:
    assert FIXTURE_DIRECTORY.is_dir()
