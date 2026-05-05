from pathlib import Path

import pytest

from carbonfactor_parser.source_acquisition import (
    SourceAcquisitionTarget,
    create_default_source_acquisition_registry,
    plan_source_acquisition_target,
    plan_source_acquisition_targets,
)
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor


def test_single_target_planning_is_deterministic(tmp_path: Path) -> None:
    descriptor = create_default_source_acquisition_registry()[0]

    first = plan_source_acquisition_target(descriptor, tmp_path)
    second = plan_source_acquisition_target(descriptor, tmp_path)

    assert first == second


def test_bulk_target_planning_preserves_default_registry_order(tmp_path: Path) -> None:
    registry = create_default_source_acquisition_registry()

    planned = plan_source_acquisition_targets(registry, tmp_path)

    assert tuple(item.source_id for item in planned) == tuple(
        descriptor.source_id for descriptor in registry
    )


def test_planning_does_not_create_directories_or_files(tmp_path: Path) -> None:
    target_base_dir = tmp_path / "planned" / "targets"
    descriptor = create_default_source_acquisition_registry()[0]

    planned = plan_source_acquisition_target(descriptor, target_base_dir)

    assert not target_base_dir.exists()
    assert not planned.local_path.exists()


def test_source_id_is_reflected_in_filename(tmp_path: Path) -> None:
    descriptor = SourceAcquisitionDescriptor(
        source_id="My Source.ID",
        source_family="family",
        display_name="Name",
        homepage_url="discovery://source/homepage",
        acquisition_url="discovery://source/acquisition",
        expected_format="csv",
        description="description",
    )

    planned = plan_source_acquisition_target(descriptor, tmp_path)

    assert planned.target_filename == "my_source.id.csv"


@pytest.mark.parametrize(
    ("expected_format", "extension"),
    [
        ("csv", ".csv"),
        ("json", ".json"),
        ("xlsx", ".xlsx"),
        ("zip", ".zip"),
        ("pdf", ".pdf"),
        ("unknown", ".dat"),
        ("html", ".dat"),
        ("discovery", ".dat"),
    ],
)
def test_expected_format_maps_to_extension(
    tmp_path: Path,
    expected_format: str,
    extension: str,
) -> None:
    descriptor = SourceAcquisitionDescriptor(
        source_id="source_one",
        source_family="family",
        display_name="Name",
        homepage_url="discovery://source/homepage",
        acquisition_url="discovery://source/acquisition",
        expected_format=expected_format,
        description="description",
    )

    planned = plan_source_acquisition_target(descriptor, tmp_path)

    assert planned.target_filename.endswith(extension)


@pytest.mark.parametrize(
    ("source_id", "source_family", "expected_format", "base_directory", "match"),
    [
        ("", "family", "csv", "/tmp", "source_id must be a non-empty string."),
        ("source", "", "csv", "/tmp", "source_family must be a non-empty string."),
        ("source", "family", "", "/tmp", "expected_format must be a non-empty string."),
        (
            "source",
            "family",
            "csv",
            "",
            "base_directory must be a non-empty path.",
        ),
    ],
)
def test_invalid_empty_values_raise_value_error(
    source_id: str,
    source_family: str,
    expected_format: str,
    base_directory: str,
    match: str,
) -> None:
    descriptor = SourceAcquisitionDescriptor(
        source_id=source_id,
        source_family=source_family,
        display_name="Name",
        homepage_url="discovery://source/homepage",
        acquisition_url="discovery://source/acquisition",
        expected_format=expected_format,
        description="description",
    )

    with pytest.raises(ValueError, match=match):
        plan_source_acquisition_target(descriptor, base_directory)


def test_source_acquisition_targets_public_exports_are_importable(tmp_path: Path) -> None:
    descriptor = create_default_source_acquisition_registry()[0]

    planned = plan_source_acquisition_target(descriptor, tmp_path)
    planned_many = plan_source_acquisition_targets((descriptor,), tmp_path)

    assert isinstance(planned, SourceAcquisitionTarget)
    assert isinstance(planned_many, tuple)
