# Local Source Manifest Boundary

This document defines what a future local source manifest may represent before any manifest model or code is added.

It is documentation-only. It adds no fixtures, example code, Python code, .NET code, manifest model, local file reading, source acquisition model code, source manifest code, real source data, real source URLs, remote behavior, credentials/secrets handling, DB/persistence behavior, scheduler/retry/cancel behavior, config loading, deployment behavior, unit conversion, or factor correctness logic.

## Purpose

A future local source manifest may describe artificial, deterministic, in-repository fixture inputs for review and handoff planning.

The manifest boundary should help future tasks explain source identity, file labels, checksum/hash metadata, and parser handoff hints without implying real-world source coverage or runtime readiness. A manifest should be treated as metadata for a scoped example or contract, not as proof of source correctness, parser correctness, normalization correctness, compliance/legal correctness, official carbon accounting correctness, or readiness for production use.

## Future Local Source Manifest Scope

A future local source manifest may describe:

- Artificial fixture identity.
- Source family label.
- Local example file name or logical fixture name.
- Declared content type or format label.
- Deterministic checksum/hash metadata for artificial fixtures only.
- Acquisition timestamp concept as an example-only field, without runtime clock behavior.
- Parser handoff hints as non-authoritative metadata.

These fields should remain descriptive. They should not imply that the repository has inspected, validated, acquired, cached, persisted, parsed, normalized, or verified a real source.

## What A Manifest Must Not Imply

A local source manifest must not imply:

- Official source correctness.
- Carbon factor correctness.
- Compliance/legal correctness.
- Production filesystem readiness.
- Arbitrary user file ingestion.
- Remote source cataloging.
- Source URL cataloging.
- Credential/config loading.
- DB persistence.
- Scheduler/retry/cancel behavior.
- Unit conversion correctness.
- Parser correctness for real external sources.
- Normalization correctness.
- Readiness for production use.

Any future task that needs one of these areas should define a separate boundary, implementation scope, tests, and review gates.

## Artificial Fixture Manifests Vs Real-World Source Manifests

Artificial fixture manifests are limited to deterministic, in-repository examples. They may help reviewers understand expected metadata shape and handoff intent.

Real-world source manifests would require separate future work for source identity, source provenance, source URL or location policy, file acquisition, checksum enforcement, cache behavior, credentials/secrets handling, persistence, scheduler/retry/cancel behavior, and operational review.

This document only covers the artificial/local boundary. It does not define real-world source manifest behavior.

## Relationship To Source Acquisition Boundary

[Source Acquisition Boundary](source-acquisition-boundary.md) separates acquisition from source adapter execution, parser execution, normalization execution, persistence, scheduling/retry, and credentials/secrets handling.

A local source manifest should follow that separation. It may describe acquisition-adjacent metadata, but it must not hide remote behavior, database writes, scheduler behavior, retry/cancel behavior, credentials/secrets handling, parser execution, or normalization execution.

## Relationship To Source Acquisition Sequencing

[Source Acquisition Sequencing Checklist](source-acquisition-sequencing-checklist.md) places manifest boundary work before implementation tasks.

This document fills that sequencing step at the documentation level only. It does not add manifest contracts/models, examples, tests, or runtime behavior.

## Relationship To Local Source Acquisition

[Local Source Acquisition Contract Boundary](local-source-acquisition-contract-boundary.md) defines future local acquisition contract concepts such as local file path, source identity, source family, source version/date, file name, media type or extension, checksum/hash, file size, acquisition timestamp, acquisition mode, manifest relationship, and source adapter handoff metadata.

[Local Source Acquisition Examples Boundary](local-source-acquisition-examples-boundary.md) limits future examples to artificial, deterministic, in-repository inputs.

A future local source manifest should fit within those boundaries. It may relate fixture metadata to local acquisition concepts, but it should not add file reading, arbitrary filesystem access, real source data, remote access, persistence, credentials, scheduler/retry/cancel behavior, or production filesystem assumptions.

## Relationship To Source Adapter And Parser Handoff

Source adapter handoff is described by [Source Adapter Contract](source-adapter-contract.md) and [Source Adapter Execution Flow](source-adapter-execution-flow.md). Parser handoff is described by [Parser Handoff Boundary](parser-handoff-boundary.md) and [Parser Contract Boundaries](parser-contract-boundaries.md).

A future local source manifest may include parser handoff hints only as non-authoritative metadata. Those hints should not change source adapter behavior, parser behavior, parser correctness, parser-to-normalization integration behavior, or normalization behavior.

## Review Checklist

Future manifest-related tasks should confirm:

- The task scope is documentation-only, example-only, contract/model-only, or implementation-specific.
- Artificial fixture scope is explicit.
- No real source data is added.
- No real source URLs are added.
- No remote download behavior is added.
- No credentials or secrets are added.
- No config loading is added.
- No DB/persistence behavior is added.
- No scheduler, retry, or cancel behavior is added.
- No local file reading or arbitrary filesystem scanning is added unless explicitly scoped in a future implementation task.
- Checksum/hash metadata is deterministic and artificial unless enforcement is explicitly scoped later.
- Parser handoff hints are non-authoritative.
- No source adapter, parser, or normalization behavior is changed.
- No source correctness, factor correctness, compliance/legal, carbon accounting, or production readiness claim is made.

## Non-Goals

This document does not add, implement, prove, or claim:

- Local source manifest model implementation.
- Source manifest code.
- Manifest persistence.
- Local source acquisition model code.
- Local file reading behavior.
- Arbitrary user file ingestion.
- Real source data.
- Real source URLs.
- Remote download behavior.
- Remote source cataloging.
- Source URL cataloging.
- Credential/secrets handling.
- Config loading.
- DB/persistence behavior.
- Scheduler behavior.
- Retry/cancel behavior.
- Source cache behavior.
- Checksum enforcement beyond artificial fixture metadata.
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

- [Source Acquisition Boundary](source-acquisition-boundary.md)
- [Source Acquisition Sequencing Checklist](source-acquisition-sequencing-checklist.md)
- [Local Source Acquisition Contract Boundary](local-source-acquisition-contract-boundary.md)
- [Local Source Acquisition Examples Boundary](local-source-acquisition-examples-boundary.md)
- [Source Adapter Contract](source-adapter-contract.md)
- [Source Adapter Execution Flow](source-adapter-execution-flow.md)
- [Parser Handoff Boundary](parser-handoff-boundary.md)
- [Parser Contract Boundaries](parser-contract-boundaries.md)
