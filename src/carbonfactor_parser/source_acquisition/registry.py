"""Source acquisition descriptor registry helpers."""

from __future__ import annotations

from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor


def create_default_source_acquisition_registry() -> tuple[SourceAcquisitionDescriptor, ...]:
    """Return deterministic Phase 1 source descriptors.

    URLs are discovery/homepage level unless explicitly verified as direct downloads
    in future tasks.
    """

    registry = (
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

    validate_source_acquisition_registry(registry)
    return registry


def validate_source_acquisition_registry(
    descriptors: tuple[SourceAcquisitionDescriptor, ...] | list[SourceAcquisitionDescriptor],
) -> tuple[SourceAcquisitionDescriptor, ...]:
    """Validate descriptor constraints for deterministic registry behavior."""

    normalized_descriptors = tuple(descriptors)
    seen_source_ids: set[str] = set()

    for index, descriptor in enumerate(normalized_descriptors):
        if not isinstance(descriptor, SourceAcquisitionDescriptor):
            raise TypeError(
                f"descriptors[{index}] must be a SourceAcquisitionDescriptor.",
            )

        _validate_required_string(descriptor.source_id, "source_id", descriptor.source_id)
        _validate_required_string(descriptor.source_family, "source_family", descriptor.source_id)
        _validate_required_string(descriptor.homepage_url, "homepage_url", descriptor.source_id)
        _validate_required_string(
            descriptor.acquisition_url,
            "acquisition_url",
            descriptor.source_id,
        )

        if descriptor.source_id in seen_source_ids:
            raise ValueError(f"Duplicate source_id found: {descriptor.source_id}")
        seen_source_ids.add(descriptor.source_id)

    return normalized_descriptors


def _validate_required_string(value: str, field_name: str, source_id: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string for source_id '{source_id}'.")
