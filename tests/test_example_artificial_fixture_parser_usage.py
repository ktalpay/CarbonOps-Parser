from examples.example_artificial_fixture_parser_usage import (
    FIXTURE_DIRECTORY,
    build_artificial_fixture_parser_usage_example,
)


def test_artificial_fixture_parser_usage_example_is_importable_and_callable() -> None:
    result = build_artificial_fixture_parser_usage_example()

    assert isinstance(result, dict)


def test_artificial_fixture_parser_usage_example_returns_deterministic_fields() -> None:
    first = build_artificial_fixture_parser_usage_example()
    second = build_artificial_fixture_parser_usage_example()

    assert first == second
    assert tuple(first) == (
        "source_family",
        "source_name",
        "input_document_count",
        "record_count",
        "warning_count",
        "error_count",
        "has_records",
        "has_warnings",
        "has_errors",
        "is_clean",
        "warnings",
        "records",
    )


def test_artificial_fixture_parser_usage_example_includes_expected_summary() -> None:
    result = build_artificial_fixture_parser_usage_example()

    assert result["source_family"] == "defra_desnz"
    assert result["source_name"] == "fixture_parser_input_mapping"
    assert result["input_document_count"] == 4
    assert result["record_count"] == 4
    assert result["warning_count"] == 0
    assert result["error_count"] == 0
    assert result["has_records"] is True
    assert result["has_warnings"] is False
    assert result["has_errors"] is False
    assert result["is_clean"] is True
    assert result["warnings"] == ()


def test_artificial_fixture_parser_usage_example_returns_artificial_records() -> None:
    result = build_artificial_fixture_parser_usage_example()

    assert result["records"] == (
        {
            "record_id": "defra_desnz:defra_desnz_malformed_factors.csv",
            "file_name": "defra_desnz_malformed_factors.csv",
            "file_extension": ".csv",
            "source_label": "defra_desnz:defra_desnz_malformed_factors.csv",
            "value_label": "artificial-fixture",
        },
        {
            "record_id": "defra_desnz:defra_desnz_metadata.json",
            "file_name": "defra_desnz_metadata.json",
            "file_extension": ".json",
            "source_label": "defra_desnz:defra_desnz_metadata.json",
            "value_label": "artificial-fixture",
        },
        {
            "record_id": "defra_desnz:defra_desnz_normalized_factors.csv",
            "file_name": "defra_desnz_normalized_factors.csv",
            "file_extension": ".csv",
            "source_label": "defra_desnz:defra_desnz_normalized_factors.csv",
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


def test_artificial_fixture_parser_usage_example_uses_artificial_fixture_directory() -> None:
    result = build_artificial_fixture_parser_usage_example()

    assert FIXTURE_DIRECTORY.is_dir()
    assert result["record_count"] == 4


def test_artificial_fixture_parser_usage_example_does_not_open_files(
    monkeypatch,
) -> None:
    def fail_open(*args, **kwargs):
        raise AssertionError("example should not open files")

    monkeypatch.setattr("builtins.open", fail_open)

    result = build_artificial_fixture_parser_usage_example()

    assert result["record_count"] == 4


def test_artificial_fixture_parser_usage_example_avoids_real_schema_fields() -> None:
    result = build_artificial_fixture_parser_usage_example()
    records_text = str(result["records"]).lower()

    assert "activity" not in records_text
    assert "unit" not in records_text
    assert "scope" not in records_text
    assert "kgco2e" not in records_text


def test_artificial_fixture_parser_usage_example_does_not_use_remote_reference() -> None:
    result = build_artificial_fixture_parser_usage_example()

    assert "://" not in str(result)
