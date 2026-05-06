# Artificial Manifest Next Phase Option Matrix

This document compares possible next directions after the artificial manifest metadata phase recap.

It is documentation-only. It adds no code, tests, fixtures, runtime behavior, real source data, real source URLs, file reading, remote access, DB/cache/persistence behavior, scheduler/retry/cancel behavior, config/credential loading, parser runtime behavior, normalization runtime behavior, source adapter dispatch behavior, manifest loading, manifest registry implementation, manifest selection implementation, unit conversion, factor correctness logic, compliance/legal interpretation, carbon accounting correctness, or readiness for production use.

## Purpose

The artificial manifest metadata phase now has stable in-memory model and summary shapes. The next phase needs an explicit option matrix because manifest-related work can easily combine too many concerns at once.

Loader, registry, selector, real source, file, URL, remote, parser, adapter, persistence, unit conversion, and factor correctness concerns must stay separated. Future work must choose one boundary per task so each change remains small, reviewable, and safe for the public repository.

## Current Baseline

The current artificial manifest metadata surface includes:

- `ArtificialSourceManifestMetadata`
- `ArtificialSourceManifestValidationSummary`
- `ArtificialSourceManifestMetadataCollection`
- `ArtificialSourceManifestCollectionValidationSummary`
- Boundary documentation for metadata, summaries, collections, and the phase recap.

This baseline is artificial-only and in-memory. It does not provide manifest loading, registry behavior, selection behavior, file reading, URL validation, remote access, persistence/cache behavior, scheduling, parser/runtime integration, source adapter dispatch, unit conversion, factor correctness, compliance/legal correctness, carbon accounting correctness, or readiness for production use.

## Option Matrix

| Option | Purpose | Expected Benefit | Scope Risk | Next Decision |
| --- | --- | --- | --- | --- |
| Artificial in-memory usage example | Demonstrate existing artificial manifest shapes together with static labels. | Low-risk usage clarity without new runtime behavior. | Low. | Recommended next. |
| Artificial manifest registry shape | Define an in-memory container or registry-like shape for artificial manifests. | Could prepare later lookup concepts. | Medium because registry wording can imply lookup, ownership, or persistence semantics. | Defer until a separate registry boundary is documented. |
| Artificial manifest selector shape | Define a shape for choosing among artificial manifest metadata records. | Could prepare later selection examples. | Medium/high because selector wording can imply filtering, routing, source choice, or runtime decision behavior. | Defer until registry and selection boundaries are separately documented. |
| Artificial manifest loader boundary documentation | Define what a future loader may and may not do. | Clarifies loader constraints before any implementation. | High because loader topics invite file reading, parsing, remote, and config behavior. | Useful later, but not the immediate next implementation step. |
| Real source manifest direction | Move from artificial metadata toward real manifest/source handling. | Eventually required for real-world workflows. | Very high because it touches real source data, URLs, file handling, remote behavior, correctness claims, and runtime integration. | Deferred. |

## Option Details

### Artificial In-Memory Usage Example

Purpose: show how the existing artificial manifest metadata shapes can be used together with deterministic in-memory values.

Expected benefit: helps readers understand the current public API without expanding behavior. It can use existing constructors and summary helpers while avoiding file paths, URLs, remote access, parser calls, adapter dispatch, persistence, config loading, unit conversion, and factor correctness.

Scope risk: low. The example can stay fully artificial and deterministic.

Why it should be next: it is the smallest useful follow-up after the phase recap. It validates that the current shapes are understandable without opening loader, registry, selector, or runtime concerns.

## Registry Shape Option

Purpose: define a future in-memory registry shape for artificial manifests.

Expected benefit: could provide a clearer place for later lookup-like concepts.

Scope risk: medium. Registry language can imply ownership, lookup guarantees, persistence, cache behavior, uniqueness guarantees beyond local shape checks, or production catalog behavior.

Why it should not be next: a registry should have its own boundary document before any shape is added. It should not be combined with loader, selector, parser, adapter, persistence, or real source behavior.

## Selector Shape Option

Purpose: define a future shape for selecting among artificial manifest metadata records.

Expected benefit: could help future artificial examples discuss a selected manifest without running parser or adapter behavior.

Scope risk: medium/high. Selector language can imply routing, filtering, source choice, adapter dispatch, parser handoff, or runtime decisions.

Why it should not be next: selection should wait until registry and selector boundaries are documented separately. A selector task must not also introduce loading, remote behavior, persistence, parser integration, adapter dispatch, unit conversion, or factor correctness.

## Loader Boundary Option

Purpose: document what a future artificial manifest loader may and may not do.

Expected benefit: useful before any loader implementation is considered.

Scope risk: high. Loader language can quickly pull in file reading, path validation, manifest parsing, config loading, remote access, cache behavior, and error handling.

Why it should not be next: the safer immediate step is to demonstrate existing in-memory shapes. Loader work should begin with a boundary-only task when explicitly selected.

## Real Source Manifest Option

Purpose: move toward real source manifest design.

Expected benefit: eventual support for real workflows would need carefully scoped real source decisions.

Scope risk: very high. This direction can involve real source data, source URLs, remote access, file reading, persistence, credentials, compliance/legal interpretation, carbon accounting correctness expectations, parser/runtime behavior, source adapter dispatch, unit conversion, and factor correctness.

Why it should not be next: it is explicitly deferred. Real source manifest work requires later explicit scope, tests, public safety review, and narrow review gates.

## Risk Ranking

- Low: artificial in-memory usage example.
- Medium: artificial manifest registry shape.
- Medium/high: artificial manifest selector shape.
- High: artificial manifest loader boundary documentation.
- Very high / deferred: real source manifest direction.

## Recommended Next Step

The recommended next step is an artificial in-memory manifest usage example.

That task should:

- Use only existing artificial manifest metadata and summary shapes.
- Use static artificial labels only.
- Avoid real source data and real source URLs.
- Avoid file paths, file reading, and directory scanning.
- Avoid remote access and downloads.
- Avoid DB/cache/persistence behavior.
- Avoid scheduler/retry/cancel behavior.
- Avoid config/credential loading.
- Avoid manifest loading, registry implementation, and selection implementation.
- Avoid parser runtime behavior, normalization runtime behavior, and source adapter dispatch.
- Avoid unit conversion and factor correctness logic.
- Avoid compliance/legal correctness, carbon accounting correctness, and readiness for production use claims.

## Deferred Areas

The following remain deferred until separately scoped:

- Manifest loading.
- Manifest registry implementation.
- Manifest selection implementation.
- Real source manifest design.
- Real source data handling.
- Real source URLs.
- File reading.
- Filesystem path validation.
- Directory scanning.
- Remote access.
- Remote downloads.
- DB/cache/persistence behavior.
- Scheduler/retry/cancel behavior.
- Config/credential loading.
- Parser/runtime integration.
- Normalization/runtime integration.
- Source adapter dispatch.
- Unit conversion.
- Factor correctness.
- Compliance/legal correctness.
- Carbon accounting correctness.
- Readiness for production use.

## Future Sequencing Rule

Future work must choose one boundary per task.

For example, a loader boundary task should not also add registry behavior. A registry task should not also add selection behavior. A selector task should not also dispatch adapters or parsers. A real source task should not be combined with file reading, remote access, persistence, compliance/legal interpretation, carbon accounting interpretation, unit conversion, or factor correctness unless a later task explicitly scopes and reviews that exact behavior.

## Review Checklist

Future next-phase tasks should confirm:

- The selected option is named clearly.
- The task covers one boundary only.
- The expected benefit is documented.
- Scope risk is documented.
- Deferred areas are listed.
- Documentation-only tasks remain documentation-only.
- Artificial examples use in-memory labels only.
- No real source data or real source URLs are introduced.
- No file reading, path validation, directory scanning, remote access, persistence, scheduling, config loading, parser/runtime integration, adapter dispatch, unit conversion, or factor correctness behavior is introduced unless explicitly scoped.
- No compliance/legal correctness, carbon accounting correctness, or readiness for production use claim is introduced.

## Related Documents

- [Artificial Manifest Metadata Phase Recap](artificial-manifest-metadata-phase-recap.md)
- [Artificial Manifest Metadata Boundaries](artificial-manifest-metadata-boundaries.md)
- [Artificial Manifest Validation Summary](artificial-manifest-validation-summary.md)
- [Artificial Manifest Metadata Collection](artificial-manifest-metadata-collection.md)
- [Artificial Manifest Collection Validation Summary](artificial-manifest-collection-validation-summary.md)
- [Source Acquisition Implementation Sequencing Checklist](source-acquisition-implementation-sequencing-checklist.md)
- [Source Acquisition Implementation Readiness Boundary](source-acquisition-implementation-readiness-boundary.md)
- [Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md)
