# Source Manifest Adapter Handoff Boundary

This document defines how future source manifest metadata may be handed to source adapters before any manifest model, adapter behavior, fixture, or example code is added.

It is documentation-only. It adds no Python code, .NET code, fixtures, example code, manifest model, adapter behavior, local file reading, source acquisition model code, source manifest code, real source data, real source URLs, remote behavior, credentials/secrets handling, config loading, DB/persistence/cache behavior, scheduler/retry/cancel behavior, deployment behavior, unit conversion, or factor correctness logic.

## Purpose

A future source manifest to adapter handoff may give source adapters explicit metadata about an artificial local fixture or future source input.

The handoff boundary should make metadata flow reviewable without implying authoritative correctness, runtime acquisition behavior, persistence, remote access, or readiness for production use. Manifest metadata may help an adapter understand labels and handoff hints, but it must not silently grant permission to read arbitrary files, access remote sources, load credentials, write to a database, schedule work, retry work, cancel work, parse content, normalize content, or make correctness claims.

## Metadata Manifest May Provide To Adapters

Future manifest metadata may provide adapters with:

- Artificial fixture identity.
- Source family label.
- Logical fixture/file label.
- Declared content type or format label.
- Deterministic checksum/hash metadata for artificial fixtures only.
- Non-authoritative parser handoff hints.
- Static illustrative acquisition metadata.

These fields should be descriptive inputs only. They should not be treated as proof that a source exists, that its contents are correct, that an adapter can process it, or that a parser can interpret it.

## What Adapters Must Not Infer

Adapters must not infer any of the following from manifest metadata:

- Official source correctness.
- Carbon factor correctness.
- Compliance/legal correctness.
- Production filesystem readiness.
- Arbitrary user file ingestion permission.
- Remote source access permission.
- Source URL cataloging.
- Credential/config availability.
- DB persistence.
- Scheduler/retry/cancel behavior.
- Unit conversion correctness.
- Parser correctness for real external sources.
- Normalization correctness.
- Readiness for production use.

Any future adapter behavior that needs one of these areas requires explicit scope, tests, and review gates.

## Boundary Separation

The handoff boundary should keep these responsibilities separate:

- Source acquisition: identifies or obtains source input metadata in a future scoped task.
- Manifest metadata: describes artificial or future source input metadata without executing acquisition.
- Source adapter execution: consumes explicit inputs in a future scoped adapter task without assuming hidden acquisition or persistence behavior.
- Parser handoff: receives parser-relevant hints or inputs only when explicitly scoped and without treating hints as authoritative.
- Normalization handoff: remains downstream of parser outputs and should not consume acquisition or manifest metadata as proof of normalization correctness.

This separation helps prevent manifest metadata from becoming an implicit runtime contract for acquisition, parsing, normalization, persistence, scheduling, credentials, or remote access.

## Future Review Questions

Before adapter code consumes manifest metadata, reviewers should ask:

- Is the task adding documentation, a contract/model, an artificial example, or runtime adapter behavior?
- Are manifest fields clearly marked as authoritative or non-authoritative?
- Are parser handoff hints explicitly non-authoritative?
- Are artificial fixture fields separated from future real-world source fields?
- Does the adapter receive only explicitly scoped metadata?
- Does the task avoid arbitrary user file ingestion?
- Does the task avoid remote source access unless separately scoped?
- Does the task avoid credentials/secrets/config loading?
- Does the task avoid DB/persistence/cache behavior?
- Does the task avoid scheduler/retry/cancel behavior?
- Does the task avoid parser, normalization, unit conversion, factor, compliance/legal, carbon accounting, or production readiness claims?
- Are tests planned for any future behavior being added?

These questions should be repeated for each future manifest, adapter, parser, or handoff task.

## Relationship To Source Acquisition Documents

[Source Acquisition Boundary](source-acquisition-boundary.md) separates acquisition from source adapter execution, parser execution, normalization execution, persistence, scheduling/retry, and credentials/secrets handling.

[Source Acquisition Sequencing Checklist](source-acquisition-sequencing-checklist.md) places boundary and handoff documentation before implementation tasks.

This document follows that sequence by documenting the manifest-to-adapter boundary only. It does not add acquisition behavior, manifest code, adapter behavior, tests, examples, or runtime behavior.

## Relationship To Local Source Acquisition Documents

[Local Source Acquisition Contract Boundary](local-source-acquisition-contract-boundary.md) describes future local acquisition contract concepts.

[Local Source Acquisition Examples Boundary](local-source-acquisition-examples-boundary.md) limits future local acquisition examples to artificial, deterministic, in-repository inputs.

Manifest metadata handed to adapters should fit within those boundaries. It should not add file reading, arbitrary filesystem scanning, real source data, remote behavior, credentials/secrets handling, persistence, scheduler/retry/cancel behavior, or production filesystem assumptions.

## Relationship To Local Source Manifest Documents

[Local Source Manifest Boundary](local-source-manifest-boundary.md) defines what a future local manifest may represent and what it must not imply.

[Local Source Manifest Examples Boundary](local-source-manifest-examples-boundary.md) limits future manifest examples to artificial metadata and non-authoritative handoff hints.

The adapter handoff should preserve those limits. Adapters may receive manifest metadata only as explicitly scoped inputs and should not treat artificial fixture metadata as real-world source authority.

## Relationship To Source Adapter And Parser Handoff

Source adapter handoff is described by [Source Adapter Contract](source-adapter-contract.md) and [Source Adapter Execution Flow](source-adapter-execution-flow.md). Parser handoff is described by [Parser Handoff Boundary](parser-handoff-boundary.md) and [Parser Contract Boundaries](parser-contract-boundaries.md).

Future manifest-to-adapter tasks should align with those documents without changing source adapter runtime behavior, parser behavior, parser-to-normalization integration behavior, normalization behavior, or public API exports unless separately scoped.

## Non-Goals

This document does not add, implement, prove, or claim:

- Manifest model implementation.
- Source manifest code.
- Source acquisition model code.
- Source adapter runtime behavior.
- Adapter consumption logic.
- Fixture files.
- Example code.
- Local file reading behavior.
- Arbitrary user file ingestion.
- Real source metadata.
- Real source data.
- Real source URLs.
- Remote download behavior.
- Remote source access permission.
- Source URL cataloging.
- Credential/secrets handling.
- Config loading.
- DB/persistence/cache behavior.
- Scheduler behavior.
- Retry/cancel behavior.
- Checksum enforcement beyond artificial fixture metadata.
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
- [Local Source Manifest Boundary](local-source-manifest-boundary.md)
- [Local Source Manifest Examples Boundary](local-source-manifest-examples-boundary.md)
- [Source Adapter Contract](source-adapter-contract.md)
- [Source Adapter Execution Flow](source-adapter-execution-flow.md)
- [Parser Handoff Boundary](parser-handoff-boundary.md)
- [Parser Contract Boundaries](parser-contract-boundaries.md)
