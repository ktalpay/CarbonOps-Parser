from dataclasses import FrozenInstanceError

import pytest

import carbonfactor_parser
from carbonfactor_parser import (
    ArtificialSourceManifestCollectionValidationSummary as RootCollectionValidationSummary,
    ArtificialSourceManifestMetadata as RootManifestMetadata,
    ArtificialSourceManifestMetadataCollection as RootManifestCollection,
    ArtificialSourceManifestValidationSummary as RootManifestValidationSummary,
)
from carbonfactor_parser import source_manifest
from carbonfactor_parser.source_manifest import (
    ArtificialSourceManifestCollectionValidationSummary,
    ArtificialSourceManifestMetadata,
    ArtificialSourceManifestMetadataCollection,
    ArtificialSourceManifestValidationSummary,
)


def valid_manifest_metadata() -> ArtificialSourceManifestMetadata:
    return ArtificialSourceManifestMetadata(
        manifest_id="artificial-manifest-001",
        source_family="artificial_source_acquisition",
        dataset_name="artificial-dataset",
        version_label="static-version-label",
        record_count=2,
        generated_by="artificial-manifest-builder",
        notes=("artificial-note-a", "artificial-note-b"),
    )


def second_manifest_metadata() -> ArtificialSourceManifestMetadata:
    return ArtificialSourceManifestMetadata(
        manifest_id="artificial-manifest-002",
        source_family="second_artificial_source_family",
        dataset_name="second-artificial-dataset",
        version_label="second-static-version-label",
        record_count=1,
        notes=("second-artificial-note",),
    )


def third_manifest_metadata() -> ArtificialSourceManifestMetadata:
    return ArtificialSourceManifestMetadata(
        manifest_id="artificial-manifest-003",
        source_family="artificial_source_acquisition",
        dataset_name="third-artificial-dataset",
        version_label="third-static-version-label",
        record_count=3,
    )


def test_valid_artificial_manifest_metadata_can_be_created() -> None:
    metadata = valid_manifest_metadata()

    assert metadata == ArtificialSourceManifestMetadata(
        manifest_id="artificial-manifest-001",
        source_family="artificial_source_acquisition",
        dataset_name="artificial-dataset",
        version_label="static-version-label",
        record_count=2,
        generated_by="artificial-manifest-builder",
        notes=("artificial-note-a", "artificial-note-b"),
    )


def test_artificial_manifest_metadata_is_immutable() -> None:
    metadata = valid_manifest_metadata()

    with pytest.raises(FrozenInstanceError):
        metadata.manifest_id = "changed"  # type: ignore[misc]


def test_notes_default_to_empty_tuple() -> None:
    metadata = ArtificialSourceManifestMetadata(
        manifest_id="artificial-manifest-001",
        source_family="artificial_source_acquisition",
        dataset_name="artificial-dataset",
        version_label="static-version-label",
        record_count=0,
    )

    assert metadata.notes == ()


def test_notes_are_stored_as_tuple() -> None:
    metadata = ArtificialSourceManifestMetadata(
        manifest_id="artificial-manifest-001",
        source_family="artificial_source_acquisition",
        dataset_name="artificial-dataset",
        version_label="static-version-label",
        record_count=1,
        notes=["artificial-note-a", "artificial-note-b"],  # type: ignore[arg-type]
    )

    assert metadata.notes == ("artificial-note-a", "artificial-note-b")


@pytest.mark.parametrize(
    ("field_name", "expected_message"),
    [
        ("manifest_id", "manifest_id must be a non-empty string."),
        ("source_family", "source_family must be a non-empty string."),
        ("dataset_name", "dataset_name must be a non-empty string."),
        ("version_label", "version_label must be a non-empty string."),
    ],
)
def test_required_strings_must_not_be_blank(
    field_name: str,
    expected_message: str,
) -> None:
    values = {
        "manifest_id": "artificial-manifest-001",
        "source_family": "artificial_source_acquisition",
        "dataset_name": "artificial-dataset",
        "version_label": "static-version-label",
        "record_count": 0,
    }
    values[field_name] = " "

    with pytest.raises(ValueError, match=expected_message):
        ArtificialSourceManifestMetadata(**values)  # type: ignore[arg-type]


def test_generated_by_is_optional() -> None:
    metadata = ArtificialSourceManifestMetadata(
        manifest_id="artificial-manifest-001",
        source_family="artificial_source_acquisition",
        dataset_name="artificial-dataset",
        version_label="static-version-label",
        record_count=0,
    )

    assert metadata.generated_by is None


def test_generated_by_must_not_be_blank_when_provided() -> None:
    with pytest.raises(ValueError, match="generated_by must be a non-empty string."):
        ArtificialSourceManifestMetadata(
            manifest_id="artificial-manifest-001",
            source_family="artificial_source_acquisition",
            dataset_name="artificial-dataset",
            version_label="static-version-label",
            record_count=0,
            generated_by=" ",
        )


@pytest.mark.parametrize("record_count", [-1, 1.5, True])
def test_record_count_must_be_non_negative_integer(record_count: object) -> None:
    with pytest.raises(
        ValueError,
        match="record_count must be a non-negative integer.",
    ):
        ArtificialSourceManifestMetadata(
            manifest_id="artificial-manifest-001",
            source_family="artificial_source_acquisition",
            dataset_name="artificial-dataset",
            version_label="static-version-label",
            record_count=record_count,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "notes",
    [
        "artificial-note",
        ("artificial-note", " "),
        ("artificial-note", 123),
    ],
)
def test_notes_must_be_iterable_of_non_empty_strings(notes: object) -> None:
    with pytest.raises(ValueError, match="notes"):
        ArtificialSourceManifestMetadata(
            manifest_id="artificial-manifest-001",
            source_family="artificial_source_acquisition",
            dataset_name="artificial-dataset",
            version_label="static-version-label",
            record_count=0,
            notes=notes,  # type: ignore[arg-type]
        )


def test_dataset_name_is_artificial_label_only() -> None:
    metadata = ArtificialSourceManifestMetadata(
        manifest_id="artificial-manifest-001",
        source_family="artificial_source_acquisition",
        dataset_name="not/a/filesystem/path.csv",
        version_label="static-version-label",
        record_count=0,
    )

    assert metadata.dataset_name == "not/a/filesystem/path.csv"


def test_artificial_manifest_metadata_collection_can_be_created_with_one_manifest() -> None:
    metadata = valid_manifest_metadata()
    collection = ArtificialSourceManifestMetadataCollection((metadata,))

    assert collection.manifests == (metadata,)
    assert collection.count == 1
    assert collection.manifest_ids == ("artificial-manifest-001",)
    assert collection.source_families == ("artificial_source_acquisition",)


def test_artificial_manifest_metadata_collection_can_be_created_with_multiple_manifests() -> None:
    first_metadata = valid_manifest_metadata()
    second_metadata = second_manifest_metadata()

    collection = ArtificialSourceManifestMetadataCollection(
        (second_metadata, first_metadata),
    )

    assert collection.manifests == (second_metadata, first_metadata)
    assert collection.count == 2
    assert collection.manifest_ids == (
        "artificial-manifest-002",
        "artificial-manifest-001",
    )
    assert collection.source_families == (
        "artificial_source_acquisition",
        "second_artificial_source_family",
    )


def test_artificial_manifest_metadata_collection_stores_incoming_list_as_tuple() -> None:
    metadata = valid_manifest_metadata()

    collection = ArtificialSourceManifestMetadataCollection(
        [metadata],  # type: ignore[arg-type]
    )

    assert collection.manifests == (metadata,)


def test_artificial_manifest_metadata_collection_allows_empty_collection() -> None:
    collection = ArtificialSourceManifestMetadataCollection()

    assert collection.manifests == ()
    assert collection.count == 0
    assert collection.manifest_ids == ()
    assert collection.source_families == ()


def test_artificial_manifest_metadata_collection_rejects_duplicate_manifest_ids() -> None:
    duplicate_metadata = ArtificialSourceManifestMetadata(
        manifest_id="artificial-manifest-001",
        source_family="second_artificial_source_family",
        dataset_name="second-artificial-dataset",
        version_label="second-static-version-label",
        record_count=1,
    )

    with pytest.raises(ValueError, match="manifest_id values must be unique."):
        ArtificialSourceManifestMetadataCollection(
            (valid_manifest_metadata(), duplicate_metadata),
        )


def test_artificial_manifest_metadata_collection_rejects_non_manifest_items() -> None:
    with pytest.raises(
        TypeError,
        match="manifests must contain only ArtificialSourceManifestMetadata.",
    ):
        ArtificialSourceManifestMetadataCollection(
            ("not-manifest-metadata",),  # type: ignore[arg-type]
        )


def test_artificial_manifest_metadata_collection_is_immutable() -> None:
    collection = ArtificialSourceManifestMetadataCollection((valid_manifest_metadata(),))

    with pytest.raises(FrozenInstanceError):
        collection.manifests = ()  # type: ignore[misc]


def test_module_public_symbols_include_artificial_manifest_metadata_shape() -> None:
    assert source_manifest.__all__ == (
        "ArtificialSourceManifestMetadata",
        "ArtificialSourceManifestMetadataCollection",
        "ArtificialSourceManifestCollectionValidationSummary",
        "ArtificialSourceManifestValidationSummary",
    )
    assert (
        source_manifest.ArtificialSourceManifestMetadata
        is ArtificialSourceManifestMetadata
    )
    assert (
        source_manifest.ArtificialSourceManifestMetadataCollection
        is ArtificialSourceManifestMetadataCollection
    )
    assert (
        source_manifest.ArtificialSourceManifestCollectionValidationSummary
        is ArtificialSourceManifestCollectionValidationSummary
    )
    assert (
        source_manifest.ArtificialSourceManifestValidationSummary
        is ArtificialSourceManifestValidationSummary
    )


def test_root_package_exports_artificial_manifest_metadata() -> None:
    assert "ArtificialSourceManifestMetadata" in carbonfactor_parser.__all__
    assert "ArtificialSourceManifestMetadataCollection" in carbonfactor_parser.__all__
    assert (
        "ArtificialSourceManifestCollectionValidationSummary"
        in carbonfactor_parser.__all__
    )
    assert carbonfactor_parser.ArtificialSourceManifestMetadata is (
        ArtificialSourceManifestMetadata
    )
    assert carbonfactor_parser.ArtificialSourceManifestMetadataCollection is (
        ArtificialSourceManifestMetadataCollection
    )
    assert carbonfactor_parser.ArtificialSourceManifestCollectionValidationSummary is (
        ArtificialSourceManifestCollectionValidationSummary
    )
    assert RootManifestMetadata is ArtificialSourceManifestMetadata
    assert RootManifestCollection is ArtificialSourceManifestMetadataCollection
    assert (
        RootCollectionValidationSummary
        is ArtificialSourceManifestCollectionValidationSummary
    )


def test_valid_artificial_manifest_collection_validation_summary_can_be_created() -> None:
    summary = ArtificialSourceManifestCollectionValidationSummary(
        manifest_count=2,
        unique_source_family_count=1,
        issue_count=0,
        is_valid=True,
    )

    assert summary.manifest_count == 2
    assert summary.unique_source_family_count == 1
    assert summary.issue_count == 0
    assert summary.is_valid is True


def test_artificial_manifest_collection_validation_summary_is_immutable() -> None:
    summary = ArtificialSourceManifestCollectionValidationSummary(
        manifest_count=1,
        unique_source_family_count=1,
        issue_count=0,
        is_valid=True,
    )

    with pytest.raises(FrozenInstanceError):
        summary.issue_count = 1  # type: ignore[misc]


def test_collection_validation_summary_from_empty_collection_is_valid() -> None:
    summary = ArtificialSourceManifestCollectionValidationSummary.from_collection(
        ArtificialSourceManifestMetadataCollection(),
        issue_count=0,
    )

    assert summary == ArtificialSourceManifestCollectionValidationSummary(
        manifest_count=0,
        unique_source_family_count=0,
        issue_count=0,
        is_valid=True,
    )


def test_collection_validation_summary_from_one_manifest_is_valid() -> None:
    collection = ArtificialSourceManifestMetadataCollection((valid_manifest_metadata(),))

    summary = ArtificialSourceManifestCollectionValidationSummary.from_collection(
        collection,
        issue_count=0,
    )

    assert summary == ArtificialSourceManifestCollectionValidationSummary(
        manifest_count=1,
        unique_source_family_count=1,
        issue_count=0,
        is_valid=True,
    )


def test_collection_validation_summary_counts_unique_source_families() -> None:
    collection = ArtificialSourceManifestMetadataCollection(
        (
            valid_manifest_metadata(),
            second_manifest_metadata(),
            third_manifest_metadata(),
        ),
    )

    summary = ArtificialSourceManifestCollectionValidationSummary.from_collection(
        collection,
        issue_count=0,
    )

    assert summary.manifest_count == 3
    assert summary.unique_source_family_count == 2
    assert summary.issue_count == 0
    assert summary.is_valid is True


def test_collection_validation_summary_from_collection_with_issues_is_invalid() -> None:
    collection = ArtificialSourceManifestMetadataCollection((valid_manifest_metadata(),))

    summary = ArtificialSourceManifestCollectionValidationSummary.from_collection(
        collection,
        issue_count=2,
    )

    assert summary.manifest_count == 1
    assert summary.unique_source_family_count == 1
    assert summary.issue_count == 2
    assert summary.is_valid is False


@pytest.mark.parametrize(
    "field_name",
    ["manifest_count", "unique_source_family_count", "issue_count"],
)
def test_collection_validation_summary_rejects_negative_counts(
    field_name: str,
) -> None:
    values = {
        "manifest_count": 0,
        "unique_source_family_count": 0,
        "issue_count": 0,
        "is_valid": True,
    }
    values[field_name] = -1

    with pytest.raises(
        ValueError,
        match=f"{field_name} must be a non-negative integer.",
    ):
        ArtificialSourceManifestCollectionValidationSummary(**values)


def test_collection_validation_summary_factory_rejects_negative_issue_count() -> None:
    with pytest.raises(
        ValueError,
        match="issue_count must be a non-negative integer.",
    ):
        ArtificialSourceManifestCollectionValidationSummary.from_collection(
            ArtificialSourceManifestMetadataCollection(),
            issue_count=-1,
        )


def test_collection_validation_summary_factory_rejects_non_collection() -> None:
    with pytest.raises(
        TypeError,
        match="collection must be an ArtificialSourceManifestMetadataCollection.",
    ):
        ArtificialSourceManifestCollectionValidationSummary.from_collection(
            valid_manifest_metadata(),  # type: ignore[arg-type]
            issue_count=0,
        )


def test_valid_artificial_manifest_validation_summary_can_be_created() -> None:
    summary = ArtificialSourceManifestValidationSummary(
        manifest_id="artificial-manifest-001",
        source_family="artificial_source_acquisition",
        dataset_name="artificial-dataset",
        issue_count=0,
        is_valid=True,
    )

    assert summary.manifest_id == "artificial-manifest-001"
    assert summary.source_family == "artificial_source_acquisition"
    assert summary.dataset_name == "artificial-dataset"
    assert summary.issue_count == 0
    assert summary.is_valid is True


def test_artificial_manifest_validation_summary_is_immutable() -> None:
    summary = ArtificialSourceManifestValidationSummary(
        manifest_id="artificial-manifest-001",
        source_family="artificial_source_acquisition",
        dataset_name="artificial-dataset",
        issue_count=0,
        is_valid=True,
    )

    with pytest.raises(FrozenInstanceError):
        summary.issue_count = 1  # type: ignore[misc]


def test_validation_summary_from_metadata_with_no_issues_is_valid() -> None:
    summary = ArtificialSourceManifestValidationSummary.from_metadata(
        valid_manifest_metadata(),
        issue_count=0,
    )

    assert summary == ArtificialSourceManifestValidationSummary(
        manifest_id="artificial-manifest-001",
        source_family="artificial_source_acquisition",
        dataset_name="artificial-dataset",
        issue_count=0,
        is_valid=True,
    )


def test_validation_summary_from_metadata_with_issues_is_invalid() -> None:
    summary = ArtificialSourceManifestValidationSummary.from_metadata(
        valid_manifest_metadata(),
        issue_count=2,
    )

    assert summary.issue_count == 2
    assert summary.is_valid is False


def test_validation_summary_rejects_negative_issue_count() -> None:
    with pytest.raises(
        ValueError,
        match="issue_count must be a non-negative integer.",
    ):
        ArtificialSourceManifestValidationSummary(
            manifest_id="artificial-manifest-001",
            source_family="artificial_source_acquisition",
            dataset_name="artificial-dataset",
            issue_count=-1,
            is_valid=False,
        )


def test_validation_summary_factory_rejects_negative_issue_count() -> None:
    with pytest.raises(
        ValueError,
        match="issue_count must be a non-negative integer.",
    ):
        ArtificialSourceManifestValidationSummary.from_metadata(
            valid_manifest_metadata(),
            issue_count=-1,
        )


def test_validation_summary_factory_rejects_non_manifest_metadata() -> None:
    with pytest.raises(
        TypeError,
        match="metadata must be an ArtificialSourceManifestMetadata.",
    ):
        ArtificialSourceManifestValidationSummary.from_metadata(  # type: ignore[arg-type]
            object(),
            issue_count=0,
        )


def test_root_package_exports_artificial_manifest_validation_summary() -> None:
    assert "ArtificialSourceManifestValidationSummary" in carbonfactor_parser.__all__
    assert carbonfactor_parser.ArtificialSourceManifestValidationSummary is (
        ArtificialSourceManifestValidationSummary
    )
    assert RootManifestValidationSummary is ArtificialSourceManifestValidationSummary
