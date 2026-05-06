# Artificial Manifest Metadata Collection

This document describes the artificial-only boundary for `ArtificialSourceManifestMetadataCollection` after CO-078A.

It is documentation-only. It adds no code, tests, fixtures, runtime behavior, real source data, real source URLs, file reading, remote access, DB/cache/persistence behavior, scheduler/retry/cancel behavior, config/credential loading, parser runtime behavior, normalization runtime behavior, source adapter dispatch behavior, registry/selection behavior, unit conversion, factor correctness logic, compliance/legal interpretation, carbon accounting correctness, or readiness for production use.

## Purpose

`ArtificialSourceManifestMetadataCollection` groups `ArtificialSourceManifestMetadata` records for artificial in-memory examples and boundary-safe tests.

The collection is intentionally small. It provides a stable container shape plus simple summary properties. It does not load manifests, discover manifests, select manifests, read files, access remote locations, persist data, schedule work, dispatch adapters, run parsers, run normalization, convert units, verify factors, interpret compliance/legal meaning, or establish carbon accounting correctness.

## Relationship To ArtificialSourceManifestMetadata

`ArtificialSourceManifestMetadataCollection` contains `ArtificialSourceManifestMetadata` values.

Each contained metadata record remains responsible for its own artificial manifest identity fields:

- `manifest_id`
- `source_family`
- `dataset_name`
- `version_label`
- `record_count`
- `generated_by`
- `notes`

The collection does not reinterpret those fields and does not expand them into real source identity, source authority, filesystem location, remote location, parser routing, normalization routing, persistence identity, scheduler identity, unit conversion semantics, or factor correctness.

## Artificial-Only In-Memory Usage Boundary

The collection may be used for:

- Artificial in-memory examples.
- Boundary-safe tests.
- Grouping already-created artificial manifest metadata records.
- Deterministic summaries over artificial metadata labels.
- Future artificial manifest validation tasks when explicitly scoped.

The collection must not be used to hide runtime behavior. It must not read files, scan directories, load manifests, fetch remote resources, validate real source URLs, persist data, cache data, schedule work, retry work, cancel work, load config, load credentials, dispatch source adapters, run parsers, run normalization, convert units, or verify factors.

## Tuple Normalization

The collection stores `manifests` as a tuple.

Callers may provide an iterable, such as a list, but the collection normalizes the value to a tuple. This keeps the shape deterministic and avoids retaining a caller-owned mutable list.

Tuple normalization is container-shape behavior only. It does not load data, validate file paths, inspect files, compute hashes, discover directories, access remote locations, or perform source acquisition.

## Summary Properties

The collection exposes these small summary properties:

- `count`: the number of artificial manifest metadata records in the collection.
- `manifest_ids`: the contained `manifest_id` values in collection order.
- `source_families`: the unique contained `source_family` values in deterministic sorted order.

These properties summarize existing in-memory metadata only. They are not registry lookup, selection, filtering, adapter routing, parser routing, normalization routing, persistence lookup, source discovery, or source correctness behavior.

## Duplicate manifest_id Handling

The collection rejects duplicate `manifest_id` values.

This is a narrow shape invariant for artificial in-memory metadata collections. It does not imply a global registry, persistence uniqueness constraint, real source catalog, source URL catalog, filesystem uniqueness check, remote availability check, or official source correctness check.

## Package-Root Import Example

Use the package-root imports for artificial in-memory metadata collection examples:

```python
from carbonfactor_parser import (
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

assert collection.count == 1
assert collection.manifest_ids == ("artificial-manifest-001",)
```

This example is artificial and in-memory only. It does not read a file, reference a real source, access a remote location, use config, use credentials, persist data, run a scheduler, dispatch an adapter, run a parser, run normalization, convert units, or check factor correctness.

## Explicit Non-Goals

`ArtificialSourceManifestMetadataCollection` is not:

- A manifest registry.
- A manifest selector.
- A manifest loader.
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

## Relationship To Manifest Metadata Boundaries

[Artificial Manifest Metadata Boundaries](artificial-manifest-metadata-boundaries.md) documents the artificial-only boundary for `ArtificialSourceManifestMetadata`.

`ArtificialSourceManifestMetadataCollection` sits on top of that metadata shape as an in-memory container only. It does not expand the metadata model into loading, acquisition, adapter handoff, parser handoff, normalization handoff, persistence, cache behavior, scheduling, retry/cancel behavior, config/credential loading, unit conversion, factor correctness, or compliance/legal interpretation.

## Relationship To Manifest Validation Summary

[Artificial Manifest Validation Summary](artificial-manifest-validation-summary.md) documents `ArtificialSourceManifestValidationSummary`.

The collection may be useful before future artificial validation summary tasks, but it does not produce validation summaries by itself. It does not validate real source correctness, official source status, parser correctness, normalization correctness, factor correctness, compliance/legal correctness, carbon accounting correctness, or readiness for production use.

## Review Checklist

Future artificial manifest metadata collection changes should confirm:

- The task scope is explicit and narrow.
- Documentation-only tasks remain documentation-only.
- Collection changes remain artificial-only unless separately scoped.
- Examples use in-memory artificial labels only.
- Tuple normalization remains container-shape behavior only.
- Duplicate `manifest_id` handling remains a local shape invariant only.
- No registry, selection, loading, lookup, or runtime dispatch behavior is introduced.
- No real source data or real source URLs are introduced.
- No file reading, path validation, or directory scanning is introduced.
- No remote access or download behavior is introduced.
- No DB/cache/persistence behavior is introduced.
- No scheduler/retry/cancel behavior is introduced.
- No config/credential loading is introduced.
- No parser, normalization, source adapter dispatch, unit conversion, or factor correctness behavior is introduced.
- No compliance/legal correctness, carbon accounting correctness, or readiness for production use claim is introduced.

## Related Documents

- [Artificial Manifest Metadata Boundaries](artificial-manifest-metadata-boundaries.md)
- [Artificial Manifest Validation Summary](artificial-manifest-validation-summary.md)
- [Artificial Source Acquisition Phase Closure](artificial-source-acquisition-phase-closure.md)
- [Source Acquisition Boundary](source-acquisition-boundary.md)
- [Source Acquisition Implementation Sequencing Checklist](source-acquisition-implementation-sequencing-checklist.md)
- [Source Acquisition Implementation Readiness Boundary](source-acquisition-implementation-readiness-boundary.md)
- [Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md)
- [Local Source Manifest Boundary](local-source-manifest-boundary.md)
- [Source Manifest Adapter Handoff Boundary](source-manifest-adapter-handoff-boundary.md)
