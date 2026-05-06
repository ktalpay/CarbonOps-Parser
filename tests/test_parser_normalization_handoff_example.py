from examples.parser_normalization_handoff_example import (
    build_parser_normalization_handoff_example,
)


def test_parser_normalization_handoff_example_is_importable_and_callable() -> None:
    result = build_parser_normalization_handoff_example()

    assert isinstance(result, dict)


def test_parser_normalization_handoff_example_returns_deterministic_fields() -> None:
    first = build_parser_normalization_handoff_example()
    second = build_parser_normalization_handoff_example()

    assert first == second
    assert tuple(first) == (
        "parser_record_count",
        "handoff_entry_count",
        "issue_count",
        "source_reference",
        "is_artificial",
        "entries",
    )


def test_parser_normalization_handoff_example_returns_expected_counts() -> None:
    result = build_parser_normalization_handoff_example()

    assert result["parser_record_count"] == 2
    assert result["handoff_entry_count"] == result["parser_record_count"]
    assert result["issue_count"] == 1


def test_parser_normalization_handoff_example_returns_deterministic_entries() -> None:
    result = build_parser_normalization_handoff_example()

    assert result["entries"] == (
        {
            "record_id": "record-001",
            "parser_record": (
                ("field_name", "alpha"),
                ("record_id", "record-001"),
                ("value_label", "one"),
            ),
            "source_reference": "fixture:artificial_parser_source",
            "is_artificial": True,
        },
        {
            "record_id": "parser-record-002",
            "parser_record": (
                ("field_name", "beta"),
                ("value_label", "two"),
            ),
            "source_reference": "fixture:artificial_parser_source",
            "is_artificial": True,
        },
    )


def test_parser_normalization_handoff_example_uses_generic_artificial_records() -> None:
    result = build_parser_normalization_handoff_example()
    result_text = str(result).lower()

    assert "field_name" in result_text
    assert "value_label" in result_text
    assert "factor" not in result_text
    assert "activity" not in result_text
    assert "kgco2e" not in result_text


def test_parser_normalization_handoff_example_does_not_require_file_io(tmp_path) -> None:
    result = build_parser_normalization_handoff_example()
    missing_path = tmp_path / "artificial_parser_source.txt"

    assert result["source_reference"] == "fixture:artificial_parser_source"
    assert not missing_path.exists()


def test_parser_normalization_handoff_example_does_not_perform_normalization() -> None:
    result = build_parser_normalization_handoff_example()
    result_text = str(result).lower()

    assert "normalized" not in result_text
    assert "converted" not in result_text
    assert "correct" not in result_text


def test_parser_normalization_handoff_example_does_not_use_remote_reference() -> None:
    result = build_parser_normalization_handoff_example()

    assert "://" not in str(result)


def test_parser_normalization_handoff_example_does_not_change_handoff_behavior() -> None:
    result = build_parser_normalization_handoff_example()

    assert result["handoff_entry_count"] == len(result["entries"])
    assert [entry["record_id"] for entry in result["entries"]] == [
        "record-001",
        "parser-record-002",
    ]
