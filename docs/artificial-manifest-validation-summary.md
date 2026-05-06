# Artificial Manifest Validation Summary

This document describes the artificial-only boundary for `ArtificialSourceManifestValidationSummary` after CO-077A.

It is documentation-only. It adds no code, tests, fixtures, runtime behavior, real source data, real source URLs, file reading, remote access, DB/cache/persistence behavior, scheduler/retry/cancel behavior, config/credential loading, parser runtime behavior, normalization runtime behavior, source adapter dispatch behavior, unit conversion, factor correctness logic, compliance/legal interpretation, carbon accounting correctness, or readiness for production use.

## Purpose

`ArtificialSourceManifestValidationSummary` represents the outcome shape for artificial manifest metadata validation.

It is intentionally small. It carries the artificial manifest identity fields needed for review and a deterministic issue count/validity flag. It does not load a manifest, inspect source content, read files, access remote locations, persist anything, schedule work, dispatch adapters, run parsers, run normalization, convert units, verify factors, interpret compliance/legal meaning, or establish carbon accounting correctness.

## Relationship To ArtificialSourceManifestMetadata

`ArtificialSourceManifestValidationSummary` is derived from `ArtificialSourceManifestMetadata` when using `from_metadata(...)`.

The summary copies these artificial identity fields:

- `manifest_id`
- `source_family`
- `dataset_name`

The summary then records:

- `issue_count`: the number of artificial validation issues already known to the caller.
- `is_valid`: a boolean derived from `issue_count` when using `from_metadata(...)`.

This relationship is metadata-only. It does not validate real source availability, source authority, file existence, file paths, checksums from files, parser behavior, normalization behavior, unit conversion, factor correctness, compliance/legal correctness, carbon accounting correctness, or readiness for production use.

## from_metadata Usage

Use `from_metadata(...)` when an artificial validation task already has an `ArtificialSourceManifestMetadata` value and a deterministic issue count:

```python
from carbonfactor_parser import (
    ArtificialSourceManifestMetadata,
    ArtificialSourceManifestValidationSummary,
)

metadata = ArtificialSourceManifestMetadata(
    manifest_id="artificial-manifest-001",
    source_family="artificial_source_family",
    dataset_name="artificial-dataset",
    version_label="static-version-label",
    record_count=2,
)

summary = ArtificialSourceManifestValidationSummary.from_metadata(
    metadata,
    issue_count=0,
)
```

This example is in-memory only. It does not read a file, reference a real source, access a remote location, use config, use credentials, persist data, run a scheduler, dispatch an adapter, run a parser, run normalization, convert units, or check factor correctness.

## issue_count Semantics

When using `from_metadata(...)`:

- `issue_count == 0` means `is_valid` is `True`.
- `issue_count > 0` means `is_valid` is `False`.
- Negative `issue_count` is invalid input.

These semantics only describe artificial validation outcome shape. They do not define a validation engine, issue taxonomy, source correctness check, manifest loader, parser contract, normalization contract, persistence contract, scheduler contract, or runtime workflow.

## Artificial-Only Usage Boundary

The summary may be used for:

- Artificial in-memory examples.
- Boundary-safe tests.
- Shape-only manifest validation result summaries.
- Deterministic identity fields and issue counts.
- Future artificial manifest validation tasks when explicitly scoped.

The summary must not be used to hide runtime behavior. It must not load manifests, read files, validate paths, discover directories, access remote locations, download source documents, persist manifests, schedule work, retry work, cancel work, load config, load credentials, dispatch adapters, run parsers, run normalization, convert units, or verify factors.

## Explicit Non-Goals

`ArtificialSourceManifestValidationSummary` is not:

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

This summary sits after that metadata shape. It represents validation outcome metadata only and does not expand the model into loading, acquisition, adapter handoff, parser handoff, normalization handoff, persistence, cache behavior, scheduling, retry/cancel behavior, config/credential loading, unit conversion, or factor correctness.

## Relationship To Source Acquisition Documents

[Artificial Source Acquisition Phase Closure](artificial-source-acquisition-phase-closure.md) closed the prior artificial source acquisition phase and named artificial manifest metadata as a safe next shape phase.

[Source Acquisition Implementation Sequencing Checklist](source-acquisition-implementation-sequencing-checklist.md) places artificial manifest metadata shape and validation shape before handoff or runtime behavior.

[Source Acquisition Implementation Readiness Boundary](source-acquisition-implementation-readiness-boundary.md) defines prerequisites before future implementation tasks add behavior.

[Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md) defines review checks that should continue to apply to manifest-related tasks.

[Source Acquisition Boundary](source-acquisition-boundary.md) separates acquisition concepts from adapter execution, parser execution, normalization execution, persistence, scheduling/retry, and credentials/secrets handling.

## Review Checklist

Future artificial manifest validation summary changes should confirm:

- The task scope is explicit and narrow.
- Documentation-only tasks remain documentation-only.
- Summary changes remain artificial-only unless separately scoped.
- Examples use in-memory artificial labels only.
- `issue_count` semantics remain deterministic.
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
- [Artificial Source Acquisition Phase Closure](artificial-source-acquisition-phase-closure.md)
- [Source Acquisition Boundary](source-acquisition-boundary.md)
- [Source Acquisition Implementation Sequencing Checklist](source-acquisition-implementation-sequencing-checklist.md)
- [Source Acquisition Implementation Readiness Boundary](source-acquisition-implementation-readiness-boundary.md)
- [Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md)
- [Local Source Manifest Boundary](local-source-manifest-boundary.md)
- [Source Manifest Adapter Handoff Boundary](source-manifest-adapter-handoff-boundary.md)
