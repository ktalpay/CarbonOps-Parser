# Artificial Source Acquisition Module Recap

This document recaps the artificial-only source acquisition module added across CO-068A through CO-072A.

It is documentation-only. It adds no implementation, tests, fixtures, runtime behavior, real source data, real source URLs, file reading, remote access, DB/cache/persistence behavior, scheduler/retry/cancel behavior, config/credential loading, parser runtime behavior, normalization runtime behavior, unit conversion, factor correctness logic, compliance/legal interpretation, carbon accounting correctness, or readiness for production use.

## Purpose

The artificial source acquisition module provides a small, deterministic source acquisition metadata and validation shape for boundary-safe examples and tests.

The module is intentionally limited to in-memory artificial metadata. It helps reviewers see how metadata construction, validation issue shapes, validation results, summaries, and a simple validation pipeline fit together before any real source acquisition work is scoped.

## Public API Summary

The current public API includes:

- `ArtificialSourceAcquisitionMetadata`: immutable artificial metadata shape for source family, logical source label, declared content type, deterministic artificial checksum, static acquisition label, and optional non-authoritative hints.
- `create_artificial_source_acquisition_metadata(...)`: factory for artificial metadata that enforces shape-only field validation.
- `SourceAcquisitionValidationIssue`: artificial validation issue shape with code, message, category, severity, and optional field name.
- `SourceAcquisitionValidationResult`: artificial validation result shape that stores issues and exposes an `is_valid` flag.
- `create_source_acquisition_validation_issue(...)`: factory for artificial validation issues.
- `create_source_acquisition_validation_result(...)`: factory for artificial validation results with tuple-normalized issues.
- `validate_artificial_source_acquisition_metadata(...)`: shape-only validation helper for artificial metadata.
- `SourceAcquisitionValidationSummary`: deterministic validation summary shape for issue totals and grouped counts.
- `summarize_source_acquisition_validation_result(...)`: helper that summarizes an existing validation result without running validation.
- `ArtificialSourceAcquisitionValidationPipelineResult`: composition result containing a validation result and summary.
- `validate_and_summarize_artificial_source_acquisition_metadata(...)`: helper that composes metadata validation and validation result summarization.

These names are exported from the package root where the source acquisition public API pattern requires it. They do not imply real source coverage, source authority, parser correctness, normalization correctness, unit conversion correctness, factor correctness, compliance/legal correctness, carbon accounting correctness, or readiness for production use.

## File Map

The artificial source acquisition module currently spans:

- `src/carbonfactor_parser/source_acquisition.py`: artificial metadata, validation issue/result, summary, and pipeline shapes and helpers.
- `src/carbonfactor_parser/__init__.py`: root package public API exports for source acquisition symbols.
- `tests/test_source_acquisition_metadata.py`: artificial metadata model and factory tests.
- `tests/test_source_acquisition_validation_result.py`: validation issue/result shape and factory tests.
- `tests/test_source_acquisition_metadata_validation.py`: shape-only metadata validation helper tests.
- `tests/test_source_acquisition_validation_summary.py`: validation summary shape and helper tests.
- `tests/test_source_acquisition_validation_pipeline.py`: validation pipeline composition tests.
- `tests/test_source_acquisition_public_api.py`: root public API export tests.
- `examples/example_artificial_source_acquisition_validation_pipeline.py`: in-memory artificial pipeline usage example.
- `docs/artificial-source-acquisition-validation-pipeline.md`: pipeline documentation and boundary notes.

## Scope Boundaries

The module scope is limited to:

- Artificial metadata only.
- In-memory usage only.
- Shape-only validation.
- Deterministic validation summaries.
- Non-authoritative parser hints.
- Non-authoritative adapter hints.
- Deterministic artificial values in examples and tests.

The module may check that artificial metadata fields have the expected shape. It must not be treated as proof that a source exists, that source metadata is official, that a file is readable, that a checksum was computed from a file, that a parser can interpret source content, that normalization is correct, that factors are correct, that compliance/legal interpretation is correct, that carbon accounting interpretation is correct, or that the repository is ready for production use.

## Explicitly Out Of Scope

The module does not add, perform, prove, or imply:

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

Any future task that touches these areas requires explicit scope, tests, and review gates.

## Relationship To Existing Documents

[Artificial Source Acquisition Validation Pipeline](artificial-source-acquisition-validation-pipeline.md) documents the pipeline helper and example added after the base metadata, validation, and summary shapes.

[Source Acquisition Implementation Sequencing Checklist](source-acquisition-implementation-sequencing-checklist.md) defines the safe implementation order that led to artificial model shape, validation shape, summary shape, pipeline shape, and artificial examples.

[Source Acquisition Implementation Readiness Boundary](source-acquisition-implementation-readiness-boundary.md) defines when source acquisition implementation tasks may be opened. This module stays within artificial, shape-only readiness.

[Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md) consolidates safety checks for source acquisition work. Future module changes should continue to pass through those checks.

[Source Acquisition Validation Boundary](source-acquisition-validation-boundary.md) defines what validation may check without implying real source correctness. This module applies that boundary to artificial metadata shape only.

[Source Acquisition Error Taxonomy Boundary](source-acquisition-error-taxonomy-boundary.md) defines safe error category and code naming concepts. This module uses deterministic artificial-safe issue shapes.

[Source Acquisition Boundary](source-acquisition-boundary.md) separates acquisition concepts from adapter execution, parser execution, normalization execution, persistence, scheduling/retry, and credentials/secrets handling. This module stays inside the artificial source acquisition metadata boundary.

## Review Checklist

Future artificial source acquisition module changes should confirm:

- The task scope is explicit, narrow, and reviewable.
- Documentation-only tasks remain documentation-only.
- Implementation tasks remain artificial-only unless separately scoped.
- Public API additions are intentional and covered by focused tests.
- Metadata remains in-memory and deterministic.
- Validation remains shape-only.
- Summaries count existing validation issues only.
- Pipeline helpers compose existing helpers instead of hiding new runtime behavior.
- Parser and adapter hints remain non-authoritative.
- No real source data or real source URLs are introduced.
- No file reading, path checks, directory scanning, or file hash computation is introduced.
- No remote access or download behavior is introduced.
- No DB/cache/persistence behavior is introduced.
- No scheduler/retry/cancel behavior is introduced.
- No config/credential loading is introduced.
- No parser, normalization, unit conversion, or factor correctness behavior is introduced.
- No compliance/legal correctness, carbon accounting correctness, or readiness for production use claim is introduced.

## Non-Goals

This recap does not add, implement, prove, or claim:

- New source acquisition behavior.
- New validation behavior.
- New summary behavior.
- New pipeline behavior.
- New tests.
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

- [Artificial Source Acquisition Validation Pipeline](artificial-source-acquisition-validation-pipeline.md)
- [Source Acquisition Boundary](source-acquisition-boundary.md)
- [Source Acquisition Implementation Sequencing Checklist](source-acquisition-implementation-sequencing-checklist.md)
- [Source Acquisition Implementation Readiness Boundary](source-acquisition-implementation-readiness-boundary.md)
- [Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md)
- [Source Acquisition Validation Boundary](source-acquisition-validation-boundary.md)
- [Source Acquisition Error Taxonomy Boundary](source-acquisition-error-taxonomy-boundary.md)
