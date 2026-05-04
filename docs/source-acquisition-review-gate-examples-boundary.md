# Source Acquisition Review Gate Examples Boundary

This document defines what future source acquisition review gate examples may and may not demonstrate.

It is documentation-only. It adds no Python code, .NET code, tests, fixtures, example code, PR automation, CI changes, GitHub Actions changes, code owners changes, branch protection changes, validation code, error taxonomy code, validation result objects, runtime error handling, retry/cancel/scheduler behavior, incident/alerting behavior, manifest model, adapter behavior, parser behavior, normalization behavior, local file reading, source acquisition model code, source manifest code, real source data, real source URLs, remote behavior, credentials/secrets handling, config loading, DB/persistence/cache behavior, deployment behavior, unit conversion, or factor correctness logic.

## Purpose

Future review gate examples may show how a reviewer could reason about artificial source acquisition task scenarios before accepting implementation-heavy work.

The examples should make review expectations easier to understand without turning the review gate into automation, CI policy, runtime behavior, or a claim that the repository is ready for production use.

## Allowed Future Example Scope

Future examples may include:

- Artificial PR review scenario examples.
- Documentation-only review checklist examples.
- Mergeable decision examples for narrow documentation-only changes.
- Scope reduction decision examples for oversized changes.
- Forbidden-scope removal decision examples for changes that include disallowed data or behavior.
- Sequencing split decision examples for changes that mix boundary docs, examples, tests, contracts/models, and implementation.
- Blocked decision examples for changes that require an explicit implementation task first.
- Artificial examples of boundary alignment checks.
- Artificial examples of validation command review.
- Human-readable review notes that do not make real source claims.

Allowed examples should remain synthetic, deterministic, and review-oriented. They may describe reviewer reasoning, but they must not enforce repository policy or introduce executable checks.

## Disallowed Future Example Scope

Future examples must not include or imply:

- PR automation implementation.
- CI workflow changes.
- GitHub Actions changes.
- Code owners changes.
- Branch protection changes.
- Real PR policy enforcement.
- Runtime validation.
- Production readiness review claims.
- Compliance/legal review claims.
- Official carbon accounting review claims.
- Real source/provider examples.
- Real source data.
- Real source URLs.
- Remote behavior.
- Credentials/secrets handling.
- Credential/config handling.
- Config loading.
- DB/persistence/cache behavior.
- Scheduler/retry/cancel behavior.
- Runtime incident/alerting behavior.
- Adapter runtime behavior.
- Parser runtime behavior.
- Normalization runtime behavior.
- Unit conversion behavior.
- Factor correctness logic.
- Source adapter correctness claims.
- Parser correctness claims.
- Normalization correctness claims.

If a future task needs any of these areas, it should be split into an explicitly scoped task with tests and review gates that match the behavior being added.

## Boundary Between Examples And Policy

Review gate examples may illustrate how a human reviewer could apply the review categories from [Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md).

They must not become binding policy, automated enforcement, CI configuration, required branch protection, or code ownership rules. Any future repository policy or automation should be introduced as a separate task with explicit scope and review.

## Boundary Between Examples And PR Automation

Review gate examples may show sample review notes such as:

- A documentation-only change is mergeable when it stays within documented boundaries.
- A task requires scope reduction when it combines unrelated source acquisition and parser behavior.
- A task requires forbidden-scope removal when it adds real source data or real URLs.
- A task requires sequencing split when it combines boundary docs with implementation.
- A task is blocked until an explicit implementation task when it attempts runtime behavior without scope and tests.

These examples are illustrative only. They do not add bots, scripts, labels, webhooks, PR templates, CI jobs, GitHub Actions, branch protection, or automated status checks.

## Boundary Between Examples And CI Checks

Future examples may mention the validation commands that reviewers should look for:

```bash
git diff --check
python -m pytest tests/test_documentation_map_references.py
python -m pytest tests/test_task_queue_consistency.py
python -m pytest
python scripts/check_public_safety.py
```

Mentioning these commands in an example does not add CI behavior, workflow files, required checks, or automated enforcement.

## Boundary Between Examples And Implementation Tasks

Review gate examples may describe why a task should be split before implementation.

They must not implement source acquisition, validation, error taxonomy, manifest models, adapter behavior, parser behavior, normalization behavior, persistence, scheduler/retry/cancel behavior, credentials/config handling, remote behavior, local file reading, or deployment behavior.

Implementation behavior belongs in future narrow tasks with explicit scope, tests, and review gates.

## Relationship To Review Gate Boundary

[Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md) defines the review gate itself: covered task types, required review checks, boundary alignment checks, validation commands, and decision categories.

This document only defines the boundary for future examples of that gate. It does not expand the gate, automate it, or change the review categories.

## Relationship To Validation And Error Taxonomy Documents

[Source Acquisition Validation Boundary](source-acquisition-validation-boundary.md), [Source Acquisition Validation Examples Boundary](source-acquisition-validation-examples-boundary.md), [Source Acquisition Error Taxonomy Boundary](source-acquisition-error-taxonomy-boundary.md), and [Source Acquisition Error Taxonomy Examples Boundary](source-acquisition-error-taxonomy-examples-boundary.md) define the validation and taxonomy tracks.

Review gate examples may reference those documents as boundaries to check against. They must not add validation code, validation tests, validation result objects, error taxonomy code, runtime error handling, or runtime incident behavior.

## Relationship To Manifest And Adapter Handoff Documents

[Source Manifest Adapter Handoff Boundary](source-manifest-adapter-handoff-boundary.md), [Source Manifest Adapter Handoff Examples Boundary](source-manifest-adapter-handoff-examples-boundary.md), [Local Source Manifest Boundary](local-source-manifest-boundary.md), and [Local Source Manifest Examples Boundary](local-source-manifest-examples-boundary.md) define the manifest and adapter-facing handoff boundaries.

Review gate examples may show artificial boundary alignment checks against those documents. They must not add manifest models, source manifest code, adapter selection logic, adapter dispatch behavior, adapter runtime behavior, or source adapter correctness claims.

## Relationship To Local Source Acquisition Documents

[Local Source Acquisition Contract Boundary](local-source-acquisition-contract-boundary.md), [Local Source Acquisition Examples Boundary](local-source-acquisition-examples-boundary.md), [Source Acquisition Boundary](source-acquisition-boundary.md), and [Source Acquisition Sequencing Checklist](source-acquisition-sequencing-checklist.md) define the local and general source acquisition boundaries.

Review gate examples may use those documents to illustrate scope checks. They must not add local file reading, arbitrary user file ingestion, real directory scanning, real source acquisition, remote acquisition, source URL cataloging, credential/config handling, DB/persistence/cache behavior, or scheduler/retry/cancel behavior.

## Relationship To Parser And Normalization Handoff

Existing parser and normalization handoff documents, including [Parser Handoff Boundary](parser-handoff-boundary.md), [Parser Contract Boundaries](parser-contract-boundaries.md), and [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md), describe downstream boundaries.

Review gate examples may cite these documents when showing why acquisition review should not imply parser behavior, parser-to-normalization integration behavior, normalization behavior, unit conversion, factor correctness, or carbon accounting correctness.

## Review Checklist For Future Review Gate Example Tasks

Future review gate example tasks should confirm:

- The task is documentation-only.
- The examples are artificial and review-oriented.
- No implementation, fixtures, tests, PR automation, or CI changes are added.
- No GitHub Actions, code owners, branch protection, or real policy enforcement changes are added.
- No real source/provider examples are added.
- No real source data or real URLs are added.
- No remote behavior is added.
- No credentials/secrets handling or config loading is added.
- No DB/persistence/cache behavior is added.
- No scheduler/retry/cancel behavior is added.
- No runtime incident/alerting behavior is added.
- No adapter/parser/normalization runtime behavior is added.
- No unit conversion or factor correctness logic is added.
- No production readiness, compliance/legal correctness, official carbon accounting correctness, source correctness, parser correctness, normalization correctness, unit conversion correctness, or factor correctness claims are made.
- Related documents are linked from the documentation map when the existing pattern requires it.
- The task queue is updated without restructuring unrelated entries.

## Non-Goals

This document does not add, implement, prove, or claim:

- Review gate example code.
- Review gate fixtures.
- Review gate tests.
- PR automation.
- CI workflow changes.
- GitHub Actions changes.
- Code owners changes.
- Branch protection changes.
- Automated policy enforcement.
- Runtime validation.
- Validation code.
- Validation tests.
- Validation result objects.
- Error taxonomy code.
- Runtime error handling.
- Runtime incident behavior.
- Alerting behavior.
- Retry/cancel/scheduler behavior.
- Manifest model implementation.
- Source manifest code.
- Source acquisition model code.
- Source acquisition implementation.
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
- Real source/provider examples.
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

- [Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md)
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
