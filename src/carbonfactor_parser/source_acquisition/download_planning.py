"""Runtime-passive source download request planning contracts."""

from __future__ import annotations

from carbonfactor_parser.source_acquisition.dry_run_execution import (
    evaluate_source_acquisition_plan_dry_run,
)
from carbonfactor_parser.source_acquisition.models import (
    SourceAcquisitionDryRunExecutionResult,
    SourceAcquisitionPlanMode,
    SourceDownloadBatchPlan,
    SourceDownloadRequest,
)


def create_source_download_batch_plan(
    dry_run_result: SourceAcquisitionDryRunExecutionResult | None = None,
) -> SourceDownloadBatchPlan:
    """Derive deterministic download requests without performing downloads."""

    active_result = (
        evaluate_source_acquisition_plan_dry_run()
        if dry_run_result is None
        else dry_run_result
    )
    if active_result.mode is not SourceAcquisitionPlanMode.DRY_RUN:
        raise ValueError("Only dry-run source download plans are supported.")

    requests: list[SourceDownloadRequest] = []
    for family_result in active_result.family_results:
        for document in family_result.discovery_result.documents:
            if document.source_family != family_result.source_family:
                raise ValueError(
                    "discovery document source_family must match family result."
                )
            requests.append(
                SourceDownloadRequest(
                    source_family=family_result.source_family,
                    source_name=document.source_name,
                    source_reference=document.source_reference,
                    target_logical_path=(
                        f"phase1/{family_result.source_family}/source"
                    ),
                    mode=SourceAcquisitionPlanMode.DRY_RUN,
                ),
            )

    return SourceDownloadBatchPlan(
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        selected_source_families=active_result.selected_source_families,
        requests=tuple(requests),
    )
