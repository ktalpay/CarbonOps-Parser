"""Artificial in-memory manifest metadata usage example."""

from __future__ import annotations

from carbonfactor_parser import (
    ArtificialSourceManifestCollectionValidationSummary,
    ArtificialSourceManifestMetadata,
    ArtificialSourceManifestMetadataCollection,
    ArtificialSourceManifestValidationSummary,
)


def build_artificial_manifest_usage_summary() -> dict[str, object]:
    first_metadata = ArtificialSourceManifestMetadata(
        manifest_id="artificial-manifest-alpha",
        source_family="artificial_manifest_family",
        dataset_name="artificial_dataset_alpha",
        version_label="static_version_alpha",
        record_count=2,
        generated_by="artificial_manifest_usage_example",
        notes=("artificial_note_alpha",),
    )
    second_metadata = ArtificialSourceManifestMetadata(
        manifest_id="artificial-manifest-beta",
        source_family="second_artificial_manifest_family",
        dataset_name="artificial_dataset_beta",
        version_label="static_version_beta",
        record_count=1,
        generated_by="artificial_manifest_usage_example",
        notes=("artificial_note_beta",),
    )

    collection = ArtificialSourceManifestMetadataCollection(
        (first_metadata, second_metadata),
    )
    manifest_summaries = tuple(
        ArtificialSourceManifestValidationSummary.from_metadata(
            metadata,
            issue_count=0,
        )
        for metadata in collection.manifests
    )
    collection_summary = (
        ArtificialSourceManifestCollectionValidationSummary.from_collection(
            collection,
            issue_count=0,
        )
    )

    return {
        "collection_count": collection.count,
        "manifest_ids": collection.manifest_ids,
        "source_families": collection.source_families,
        "manifests": tuple(
            {
                "manifest_id": metadata.manifest_id,
                "source_family": metadata.source_family,
                "dataset_name": metadata.dataset_name,
                "version_label": metadata.version_label,
                "record_count": metadata.record_count,
                "generated_by": metadata.generated_by,
                "notes": metadata.notes,
            }
            for metadata in collection.manifests
        ),
        "manifest_validation_summaries": tuple(
            {
                "manifest_id": summary.manifest_id,
                "source_family": summary.source_family,
                "dataset_name": summary.dataset_name,
                "issue_count": summary.issue_count,
                "is_valid": summary.is_valid,
            }
            for summary in manifest_summaries
        ),
        "collection_validation_summary": {
            "manifest_count": collection_summary.manifest_count,
            "unique_source_family_count": (
                collection_summary.unique_source_family_count
            ),
            "issue_count": collection_summary.issue_count,
            "is_valid": collection_summary.is_valid,
        },
    }
