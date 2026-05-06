from pathlib import Path

from examples.local_source_fixture_discovery_example import (
    FIXTURE_DIRECTORY,
    discover_fixture_documents,
    fixture_document_metadata,
)
from carbonfactor_parser.source_adapters import SourceFamily


def test_example_discovers_expected_fixture_files() -> None:
    documents = discover_fixture_documents()

    assert [document.source_name for document in documents] == [
        "sample_factors.csv",
        "sample_metadata.json",
    ]
    assert {document.source_family for document in documents} == {
        SourceFamily.GHG_PROTOCOL
    }


def test_example_results_are_deterministic() -> None:
    first = fixture_document_metadata()
    second = fixture_document_metadata()

    assert first == second
    assert [metadata["source_name"] for metadata in first] == [
        "sample_factors.csv",
        "sample_metadata.json",
    ]


def test_example_demonstrates_extension_filtering() -> None:
    metadata = fixture_document_metadata(allowed_extensions=".txt")

    assert metadata == (
        {
            "source_family": SourceFamily.GHG_PROTOCOL.value,
            "source_name": "notes.txt",
            "file_reference": str(FIXTURE_DIRECTORY / "notes.txt"),
            "extension": ".txt",
        },
    )


def test_example_does_not_parse_fixture_contents() -> None:
    metadata = fixture_document_metadata(allowed_extensions=(".csv", ".json", ".txt"))

    assert {tuple(item) for item in metadata} == {
        ("source_family", "source_name", "file_reference", "extension")
    }
    assert "factor_id" not in str(metadata)
    assert "Example fixture metadata" not in str(metadata)


def test_example_fixture_directory_is_resolved_from_repository() -> None:
    assert FIXTURE_DIRECTORY.is_dir()
    assert FIXTURE_DIRECTORY == (
        Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "source_documents"
    )
