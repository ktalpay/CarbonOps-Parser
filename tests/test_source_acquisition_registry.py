from dataclasses import FrozenInstanceError

import pytest

from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor
from carbonfactor_parser.source_acquisition.registry import (
    create_default_source_acquisition_registry,
    validate_source_acquisition_registry,
)


def test_default_registry_contains_exactly_phase1_source_descriptors() -> None:
    registry = create_default_source_acquisition_registry()

    assert tuple(descriptor.source_id for descriptor in registry) == (
        "ghg_protocol",
        "defra_desnz",
        "ipcc_efdb",
    )


def test_default_registry_source_ids_are_unique() -> None:
    registry = create_default_source_acquisition_registry()

    assert len({descriptor.source_id for descriptor in registry}) == len(registry)


def test_default_registry_required_fields_are_non_empty() -> None:
    registry = create_default_source_acquisition_registry()

    for descriptor in registry:
        assert descriptor.source_id.strip()
        assert descriptor.source_family.strip()
        assert descriptor.homepage_url.strip()
        assert descriptor.acquisition_url.strip()


def test_source_acquisition_descriptor_is_immutable() -> None:
    descriptor = create_default_source_acquisition_registry()[0]

    with pytest.raises(FrozenInstanceError):
        descriptor.source_id = "mutated"  # type: ignore[misc]


def test_duplicate_source_ids_raise_clear_exception() -> None:
    duplicate_registry = (
        SourceAcquisitionDescriptor(
            source_id="duplicate_source",
            source_family="family_one",
            display_name="One",
            homepage_url="discovery://test/one",
            acquisition_url="discovery://test/one/discovery",
            expected_format="discovery",
            description="placeholder",
            enabled=True,
        ),
        SourceAcquisitionDescriptor(
            source_id="duplicate_source",
            source_family="family_two",
            display_name="Two",
            homepage_url="discovery://test/two",
            acquisition_url="discovery://test/two/discovery",
            expected_format="discovery",
            description="placeholder",
            enabled=True,
        ),
    )

    with pytest.raises(ValueError, match="Duplicate source_id found: duplicate_source"):
        validate_source_acquisition_registry(duplicate_registry)


def test_registry_exports_are_stable_and_deterministic() -> None:
    assert create_default_source_acquisition_registry() == (
        SourceAcquisitionDescriptor(
            source_id="ghg_protocol",
            source_family="ghg_protocol",
            display_name="GHG Protocol",
            homepage_url="discovery://ghg_protocol/homepage",
            acquisition_url="discovery://ghg_protocol/acquisition",
            expected_format="discovery",
            description=(
                "Discovery URL placeholder for future source-specific acquisition "
                "work; not a verified direct download endpoint."
            ),
            enabled=True,
        ),
        SourceAcquisitionDescriptor(
            source_id="defra_desnz",
            source_family="defra_desnz",
            display_name="DEFRA/DESNZ",
            homepage_url="discovery://defra_desnz/homepage",
            acquisition_url="discovery://defra_desnz/homepage",
            expected_format="discovery",
            description=(
                "Discovery URL placeholder for future source-specific acquisition "
                "work; not a verified direct download endpoint."
            ),
            enabled=True,
        ),
        SourceAcquisitionDescriptor(
            source_id="ipcc_efdb",
            source_family="ipcc_efdb",
            display_name="IPCC EFDB",
            homepage_url="discovery://ipcc_efdb/homepage",
            acquisition_url="discovery://ipcc_efdb/homepage",
            expected_format="discovery",
            description=(
                "Discovery URL placeholder for future source-specific acquisition "
                "work; not a verified direct download endpoint."
            ),
            enabled=True,
        ),
    )
