# Source Acquisition Implementation Sequencing Checklist

This document defines a safe order for future source acquisition implementation tasks after the boundary and readiness documentation phase.

It is documentation-only. It adds no Python code, .NET code, tests, fixtures, example code, PR automation, CI changes, GitHub Actions changes, validation code, error taxonomy code, validation result objects, runtime error handling, retry/cancel/scheduler behavior, incident/alerting behavior, manifest model, adapter behavior, parser behavior, normalization behavior, local file reading, source acquisition model code, source manifest code, real source data, real source URLs, remote behavior, credentials/secrets handling, config loading, DB/persistence/cache behavior, deployment behavior, unit conversion, or factor correctness logic.

## Purpose

The implementation sequencing checklist gives future source acquisition tasks a narrow, reviewable order before behavior is added.

It does not open implementation work by itself. It does not claim source correctness, source adapter correctness, parser correctness, normalization correctness, unit conversion correctness, factor correctness, compliance/legal correctness, official carbon accounting correctness, operational readiness, or readiness for production use.

## Preconditions Before Implementation Starts

Before a future source acquisition implementation task starts, reviewers should confirm:

- Relevant boundary docs exist.
- The source acquisition review gate is applied.
- The implementation readiness boundary is satisfied.
- Task scope is explicit.
- Forbidden scope is explicitly excluded.
- Tests and checks are listed.
- Affected documentation files are named.
- Documentation map impact is known.
- The task can be completed as a small, reviewable change.
- The task does not combine documentation, model shape, validation, taxonomy, handoff, examples, tests, and runtime behavior unless explicitly scoped.

If these preconditions are not met, the task should stay in documentation-first sequencing or be split before implementation starts.

## Suggested Safe Sequence For Future Implementation Tasks

Future source acquisition implementation work should generally proceed in this order:

1. Artificial metadata model shape only.
2. Artificial manifest metadata shape only.
3. Validation shape only.
4. Error taxonomy shape only.
5. Adapter handoff shape only.
6. Parser handoff shape only.
7. Artificial fixture-only examples.
8. Artificial boundary-safe tests.
9. Documentation map updates.

Each step should be a separate small task unless a future task explicitly justifies combining steps and remains reviewable.

## Step 1: Artificial Metadata Model Shape Only

The first implementation-oriented task should define only artificial source acquisition metadata shape when explicitly scoped.

It should not add local file reading, arbitrary user file ingestion, real source data, real source URLs, remote behavior, credential/config handling, persistence/cache behavior, scheduler/retry/cancel behavior, adapter behavior, parser behavior, normalization behavior, unit conversion, or factor correctness logic.

## Step 2: Artificial Manifest Metadata Shape Only

Manifest metadata shape should follow the artificial metadata shape.

This step may define artificial manifest fields only when explicitly scoped. It should not add source manifest persistence, source cache behavior, checksum enforcement beyond artificial examples, source URL cataloging, real source metadata, remote acquisition, or production filesystem assumptions.

## Step 3: Validation Shape Only

Validation shape should follow the metadata and manifest shape.

This step may define artificial metadata shape validation boundaries only when explicitly scoped. It should not add real source validation, real source URL validation, remote availability checks, credential/config validation, DB/cache validation, scheduler/retry/cancel validation, adapter/parser/normalization runtime validation, unit conversion validation, or factor correctness validation.

## Step 4: Error Taxonomy Shape Only

Error taxonomy shape should follow validation shape.

This step may define deterministic artificial categories, severities, status labels, or code prefixes only when explicitly scoped. It should not add runtime error handling, incident/alerting behavior, retry/cancel behavior, scheduler behavior, provider-specific errors, compliance/legal errors, carbon accounting errors, or official source catalog errors.

## Step 5: Adapter Handoff Shape Only

Adapter handoff shape should follow metadata, manifest, validation, and taxonomy shape.

This step may define how artificial metadata could be handed toward source adapters only when explicitly scoped. It should not add adapter selection logic, adapter dispatch behavior, adapter runtime behavior, source adapter correctness claims, parser behavior, normalization behavior, or runtime acquisition behavior.

## Step 6: Parser Handoff Shape Only

Parser handoff shape should follow adapter handoff shape.

This step may define downstream handoff shape only when explicitly scoped. It should not add parser runtime behavior, parser correctness claims, parser-to-normalization integration behavior, normalization runtime behavior, normalization correctness, unit conversion, factor correctness, or carbon accounting correctness.

## Step 7: Artificial Fixture-Only Examples

Artificial fixture-only examples should follow shape definitions.

This step may add deterministic artificial examples only when explicitly scoped. It should not add real source data, real source URLs, arbitrary user file ingestion, real directory scanning, remote downloads, credentials/config loading, DB/persistence/cache behavior, scheduler/retry/cancel behavior, or correctness claims beyond the artificial example scope.

## Step 8: Artificial Boundary-Safe Tests

Artificial boundary-safe tests should follow explicitly scoped artificial examples or shape tasks.

Tests should remain artificial, deterministic, local-only, and tied to the explicit behavior under review. They should not validate real source coverage, official source correctness, compliance/legal correctness, official carbon accounting correctness, unit conversion correctness, factor correctness, or production filesystem readiness.

## Step 9: Documentation Map Updates

Documentation map updates should accompany any future task that adds, renames, or removes public docs.

Map updates should remain small and should not be used to hide unrelated implementation, examples, tests, automation, CI changes, or runtime behavior.

## Explicitly Blocked Unless Separately Scoped

The following areas remain blocked unless a future task separately scopes them, adds appropriate tests, and passes the review gate:

- Real source data.
- Real source URLs.
- Remote download behavior.
- Arbitrary user file ingestion.
- Real directory scanning.
- Credentials/secrets handling.
- Credential/config loading.
- Config loading.
- DB/persistence/cache behavior.
- Scheduler/retry/cancel behavior.
- Runtime incident/alerting behavior.
- Production filesystem readiness claims.
- Official source correctness claims.
- Carbon factor correctness claims.
- Compliance/legal correctness claims.
- Unit conversion correctness claims.
- Adapter runtime behavior beyond explicitly scoped handoff shape.
- Parser runtime behavior beyond explicitly scoped handoff shape.
- Normalization runtime behavior beyond explicitly scoped handoff shape.
- Source adapter correctness claims.
- Parser correctness claims.
- Normalization correctness claims.
- Carbon accounting correctness claims.
- Deployment behavior.
- PR automation or CI enforcement.

## Split Guidance

Split documentation from implementation when a task both defines a boundary and adds behavior.

Split model shape from validation when a task both defines fields and evaluates those fields.

Split validation from error taxonomy when a task both checks metadata shape and names reusable error categories or codes.

Split adapter handoff from parser handoff when a task crosses from source adapter-facing metadata into downstream parser input shape.

Defer tests until artificial fixtures or artificial shapes are explicitly scoped and the expected behavior can be verified without real source data, real URLs, remote access, credentials, persistence, scheduler/retry/cancel behavior, unit conversion, or factor correctness logic.

Split examples from runtime behavior when a task both demonstrates artificial scenarios and changes source acquisition, adapter, parser, or normalization behavior.

## Required Review Commands For Future Implementation PRs

Future source acquisition implementation PRs should include:

```bash
git diff --check
python -m pytest tests/test_documentation_map_references.py
python -m pytest tests/test_task_queue_consistency.py
python -m pytest
python scripts/check_public_safety.py
```

Passing these commands does not prove real source correctness, parser correctness, normalization correctness, unit conversion correctness, factor correctness, compliance/legal correctness, official carbon accounting correctness, or readiness for production use.

## Relationship To Implementation Readiness Documents

[Source Acquisition Implementation Readiness Boundary](source-acquisition-implementation-readiness-boundary.md) defines prerequisites and blocked areas for future source acquisition implementation tasks.

[Source Acquisition Implementation Readiness Examples Boundary](source-acquisition-implementation-readiness-examples-boundary.md) defines what future readiness examples may demonstrate.

This checklist orders future implementation task families after those readiness boundaries are satisfied. It does not replace them.

## Relationship To Review Gate Documents

[Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md) defines review checks for future source acquisition related PRs.

[Source Acquisition Review Gate Examples Boundary](source-acquisition-review-gate-examples-boundary.md) defines what future review gate examples may show.

This checklist should be used with the review gate, not instead of it.

## Relationship To Validation And Error Taxonomy Documents

[Source Acquisition Validation Boundary](source-acquisition-validation-boundary.md), [Source Acquisition Validation Examples Boundary](source-acquisition-validation-examples-boundary.md), [Source Acquisition Error Taxonomy Boundary](source-acquisition-error-taxonomy-boundary.md), and [Source Acquisition Error Taxonomy Examples Boundary](source-acquisition-error-taxonomy-examples-boundary.md) define validation and taxonomy boundaries.

This checklist places validation shape before error taxonomy shape so future tasks do not name reusable taxonomy categories before the artificial validation scope is clear.

## Relationship To Manifest And Adapter Handoff Documents

[Source Manifest Adapter Handoff Boundary](source-manifest-adapter-handoff-boundary.md), [Source Manifest Adapter Handoff Examples Boundary](source-manifest-adapter-handoff-examples-boundary.md), [Local Source Manifest Boundary](local-source-manifest-boundary.md), and [Local Source Manifest Examples Boundary](local-source-manifest-examples-boundary.md) define manifest metadata and adapter-facing handoff boundaries.

This checklist places manifest metadata shape before adapter handoff shape so future adapter-facing tasks have documented artificial metadata scope to reference.

## Relationship To Local Source Acquisition Documents

[Local Source Acquisition Contract Boundary](local-source-acquisition-contract-boundary.md), [Local Source Acquisition Examples Boundary](local-source-acquisition-examples-boundary.md), [Source Acquisition Boundary](source-acquisition-boundary.md), and [Source Acquisition Sequencing Checklist](source-acquisition-sequencing-checklist.md) define local and general source acquisition boundaries.

This checklist narrows the implementation order after those boundary and sequencing documents. It does not add local file reading, arbitrary user file ingestion, remote acquisition, source URL cataloging, credential/config handling, persistence/cache behavior, or scheduler/retry/cancel behavior.

## Relationship To Parser And Normalization Handoff

Existing parser and normalization handoff documents, including [Parser Handoff Boundary](parser-handoff-boundary.md), [Parser Contract Boundaries](parser-contract-boundaries.md), and [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md), define downstream boundaries.

This checklist places parser handoff shape after adapter handoff shape and does not imply parser runtime behavior, parser correctness, parser-to-normalization integration behavior, normalization runtime behavior, normalization correctness, unit conversion, factor correctness, or carbon accounting correctness.

## Non-Goals

This document does not add, implement, prove, or claim:

- Source acquisition implementation.
- Source acquisition model code.
- Source manifest code.
- Manifest model implementation.
- Source cache implementation.
- Manifest persistence.
- Validation code.
- Validation tests.
- Validation result objects.
- Error taxonomy code.
- Runtime error handling.
- Runtime incident behavior.
- Alerting behavior.
- Retry/cancel/scheduler behavior.
- PR automation.
- CI workflow changes.
- GitHub Actions changes.
- Code owners changes.
- Branch protection changes.
- Automated policy enforcement.
- Fixtures.
- Example code.
- Adapter selection logic.
- Adapter dispatch behavior.
- Source adapter runtime behavior.
- Parser runtime behavior.
- Normalization runtime behavior.
- Parser-to-normalization integration behavior.
- Local file reading behavior.
- Arbitrary user file ingestion.
- Real directory scanning.
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
- Checksum enforcement beyond artificial examples.
- Source adapter correctness for real external sources.
- Parser correctness for real external sources.
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

- [Source Acquisition Implementation Readiness Boundary](source-acquisition-implementation-readiness-boundary.md)
- [Source Acquisition Implementation Readiness Examples Boundary](source-acquisition-implementation-readiness-examples-boundary.md)
- [Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md)
- [Source Acquisition Review Gate Examples Boundary](source-acquisition-review-gate-examples-boundary.md)
- [Source Acquisition Error Taxonomy Boundary](source-acquisition-error-taxonomy-boundary.md)
- [Source Acquisition Error Taxonomy Examples Boundary](source-acquisition-error-taxonomy-examples-boundary.md)
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
