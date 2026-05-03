from examples.defra_desnz_parser_usage_example import (
    build_defra_desnz_parser_usage_example,
)


def test_defra_desnz_parser_usage_example_is_importable_and_callable() -> None:
    result = build_defra_desnz_parser_usage_example()

    assert isinstance(result, dict)


def test_defra_desnz_parser_usage_example_returns_deterministic_fields() -> None:
    first = build_defra_desnz_parser_usage_example()
    second = build_defra_desnz_parser_usage_example()

    assert first == second
    assert tuple(first) == (
        "source_family",
        "source_name",
        "record_count",
        "warning_count",
        "error_count",
        "has_records",
        "has_warnings",
        "has_errors",
        "is_clean",
        "records",
        "issues",
    )


def test_defra_desnz_parser_usage_example_includes_expected_summary() -> None:
    result = build_defra_desnz_parser_usage_example()

    assert result["record_count"] == 2
    assert result["warning_count"] == 0
    assert result["error_count"] == 0
    assert result["has_records"] is True
    assert result["has_warnings"] is False
    assert result["has_errors"] is False
    assert result["is_clean"] is True


def test_defra_desnz_parser_usage_example_includes_source_label() -> None:
    result = build_defra_desnz_parser_usage_example()

    assert result["source_family"] == "defra_desnz"
    assert result["source_name"] == "fixture:defra_desnz_artificial_parser"


def test_defra_desnz_parser_usage_example_uses_generic_artificial_records() -> None:
    result = build_defra_desnz_parser_usage_example()

    assert result["records"] == (
        {
            "record_id": "record-1",
            "source_label": "defra-desnz-artificial",
            "value_label": "one",
        },
        {
            "record_id": "record-2",
            "source_label": "defra-desnz-artificial",
            "value_label": "two",
        },
    )
    assert tuple(result["records"][0]) == ("record_id", "source_label", "value_label")


def test_defra_desnz_parser_usage_example_does_not_require_file_io(
    monkeypatch,
    tmp_path,
) -> None:
    missing_path = tmp_path / "unused.txt"

    def fail_open(*args, **kwargs):
        raise AssertionError("example should not open files")

    monkeypatch.setattr("builtins.open", fail_open)

    result = build_defra_desnz_parser_usage_example()

    assert result["record_count"] == 2
    assert not missing_path.exists()


def test_defra_desnz_parser_usage_example_avoids_real_schema_fields() -> None:
    result = build_defra_desnz_parser_usage_example()
    records_text = str(result["records"]).lower()

    assert "factor" not in records_text
    assert "activity" not in records_text
    assert "unit" not in records_text
    assert "scope" not in records_text


def test_defra_desnz_parser_usage_example_does_not_use_real_source_data() -> None:
    result = build_defra_desnz_parser_usage_example()
    records_text = str(result["records"]).lower()

    assert "://" not in str(result)
    assert "2024" not in records_text
    assert "2025" not in records_text
    assert "kgco2e" not in records_text
