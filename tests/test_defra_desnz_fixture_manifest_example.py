from examples.defra_desnz_fixture_manifest_example import (
    FIXTURE_DIRECTORY,
    build_defra_desnz_fixture_manifest_example,
)
from carbonfactor_parser.source_adapters import SourceFamily


def test_defra_desnz_manifest_example_is_importable_and_callable() -> None:
    manifest = build_defra_desnz_fixture_manifest_example()

    assert isinstance(manifest, dict)


def test_defra_desnz_manifest_example_returns_deterministic_fields() -> None:
    first = build_defra_desnz_fixture_manifest_example()
    second = build_defra_desnz_fixture_manifest_example()

    assert first == second
    assert tuple(first) == (
        "source_family",
        "source_name",
        "document_count",
        "is_artificial_fixture",
        "warnings",
        "entries",
    )


def test_defra_desnz_manifest_example_uses_artificial_fixture_directory() -> None:
    manifest = build_defra_desnz_fixture_manifest_example()

    assert FIXTURE_DIRECTORY.is_dir()
    assert all(
        str(FIXTURE_DIRECTORY) in entry["path_reference"]
        for entry in manifest["entries"]
    )


def test_defra_desnz_manifest_example_has_expected_document_count() -> None:
    manifest = build_defra_desnz_fixture_manifest_example()

    assert manifest["document_count"] == 2
    assert manifest["warnings"] == ()


def test_defra_desnz_manifest_example_marks_entries_as_artificial() -> None:
    manifest = build_defra_desnz_fixture_manifest_example()

    assert manifest["is_artificial_fixture"] is True
    assert all(entry["is_artificial_fixture"] is True for entry in manifest["entries"])


def test_defra_desnz_manifest_example_derives_file_names_and_extensions() -> None:
    manifest = build_defra_desnz_fixture_manifest_example()

    assert [
        (entry["file_name"], entry["file_extension"])
        for entry in manifest["entries"]
    ] == [
        ("defra_desnz_metadata.json", ".json"),
        ("defra_desnz_sample_factors.csv", ".csv"),
    ]


def test_defra_desnz_manifest_example_keeps_source_metadata() -> None:
    manifest = build_defra_desnz_fixture_manifest_example()

    assert manifest["source_family"] == SourceFamily.DEFRA_DESNZ.value
    assert manifest["source_name"] == "defra_desnz"
    assert [entry["source_name"] for entry in manifest["entries"]] == [
        "defra_desnz:defra_desnz_metadata.json",
        "defra_desnz:defra_desnz_sample_factors.csv",
    ]


def test_defra_desnz_manifest_example_does_not_parse_fixture_contents() -> None:
    manifest = build_defra_desnz_fixture_manifest_example()

    assert "Artificial local fixture" not in str(manifest)
    assert "adapter skeleton discovery" not in str(manifest)


def test_defra_desnz_manifest_example_does_not_require_remote_access() -> None:
    manifest = build_defra_desnz_fixture_manifest_example()

    assert "://" not in str(manifest)
