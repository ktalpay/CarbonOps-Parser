"""Runtime-passive source document manifest contracts."""

from __future__ import annotations

from carbonfactor_parser.source_acquisition.download_planning import (
    create_source_download_batch_plan,
)
from carbonfactor_parser.source_acquisition.models import (
    SourceAcquisitionPlanMode,
    SourceDocumentChecksum,
    SourceDocumentChecksumStatus,
    SourceDocumentManifest,
    SourceDocumentManifestEntry,
    SourceDownloadBatchPlan,
)


DRY_RUN_SOURCE_DOCUMENT_CHECKSUM = SourceDocumentChecksum(
    algorithm="sha256",
    value=None,
    status=SourceDocumentChecksumStatus.DRY_RUN_UNAVAILABLE,
)


def create_source_document_manifest(
    download_plan: SourceDownloadBatchPlan | None = None,
) -> SourceDocumentManifest:
    """Derive deterministic source document identity metadata without file I/O."""

    active_plan = (
        create_source_download_batch_plan() if download_plan is None else download_plan
    )
    if active_plan.mode is not SourceAcquisitionPlanMode.DRY_RUN:
        raise ValueError("Only dry-run source document manifests are supported.")

    entries = tuple(
        SourceDocumentManifestEntry(
            source_family=request.source_family,
            logical_document_name=request.source_name,
            source_reference=request.source_reference,
            target_logical_path=request.target_logical_path,
            checksum=DRY_RUN_SOURCE_DOCUMENT_CHECKSUM,
            mode=SourceAcquisitionPlanMode.DRY_RUN,
        )
        for request in active_plan.requests
    )

    return SourceDocumentManifest(
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        selected_source_families=active_plan.selected_source_families,
        entries=entries,
    )
