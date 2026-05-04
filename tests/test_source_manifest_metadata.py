from dataclasses import FrozenInstanceError

import pytest

import carbonfactor_parser
from carbonfactor_parser import source_manifest
from carbonfactor_parser.source_manifest import ArtificialSourceManifestMetadata


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


def test_module_public_symbols_include_artificial_manifest_metadata_shape() -> None:
    assert source_manifest.__all__ == ("ArtificialSourceManifestMetadata",)
    assert (
        source_manifest.ArtificialSourceManifestMetadata
        is ArtificialSourceManifestMetadata
    )


def test_root_package_does_not_export_manifest_metadata_yet() -> None:
    assert "ArtificialSourceManifestMetadata" not in carbonfactor_parser.__all__
    assert not hasattr(carbonfactor_parser, "ArtificialSourceManifestMetadata")
