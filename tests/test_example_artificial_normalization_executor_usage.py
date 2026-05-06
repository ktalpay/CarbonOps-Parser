from examples.example_artificial_normalization_executor_usage import (
    build_artificial_normalization_executor_usage,
)


def test_artificial_normalization_executor_usage_is_importable_and_callable() -> None:
    result = build_artificial_normalization_executor_usage()

    assert isinstance(result, dict)


def test_artificial_normalization_executor_usage_returns_deterministic_output() -> None:
    first = build_artificial_normalization_executor_usage()
    second = build_artificial_normalization_executor_usage()

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
    )


def test_artificial_normalization_executor_usage_uses_executor_output() -> None:
    result = build_artificial_normalization_executor_usage()

    assert result["normalized_record_count"] == 2
    assert len(result["records"]) == result["normalized_record_count"]
    assert result["has_normalized_records"] is True
    assert result["warning_count"] == 0
    assert result["error_count"] == 0
    assert result["is_clean"] is True


def test_artificial_normalization_executor_usage_returns_artificial_records() -> None:
    result = build_artificial_normalization_executor_usage()

    assert result["records"] == (
        {
            "record_id": "record-001",
            "fields": (
                (
                    "parser_record",
                    (
                        ("field_name", "alpha"),
                        ("value_label", "one"),
                    ),
                ),
                (
                    "parser_source_reference",
                    "fixture:artificial_parser_source",
                ),
                (
                    "handoff_source_reference",
                    "fixture:artificial_parser_source",
                ),
                ("handoff_is_artificial", True),
            ),
            "source_reference": "fixture:artificial_parser_source",
            "is_artificial": True,
        },
        {
            "record_id": "record-002",
            "fields": (
                (
                    "parser_record",
                    (
                        ("field_name", "beta"),
                        ("value_label", "two"),
                    ),
                ),
                (
                    "parser_source_reference",
                    "fixture:artificial_parser_source",
                ),
                (
                    "handoff_source_reference",
                    "fixture:artificial_parser_source",
                ),
                ("handoff_is_artificial", True),
            ),
            "source_reference": "fixture:artificial_parser_source",
            "is_artificial": True,
        },
    )


def test_artificial_normalization_executor_usage_does_not_require_files(tmp_path) -> None:
    result = build_artificial_normalization_executor_usage()
    missing_path = tmp_path / "artificial_parser_source.txt"

    assert result["records"][0]["source_reference"] == "fixture:artificial_parser_source"
    assert not missing_path.exists()


def test_artificial_normalization_executor_usage_does_not_use_remote_config_or_db() -> None:
    result = build_artificial_normalization_executor_usage()
    result_text = str(result).lower()

    assert "://" not in result_text
    assert "config" not in result_text
    assert "database" not in result_text
    assert "credential" not in result_text
    assert "schedule" not in result_text


def test_artificial_normalization_executor_usage_does_not_apply_conversion_or_correctness() -> None:
    result = build_artificial_normalization_executor_usage()
    result_text = str(result).lower()

    assert "converted" not in result_text
    assert "correct" not in result_text
    assert "factor" not in result_text
    assert "kgco2e" not in result_text
