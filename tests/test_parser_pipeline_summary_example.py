from examples.parser_pipeline_summary_example import (
    FIXTURE_DIRECTORY,
    build_parser_pipeline_summary_example,
)


def test_parser_pipeline_summary_example_is_importable_and_callable() -> None:
    result = build_parser_pipeline_summary_example()

    assert isinstance(result, dict)


def test_parser_pipeline_summary_example_returns_deterministic_fields() -> None:
    first = build_parser_pipeline_summary_example()
    second = build_parser_pipeline_summary_example()

    assert first == second
    assert tuple(first) == (
        "discovered_document_count",
        "mapping_entry_count",
        "parser_record_count",
        "parser_warning_count",
        "parser_error_count",
        "has_discovered_documents",
        "has_mapping_entries",
        "has_parser_records",
        "has_parser_warnings",
        "has_parser_errors",
        "is_clean",
        "source_families",
        "source_names",
    )


def test_parser_pipeline_summary_example_counts_are_consistent() -> None:
    result = build_parser_pipeline_summary_example()

    assert result["discovered_document_count"] == 2
    assert result["mapping_entry_count"] == result["discovered_document_count"]
    assert result["parser_record_count"] == result["mapping_entry_count"]


def test_parser_pipeline_summary_example_warning_and_error_counts_are_stable() -> None:
    result = build_parser_pipeline_summary_example()

    assert result["parser_warning_count"] == 0
    assert result["parser_error_count"] == 0
    assert result["has_parser_warnings"] is False
    assert result["has_parser_errors"] is False
    assert result["is_clean"] is True


def test_parser_pipeline_summary_example_boolean_flags_are_stable() -> None:
    result = build_parser_pipeline_summary_example()

    assert result["has_discovered_documents"] is True
    assert result["has_mapping_entries"] is True
    assert result["has_parser_records"] is True


def test_parser_pipeline_summary_example_includes_expected_source_metadata() -> None:
    result = build_parser_pipeline_summary_example()

    assert result["source_families"] == ("defra_desnz",)
    assert result["source_names"] == (
        "defra_desnz:defra_desnz_metadata.json",
        "defra_desnz:defra_desnz_sample_factors.csv",
    )


def test_parser_pipeline_summary_example_uses_artificial_fixture_directory() -> None:
    result = build_parser_pipeline_summary_example()

    assert FIXTURE_DIRECTORY.is_dir()
    assert result["discovered_document_count"] == 2


def test_parser_pipeline_summary_example_does_not_read_file_contents(monkeypatch) -> None:
    def fail_open(*args, **kwargs):
        raise AssertionError("example should not open files")

    monkeypatch.setattr("builtins.open", fail_open)

    result = build_parser_pipeline_summary_example()

    assert result["parser_record_count"] == 2


def test_parser_pipeline_summary_example_does_not_use_real_source_data() -> None:
    result = build_parser_pipeline_summary_example()
    result_text = str(result).lower()

    assert "://" not in result_text
    assert "activity" not in result_text
    assert "unit" not in result_text
    assert "scope" not in result_text
    assert "kgco2e" not in result_text


def test_parser_pipeline_summary_example_does_not_change_pipeline_behavior() -> None:
    result = build_parser_pipeline_summary_example()

    assert result["discovered_document_count"] == 2
    assert result["mapping_entry_count"] == 2
    assert result["parser_record_count"] == 2
