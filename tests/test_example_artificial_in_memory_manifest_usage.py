import inspect

from carbonfactor_parser import (
    ArtificialSourceManifestCollectionValidationSummary,
    ArtificialSourceManifestMetadata,
    ArtificialSourceManifestMetadataCollection,
    ArtificialSourceManifestValidationSummary,
)
from examples import example_artificial_in_memory_manifest_usage as example
from examples.example_artificial_in_memory_manifest_usage import (
    build_artificial_manifest_usage_summary,
)


def test_artificial_in_memory_manifest_usage_example_is_callable() -> None:
    result = build_artificial_manifest_usage_summary()

    assert isinstance(result, dict)


def test_artificial_in_memory_manifest_usage_example_is_deterministic() -> None:
    first = build_artificial_manifest_usage_summary()
    second = build_artificial_manifest_usage_summary()

    assert first == second
    assert tuple(first) == (
        "collection_count",
        "manifest_ids",
        "source_families",
        "manifests",
        "manifest_validation_summaries",
        "collection_validation_summary",
    )


def test_artificial_in_memory_manifest_usage_example_uses_public_manifest_shapes() -> None:
    source = inspect.getsource(example.build_artificial_manifest_usage_summary)

    assert example.ArtificialSourceManifestMetadata is ArtificialSourceManifestMetadata
    assert (
        example.ArtificialSourceManifestMetadataCollection
        is ArtificialSourceManifestMetadataCollection
    )
    assert (
        example.ArtificialSourceManifestValidationSummary
        is ArtificialSourceManifestValidationSummary
    )
    assert (
        example.ArtificialSourceManifestCollectionValidationSummary
        is ArtificialSourceManifestCollectionValidationSummary
    )
    assert "ArtificialSourceManifestMetadata(" in source
    assert "ArtificialSourceManifestMetadataCollection(" in source
    assert "ArtificialSourceManifestValidationSummary.from_metadata(" in source
    assert (
        "ArtificialSourceManifestCollectionValidationSummary.from_collection("
        in source
    )


def test_artificial_in_memory_manifest_usage_example_returns_collection_summary() -> None:
    result = build_artificial_manifest_usage_summary()

    assert result["collection_count"] == 2
    assert result["manifest_ids"] == (
        "artificial-manifest-alpha",
        "artificial-manifest-beta",
    )
    assert result["source_families"] == (
        "artificial_manifest_family",
        "second_artificial_manifest_family",
    )


def test_artificial_in_memory_manifest_usage_example_returns_manifest_records() -> None:
    result = build_artificial_manifest_usage_summary()

    assert result["manifests"] == (
        {
            "manifest_id": "artificial-manifest-alpha",
            "source_family": "artificial_manifest_family",
            "dataset_name": "artificial_dataset_alpha",
            "version_label": "static_version_alpha",
            "record_count": 2,
            "generated_by": "artificial_manifest_usage_example",
            "notes": ("artificial_note_alpha",),
        },
        {
            "manifest_id": "artificial-manifest-beta",
            "source_family": "second_artificial_manifest_family",
            "dataset_name": "artificial_dataset_beta",
            "version_label": "static_version_beta",
            "record_count": 1,
            "generated_by": "artificial_manifest_usage_example",
            "notes": ("artificial_note_beta",),
        },
    )


def test_artificial_in_memory_manifest_usage_example_returns_manifest_validation_summaries() -> None:
    result = build_artificial_manifest_usage_summary()

    assert result["manifest_validation_summaries"] == (
        {
            "manifest_id": "artificial-manifest-alpha",
            "source_family": "artificial_manifest_family",
            "dataset_name": "artificial_dataset_alpha",
            "issue_count": 0,
            "is_valid": True,
        },
        {
            "manifest_id": "artificial-manifest-beta",
            "source_family": "second_artificial_manifest_family",
            "dataset_name": "artificial_dataset_beta",
            "issue_count": 0,
            "is_valid": True,
        },
    )


def test_artificial_in_memory_manifest_usage_example_returns_collection_validation_summary() -> None:
    result = build_artificial_manifest_usage_summary()

    assert result["collection_validation_summary"] == {
        "manifest_count": 2,
        "unique_source_family_count": 2,
        "issue_count": 0,
        "is_valid": True,
    }


def test_artificial_in_memory_manifest_usage_example_does_not_open_files(
    monkeypatch,
) -> None:
    def fail_open(*args, **kwargs):
        raise AssertionError("example should not open files")

    monkeypatch.setattr("builtins.open", fail_open)

    result = build_artificial_manifest_usage_summary()

    assert result["collection_count"] == 2


def test_artificial_in_memory_manifest_usage_example_does_not_use_runtime_services() -> None:
    result = build_artificial_manifest_usage_summary()
    result_text = str(result).lower()

    assert "://" not in result_text
    assert "/" not in result_text
    assert "\\" not in result_text
    assert "config" not in result_text
    assert "credential" not in result_text
    assert "database" not in result_text
    assert "cache" not in result_text
    assert "schedule" not in result_text
    assert "registry" not in result_text
    assert "selector" not in result_text


def test_artificial_in_memory_manifest_usage_example_does_not_apply_conversion_or_factor_logic() -> None:
    result = build_artificial_manifest_usage_summary()
    result_text = str(result).lower()

    assert "converted" not in result_text
    assert "conversion" not in result_text
    assert "factor" not in result_text
    assert "kgco2e" not in result_text
