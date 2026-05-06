# Source Acquisition Error Taxonomy Boundary

This document defines how future source acquisition error taxonomy may be described before any error taxonomy code, validation error implementation, fixtures, tests, or examples are added.

It is documentation-only. It adds no Python code, .NET code, validation code, error taxonomy code, validation tests, fixtures, example code, runtime error handling, retry/cancel/scheduler behavior, manifest model, adapter behavior, parser behavior, normalization behavior, local file reading, source acquisition model code, source manifest code, real source data, real source URLs, remote behavior, credentials/secrets handling, config loading, DB/persistence/cache behavior, deployment behavior, unit conversion, or factor correctness logic.

## Purpose

Future source acquisition error taxonomy may give validation and review tasks stable names for artificial metadata shape issues.

The taxonomy boundary should help future work discuss categories, code prefixes, severity labels, and human-readable messages without implementing validation logic or runtime error handling. Taxonomy names should describe artificial boundary issues only. They must not imply source correctness, source availability, source adapter correctness, parser correctness, normalization correctness, unit conversion correctness, factor correctness, compliance/legal correctness, carbon accounting correctness, incident handling, alerting, retry behavior, or readiness for production use.

## Allowed Future Taxonomy Concepts

Future taxonomy docs or contracts may define concepts such as:

- Metadata shape errors.
- Missing artificial fixture fields.
- Invalid declared source family label.
- Invalid declared content type or format label.
- Missing artificial checksum/hash metadata.
- Invalid non-authoritative parser/adapter handoff hint shape.
- Boundary-safe status/category/severity labels.
- Deterministic artificial example error codes.

These concepts should remain scoped to artificial metadata and boundary validation. They should not be used as evidence that real source acquisition, file reading, remote access, persistence, adapter execution, parser execution, or normalization behavior exists.

## What The Taxonomy Must Not Imply

Source acquisition error taxonomy must not imply:

- Official source correctness validation.
- Carbon factor correctness validation.
- Compliance/legal correctness validation.
- Production filesystem readiness.
- Arbitrary user file ingestion support.
- Real source discovery.
- Real source URL validation.
- Remote source availability.
- Credential/config availability.
- DB/cache persistence.
- Scheduler/retry/cancel behavior.
- Runtime incident/alerting behavior.
- Unit conversion correctness.
- Parser correctness.
- Normalization correctness.
- Source adapter correctness for real external sources.
- Readiness for production use.

Any future task that needs one of these areas requires explicit implementation scope, tests, and review gates.

## Boundary Separation

Future taxonomy work should keep these boundaries separate:

- Source acquisition validation: checks artificial metadata shape only when explicitly scoped.
- Taxonomy naming: provides stable names, code prefixes, categories, and severity labels without runtime behavior.
- Future validation result objects: may carry taxonomy names later, but require separate contract/model scope.
- Source adapter handoff: receives explicit metadata and must not infer adapter behavior from taxonomy labels.
- Parser handoff: receives non-authoritative hints only when explicitly scoped.
- Normalization handoff: remains downstream of parser outputs and is not validated by acquisition taxonomy labels.

Taxonomy naming should not become hidden validation code, validation result modeling, file reading, source discovery, adapter dispatch, parser execution, normalization execution, persistence, cache behavior, scheduler behavior, retry/cancel behavior, credential/config loading, remote access, incident handling, or alerting.

## Naming Guidance

Future taxonomy naming should prefer:

- Stable category names.
- Deterministic code prefixes.
- Human-readable messages without real source claims.
- Boundary-safe severity labels that describe review priority, not operational incident severity.
- Source-agnostic wording unless a future task explicitly scopes a source-specific boundary.

Future taxonomy naming should avoid:

- Provider-specific claims.
- Official-source-specific claims.
- Messages that imply real source discovery or real source validation.
- Messages that imply parser, normalization, unit conversion, factor, compliance/legal, carbon accounting, or production readiness correctness.
- Labels that imply retry, alerting, incident response, persistence, scheduler, credential, config, cache, or remote availability behavior.

Example code prefixes, if added later, should be deterministic and artificial. They should not encode real provider names, real source URLs, credentials, operational incidents, or production behavior.

## Future Review Questions

Before source acquisition error taxonomy code or docs expand, reviewers should ask:

- Is the task documenting taxonomy, adding contracts/models, adding artificial examples, or implementing validation behavior?
- Are category names source-agnostic and boundary-safe?
- Are code prefixes deterministic and artificial?
- Are severity labels review-oriented rather than operational incident labels?
- Do messages avoid real source claims?
- Do messages avoid provider-specific or official-source-specific claims?
- Does the task avoid runtime error handling?
- Does the task avoid retry/cancel/scheduler behavior?
- Does the task avoid DB/persistence/cache behavior?
- Does the task avoid credentials/secrets/config loading?
- Does the task avoid parser, normalization, unit conversion, factor, compliance/legal, carbon accounting, or production readiness claims?
- Are tests planned for any future taxonomy behavior?

These questions should be repeated for each future taxonomy, validation, or result-object task.

## Relationship To Source Acquisition Validation Documents

[Source Acquisition Validation Boundary](source-acquisition-validation-boundary.md) defines what future validation may check and what it must not imply.

[Source Acquisition Validation Examples Boundary](source-acquisition-validation-examples-boundary.md) limits future validation examples to artificial metadata shape scenarios.

This document names the error taxonomy boundary only. It does not add validation code, validation tests, validation result objects, fixtures, examples, or runtime behavior.

## Relationship To Manifest And Adapter Handoff Documents

[Source Manifest Adapter Handoff Boundary](source-manifest-adapter-handoff-boundary.md) defines what manifest metadata may provide to adapters and what adapters must not infer.

[Source Manifest Adapter Handoff Examples Boundary](source-manifest-adapter-handoff-examples-boundary.md) limits future handoff examples to artificial metadata and illustrative adapter-facing hints.

Future taxonomy may describe invalid handoff hint shape only when explicitly scoped. It should not add adapter selection logic, adapter dispatch behavior, source adapter runtime behavior, or source adapter correctness claims.

## Relationship To Local Source Manifest Documents

[Local Source Manifest Boundary](local-source-manifest-boundary.md) defines what a future local manifest may represent and what it must not imply.

[Local Source Manifest Examples Boundary](local-source-manifest-examples-boundary.md) limits future manifest examples to artificial metadata and non-authoritative handoff hints.

Future taxonomy may name artificial manifest metadata issues only when explicitly scoped. It should not treat manifest metadata as proof of real source correctness, source availability, checksum enforcement, cache behavior, or persistence.

## Relationship To Local Source Acquisition Documents

[Local Source Acquisition Contract Boundary](local-source-acquisition-contract-boundary.md) describes future local acquisition contract concepts.

[Local Source Acquisition Examples Boundary](local-source-acquisition-examples-boundary.md) limits future examples to artificial, deterministic, in-repository inputs.

Future taxonomy may name local acquisition metadata shape issues only as artificial boundary concepts. It must not add local file reading, arbitrary filesystem scanning, real source data, source acquisition model code, source manifest code, or production filesystem assumptions.

## Relationship To Source Acquisition Sequencing

[Source Acquisition Boundary](source-acquisition-boundary.md) separates acquisition from source adapter execution, parser execution, normalization execution, persistence, scheduling/retry, and credentials/secrets handling.

[Source Acquisition Sequencing Checklist](source-acquisition-sequencing-checklist.md) places boundary documentation before implementation tasks.

Future taxonomy work should preserve that sequence. It should not skip ahead into validation implementation, validation result implementation, acquisition implementation, cache behavior, remote access, persistence, scheduler/retry/cancel behavior, credentials/secrets handling, config loading, deployment behavior, runtime incident handling, or alerting.

## Relationship To Parser And Normalization Documents

Parser handoff is described by [Parser Handoff Boundary](parser-handoff-boundary.md) and [Parser Contract Boundaries](parser-contract-boundaries.md). Normalization handoff is described by [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md).

Future taxonomy may reference parser or normalization handoff terminology, but it must not validate parser behavior, parser correctness, parser-to-normalization integration behavior, normalization behavior, unit conversion, or factor correctness.

## Non-Goals

This document does not add, implement, prove, or claim:

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
- Real source discovery.
- Real source metadata.
- Real source data.
- Real source URLs.
- Real source URL validation.
- Official source catalog validation.
- Remote download behavior.
- Remote source availability.
- Source URL cataloging.
- Credential/secrets handling.
- Credential/config availability.
- Config loading.
- DB/persistence/cache behavior.
- Scheduler behavior.
- Checksum enforcement beyond artificial metadata shape.
- Source adapter correctness for real external sources.
- Parser correctness for real external sources.
- Parser-to-normalization integration behavior.
- Normalization correctness.
- Unit conversion.
- Unit conversion correctness.
- Factor correctness.
- Factor correctness validation.
- Carbon accounting correctness.
- Compliance or legal interpretation.
- Deployment behavior.
- Readiness for production use.

## Related Documents

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
