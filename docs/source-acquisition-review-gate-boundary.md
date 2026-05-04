# Source Acquisition Review Gate Boundary

This document defines a future review gate for source acquisition related tasks.

It is documentation-only. It adds no Python code, .NET code, tests, fixtures, example code, validation code, error taxonomy code, validation result objects, runtime error handling, retry/cancel/scheduler behavior, incident/alerting behavior, manifest model, adapter behavior, parser behavior, normalization behavior, local file reading, source acquisition model code, source manifest code, real source data, real source URLs, remote behavior, credentials/secrets handling, config loading, DB/persistence/cache behavior, deployment behavior, unit conversion, or factor correctness logic.

## Purpose

The source acquisition review gate consolidates safety checks for future tasks that touch source acquisition, local acquisition, manifest metadata, source adapter handoff, validation, and error taxonomy boundaries.

The gate is intended to keep future changes small, explicit, and sequenced. It does not certify implementation readiness, source correctness, source adapter correctness, parser correctness, normalization correctness, unit conversion correctness, factor correctness, compliance/legal correctness, carbon accounting correctness, operational readiness, or readiness for production use.

## Task Types Covered By The Gate

Future tasks should pass through this review gate when they touch:

- Source acquisition boundary docs.
- Local source acquisition docs.
- Manifest metadata docs.
- Manifest-to-adapter handoff docs.
- Validation boundary docs.
- Error taxonomy docs.
- Future code tasks that touch these areas.

The gate should apply whether the change is documentation-only, example-only, contract/model-oriented, or implementation-oriented.

## Required Review Checks

Reviewers should confirm:

- Documentation-only tasks remain documentation-only.
- No real source data is added.
- No real URLs are added.
- No remote download behavior is added.
- No credential/config loading is added.
- No DB/persistence/cache behavior is added.
- No scheduler/retry/cancel behavior is added.
- No runtime incident/alerting behavior is added.
- No arbitrary user file ingestion is added.
- No real directory scanning is added.
- No production filesystem readiness claim is made.
- No official source correctness claim is made.
- No carbon factor correctness claim is made.
- No compliance/legal correctness claim is made.
- No unit conversion correctness claim is made unless explicitly scoped.
- No parser, normalization, factor, or carbon accounting correctness claim is made unless explicitly scoped and tested.

For implementation tasks, reviewers should also confirm that the implementation scope is narrow, tests are planned or included, and the task does not bundle unrelated acquisition, manifest, adapter, parser, normalization, persistence, scheduler, retry, credential, config, cache, or deployment behavior.

## Boundary Alignment Checks

Reviewers should confirm that future tasks align with:

- [Source Acquisition Boundary](source-acquisition-boundary.md).
- [Source Acquisition Sequencing Checklist](source-acquisition-sequencing-checklist.md).
- [Local Source Acquisition Contract Boundary](local-source-acquisition-contract-boundary.md).
- [Local Source Acquisition Examples Boundary](local-source-acquisition-examples-boundary.md).
- [Local Source Manifest Boundary](local-source-manifest-boundary.md).
- [Local Source Manifest Examples Boundary](local-source-manifest-examples-boundary.md).
- [Source Manifest Adapter Handoff Boundary](source-manifest-adapter-handoff-boundary.md).
- [Source Manifest Adapter Handoff Examples Boundary](source-manifest-adapter-handoff-examples-boundary.md).
- [Source Acquisition Validation Boundary](source-acquisition-validation-boundary.md).
- [Source Acquisition Validation Examples Boundary](source-acquisition-validation-examples-boundary.md).
- [Source Acquisition Error Taxonomy Boundary](source-acquisition-error-taxonomy-boundary.md).
- [Source Acquisition Error Taxonomy Examples Boundary](source-acquisition-error-taxonomy-examples-boundary.md).

If a task conflicts with one of these boundaries, reviewers should require scope reduction, sequencing split, or a new explicit boundary task before implementation continues.

## Required Validation Commands

Future source acquisition related PR review should include:

```bash
git diff --check
python -m pytest tests/test_documentation_map_references.py
python -m pytest tests/test_task_queue_consistency.py
python -m pytest
python scripts/check_public_safety.py
```

Documentation-only changes may still run the full command set so that documentation maps, task queue consistency, and public safety wording remain guarded.

## Review Decision Categories

Reviewers may use these decision categories:

- Mergeable: scope is clear, boundaries are respected, required checks pass, and no forbidden scope is present.
- Requires scope reduction: the task is directionally safe but includes unrelated or oversized work.
- Requires forbidden-scope removal: the task includes real data, real URLs, credentials, remote behavior, persistence, scheduler/retry/cancel behavior, config loading, deployment behavior, or unsupported correctness claims.
- Requires sequencing split: the task mixes boundary docs, contracts/models, examples, tests, and implementation in a way that should be reviewed separately.
- Blocked until explicit implementation task: the task attempts behavior that has not been explicitly scoped, tested, and reviewed as implementation work.

These categories are review aids only. They do not replace human review or project maintainership.

## Future Code Task Expectations

When a future task moves beyond documentation, reviewers should confirm:

- The implementation task explicitly names the behavior being added.
- The task states which boundaries it depends on.
- Tests cover the new behavior.
- Artificial examples remain clearly artificial.
- Real source data, real URLs, credentials, remote behavior, persistence, scheduler/retry/cancel behavior, config loading, deployment behavior, unit conversion, and factor correctness remain out of scope unless explicitly included.
- Public wording avoids production readiness, compliance/legal correctness, official carbon accounting correctness, source correctness, parser correctness, normalization correctness, unit conversion correctness, and factor correctness claims unless explicitly scoped and tested.

If these expectations are not met, the task should be split or blocked.

## Relationship To Source Acquisition Documents

[Source Acquisition Boundary](source-acquisition-boundary.md) defines the broad separation between source acquisition, source adapter execution, parser execution, normalization execution, persistence, scheduling/retry, and credentials/secrets handling.

[Source Acquisition Sequencing Checklist](source-acquisition-sequencing-checklist.md) defines a safe order before implementation.

The review gate uses those documents as the first check for scope and sequencing.

## Relationship To Local Acquisition And Manifest Documents

[Local Source Acquisition Contract Boundary](local-source-acquisition-contract-boundary.md), [Local Source Acquisition Examples Boundary](local-source-acquisition-examples-boundary.md), [Local Source Manifest Boundary](local-source-manifest-boundary.md), and [Local Source Manifest Examples Boundary](local-source-manifest-examples-boundary.md) define the local/artificial side of the acquisition track.

The review gate should reject changes that turn artificial local metadata into arbitrary user file ingestion, real source metadata, real directory scanning, production filesystem assumptions, or source correctness claims.

## Relationship To Adapter, Parser, And Normalization Handoff

[Source Manifest Adapter Handoff Boundary](source-manifest-adapter-handoff-boundary.md) and [Source Manifest Adapter Handoff Examples Boundary](source-manifest-adapter-handoff-examples-boundary.md) define the adapter-facing handoff boundary.

Parser handoff is described by [Parser Handoff Boundary](parser-handoff-boundary.md) and [Parser Contract Boundaries](parser-contract-boundaries.md). Normalization handoff is described by [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md).

The review gate should reject changes that use acquisition metadata or manifest hints as proof of source adapter behavior, parser behavior, parser-to-normalization integration behavior, normalization behavior, unit conversion, or factor correctness.

## Relationship To Validation And Error Taxonomy

[Source Acquisition Validation Boundary](source-acquisition-validation-boundary.md), [Source Acquisition Validation Examples Boundary](source-acquisition-validation-examples-boundary.md), [Source Acquisition Error Taxonomy Boundary](source-acquisition-error-taxonomy-boundary.md), and [Source Acquisition Error Taxonomy Examples Boundary](source-acquisition-error-taxonomy-examples-boundary.md) define the validation and taxonomy track.

The review gate should reject changes that turn validation or taxonomy naming into runtime validation behavior, validation result objects, incident/alerting behavior, retry/cancel/scheduler behavior, DB/persistence/cache behavior, credential/config loading, or production claims without explicit implementation scope.

## Non-Goals

This document does not add, implement, prove, or claim:

- Source acquisition implementation.
- Source acquisition review automation.
- Source acquisition validation code.
- Source acquisition validation tests.
- Source acquisition error taxonomy code.
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

- [Source Acquisition Boundary](source-acquisition-boundary.md)
- [Source Acquisition Sequencing Checklist](source-acquisition-sequencing-checklist.md)
- [Local Source Acquisition Contract Boundary](local-source-acquisition-contract-boundary.md)
- [Local Source Acquisition Examples Boundary](local-source-acquisition-examples-boundary.md)
- [Local Source Manifest Boundary](local-source-manifest-boundary.md)
- [Local Source Manifest Examples Boundary](local-source-manifest-examples-boundary.md)
- [Source Manifest Adapter Handoff Boundary](source-manifest-adapter-handoff-boundary.md)
- [Source Manifest Adapter Handoff Examples Boundary](source-manifest-adapter-handoff-examples-boundary.md)
- [Source Acquisition Validation Boundary](source-acquisition-validation-boundary.md)
- [Source Acquisition Validation Examples Boundary](source-acquisition-validation-examples-boundary.md)
- [Source Acquisition Error Taxonomy Boundary](source-acquisition-error-taxonomy-boundary.md)
- [Source Acquisition Error Taxonomy Examples Boundary](source-acquisition-error-taxonomy-examples-boundary.md)
- [Source Adapter Error And Warning Handling](source-adapter-error-warning-handling.md)
- [Source Adapter Contract](source-adapter-contract.md)
- [Parser Handoff Boundary](parser-handoff-boundary.md)
- [Parser Contract Boundaries](parser-contract-boundaries.md)
- [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md)
