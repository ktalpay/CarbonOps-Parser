# Phase 2 Runtime And Source Expansion Review Gate

Task-ID: PH-004
Task-Issue: #561

## Purpose

This document defines the Phase 2 review gate that must pass before any newly
onboarded source family is considered production-ready. It turns the Phase 2
roadmap into concrete acceptance gates for source onboarding, data quality,
Python/.NET parity, runtime safety, persistence and idempotency, observability,
and release readiness.

This is a review-only gate. It does not implement runtime code, add parsers,
call live endpoints, execute database operations, add credentials, or certify
source, legal, compliance, carbon-accounting, unit-conversion, or factor
correctness.

## When To Use This Gate

Use this gate for any Phase 2 source-family readiness review that proposes one
of these outcomes:

- Marking a new source family production-ready.
- Marking a source family production-ready with accepted risks.
- Blocking a source family from production readiness until follow-up work is
  complete.
- Promoting source onboarding, parser/runtime hardening, persistence,
  observability, or release checks from local review evidence to production
  readiness evidence.

The review must name the exact source family, implementation slice, branch or
PR, fixture set, contracts, tests, and docs under review. Readiness applies only
to that named slice.

## Required Review Inputs

A Phase 2 readiness review must include:

- Source-family identity, source keys, and supported document or artifact
  types.
- Scope statement that separates source acquisition, parsing, normalization,
  persistence, scheduler/service behavior, and release packaging.
- Links to source onboarding, parser, normalization, persistence, runtime,
  diagnostic, and release documents changed by the slice.
- Python and .NET contract/test evidence, or a documented reason why the slice
  has `no-parity-impact`.
- Deterministic local fixtures and expected outputs used for review.
- Validation command results, including CI checks that are required for the
  slice.
- Known limitations, accepted risks, and deferred work.
- Explicit recommendation: production-ready, production-ready with accepted
  risks, or blocked.

## Source Onboarding Review Checklist

Before a source family can be considered production-ready, reviewers must
confirm:

- Source-family identity is stable and uses the same canonical key across
  acquisition, parser input, parser output, normalization, persistence
  readiness, diagnostics, docs, and tests.
- Supported source documents, versions, formats, artifact types, and update
  cadence are documented.
- Public availability and licensing assumptions are documented without adding
  confidential, private, or copied source data.
- Local deterministic fixtures exist for the supported artifacts under review.
- Fixture provenance, checksum or hash expectations, source document version,
  reporting year or effective period, and row/document identity are captured
  where the contracts require them.
- Unsupported formats, missing files, malformed inputs, empty inputs, duplicate
  identities, and warning-only cases have deterministic review evidence.
- Live endpoint use is either out of scope or explicitly reviewed as opt-in
  behavior with timeout, retry, rate-limit, authentication, redaction, and
  operator controls.
- Source discovery/download remains separate from parser execution,
  normalization, persistence, scheduling, and database execution unless the
  reviewed task explicitly scopes the coupling.
- No production source coverage, source-owner correctness, legal correctness,
  compliance correctness, carbon-accounting correctness, unit-conversion
  correctness, or factor correctness claim is made.

## Data Quality Validation Checklist

Reviewers must confirm that validation evidence is structured, deterministic,
and reviewable:

- Required provenance fields are present for records, documents, artifacts, and
  run summaries.
- Source identity, document identity, parser identity, version/checksum
  metadata, row identity, and traceability fields are preserved from parser
  output through normalization and persistence readiness where applicable.
- Structural validation, parser-readiness validation, normalization validation,
  persistence-readiness validation, and production-readiness validation are
  distinguishable.
- Validation issues carry stable severity, code, message, field/path, source
  document, row/document identity, stage, and run correlation fields where the
  relevant contract supports them.
- Summary outputs expose accepted, rejected, warning, skipped, persisted, and
  failed counts without hiding row-level or document-level issues needed for
  review.
- Fixture expectations cover accepted records, rejected records, partial
  success, warning-only records, duplicate identities, missing required fields,
  unsupported values, and empty inputs.
- Warning-to-blocking promotion is explicitly documented and tested; it is not
  inferred from wording alone.
- Data quality checks do not require network access, production credentials,
  database writes, scheduler behavior, or live source availability by default.

## Python/.NET Parity Checklist

For every shared source-family readiness slice, reviewers must assign and
verify a parity mode:

- `no-parity-impact`: no shared contract, serialized payload, status, fixture,
  diagnostic, or public behavior changed.
- `parity-planning`: the task defines future parity expectations but changes no
  runtime behavior.
- `python-first-with-parity-follow-up`: a Python change is accepted only with a
  named follow-up parity review for affected shared behavior.
- `lockstep-parity`: Python and .NET contracts, fixtures, tests, and docs move
  together in the same slice.
- `parity-review`: the task compares existing Python and .NET behavior without
  adding runtime behavior.

When parity applies, reviewers must confirm:

- Source-family keys, parser keys, status values, enum/wire names, issue codes,
  severities, stage names, and diagnostic event names are aligned or explicitly
  documented as accepted drift.
- Required and optional serialized fields match the shared contract
  expectations.
- Null, empty, default, duplicate, and unsupported cases have equivalent
  observable behavior.
- Python and .NET tests use equivalent fixture expectations or a shared parity
  fixture where available.
- Contract docs identify which behavior is public, internal, deferred, or
  implementation-specific.
- Coarser behavior in one language is accepted only when structured details
  still preserve reviewable failure stage, code, and source-family context.
- No source family is marked production-ready when shared public behavior has an
  unexplained parity mismatch.

## Runtime Safety Checklist

Reviewers must confirm that Phase 2 runtime behavior remains bounded and
operator-safe:

- Default execution is local, deterministic, non-destructive, and fail-closed.
- Live network calls are disabled by default or require explicit opt-in,
  configured timeout, retry/backoff policy, rate-limit handling, authentication
  boundary, redaction boundary, and operator-visible failure reporting.
- Database execution is disabled by default unless a separate reviewed task
  explicitly promotes opt-in runtime writes.
- Runtime configuration does not load production credentials, raw connection
  strings, secret files, or environment-derived secrets unless the reviewed task
  explicitly scopes and tests that behavior.
- Parser, downloader, scheduler, database, and service-host coupling is limited
  to the reviewed slice.
- Unsupported, not-ready, skipped, warning, failed, and completed states are
  deterministic and structured.
- Cancellation, retry, replay, and dead-letter behavior are either out of scope
  or explicitly reviewed with bounded semantics and idempotency evidence.
- Failures do not expose credential-shaped values, private paths, raw source
  payloads, or confidential material in logs, exceptions, diagnostics, fixtures,
  or docs.
- Runtime changes preserve existing public APIs unless the task explicitly
  scopes an API change and includes migration notes.

## Persistence And Idempotency Checklist

Before a source family can be production-ready with persistence enabled,
reviewers must confirm:

- Persistence execution mode is explicit: disabled, preview-only, opt-in test,
  or production-enabled for the reviewed slice.
- Source document identity, source family, source key, artifact checksum/hash,
  parser version or mapping identity, row identity, and normalized record
  identity are stable enough for replay review.
- Duplicate input records, duplicate source documents, repeated runs, partial
  failures, and retry attempts have deterministic expected outcomes.
- Conflict handling is documented for insert, update, skip, reject, and
  warning-only paths.
- Transaction boundaries, rollback behavior, commit timing, and partial
  persistence summaries are reviewed for the exact execution mode.
- Persistence summaries distinguish attempted, accepted, rejected, skipped,
  persisted, duplicate, and failed counts.
- Idempotency expectations are tested against local deterministic fixtures or
  explicitly documented as a blocker.
- No destructive DDL, destructive DML, migration, rollback cleanup, table drop,
  data deletion, or production write behavior is introduced without a separate
  production-readiness review.

## Observability And Redaction Checklist

Safe diagnostics are required for production readiness. Reviewers must confirm:

- Diagnostic payloads include run identity, correlation identity, source family,
  source key, document or artifact identity, stage, status, issue code, severity,
  and counts needed for triage.
- Logs and diagnostics expose enough context to locate a failed source-family
  slice without exposing raw credentials, tokens, connection strings, private
  paths, confidential material, copied source payloads, or arbitrary raw
  exception payloads.
- Credential-shaped fields are redacted in Python and .NET diagnostic helpers
  where shared diagnostics apply.
- Safe checksums, document identifiers, artifact references, and parser/source
  metadata are used instead of raw payload dumps.
- Error messages distinguish operator action, unsupported source input,
  validation failure, parser failure, persistence failure, runtime block, and
  infrastructure failure where the reviewed contracts support those stages.
- Metrics, traces, alerts, dashboards, centralized log ingestion, retention,
  and SLOs are either reviewed with evidence or listed as limitations.
- Redaction tests or review evidence cover common secret-bearing fields such as
  password, token, secret, credential, DSN, connection string, URI, database
  URL, username, host, and application name where those values can appear in
  diagnostics.

## CI And Release Gate Expectations

A source-family readiness review must state which checks are required for the
slice and whether each check passed, failed, or was intentionally skipped.

Minimum local validation for documentation-only gate changes:

```bash
git diff --check
```

Minimum validation when Python package behavior, examples, fixtures, or tests
are affected:

```bash
python -m pytest
git diff --check
```

Release readiness reviews should also consider, when applicable:

- Focused Python tests for the changed source-family, parser, validation,
  normalization, persistence, or diagnostic behavior.
- Focused .NET tests for changed shared contracts or diagnostic behavior.
- Parity fixtures or parity-review evidence for shared wire names, statuses,
  issues, and summaries.
- Public-safety wording checks.
- Documentation index/map checks when docs are added or renamed.
- Opt-in integration tests only when the reviewed task explicitly scopes
  database or live endpoint behavior.
- CI stability evidence for checks proposed as release gates.

Generated artifacts must not be tracked unless the task explicitly requests and
reviews them.

## Decision Criteria

### Production-Ready

Use this decision only when all required checklists pass for the reviewed
source-family slice:

- Source onboarding evidence is complete for the supported formats and versions.
- Data quality validation is deterministic and covers accepted, rejected,
  partial, duplicate, empty, malformed, and warning-only cases.
- Python/.NET parity is satisfied or marked `no-parity-impact` with evidence.
- Runtime behavior is bounded, fail-closed by default, and operator-safe.
- Persistence and idempotency expectations are proven for the promoted
  execution mode.
- Diagnostics include safe correlation and redacted failure context.
- Required CI/release gates pass.
- Known limitations do not undermine the production claim for the exact slice.

### Production-Ready With Accepted Risks

Use this decision when the slice is safe to promote but has documented residual
risks that owners explicitly accept:

- Each accepted risk has an owner, impact, mitigation, review date or follow-up
  task, and reason it does not block the exact production slice.
- The risk does not involve unredacted secrets, confidential/private data,
  destructive database behavior, unexplained Python/.NET contract drift,
  missing idempotency for enabled writes, or unsupported production correctness
  claims.
- CI/release gates required for the slice still pass.
- Operators can detect and safely respond to the accepted risk through
  diagnostics, run summaries, rollback procedure, or documented disablement.

### Blocked

Use this decision when any blocking condition is present:

- Source-family identity, supported formats, fixtures, or provenance evidence
  are incomplete for the claimed production slice.
- Data quality validation is not deterministic or misses material failure cases.
- Python/.NET shared behavior has unexplained parity drift.
- Safe diagnostics are missing, ambiguous, or leak credential-shaped values,
  private data, copied source payloads, or raw sensitive exception context.
- Runtime behavior requires live endpoints, credentials, scheduler coupling, or
  database writes without explicit opt-in controls and review evidence.
- Persistence/idempotency evidence is missing for enabled write paths.
- Required tests or CI/release gates fail or are skipped without accepted risk
  approval.
- The review relies on production, legal, compliance, source-owner,
  carbon-accounting, unit-conversion, or factor correctness claims that are not
  explicitly scoped and proven.

## Review Output Template

Each Phase 2 readiness review should record:

- Reviewed source family and production slice.
- Reviewed files, fixtures, contracts, tests, docs, and CI runs.
- Checklist results by section.
- Python/.NET parity mode and findings.
- Diagnostics and redaction findings.
- Persistence/idempotency findings.
- Known limitations.
- Accepted risks, if any.
- Final decision: production-ready, production-ready with accepted risks, or
  blocked.
- Required follow-up tasks.

## Non-Goals

This gate does not add, implement, prove, or claim:

- Runtime code.
- Source parsers.
- Live endpoint access.
- Database operations.
- Production credentials or secret handling.
- Scheduler, queue, distributed lock, replay, or dead-letter behavior.
- Production source coverage.
- Legal, compliance, source-owner, carbon-accounting, unit-conversion, or factor
  correctness.
- Release approval beyond the exact reviewed slice.

## Related Documents

- [Phase 2 Roadmap And Execution Boundary](phase2-roadmap.md)
- [Review Readiness Checklist](review-readiness-checklist.md)
- [Source Acquisition Review Gate Boundary](source-acquisition-review-gate-boundary.md)
- [PostgreSQL Runtime Readiness Checklist](postgresql-runtime-readiness-checklist.md)
- [Final Phase 1 Production Readiness Review](final-phase1-production-readiness-review.md)
