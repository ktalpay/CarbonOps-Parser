"""Runtime-passive source acquisition request planning contracts."""

from __future__ import annotations

from carbonfactor_parser.source_acquisition.models import (
    SourceAcquisitionPlan,
    SourceAcquisitionPlanMode,
    SourceAcquisitionRequest,
)
from carbonfactor_parser.source_adapters.discovery import (
    discover_phase1_sources_dry_run,
)

_PHASE1_SOURCE_FAMILIES = (
    "ghg_protocol",
    "defra_desnz",
    "ipcc_efdb",
)


def create_phase1_source_acquisition_request(
    selected_source_families: tuple[str, ...] | list[str] | None = None,
) -> SourceAcquisitionRequest:
    """Create a dry-run Phase 1 acquisition request without runtime work."""

    requested_families = (
        _PHASE1_SOURCE_FAMILIES
        if selected_source_families is None
        else tuple(selected_source_families)
    )
    _validate_selected_source_families(requested_families)
    return SourceAcquisitionRequest(
        selected_source_families=requested_families,
        mode=SourceAcquisitionPlanMode.DRY_RUN,
    )


def create_phase1_source_acquisition_plan(
    request: SourceAcquisitionRequest | None = None,
) -> SourceAcquisitionPlan:
    """Return a deterministic dry-run acquisition plan for Phase 1 sources."""

    active_request = (
        create_phase1_source_acquisition_request()
        if request is None
        else request
    )
    if active_request.mode is not SourceAcquisitionPlanMode.DRY_RUN:
        raise ValueError("Only dry-run source acquisition plans are supported.")

    _validate_selected_source_families(active_request.selected_source_families)
    selected_family_set = frozenset(active_request.selected_source_families)
    discovery_results = tuple(
        result
        for result in discover_phase1_sources_dry_run()
        if result.documents
        and result.documents[0].source_family in selected_family_set
    )

    return SourceAcquisitionPlan(
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        selected_source_families=active_request.selected_source_families,
        discovery_results=discovery_results,
    )


def _validate_selected_source_families(source_families: tuple[str, ...]) -> None:
    if not source_families:
        raise ValueError("selected_source_families must not be empty.")

    unknown_families = tuple(
        source_family
        for source_family in source_families
        if source_family not in _PHASE1_SOURCE_FAMILIES
    )
    if unknown_families:
        raise ValueError(f"Unknown source families: {unknown_families!r}")

    if len(set(source_families)) != len(source_families):
        raise ValueError("selected_source_families must not contain duplicates.")
