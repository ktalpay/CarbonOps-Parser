# Local Source Manifest Examples Boundary

This document defines what future local source manifest examples may and may not demonstrate.

It is documentation-only. It adds no fixtures, example code, Python code, .NET code, manifest model, local file reading, source acquisition model code, source manifest code, real source data, real source URLs, remote behavior, credentials/secrets handling, config loading, DB/persistence/cache behavior, scheduler/retry/cancel behavior, deployment behavior, unit conversion, or factor correctness logic.

## Purpose

Future local source manifest examples may help reviewers understand artificial manifest metadata shapes before any manifest model or code exists.

Those examples should be limited to deterministic, in-repository, artificial metadata. They must not imply real source metadata coverage, official source cataloging, source adapter correctness for real external sources, parser correctness for real external sources, normalization correctness, unit conversion correctness, factor correctness, compliance/legal interpretation, carbon accounting interpretation, or readiness for production use.

## Allowed Future Example Scope

Future local source manifest examples may demonstrate:

- Artificial fixture metadata only.
- Deterministic logical fixture names.
- Source family labels.
- Declared content type or format labels.
- Deterministic checksum/hash values for artificial fixtures only.
- Parser handoff hints as non-authoritative metadata.
- Static example timestamps as illustrative fields only, without runtime clock behavior.

Allowed examples should be small, deterministic, local-only, and clearly marked as artificial. They may help explain shape, but they should not claim source correctness or runtime behavior.

## Disallowed Future Example Scope

Future local source manifest examples must not demonstrate:

- Real source metadata.
- Real source URLs.
- Official source cataloging.
- Arbitrary user file manifesting.
- Real directory scanning.
- Remote downloads.
- Credentials/secrets/config loading.
- DB/persistence/cache behavior.
- Scheduler/retry/cancel behavior.
- Checksum enforcement beyond artificial fixtures.
- Unit conversion or factor correctness.
- Compliance/legal interpretation.
- Carbon accounting interpretation.
- Production filesystem assumptions.
- Source adapter, parser, or normalization runtime behavior.

Any item in this section requires a separate future boundary and explicitly scoped implementation task before it can be considered.

## Artificial Manifest Examples Vs Future Real-World Manifest Design

Artificial manifest examples may use deterministic labels and metadata to explain expected review shape.

Future real-world manifest design would require separate work for source provenance, source location policy, source URL cataloging, acquisition behavior, cache behavior, checksum enforcement, credentials/secrets handling, config loading, DB/persistence behavior, scheduler/retry/cancel behavior, observability, and operational review.

This document only covers artificial local examples. It does not define future real-world manifest design or implementation.

## Relationship To Local Source Manifest Boundary

[Local Source Manifest Boundary](local-source-manifest-boundary.md) defines what a future local source manifest may represent and what it must not imply.

Future examples should follow that boundary by keeping artificial fixture metadata descriptive, deterministic, and non-authoritative. Examples must not add manifest model code, source manifest code, fixture files, file reading, persistence, remote behavior, or runtime behavior.

## Relationship To Local Source Acquisition Boundaries

[Local Source Acquisition Examples Boundary](local-source-acquisition-examples-boundary.md) limits local source acquisition examples to artificial, deterministic, in-repository inputs.

[Local Source Acquisition Contract Boundary](local-source-acquisition-contract-boundary.md) describes future local source acquisition contract concepts. Manifest examples may reference those concepts only as illustrative metadata and must not create contract/model code.

## Relationship To Source Acquisition Sequencing

[Source Acquisition Boundary](source-acquisition-boundary.md) separates acquisition from source adapter execution, parser execution, normalization execution, persistence, scheduling/retry, and credentials/secrets handling.

[Source Acquisition Sequencing Checklist](source-acquisition-sequencing-checklist.md) places manifest and example boundaries before implementation tasks.

Future manifest examples should preserve that sequence. They should not skip ahead into remote acquisition, cache, persistence, scheduler/retry/cancel behavior, credentials/secrets handling, or implementation behavior.

## Relationship To Source Adapter And Parser Handoff

Source adapter handoff is described by [Source Adapter Contract](source-adapter-contract.md) and [Source Adapter Execution Flow](source-adapter-execution-flow.md). Parser handoff is described by [Parser Handoff Boundary](parser-handoff-boundary.md) and [Parser Contract Boundaries](parser-contract-boundaries.md).

Future manifest examples may include parser handoff hints only as non-authoritative metadata. Those hints should not change source adapter behavior, parser behavior, parser correctness, parser-to-normalization integration behavior, or normalization behavior.

## Review Checklist

Future manifest example tasks should confirm:

- The task is documentation-only or example-only.
- No Python or .NET implementation code is added.
- No fixtures are added unless explicitly scoped in a future example task.
- No manifest model or source acquisition model code is added.
- Metadata is artificial and deterministic.
- Logical fixture names are artificial.
- Source family labels are illustrative.
- Checksum/hash values are deterministic and artificial.
- Timestamps are static illustrative fields only.
- Parser handoff hints are non-authoritative.
- No real source metadata is added.
- No real source URLs are added.
- No remote download behavior is added.
- No credentials/secrets/config loading is added.
- No DB/persistence/cache behavior is added.
- No scheduler, retry, or cancel behavior is added.
- No checksum enforcement is implied beyond artificial fixtures.
- No unit conversion, factor correctness, compliance/legal, carbon accounting, or production readiness claim is made.

## Non-Goals

This document does not add, implement, prove, or claim:

- Local source manifest example code.
- Local source manifest model implementation.
- Source manifest code.
- Source acquisition model code.
- Local file reading behavior.
- Fixture files.
- Real source metadata.
- Real source data.
- Real source URLs.
- Official source cataloging.
- Arbitrary user file manifesting.
- Real directory scanning.
- Remote download behavior.
- Remote source cataloging.
- Source URL cataloging.
- Credential/secrets handling.
- Config loading.
- DB/persistence/cache behavior.
- Scheduler behavior.
- Retry/cancel behavior.
- Checksum enforcement beyond artificial fixtures.
- Source adapter runtime behavior.
- Source adapter correctness for real external sources.
- Parser runtime behavior.
- Parser correctness for real external sources.
- Parser-to-normalization integration behavior.
- Normalization runtime behavior.
- Normalization correctness.
- Unit conversion.
- Unit conversion correctness.
- Factor correctness.
- Carbon accounting correctness.
- Compliance or legal interpretation.
- Deployment behavior.
- Readiness for production use.

## Related Documents

- [Local Source Manifest Boundary](local-source-manifest-boundary.md)
- [Local Source Acquisition Examples Boundary](local-source-acquisition-examples-boundary.md)
- [Local Source Acquisition Contract Boundary](local-source-acquisition-contract-boundary.md)
- [Source Acquisition Boundary](source-acquisition-boundary.md)
- [Source Acquisition Sequencing Checklist](source-acquisition-sequencing-checklist.md)
- [Source Adapter Contract](source-adapter-contract.md)
- [Source Adapter Execution Flow](source-adapter-execution-flow.md)
- [Parser Handoff Boundary](parser-handoff-boundary.md)
- [Parser Contract Boundaries](parser-contract-boundaries.md)
