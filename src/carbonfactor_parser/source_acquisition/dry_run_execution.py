"""Runtime-passive source acquisition dry-run execution contracts."""

from __future__ import annotations

from carbonfactor_parser.source_acquisition.models import (
    SourceAcquisitionDryRunExecutionResult,
    SourceAcquisitionDryRunFamilyResult,
    SourceAcquisitionDryRunResultStatus,
    SourceAcquisitionPlan,
    SourceAcquisitionPlanMode,
    SourceDiscoveryResult,
)
from carbonfactor_parser.source_acquisition.planning import (
    create_phase1_source_acquisition_plan,
)


def evaluate_source_acquisition_plan_dry_run(
    plan: SourceAcquisitionPlan | None = None,
) -> SourceAcquisitionDryRunExecutionResult:
    """Return a deterministic dry-run result without acquisition execution."""

    active_plan = plan if plan is not None else create_phase1_source_acquisition_plan()
    if active_plan.mode is not SourceAcquisitionPlanMode.DRY_RUN:
        raise ValueError("Only dry-run source acquisition plans can be evaluated.")

    family_results = tuple(
        SourceAcquisitionDryRunFamilyResult(
            source_family=_source_family_for_discovery_result(discovery_result),
            status=SourceAcquisitionDryRunResultStatus.PLANNED,
            planned_document_count=len(discovery_result.documents),
            discovery_result=discovery_result,
            warnings=discovery_result.warnings,
        )
        for discovery_result in active_plan.discovery_results
    )

    return SourceAcquisitionDryRunExecutionResult(
        status=SourceAcquisitionDryRunResultStatus.PLANNED,
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        selected_source_families=active_plan.selected_source_families,
        family_results=family_results,
    )


def _source_family_for_discovery_result(
    discovery_result: SourceDiscoveryResult,
) -> str:
    if not discovery_result.documents:
        raise ValueError("discovery_result must include at least one document.")
    return discovery_result.documents[0].source_family
