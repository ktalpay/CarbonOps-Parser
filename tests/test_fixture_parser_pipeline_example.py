from examples.fixture_parser_pipeline_example import (
    FIXTURE_DIRECTORY,
    build_fixture_parser_pipeline_example,
)


def test_fixture_parser_pipeline_example_is_importable_and_callable() -> None:
    result = build_fixture_parser_pipeline_example()

    assert isinstance(result, dict)


def test_fixture_parser_pipeline_example_returns_deterministic_fields() -> None:
    first = build_fixture_parser_pipeline_example()
    second = build_fixture_parser_pipeline_example()

    assert first == second
    assert tuple(first) == (
        "discovered_document_count",
        "mapping_document_count",
        "parser_record_count",
        "parser_warning_count",
        "parser_error_count",
        "parser_has_records",
        "parser_has_warnings",
        "parser_has_errors",
        "parser_is_clean",
        "discovery_warnings",
        "mapping_entries",
        "records",
    )


def test_fixture_parser_pipeline_counts_are_consistent() -> None:
    result = build_fixture_parser_pipeline_example()

    assert result["discovered_document_count"] == 2
    assert result["mapping_document_count"] == result["discovered_document_count"]
    assert result["parser_record_count"] == result["mapping_document_count"]
    assert result["parser_warning_count"] == 0
    assert result["parser_error_count"] == 0
    assert result["parser_has_records"] is True
    assert result["parser_has_warnings"] is False
    assert result["parser_has_errors"] is False
    assert result["parser_is_clean"] is True
    assert result["discovery_warnings"] == ()


def test_fixture_parser_pipeline_returns_expected_mapping_metadata() -> None:
    result = build_fixture_parser_pipeline_example()

    assert result["mapping_entries"] == (
        {
            "document_id": "defra_desnz:defra_desnz_metadata.json",
            "file_name": "defra_desnz_metadata.json",
            "file_extension": ".json",
            "is_artificial_fixture": True,
        },
        {
            "document_id": "defra_desnz:defra_desnz_sample_factors.csv",
            "file_name": "defra_desnz_sample_factors.csv",
            "file_extension": ".csv",
            "is_artificial_fixture": True,
        },
    )


def test_fixture_parser_pipeline_returns_expected_artificial_records() -> None:
    result = build_fixture_parser_pipeline_example()

    assert result["records"] == (
        {
            "record_id": "defra_desnz:defra_desnz_metadata.json",
            "file_name": "defra_desnz_metadata.json",
            "file_extension": ".json",
            "source_label": "defra_desnz:defra_desnz_metadata.json",
            "value_label": "artificial-fixture",
        },
        {
            "record_id": "defra_desnz:defra_desnz_sample_factors.csv",
            "file_name": "defra_desnz_sample_factors.csv",
            "file_extension": ".csv",
            "source_label": "defra_desnz:defra_desnz_sample_factors.csv",
            "value_label": "artificial-fixture",
        },
    )


def test_fixture_parser_pipeline_uses_artificial_fixture_directory() -> None:
    result = build_fixture_parser_pipeline_example()

    assert FIXTURE_DIRECTORY.is_dir()
    assert result["discovered_document_count"] == 2


def test_fixture_parser_pipeline_does_not_read_file_contents(monkeypatch) -> None:
    def fail_open(*args, **kwargs):
        raise AssertionError("example should not open files")

    monkeypatch.setattr("builtins.open", fail_open)

    result = build_fixture_parser_pipeline_example()

    assert result["parser_record_count"] == 2


def test_fixture_parser_pipeline_does_not_use_real_source_data() -> None:
    result = build_fixture_parser_pipeline_example()
    result_text = str(result).lower()

    assert "://" not in result_text
    assert "activity" not in result_text
    assert "unit" not in result_text
    assert "scope" not in result_text
    assert "kgco2e" not in result_text


def test_fixture_parser_pipeline_does_not_change_adapter_mapping_or_parser_behavior() -> None:
    result = build_fixture_parser_pipeline_example()

    assert [entry["document_id"] for entry in result["mapping_entries"]] == [
        record["record_id"] for record in result["records"]
    ]
