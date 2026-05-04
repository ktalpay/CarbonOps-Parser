# Artificial Manifest Collection Validation Summary

This document describes the artificial-only boundary for `ArtificialSourceManifestCollectionValidationSummary` after CO-079A.

It is documentation-only. It adds no code, tests, fixtures, runtime behavior, real source data, real source URLs, file reading, remote access, DB/cache/persistence behavior, scheduler/retry/cancel behavior, config/credential loading, parser runtime behavior, normalization runtime behavior, source adapter dispatch behavior, manifest loading, manifest registry behavior, manifest selection behavior, unit conversion, factor correctness logic, compliance/legal interpretation, carbon accounting correctness, or readiness for production use.

## Purpose

`ArtificialSourceManifestCollectionValidationSummary` represents a collection-level validation outcome shape for `ArtificialSourceManifestMetadataCollection`.

It is intentionally small. It records how many artificial manifest metadata records are present, how many unique artificial source family labels are present, and whether an already-known artificial issue count represents a valid or invalid collection-level outcome.

It does not load manifests, discover manifests, register manifests, select manifests, read files, access remote locations, persist data, schedule work, dispatch adapters, run parsers, run normalization, convert units, verify factors, interpret compliance/legal meaning, or establish carbon accounting correctness.

## Relationship To ArtificialSourceManifestMetadataCollection

`ArtificialSourceManifestCollectionValidationSummary` summarizes an `ArtificialSourceManifestMetadataCollection`.

The collection remains responsible for holding in-memory `ArtificialSourceManifestMetadata` records. The summary only captures collection-level counts and an issue outcome:

- `manifest_count`
- `unique_source_family_count`
- `issue_count`
- `is_valid`

This relationship is in-memory and artificial-only. It does not create a manifest registry, source catalog, selection mechanism, loader, file contract, adapter contract, parser contract, normalization contract, persistence contract, scheduler contract, unit conversion contract, or factor correctness contract.

## from_collection Usage

Use `from_collection(...)` when an artificial validation task already has an `ArtificialSourceManifestMetadataCollection` value and a deterministic issue count:

```python
from carbonfactor_parser import (
    ArtificialSourceManifestCollectionValidationSummary,
    ArtificialSourceManifestMetadata,
    ArtificialSourceManifestMetadataCollection,
)

metadata = ArtificialSourceManifestMetadata(
    manifest_id="artificial-manifest-001",
    source_family="artificial_source_family",
    dataset_name="artificial-dataset",
    version_label="static-version-label",
    record_count=2,
)

collection = ArtificialSourceManifestMetadataCollection([metadata])

summary = ArtificialSourceManifestCollectionValidationSummary.from_collection(
    collection,
    issue_count=0,
)
```

This example is artificial and in-memory only. It does not read a file, reference a real source, access a remote location, use config, use credentials, persist data, run a scheduler, dispatch an adapter, run a parser, run normalization, convert units, or check factor correctness.

## Collection-Level Summary Fields

`ArtificialSourceManifestCollectionValidationSummary` contains:

- `manifest_count`: the number of artificial manifest metadata records in the collection.
- `unique_source_family_count`: the number of unique artificial `source_family` labels in the collection.
- `issue_count`: the number of artificial collection-level validation issues already known to the caller.
- `is_valid`: a boolean derived from `issue_count` when using `from_collection(...)`.

These fields summarize existing in-memory metadata only. They are not lookup, selection, filtering, manifest loading, source discovery, adapter routing, parser routing, normalization routing, persistence lookup, remote availability checking, source correctness checking, unit conversion, or factor correctness behavior.

## issue_count Semantics

When using `from_collection(...)`:

- `issue_count == 0` means `is_valid` is `True`.
- `issue_count > 0` means `is_valid` is `False`.
- Negative `issue_count` is invalid input.

These semantics only describe artificial collection-level validation outcome shape. They do not define a validation engine, issue taxonomy, registry, selector, manifest loader, parser contract, normalization contract, persistence contract, scheduler contract, or runtime workflow.

## Artificial-Only In-Memory Usage Boundary

The summary may be used for:

- Artificial in-memory examples.
- Boundary-safe tests.
- Shape-only collection validation result summaries.
- Deterministic collection counts and issue outcomes.
- Future artificial manifest collection validation tasks when explicitly scoped.

The summary must not be used to hide runtime behavior. It must not load manifests, register manifests, select manifests, read files, validate paths, discover directories, access remote locations, download source documents, persist manifests, cache manifests, schedule work, retry work, cancel work, load config, load credentials, dispatch adapters, run parsers, run normalization, convert units, or verify factors.

## Explicit Non-Goals

`ArtificialSourceManifestCollectionValidationSummary` is not:

- A manifest loader.
- A manifest registry.
- A manifest selector.
- A file reader.
- A filesystem path validator.
- A directory scanner.
- A remote downloader.
- A remote availability checker.
- A real source URL validator.
- A source URL catalog.
- A credential/config loader.
- A persistence/cache model.
- A DB model.
- A scheduler/retry/cancel model.
- A parser runtime contract.
- A normalization runtime contract.
- A source adapter dispatcher.
- A checksum enforcement mechanism.
- A unit conversion contract.
- A factor correctness contract.
- A compliance/legal correctness contract.
- A carbon accounting correctness contract.
- A production readiness claim.

Any future task that needs one of these areas requires explicit scope, tests, and review gates.

## Relationship To Manifest Collection Boundary

[Artificial Manifest Metadata Collection](artificial-manifest-metadata-collection.md) documents the artificial-only boundary for `ArtificialSourceManifestMetadataCollection`.

`ArtificialSourceManifestCollectionValidationSummary` sits after that collection shape. It represents collection-level validation outcome metadata only and does not expand the collection into loading, registry, selection, acquisition, adapter handoff, parser handoff, normalization handoff, persistence, cache behavior, scheduling, retry/cancel behavior, config/credential loading, unit conversion, factor correctness, or compliance/legal interpretation.

## Relationship To Manifest Validation Summary

[Artificial Manifest Validation Summary](artificial-manifest-validation-summary.md) documents `ArtificialSourceManifestValidationSummary` for a single artificial manifest metadata record.

`ArtificialSourceManifestCollectionValidationSummary` provides a collection-level companion shape. It does not replace single-record summaries and does not validate real source correctness, official source status, parser correctness, normalization correctness, factor correctness, compliance/legal correctness, carbon accounting correctness, or readiness for production use.

## Review Checklist

Future artificial manifest collection validation summary changes should confirm:

- The task scope is explicit and narrow.
- Documentation-only tasks remain documentation-only.
- Summary changes remain artificial-only unless separately scoped.
- Examples use in-memory artificial labels only.
- `issue_count` semantics remain deterministic.
- Collection counts remain derived from in-memory collection shape only.
- No manifest registry, selection, loading, lookup, or runtime dispatch behavior is introduced.
- No real source data or real source URLs are introduced.
- No file reading, path validation, or directory scanning is introduced.
- No remote access or download behavior is introduced.
- No DB/cache/persistence behavior is introduced.
- No scheduler/retry/cancel behavior is introduced.
- No config/credential loading is introduced.
- No parser, normalization, source adapter dispatch, unit conversion, or factor correctness behavior is introduced.
- No compliance/legal correctness, carbon accounting correctness, or readiness for production use claim is introduced.

## Related Documents

- [Artificial Manifest Metadata Collection](artificial-manifest-metadata-collection.md)
- [Artificial Manifest Metadata Boundaries](artificial-manifest-metadata-boundaries.md)
- [Artificial Manifest Validation Summary](artificial-manifest-validation-summary.md)
- [Artificial Source Acquisition Phase Closure](artificial-source-acquisition-phase-closure.md)
- [Source Acquisition Boundary](source-acquisition-boundary.md)
- [Source Acquisition Implementation Sequencing Checklist](source-acquisition-implementation-sequencing-checklist.md)
- [Source Acquisition Implementation Readiness Boundary](source-acquisition-implementation-readiness-boundary.md)
- [Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md)
- [Local Source Manifest Boundary](local-source-manifest-boundary.md)
- [Source Manifest Adapter Handoff Boundary](source-manifest-adapter-handoff-boundary.md)
