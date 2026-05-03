from examples.example_in_memory_parser_usage import (
    build_example_in_memory_parser_usage,
)


def test_example_in_memory_parser_usage_is_importable_and_callable() -> None:
    result = build_example_in_memory_parser_usage()

    assert isinstance(result, dict)


def test_example_in_memory_parser_usage_returns_deterministic_fields() -> None:
    first = build_example_in_memory_parser_usage()
    second = build_example_in_memory_parser_usage()

    assert first == second
    assert tuple(first) == (
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


def test_example_in_memory_parser_usage_includes_expected_summary() -> None:
    result = build_example_in_memory_parser_usage()

    assert result["record_count"] == 2
    assert result["warning_count"] == 0
    assert result["error_count"] == 0
    assert result["has_records"] is True
    assert result["has_warnings"] is False
    assert result["has_errors"] is False
    assert result["is_clean"] is True


def test_example_in_memory_parser_usage_uses_generic_artificial_records() -> None:
    result = build_example_in_memory_parser_usage()

    assert result["records"] == (
        {"record_id": "record-1", "category": "alpha", "value_label": "one"},
        {"record_id": "record-2", "category": "beta", "value_label": "two"},
    )
    assert "factor" not in str(result["records"]).lower()
    assert "defra" not in str(result["records"]).lower()
    assert "desnz" not in str(result["records"]).lower()


def test_example_in_memory_parser_usage_does_not_require_file_io(
    monkeypatch,
    tmp_path,
) -> None:
    missing_path = tmp_path / "unused.txt"

    def fail_open(*args, **kwargs):
        raise AssertionError("example should not open files")

    monkeypatch.setattr("builtins.open", fail_open)

    result = build_example_in_memory_parser_usage()

    assert result["record_count"] == 2
    assert not missing_path.exists()


def test_example_in_memory_parser_usage_does_not_use_remote_reference() -> None:
    result = build_example_in_memory_parser_usage()

    assert "://" not in str(result)
