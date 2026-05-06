# Artificial Manifest Metadata Boundaries

This document describes the artificial-only boundary for `ArtificialSourceManifestMetadata` after CO-076A and CO-076B.

It is documentation-only. It adds no code, tests, fixtures, runtime behavior, real source data, real source URLs, file reading, remote access, DB/cache/persistence behavior, scheduler/retry/cancel behavior, config/credential loading, parser runtime behavior, normalization runtime behavior, source adapter dispatch behavior, unit conversion, factor correctness logic, compliance/legal interpretation, carbon accounting correctness, or readiness for production use.

## Purpose

`ArtificialSourceManifestMetadata` is a small model for describing artificial manifest metadata in memory.

It exists so future artificial manifest tasks can refer to a stable shape for manifest identity, source-family labeling, dataset labeling, version labeling, record counts, optional generator labels, and optional notes. It does not represent real source acquisition, source authority, source availability, parser behavior, normalization behavior, persistence, scheduling, unit conversion, factor correctness, compliance/legal interpretation, carbon accounting interpretation, or readiness for production use.

## Field Meaning

The current fields are conceptual and artificial-only:

- `manifest_id`: A deterministic artificial manifest identifier.
- `source_family`: A source-family label for artificial grouping only.
- `dataset_name`: A deterministic artificial dataset label, not a file path and not a real dataset claim.
- `version_label`: A static artificial version label.
- `record_count`: A non-negative count declared by the artificial manifest metadata.
- `generated_by`: An optional artificial label for the process or example that produced the metadata.
- `notes`: Optional artificial notes stored as a tuple of non-empty strings.

These fields are descriptive metadata only. They do not prove that a file exists, a source exists, a version exists, records were read, records were parsed, a checksum was computed, a dataset is official, or any source content is correct.

## Artificial-Only Usage Boundary

The model may be used for:

- Artificial in-memory examples.
- Boundary-safe tests.
- Shape-only manifest metadata exercises.
- Deterministic labels and counts.
- Future artificial manifest validation tasks when explicitly scoped.

The model must not be used as hidden runtime behavior. It must not read files, validate paths, discover directories, access remote locations, download source documents, persist manifests, schedule work, retry work, cancel work, load config, load credentials, dispatch adapters, run parsers, run normalization, convert units, or verify factors.

## Package Root Example

The model is exported from the package root for artificial-only usage:

```python
from carbonfactor_parser import ArtificialSourceManifestMetadata

manifest_metadata = ArtificialSourceManifestMetadata(
    manifest_id="artificial-manifest-001",
    source_family="artificial_source_family",
    dataset_name="artificial-dataset",
    version_label="static-version-label",
    record_count=2,
    generated_by="artificial-manifest-example",
    notes=("artificial-note-a", "artificial-note-b"),
)
```

This example is in-memory only. It does not read a file, reference a real source, access a remote location, use config, use credentials, persist data, run a scheduler, dispatch an adapter, run a parser, run normalization, convert units, or check factor correctness.

## Explicit Non-Goals

`ArtificialSourceManifestMetadata` is not:

- A real source manifest loader.
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

## Relationship To Source Acquisition Documents

[Artificial Source Acquisition Phase Closure](artificial-source-acquisition-phase-closure.md) closed the prior artificial source acquisition phase and named artificial manifest metadata as a safe next shape phase.

[Source Acquisition Implementation Sequencing Checklist](source-acquisition-implementation-sequencing-checklist.md) places artificial manifest metadata shape after artificial source acquisition metadata shape.

[Source Acquisition Implementation Readiness Boundary](source-acquisition-implementation-readiness-boundary.md) defines prerequisites before future implementation tasks add behavior.

[Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md) defines review checks that should continue to apply to manifest-related tasks.

[Source Acquisition Boundary](source-acquisition-boundary.md) separates acquisition concepts from adapter execution, parser execution, normalization execution, persistence, scheduling/retry, and credentials/secrets handling.

## Relationship To Manifest And Handoff Documents

[Local Source Manifest Boundary](local-source-manifest-boundary.md) describes what future local source manifests may represent and what they must not imply.

[Local Source Manifest Examples Boundary](local-source-manifest-examples-boundary.md) limits future manifest examples to artificial metadata and non-authoritative handoff hints.

[Source Manifest Adapter Handoff Boundary](source-manifest-adapter-handoff-boundary.md) describes the boundary between manifest metadata and adapter-facing handoff.

`ArtificialSourceManifestMetadata` does not implement adapter handoff, parser handoff, normalization handoff, manifest persistence, cache behavior, checksum enforcement, or runtime acquisition behavior.

## Review Checklist

Future artificial manifest metadata changes should confirm:

- The task scope is explicit and narrow.
- Documentation-only tasks remain documentation-only.
- Model changes remain artificial-only unless separately scoped.
- Examples use in-memory artificial labels only.
- No real source data or real source URLs are introduced.
- No file reading, path validation, or directory scanning is introduced.
- No remote access or download behavior is introduced.
- No DB/cache/persistence behavior is introduced.
- No scheduler/retry/cancel behavior is introduced.
- No config/credential loading is introduced.
- No parser, normalization, source adapter dispatch, unit conversion, or factor correctness behavior is introduced.
- No compliance/legal correctness, carbon accounting correctness, or readiness for production use claim is introduced.

## Related Documents

- [Artificial Source Acquisition Phase Closure](artificial-source-acquisition-phase-closure.md)
- [Source Acquisition Boundary](source-acquisition-boundary.md)
- [Source Acquisition Implementation Sequencing Checklist](source-acquisition-implementation-sequencing-checklist.md)
- [Source Acquisition Implementation Readiness Boundary](source-acquisition-implementation-readiness-boundary.md)
- [Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md)
- [Local Source Manifest Boundary](local-source-manifest-boundary.md)
- [Local Source Manifest Examples Boundary](local-source-manifest-examples-boundary.md)
- [Source Manifest Adapter Handoff Boundary](source-manifest-adapter-handoff-boundary.md)
