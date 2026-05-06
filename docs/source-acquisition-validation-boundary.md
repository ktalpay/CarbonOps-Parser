# Source Acquisition Validation Boundary

This document defines what future source acquisition validation may check before any validation code, fixtures, tests, or examples are added.

It is documentation-only. It adds no Python code, .NET code, validation code, fixtures, tests, example code, manifest model, adapter behavior, parser behavior, normalization behavior, local file reading, source acquisition model code, source manifest code, real source data, real source URLs, remote behavior, credentials/secrets handling, config loading, DB/persistence/cache behavior, scheduler/retry/cancel behavior, deployment behavior, unit conversion, or factor correctness logic.

## Purpose

Future source acquisition validation may help reviewers confirm that artificial acquisition metadata has the expected shape before adapter or parser handoff.

Validation at this boundary should remain narrow. It may check declared metadata structure for artificial examples, but it must not imply source correctness, source availability, source adapter correctness, parser correctness, normalization correctness, unit conversion correctness, factor correctness, compliance/legal correctness, carbon accounting correctness, or readiness for production use.

## Future Validation Scope

Future source acquisition validation tasks may check:

- Metadata shape.
- Required artificial fixture fields.
- Deterministic logical fixture names.
- Declared source family labels.
- Declared content type or format labels.
- Presence of artificial checksum/hash metadata.
- Non-authoritative parser/adapter handoff hint shape.
- Boundary-safe status values for artificial examples.

These checks should be treated as shape and boundary checks only. They should not be treated as proof that a source exists, that a file is readable, that a checksum is enforced, that an adapter can process a source, or that a parser can interpret content.

## What Validation Must Not Imply

Source acquisition validation must not imply:

- Official source correctness.
- Carbon factor correctness.
- Compliance/legal correctness.
- Production filesystem readiness.
- Arbitrary user file ingestion support.
- Real source discovery.
- Real source URL validation.
- Remote source availability.
- Credential/config availability.
- DB/cache persistence.
- Scheduler/retry/cancel behavior.
- Unit conversion correctness.
- Parser correctness.
- Normalization correctness.
- Source adapter correctness for real external sources.
- Readiness for production use.

Any future validation task that needs one of these areas requires explicit scope, tests, and review gates.

## Boundary Separation

Future validation work should keep these boundaries separate:

- Source acquisition boundary: defines what acquisition may represent without adding runtime acquisition behavior.
- Local source acquisition contract: defines future field concepts without implementing contracts/models in this task.
- Manifest metadata: describes artificial or future source metadata without proving source authority.
- Adapter handoff: receives explicit metadata without inferring runtime adapter behavior.
- Parser handoff: receives non-authoritative hints only when explicitly scoped.
- Normalization handoff: remains downstream of parser outputs and is not validated by acquisition metadata checks.

Validation should not become hidden file reading, source discovery, adapter dispatch, parser execution, normalization execution, persistence, cache behavior, scheduler behavior, retry/cancel behavior, credential loading, config loading, or remote access.

## Future Review Questions

Before source acquisition validation code is added, reviewers should ask:

- Is the task validating documentation shape, contract/model shape, artificial example shape, or runtime behavior?
- Are all validated fields artificial, deterministic, and explicitly scoped?
- Are status values boundary-safe and local to artificial examples?
- Are parser and adapter handoff hints non-authoritative?
- Does validation avoid real source metadata and real source URLs?
- Does validation avoid local file reading and arbitrary filesystem scanning unless separately scoped?
- Does validation avoid remote download behavior?
- Does validation avoid credentials/secrets/config loading?
- Does validation avoid DB/persistence/cache behavior?
- Does validation avoid scheduler/retry/cancel behavior?
- Does validation avoid parser, normalization, unit conversion, factor, compliance/legal, carbon accounting, or production readiness claims?
- Are tests planned for any future validation behavior?

These questions should be repeated for each future validation slice.

## Relationship To Source Acquisition Documents

[Source Acquisition Boundary](source-acquisition-boundary.md) separates acquisition from source adapter execution, parser execution, normalization execution, persistence, scheduling/retry, and credentials/secrets handling.

[Source Acquisition Sequencing Checklist](source-acquisition-sequencing-checklist.md) places boundary and validation planning before implementation tasks.

This document follows that sequence by documenting validation boundaries only. It does not add validation code, acquisition behavior, manifest code, adapter behavior, tests, examples, or runtime behavior.

## Relationship To Local Source Acquisition Documents

[Local Source Acquisition Contract Boundary](local-source-acquisition-contract-boundary.md) describes future local acquisition contract concepts.

[Local Source Acquisition Examples Boundary](local-source-acquisition-examples-boundary.md) limits future examples to artificial, deterministic, in-repository inputs.

Future validation may check local acquisition metadata shape only when explicitly scoped. It should not add local file reading, arbitrary filesystem scanning, real source data, source acquisition model code, or production filesystem assumptions.

## Relationship To Manifest Documents

[Local Source Manifest Boundary](local-source-manifest-boundary.md) defines what a future local manifest may represent and what it must not imply.

[Local Source Manifest Examples Boundary](local-source-manifest-examples-boundary.md) limits future manifest examples to artificial metadata and non-authoritative handoff hints.

Future validation may check manifest metadata shape only when explicitly scoped. It should not treat manifest metadata as proof of real source correctness, source availability, checksum enforcement, cache behavior, or persistence.

## Relationship To Adapter Handoff Documents

[Source Manifest Adapter Handoff Boundary](source-manifest-adapter-handoff-boundary.md) defines what manifest metadata may provide to adapters and what adapters must not infer.

[Source Manifest Adapter Handoff Examples Boundary](source-manifest-adapter-handoff-examples-boundary.md) limits future handoff examples to artificial metadata and illustrative adapter-facing hints.

Future validation may check adapter handoff hint shape only when explicitly scoped. It should not add adapter selection logic, adapter dispatch behavior, source adapter runtime behavior, or source adapter correctness claims.

## Relationship To Parser And Normalization Documents

Parser handoff is described by [Parser Handoff Boundary](parser-handoff-boundary.md) and [Parser Contract Boundaries](parser-contract-boundaries.md). Normalization handoff is described by [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md).

Future acquisition validation may reference parser or normalization handoff terminology, but it must not validate parser behavior, parser correctness, parser-to-normalization integration behavior, normalization behavior, unit conversion, or factor correctness.

## Non-Goals

This document does not add, implement, prove, or claim:

- Source acquisition validation code.
- Source acquisition validation tests.
- Validation fixtures.
- Example code.
- Manifest model implementation.
- Source manifest code.
- Source acquisition model code.
- Adapter selection logic.
- Adapter dispatch behavior.
- Source adapter runtime behavior.
- Parser runtime behavior.
- Normalization runtime behavior.
- Local file reading behavior.
- Arbitrary user file ingestion.
- Real source discovery.
- Real source metadata.
- Real source data.
- Real source URLs.
- Real source URL validation.
- Remote download behavior.
- Remote source availability.
- Source URL cataloging.
- Credential/secrets handling.
- Config loading.
- DB/persistence/cache behavior.
- Scheduler behavior.
- Retry/cancel behavior.
- Checksum enforcement beyond artificial metadata shape.
- Source adapter correctness for real external sources.
- Parser correctness for real external sources.
- Parser-to-normalization integration behavior.
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
- [Source Manifest Adapter Handoff Boundary](source-manifest-adapter-handoff-boundary.md)
- [Source Manifest Adapter Handoff Examples Boundary](source-manifest-adapter-handoff-examples-boundary.md)
- [Source Adapter Contract](source-adapter-contract.md)
- [Source Adapter Error And Warning Handling](source-adapter-error-warning-handling.md)
- [Parser Handoff Boundary](parser-handoff-boundary.md)
- [Parser Contract Boundaries](parser-contract-boundaries.md)
- [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md)
