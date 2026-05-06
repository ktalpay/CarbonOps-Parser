# Source Acquisition Error Taxonomy Examples Boundary

This document defines what future source acquisition error taxonomy examples may and may not demonstrate.

It is documentation-only. It adds no Python code, .NET code, validation code, error taxonomy code, validation tests, validation result objects, fixtures, example code, runtime error handling, retry/cancel/scheduler behavior, incident/alerting behavior, manifest model, adapter behavior, parser behavior, normalization behavior, local file reading, source acquisition model code, source manifest code, real source data, real source URLs, remote behavior, credentials/secrets handling, config loading, DB/persistence/cache behavior, deployment behavior, unit conversion, or factor correctness logic.

## Purpose

Future source acquisition error taxonomy examples may show how artificial metadata shape issues could be named for review before taxonomy code or validation result objects exist.

These examples should remain deterministic, artificial, source-agnostic, and local to documentation or explicitly scoped example tasks. They must not imply real source validation, source availability, source adapter correctness, parser correctness, normalization correctness, unit conversion correctness, factor correctness, compliance/legal correctness, carbon accounting correctness, incident handling, alerting, retry behavior, or readiness for production use.

## Allowed Future Example Scope

Future error taxonomy examples may demonstrate:

- Artificial metadata shape error examples.
- Deterministic artificial error code examples.
- Stable category name examples.
- Severity/status label examples for artificial scenarios.
- Missing artificial fixture field examples.
- Invalid declared source family label examples.
- Invalid declared content type or format label examples.
- Invalid non-authoritative parser/adapter handoff hint shape examples.
- Human-readable message examples without real source claims.

Allowed examples should make their artificial scope explicit. They may illustrate taxonomy naming style, but they must not implement taxonomy code, validation result objects, validation tests, runtime error handling, retry behavior, alerting behavior, or operational incident behavior.

## Disallowed Future Example Scope

Future error taxonomy examples must not demonstrate:

- Real source/provider-specific error examples.
- Official source catalog errors.
- Real source URL validation errors.
- Arbitrary user file ingestion errors.
- Real directory scanning errors.
- Remote availability errors.
- Credentials/secrets/config errors.
- DB/persistence/cache errors.
- Scheduler/retry/cancel errors.
- Runtime incident/alerting errors.
- Checksum enforcement beyond artificial fixtures.
- Adapter runtime errors.
- Parser runtime errors.
- Normalization runtime errors.
- Unit conversion or factor correctness errors.
- Compliance/legal errors.
- Carbon accounting errors.
- Production filesystem assumptions.

Any item in this section requires a separate future boundary and explicitly scoped implementation task before it can be considered.

## Boundary Separation

Future taxonomy examples should keep these boundaries separate:

- Taxonomy example naming: static names, code prefixes, labels, and messages only.
- Future taxonomy implementation: code and enums remain separate.
- Validation result objects: structured result models remain separate.
- Source acquisition validation: future validation behavior remains separate.
- Source adapter handoff: adapter-facing hints remain non-authoritative.
- Parser handoff: parser-facing hints remain non-authoritative.
- Normalization handoff: remains downstream of parser outputs and is not described by taxonomy examples.

This separation prevents taxonomy examples from becoming hidden validation code, validation result modeling, runtime error handling, file reading, source discovery, adapter dispatch, parser execution, normalization execution, persistence, cache behavior, scheduler behavior, retry/cancel behavior, credential/config loading, remote access, incident handling, or alerting.

## Relationship To Error Taxonomy Boundary

[Source Acquisition Error Taxonomy Boundary](source-acquisition-error-taxonomy-boundary.md) defines how future taxonomy may be described without adding implementation or runtime behavior.

Future examples should follow that boundary by using source-agnostic category names, deterministic artificial code prefixes, and human-readable messages without real source claims. They should not use provider-specific names, official-source-specific claims, real source URLs, operational incident labels, or production behavior labels.

## Relationship To Source Acquisition Validation Documents

[Source Acquisition Validation Boundary](source-acquisition-validation-boundary.md) defines what future validation may check and what it must not imply.

[Source Acquisition Validation Examples Boundary](source-acquisition-validation-examples-boundary.md) limits future validation examples to artificial metadata shape scenarios.

Future taxonomy examples may describe names for artificial validation issues only. They should not add validation code, validation tests, validation result objects, fixtures, examples that execute behavior, or runtime behavior.

## Relationship To Manifest And Adapter Handoff Documents

[Source Manifest Adapter Handoff Boundary](source-manifest-adapter-handoff-boundary.md) defines what manifest metadata may provide to adapters and what adapters must not infer.

[Source Manifest Adapter Handoff Examples Boundary](source-manifest-adapter-handoff-examples-boundary.md) limits future handoff examples to artificial metadata and illustrative adapter-facing hints.

Future taxonomy examples may name invalid handoff hint shape only as artificial examples. They should not add adapter selection logic, adapter dispatch behavior, source adapter runtime behavior, or source adapter correctness claims.

## Relationship To Local Source Manifest Documents

[Local Source Manifest Boundary](local-source-manifest-boundary.md) defines what a future local manifest may represent and what it must not imply.

[Local Source Manifest Examples Boundary](local-source-manifest-examples-boundary.md) limits future manifest examples to artificial metadata and non-authoritative handoff hints.

Future taxonomy examples may name artificial manifest metadata issues only. They should not treat manifest metadata as proof of real source correctness, source availability, checksum enforcement, cache behavior, or persistence.

## Relationship To Local Source Acquisition Documents

[Local Source Acquisition Contract Boundary](local-source-acquisition-contract-boundary.md) describes future local acquisition contract concepts.

[Local Source Acquisition Examples Boundary](local-source-acquisition-examples-boundary.md) limits future examples to artificial, deterministic, in-repository inputs.

Future taxonomy examples may name local acquisition metadata shape issues only as artificial boundary examples. They must not add local file reading, arbitrary filesystem scanning, real source data, source acquisition model code, source manifest code, or production filesystem assumptions.

## Relationship To Source Acquisition Sequencing

[Source Acquisition Boundary](source-acquisition-boundary.md) separates acquisition from source adapter execution, parser execution, normalization execution, persistence, scheduling/retry, and credentials/secrets handling.

[Source Acquisition Sequencing Checklist](source-acquisition-sequencing-checklist.md) places boundary documentation before implementation tasks.

Future taxonomy examples should preserve that sequence. They should not skip ahead into taxonomy implementation, validation implementation, validation result implementation, acquisition implementation, cache behavior, remote access, persistence, scheduler/retry/cancel behavior, credentials/secrets handling, config loading, deployment behavior, runtime incident handling, or alerting.

## Relationship To Parser And Normalization Documents

Parser handoff is described by [Parser Handoff Boundary](parser-handoff-boundary.md) and [Parser Contract Boundaries](parser-contract-boundaries.md). Normalization handoff is described by [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md).

Future taxonomy examples may reference parser or normalization handoff terminology, but they must not define parser runtime errors, parser correctness errors, parser-to-normalization integration errors, normalization runtime errors, unit conversion errors, or factor correctness errors.

## Review Checklist

Future error taxonomy example tasks should confirm:

- The task is documentation-only or example-only.
- No Python or .NET implementation code is added.
- No error taxonomy code is added.
- No validation code is added.
- No validation tests are added.
- No validation result objects are added.
- No fixtures are added unless explicitly scoped in a future example task.
- Example category names are stable and source-agnostic.
- Example code prefixes are deterministic and artificial.
- Severity/status labels are review-oriented and artificial.
- Messages are human-readable and avoid real source claims.
- No provider-specific or official-source-specific claims are added.
- No real source data or real source URLs are added.
- No runtime error handling is added.
- No incident/alerting behavior is added.
- No retry/cancel/scheduler behavior is added.
- No DB/persistence/cache behavior is added.
- No credentials/secrets/config loading is added.
- No adapter, parser, or normalization runtime errors are implied.
- No unit conversion, factor correctness, compliance/legal, carbon accounting, or production readiness claim is made.

## Non-Goals

This document does not add, implement, prove, or claim:

- Source acquisition error taxonomy example code.
- Source acquisition error taxonomy code.
- Source acquisition validation error implementation.
- Source acquisition validation code.
- Source acquisition validation tests.
- Validation result objects.
- Runtime error handling.
- Runtime incident behavior.
- Alerting behavior.
- Retry/cancel/scheduler behavior.
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
- Real directory scanning.
- Real source/provider-specific error examples.
- Real source discovery.
- Real source metadata.
- Real source data.
- Real source URLs.
- Real source URL validation errors.
- Official source catalog errors.
- Remote download behavior.
- Remote availability errors.
- Source URL cataloging.
- Credential/secrets handling.
- Credentials/secrets/config errors.
- Config loading.
- DB/persistence/cache behavior.
- DB/persistence/cache errors.
- Scheduler/retry/cancel errors.
- Checksum enforcement beyond artificial metadata shape.
- Adapter runtime errors.
- Parser runtime errors.
- Normalization runtime errors.
- Source adapter correctness for real external sources.
- Parser correctness for real external sources.
- Parser-to-normalization integration behavior.
- Normalization correctness.
- Unit conversion.
- Unit conversion correctness.
- Factor correctness.
- Factor correctness errors.
- Carbon accounting correctness.
- Compliance or legal interpretation.
- Deployment behavior.
- Readiness for production use.

## Related Documents

- [Source Acquisition Error Taxonomy Boundary](source-acquisition-error-taxonomy-boundary.md)
- [Source Acquisition Validation Boundary](source-acquisition-validation-boundary.md)
- [Source Acquisition Validation Examples Boundary](source-acquisition-validation-examples-boundary.md)
- [Source Manifest Adapter Handoff Boundary](source-manifest-adapter-handoff-boundary.md)
- [Source Manifest Adapter Handoff Examples Boundary](source-manifest-adapter-handoff-examples-boundary.md)
- [Local Source Manifest Boundary](local-source-manifest-boundary.md)
- [Local Source Manifest Examples Boundary](local-source-manifest-examples-boundary.md)
- [Local Source Acquisition Contract Boundary](local-source-acquisition-contract-boundary.md)
- [Local Source Acquisition Examples Boundary](local-source-acquisition-examples-boundary.md)
- [Source Acquisition Boundary](source-acquisition-boundary.md)
- [Source Acquisition Sequencing Checklist](source-acquisition-sequencing-checklist.md)
- [Source Adapter Error And Warning Handling](source-adapter-error-warning-handling.md)
- [Source Adapter Contract](source-adapter-contract.md)
- [Parser Handoff Boundary](parser-handoff-boundary.md)
- [Parser Contract Boundaries](parser-contract-boundaries.md)
- [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md)
