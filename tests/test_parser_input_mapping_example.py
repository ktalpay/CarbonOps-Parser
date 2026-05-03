from examples.parser_input_mapping_example import (
    FIXTURE_DIRECTORY,
    build_parser_input_mapping_example,
)


def test_parser_input_mapping_example_is_importable_and_callable() -> None:
    mapping = build_parser_input_mapping_example()

    assert isinstance(mapping, dict)


def test_parser_input_mapping_example_returns_deterministic_fields() -> None:
    first = build_parser_input_mapping_example()
    second = build_parser_input_mapping_example()

    assert first == second
    assert tuple(first) == (
        "source_family",
        "source_name",
        "document_count",
        "parser_hint",
        "is_artificial_fixture",
        "warnings",
        "entries",
    )


def test_parser_input_mapping_example_includes_expected_document_count() -> None:
    mapping = build_parser_input_mapping_example()

    assert mapping["document_count"] == 2
    assert mapping["warnings"] == ()


def test_parser_input_mapping_example_derives_file_names_and_extensions() -> None:
    mapping = build_parser_input_mapping_example()

    assert [
        (entry["file_name"], entry["file_extension"])
        for entry in mapping["entries"]
    ] == [
        ("defra_desnz_metadata.json", ".json"),
        ("defra_desnz_sample_factors.csv", ".csv"),
    ]


def test_parser_input_mapping_example_marks_entries_as_artificial() -> None:
    mapping = build_parser_input_mapping_example()

    assert mapping["is_artificial_fixture"] is True
    assert all(entry["is_artificial_fixture"] is True for entry in mapping["entries"])
    assert mapping["parser_hint"] == "artificial-fixture"
    assert all(
        entry["parser_hint"] == "artificial-fixture" for entry in mapping["entries"]
    )


def test_parser_input_mapping_example_uses_artificial_fixture_directory() -> None:
    mapping = build_parser_input_mapping_example()

    assert FIXTURE_DIRECTORY.is_dir()
    assert all(
        str(FIXTURE_DIRECTORY) in entry["document_path"]
        for entry in mapping["entries"]
    )


def test_parser_input_mapping_example_does_not_require_content_parsing(
    monkeypatch,
) -> None:
    def fail_open(*args, **kwargs):
        raise AssertionError("example should not open files")

    monkeypatch.setattr("builtins.open", fail_open)

    mapping = build_parser_input_mapping_example()

    assert mapping["document_count"] == 2


def test_parser_input_mapping_example_does_not_use_real_source_data() -> None:
    mapping = build_parser_input_mapping_example()
    mapping_text = str(mapping).lower()

    assert "://" not in mapping_text
    assert "artificial local fixture" not in mapping_text
    assert "adapter skeleton discovery" not in mapping_text
    assert "kgco2e" not in mapping_text


def test_parser_input_mapping_example_does_not_change_mapping_behavior() -> None:
    mapping = build_parser_input_mapping_example()

    assert mapping["source_family"] == "defra_desnz"
    assert mapping["source_name"] == "fixture_parser_input_mapping"
    assert [entry["document_id"] for entry in mapping["entries"]] == [
        "defra_desnz:defra_desnz_metadata.json",
        "defra_desnz:defra_desnz_sample_factors.csv",
    ]
