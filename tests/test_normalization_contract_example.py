from examples.normalization_contract_example import (
    build_normalization_contract_example,
    build_normalization_error_example,
)


def test_normalization_contract_example_is_importable_and_callable() -> None:
    result = build_normalization_contract_example()

    assert isinstance(result, dict)


def test_normalization_contract_example_returns_deterministic_fields() -> None:
    first = build_normalization_contract_example()
    second = build_normalization_contract_example()

    assert first == second
    assert tuple(first) == (
        "normalized_record_count",
        "warning_count",
        "error_count",
        "has_normalized_records",
        "has_warnings",
        "has_errors",
        "is_clean",
        "records",
        "issues",
    )


def test_normalization_contract_example_includes_expected_record_count() -> None:
    result = build_normalization_contract_example()

    assert result["normalized_record_count"] == 2
    assert result["has_normalized_records"] is True


def test_normalization_contract_example_includes_expected_warning_count() -> None:
    result = build_normalization_contract_example()

    assert result["warning_count"] == 1
    assert result["has_warnings"] is True
    assert result["error_count"] == 0
    assert result["has_errors"] is False
    assert result["is_clean"] is False


def test_normalization_contract_error_example_represents_error_issue() -> None:
    result = build_normalization_error_example()

    assert result["normalized_record_count"] == 0
    assert result["warning_count"] == 0
    assert result["error_count"] == 1
    assert result["has_errors"] is True
    assert result["issues"] == (
        {
            "code": "example_error",
            "message": "Artificial normalization error",
            "severity": "error",
            "location": "record 1",
        },
    )


def test_normalization_contract_example_uses_generic_artificial_records() -> None:
    result = build_normalization_contract_example()

    assert result["records"] == (
        {
            "record_id": "record-001",
            "fields": (
                ("field_name", "alpha"),
                ("value_label", "one"),
            ),
            "source_reference": "fixture:artificial_record_001",
            "is_artificial": True,
        },
        {
            "record_id": "record-002",
            "fields": (
                ("field_name", "beta"),
                ("value_label", "two"),
            ),
            "source_reference": "fixture:artificial_record_002",
            "is_artificial": True,
        },
    )


def test_normalization_contract_example_does_not_require_file_io(tmp_path) -> None:
    result = build_normalization_contract_example()
    missing_path = tmp_path / "artificial_record.txt"

    assert result["records"][0]["source_reference"] == "fixture:artificial_record_001"
    assert not missing_path.exists()


def test_normalization_contract_example_does_not_use_real_source_data() -> None:
    result = build_normalization_contract_example()
    result_text = str(result).lower()

    assert "://" not in result_text
    assert "factor" not in result_text
    assert "activity" not in result_text
    assert "unit" not in result_text
    assert "scope" not in result_text
    assert "kgco2e" not in result_text


def test_normalization_contract_example_does_not_change_contract_behavior() -> None:
    result = build_normalization_contract_example()

    assert result["normalized_record_count"] == len(result["records"])
    assert result["warning_count"] == len(result["issues"])
