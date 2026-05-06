# Artificial In-Memory Manifest Usage Example

This document describes the artificial-only in-memory manifest usage example added in CO-081B.

It is documentation-only. It adds no code, tests, fixtures, runtime behavior, real source data, real source URLs, file reading, remote access, DB/cache/persistence behavior, scheduler/retry/cancel behavior, config/credential loading, parser runtime behavior, normalization runtime behavior, source adapter dispatch behavior, manifest loading, manifest registry behavior, manifest selection behavior, unit conversion, factor correctness logic, compliance/legal interpretation, carbon accounting correctness, or readiness for production use.

## Purpose

The example demonstrates how the existing artificial manifest metadata shapes can be used together with deterministic in-memory values.

It is intended to make the current public API easier to understand after the artificial manifest metadata phase recap and next-phase option matrix. It does not introduce new behavior beyond constructing artificial metadata records, grouping them in an in-memory collection, creating per-manifest validation summaries, and creating a collection-level validation summary.

## Example Location

The example module is:

- [examples/example_artificial_in_memory_manifest_usage.py](../examples/example_artificial_in_memory_manifest_usage.py)

The module exposes `build_artificial_manifest_usage_summary()`.

## Public API Types Demonstrated

The example uses these package-root public API types:

- `ArtificialSourceManifestMetadata`
- `ArtificialSourceManifestMetadataCollection`
- `ArtificialSourceManifestValidationSummary`
- `ArtificialSourceManifestCollectionValidationSummary`

These types remain artificial-only. Their use in the example does not imply manifest loading, registry behavior, selection behavior, file reading, remote access, persistence/cache integration, scheduler behavior, parser/runtime integration, source adapter dispatch, unit conversion, factor correctness, compliance/legal correctness, carbon accounting correctness, or readiness for production use.

## What The Example Returns

`build_artificial_manifest_usage_summary()` returns deterministic plain summary data.

At a conceptual level, the returned dictionary includes:

- `collection_count`: the number of artificial manifest metadata records.
- `manifest_ids`: deterministic artificial manifest identifiers.
- `source_families`: deterministic artificial source family labels.
- `manifests`: artificial metadata values represented as plain dictionaries.
- `manifest_validation_summaries`: per-manifest validation summary values represented as plain dictionaries.
- `collection_validation_summary`: collection-level validation summary values represented as a plain dictionary.

The returned data is intended for tests and documentation clarity. It does not include real source names, URLs, file paths, credentials, config values, persistence identifiers, parser results, normalization results, unit conversion output, factor correctness output, compliance/legal interpretation, carbon accounting interpretation, or production readiness signals.

## Artificial-Only In-Memory Boundary

The example is limited to:

- Static artificial manifest identifiers.
- Static artificial source family labels.
- Static artificial dataset labels.
- Static artificial version labels.
- In-memory metadata construction.
- In-memory collection construction.
- Per-manifest validation summaries with deterministic issue counts.
- Collection-level validation summary with a deterministic issue count.
- Deterministic plain output for focused tests.

The example must not be expanded into runtime behavior. Any future change that adds loader, registry, selector, file, URL, remote, persistence, scheduler, config, credential, parser, normalization, adapter, unit conversion, or factor correctness behavior requires a separate explicitly scoped task.

## Explicit Non-Goals

The example is not:

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
- A persistence/cache integration.
- A DB integration.
- A scheduler/retry/cancel model.
- A parser runtime integration.
- A normalization runtime integration.
- A source adapter dispatcher.
- A checksum enforcement mechanism.
- A unit conversion contract.
- A factor correctness contract.
- A compliance/legal correctness contract.
- A carbon accounting correctness contract.
- A production readiness claim.

## Relationship To The Option Matrix

[Artificial Manifest Next Phase Option Matrix](artificial-manifest-next-phase-option-matrix.md) recommended an artificial in-memory manifest usage example as the lowest-risk next step.

This example follows that recommendation by demonstrating the existing artificial manifest shapes without implementing loader, registry, selector, real source, file/URL/remote, parser/adapter/runtime integration, persistence/cache, unit conversion, or factor correctness behavior.

## Review Checklist

Future changes to the artificial in-memory manifest usage example should confirm:

- The example stays artificial-only and in-memory.
- Returned values remain deterministic.
- No real source data or real source URLs are introduced.
- No file paths, file reading, path validation, or directory scanning are introduced.
- No remote access or download behavior is introduced.
- No DB/cache/persistence behavior is introduced.
- No scheduler/retry/cancel behavior is introduced.
- No config/credential loading is introduced.
- No manifest loading, registry behavior, or selection behavior is introduced.
- No parser runtime behavior, normalization runtime behavior, or source adapter dispatch is introduced.
- No unit conversion or factor correctness behavior is introduced.
- No compliance/legal correctness, carbon accounting correctness, or readiness for production use claim is introduced.

## Related Documents

- [Artificial Manifest Next Phase Option Matrix](artificial-manifest-next-phase-option-matrix.md)
- [Artificial Manifest Metadata Phase Recap](artificial-manifest-metadata-phase-recap.md)
- [Artificial Manifest Metadata Boundaries](artificial-manifest-metadata-boundaries.md)
- [Artificial Manifest Validation Summary](artificial-manifest-validation-summary.md)
- [Artificial Manifest Metadata Collection](artificial-manifest-metadata-collection.md)
- [Artificial Manifest Collection Validation Summary](artificial-manifest-collection-validation-summary.md)
- [Source Acquisition Implementation Sequencing Checklist](source-acquisition-implementation-sequencing-checklist.md)
- [Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md)
