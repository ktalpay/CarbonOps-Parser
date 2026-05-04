# Artificial Source Acquisition Validation Pipeline

This document explains the artificial-only source acquisition validation pipeline added across CO-068A through CO-071B.

It is documentation-only. It adds no implementation, tests, fixtures, runtime behavior, real source data, real source URLs, file reading, remote access, DB/cache/persistence behavior, scheduler/retry/cancel behavior, config/credential loading, parser runtime behavior, normalization runtime behavior, unit conversion, factor correctness logic, compliance/legal interpretation, carbon accounting correctness, or readiness for production use.

## Purpose

The artificial source acquisition validation pipeline gives contributors a small, deterministic way to exercise source acquisition metadata shape checks in memory.

The pipeline exists to compose already-scoped artificial helpers:

- Create artificial metadata.
- Validate metadata shape.
- Summarize validation issues.
- Return both the validation result and summary together.

It is intended for boundary-safe examples and tests only. It does not acquire sources, read files, inspect paths, compute file hashes, download content, persist metadata, schedule work, retry work, cancel work, load configuration, load credentials, run parsers, run normalization, convert units, prove factor correctness, prove compliance/legal correctness, prove carbon accounting correctness, or establish readiness for production use.

## Scope

The pipeline scope is limited to:

- Artificial metadata only.
- In-memory usage only.
- Shape-only validation.
- Deterministic validation issue summaries.
- Non-authoritative parser hints.
- Non-authoritative adapter hints.
- Artificial static labels and deterministic artificial checksum strings.

The pipeline may confirm that artificial metadata fields have the expected shape. It must not be treated as proof that a source exists, a source is official, a file is readable, a checksum was computed from a file, a parser can interpret source content, normalization is correct, factors are correct, compliance/legal interpretation is correct, carbon accounting interpretation is correct, or the repository is ready for production use.

## Components

The pipeline is built from these public source acquisition shapes and helpers:

- `ArtificialSourceAcquisitionMetadata`: artificial metadata shape for source family, logical source name, declared content type, deterministic artificial checksum, static acquisition label, and optional non-authoritative hints.
- `create_artificial_source_acquisition_metadata(...)`: factory that creates artificial metadata after shape validation.
- `validate_artificial_source_acquisition_metadata(...)`: shape-only validation helper for artificial metadata.
- `SourceAcquisitionValidationIssue`: artificial validation issue shape.
- `SourceAcquisitionValidationResult`: validation result shape with issue storage and an `is_valid` flag.
- `SourceAcquisitionValidationSummary`: deterministic summary shape for issue counts.
- `summarize_source_acquisition_validation_result(...)`: summary helper for an existing validation result.
- `ArtificialSourceAcquisitionValidationPipelineResult`: composition result containing the validation result and summary.
- `validate_and_summarize_artificial_source_acquisition_metadata(...)`: composition helper that validates artificial metadata and summarizes the resulting issues.

The pipeline helper should stay a composition layer. Future changes should avoid duplicating validation rules inside the pipeline unless a separate narrow task explicitly changes the validation contract.

## Example Reference

`examples/example_artificial_source_acquisition_validation_pipeline.py` demonstrates the pipeline with in-memory artificial metadata and deterministic static values.

The example returns plain Python data for review and tests. It does not read files, scan directories, compute hashes from files, access remote locations, use real source URLs, use DB/cache/persistence behavior, use scheduler/retry/cancel behavior, load config/credentials, run parser behavior, run normalization behavior, convert units, or apply factor correctness logic.

## What This Pipeline Does Not Do

This pipeline does not add, perform, prove, or imply:

- Real source acquisition.
- File reading.
- Filesystem path validation.
- Hash computation from files.
- Remote downloads.
- Real source URL validation.
- DB/cache/persistence behavior.
- Scheduler/retry/cancel behavior.
- Config/credential loading.
- Parser runtime behavior.
- Normalization runtime behavior.
- Source adapter runtime behavior.
- Unit conversion.
- Factor correctness.
- Compliance/legal correctness.
- Carbon accounting correctness.
- Readiness for production use.

Any future task that needs one of these areas requires explicit scope, tests, and review gates.

## Review Checklist

Future pipeline changes should confirm:

- The task scope is explicit and narrow.
- Documentation-only tasks remain documentation-only.
- Implementation tasks remain artificial-only unless separately scoped.
- The pipeline composes existing helpers instead of hiding new runtime behavior.
- Artificial metadata remains in-memory and deterministic.
- Parser and adapter hints remain non-authoritative.
- No real source data or real source URLs are introduced.
- No file reading, path checks, directory scanning, or file hash computation is introduced.
- No remote access or download behavior is introduced.
- No DB/cache/persistence behavior is introduced.
- No scheduler/retry/cancel behavior is introduced.
- No config/credential loading is introduced.
- No parser, normalization, unit conversion, or factor correctness behavior is introduced.
- No compliance/legal correctness, carbon accounting correctness, or readiness for production use claim is introduced.
- Tests remain focused on artificial shape behavior when implementation changes are explicitly scoped.

## Relationship To Existing Boundaries

[Source Acquisition Implementation Sequencing Checklist](source-acquisition-implementation-sequencing-checklist.md) describes the safe order for implementation tasks after the boundary/readiness documentation phase. This pipeline sits within the artificial model-shape, validation-shape, summary-shape, and example-only portions of that sequence.

[Source Acquisition Implementation Readiness Boundary](source-acquisition-implementation-readiness-boundary.md) defines when future implementation tasks may be opened. This pipeline remains within artificial, in-memory, shape-only readiness.

[Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md) consolidates safety checks for source acquisition tasks. Future pipeline changes should pass through those checks.

[Source Acquisition Validation Boundary](source-acquisition-validation-boundary.md) defines what validation may check without implying real source correctness. The pipeline uses that validation boundary only for artificial metadata shape.

[Source Acquisition Error Taxonomy Boundary](source-acquisition-error-taxonomy-boundary.md) defines safe error naming concepts. Pipeline validation issues should remain deterministic and artificial-safe.

[Source Manifest Adapter Handoff Boundary](source-manifest-adapter-handoff-boundary.md) explains that handoff hints are non-authoritative. Pipeline parser and adapter hints follow the same rule.

[Local Source Manifest Boundary](local-source-manifest-boundary.md) separates artificial metadata concepts from real-world manifest behavior. The pipeline does not implement manifest behavior.

[Source Acquisition Boundary](source-acquisition-boundary.md) separates source acquisition from adapter execution, parser execution, normalization execution, persistence, scheduling/retry, and credentials/secrets handling. The pipeline stays inside the artificial source acquisition metadata boundary.

## Non-Goals

This document does not add, implement, prove, or claim:

- New source acquisition behavior.
- New validation behavior.
- New validation tests.
- Fixtures.
- Example code.
- Real source data.
- Real source URLs.
- File reading.
- Filesystem path validation.
- Directory scanning.
- Hash computation from files.
- Remote access.
- Remote downloads.
- DB/cache/persistence behavior.
- Scheduler behavior.
- Retry/cancel behavior.
- Config loading.
- Credential loading.
- Parser runtime behavior.
- Normalization runtime behavior.
- Source adapter runtime behavior.
- Unit conversion.
- Unit conversion correctness.
- Factor correctness.
- Compliance/legal interpretation.
- Carbon accounting correctness.
- Deployment behavior.
- Readiness for production use.

## Related Documents

- [Source Acquisition Boundary](source-acquisition-boundary.md)
- [Source Acquisition Implementation Sequencing Checklist](source-acquisition-implementation-sequencing-checklist.md)
- [Source Acquisition Implementation Readiness Boundary](source-acquisition-implementation-readiness-boundary.md)
- [Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md)
- [Source Acquisition Validation Boundary](source-acquisition-validation-boundary.md)
- [Source Acquisition Error Taxonomy Boundary](source-acquisition-error-taxonomy-boundary.md)
- [Source Manifest Adapter Handoff Boundary](source-manifest-adapter-handoff-boundary.md)
- [Local Source Manifest Boundary](local-source-manifest-boundary.md)
