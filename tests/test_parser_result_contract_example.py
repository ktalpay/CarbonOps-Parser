from examples.parser_result_contract_example import (
    build_parser_result_contract_example,
    build_parser_result_error_example,
)


def test_parser_result_contract_example_is_importable_and_callable() -> None:
    result = build_parser_result_contract_example()

    assert isinstance(result, dict)


def test_parser_result_contract_example_returns_deterministic_fields() -> None:
    first = build_parser_result_contract_example()
    second = build_parser_result_contract_example()

    assert first == second
    assert tuple(first) == (
        "source_family",
        "source_name",
        "file_reference",
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


def test_parser_result_contract_example_includes_expected_record_count() -> None:
    result = build_parser_result_contract_example()

    assert result["record_count"] == 2
    assert result["has_records"] is True


def test_parser_result_contract_example_includes_expected_warning_count() -> None:
    result = build_parser_result_contract_example()

    assert result["warning_count"] == 1
    assert result["has_warnings"] is True
    assert result["error_count"] == 0
    assert result["has_errors"] is False
    assert result["is_clean"] is False


def test_parser_result_contract_error_example_represents_error_issue() -> None:
    result = build_parser_result_error_example()

    assert result["record_count"] == 0
    assert result["warning_count"] == 0
    assert result["error_count"] == 1
    assert result["has_errors"] is True
    assert result["issues"] == (
        {
            "code": "example_error",
            "message": "Artificial parser error",
            "severity": "error",
            "location": "record 1",
        },
    )


def test_parser_result_contract_example_does_not_require_file_io(tmp_path) -> None:
    result = build_parser_result_contract_example()
    missing_path = tmp_path / "artificial_source.txt"

    assert result["file_reference"] == "fixtures/artificial_source.txt"
    assert not missing_path.exists()


def test_parser_result_contract_example_uses_generic_artificial_records() -> None:
    result = build_parser_result_contract_example()

    assert result["records"] == (
        {"field_name": "alpha", "raw_value": "one"},
        {"field_name": "beta", "raw_value": "two"},
    )
    assert "factor" not in str(result["records"]).lower()


def test_parser_result_contract_example_does_not_use_remote_reference() -> None:
    result = build_parser_result_contract_example()

    assert "://" not in str(result)
