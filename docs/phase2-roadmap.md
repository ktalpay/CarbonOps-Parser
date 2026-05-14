# Phase 2 Roadmap And Execution Boundary

## Executive Summary

Phase 2 starts from the accepted Phase 1 production readiness checkpoint and
turns the repository from a local-only, fail-closed, reviewable production
candidate into a broader implementation program. The priority is controlled
expansion: source onboarding, parser fidelity, data quality validation,
PostgreSQL runtime hardening, operational packaging, and release-gate coverage
must advance through small tasks with explicit planning, implementation,
Python/.NET parity review, and production-readiness review stages.

Phase 2 does not relax the Phase 1 safety posture. Runtime writes, live source
execution, scheduler behavior, credentials, destructive database operations,
and production correctness claims remain disabled or out of scope until a
separately reviewed task explicitly enables them.

## Confirmed Phase 1 Baseline And Assumptions

Phase 2 assumes the Phase 1 baseline recorded by the final production
readiness review:

- Python source acquisition, parser execution, normalization, persistence
  handoff, orchestration, service-host, diagnostics, and local validation
  boundaries are ready for the Phase 1 contract and operator release.
- .NET contract records and focused production-safety tests are ready for
  Phase 1 parity release.
- PostgreSQL behavior is fail-closed by default. Schema readiness and preview
  paths exist, but production database writes remain explicitly gated.
- Source acquisition supports local and dry-run operation. Live source
  availability, upstream variability, authentication, retry/rate-limit
  behavior, and scheduling are not proven by the default gate.
- Parser, normalization, and persistence paths are validated against
  deterministic local fixtures and contract handoffs. They do not claim
  complete source correctness or carbon-accounting correctness.
- Operational diagnostics redact credential-shaped values and expose run
  identity and failure context, but metrics, traces, alerts, dashboards, and
  centralized log ingestion remain future work.
- Default validation remains local-only and non-destructive. Full Python tests,
  full .NET tests, full public-safety scan, opt-in PostgreSQL integration, and
  live source checks are not default release requirements until separately
  promoted.

Any task that depends on a stronger assumption must first add a planning or
review task that proves and documents the new baseline.

## Phase 2 Workstreams And Sequencing

Phase 2 work should proceed through the following workstreams. Workstreams may
overlap only when their tasks do not change the same public contracts or
runtime behavior.

| Sequence | Workstream | Primary outcome | Required gate before next stage |
| --- | --- | --- | --- |
| 1 | Planning and scope confirmation | Convert roadmap items into small task tickets with explicit non-goals and validation. | Review confirms no runtime behavior change in planning-only tasks. |
| 2 | Source onboarding readiness | Define source selection criteria, fixture capture rules, source metadata expectations, and local-only onboarding checks. | Source onboarding review confirms no live calls or parser claims unless explicitly scoped. |
| 3 | Data quality and validation | Extend deterministic validation rules, issue taxonomy, fixture expectations, and reviewable quality summaries. | Python and .NET contracts agree on status, issue, and summary semantics where shared. |
| 4 | Parser/runtime hardening | Improve parser fidelity, acquisition resilience, runtime handoffs, and failure reporting in narrow source-specific slices. | Focused tests and parity review pass for each changed contract or shared expectation. |
| 5 | PostgreSQL runtime hardening | Promote disabled/preview persistence toward opt-in execution with transaction, conflict, migration, rollback, and recovery boundaries. | Integration remains opt-in until production-readiness review promotes it. |
| 6 | Operational packaging and scheduling | Define service packaging, process supervision, health probes, scheduler identity, leases, cancellation, retry/backoff, replay, and dead-letter behavior. | Review confirms non-destructive defaults and no production credential coupling. |
| 7 | Release-gate expansion | Promote broader Python, .NET, public-safety, integration, and production RC checks into stable default gates. | Gate promotion review proves checks are deterministic and local-safe by default. |
| 8 | Production-readiness review | Consolidate evidence, accepted risks, operator rules, and release recommendation for Phase 2 slices. | Release candidate remains blocked until review signs off on the exact slice. |

The first practical implementation sequence is:

1. Create planning tickets for source onboarding, data quality, parser
   hardening, PostgreSQL runtime execution, operations packaging, and release
   gate promotion.
2. Add a source onboarding readiness document and fixture policy before any new
   source parser or live source behavior.
3. Add deterministic validation/quality contracts and parity expectations for
   shared status and issue semantics.
4. Implement one narrow parser/source hardening slice using local fixtures only.
5. Run a parity review for the changed Python and .NET contracts.
6. Run a production-readiness review before enabling any live execution,
   scheduler behavior, or database write path.

## Source Onboarding Expansion Strategy

Source onboarding must be evidence-led and fixture-first:

- Start with source selection criteria: source family, document format,
  licensing/public availability, update cadence, expected stability,
  provenance fields, and known variability.
- Add local deterministic fixtures before adding runtime source code.
- Document source identity, source document versioning, checksum expectations,
  parser input mapping, and normalization handoff fields.
- Keep source discovery/download execution separate from parser execution and
  persistence.
- Add one source or one source-family slice per task. Do not bundle unrelated
  source families in the same implementation task.
- Treat live endpoints as opt-in validation only after a planning task defines
  network, retry, timeout, rate-limit, authentication, redaction, and operator
  controls.

Source onboarding tasks must avoid production claims. A source can be marked
implemented for a fixture/local path without claiming live-source correctness,
complete upstream coverage, or carbon-accounting correctness.

## Data Quality And Validation Strategy

Phase 2 data quality work should make validation outcomes reviewable before
making them operationally decisive:

- Define required provenance, identity, version, checksum, timestamp, parser,
  and traceability fields for every source-family slice.
- Separate structural validation, parser-readiness validation, normalization
  validation, persistence-readiness validation, and production-readiness
  validation.
- Use deterministic fixtures for accepted rows, malformed rows, empty inputs,
  unsupported formats, duplicate identities, missing metadata, and warning-only
  cases.
- Preserve structured issue severity, issue code, field/path, source document,
  and run correlation fields.
- Add summary outputs that operators and reviewers can compare without reading
  raw records.
- Promote validation from warning to blocking only through a task that updates
  tests, docs, and parity expectations.

Validation must not introduce network calls, database writes, environment
credential loading, or scheduler behavior unless those behaviors are the
explicit subject of the task.

## Parser And Runtime Hardening Strategy

Parser and runtime hardening should advance through narrow, reversible slices:

- Harden one source family, adapter, parser, or runtime boundary at a time.
- Prefer already-loaded content and fixture-driven tests before downloader or
  scheduler integration.
- Keep acquisition, parsing, normalization, persistence, and orchestration
  contracts independently reviewable.
- Preserve explicit unsupported and not-ready statuses instead of raising
  ambiguous runtime failures.
- Add retry, timeout, cancellation, replay, and dead-letter semantics only
  behind documented operational boundaries.
- Preserve fail-closed defaults for database execution and production runtime
  modes.

Any task that changes runtime behavior must include focused tests and a
documentation update describing the before/after boundary.

## Python/.NET Parity Expectations

Parity is required for shared contracts, public statuses, serialized field
names, issue semantics, run identity, source-family identity, and operational
diagnostics. Phase 2 tasks must identify one of these parity modes:

- `no-parity-impact`: Documentation-only or Python-internal work with no
  shared contract change.
- `parity-planning`: Planning or review task that defines a future shared
  contract expectation.
- `python-first-with-parity-follow-up`: Narrow implementation allowed only when
  the task creates or references a follow-up parity review.
- `lockstep-parity`: Python and .NET contract/test updates happen in the same
  task because serialized behavior or public contract shape changes.
- `parity-review`: Review-only task that compares Python, .NET, docs, and
  fixtures without adding runtime behavior.

Parity reviews must check wire names, enum/status values, required and optional
fields, validation issue semantics, fixture expectations, and documentation
links. They must not approve runtime enablement unless the task explicitly
includes production-readiness review.

## Operational Safety And Non-Destructive Execution Rules

Phase 2 tasks must preserve these rules unless a separately approved task
changes them:

- No PR merges, PR approvals, issue closures, branch deletion, or worktree
  deletion from implementation tasks.
- No production credentials, raw connection strings, secrets, or private source
  data in repository files, examples, logs, docs, fixtures, or tests.
- No live source endpoint calls by default.
- No database operations by default. Integration checks must remain opt-in and
  use externally supplied test configuration.
- No destructive database commands, migrations, rollback operations, table
  drops, data deletion, or production writes without explicit production
  readiness approval.
- No scheduler, downloader, parser, normalizer, persistence, or service-host
  coupling unless the task explicitly requests it.
- No generated artifacts unless the task explicitly requests and reviews them.
- No production, compliance, legal, or carbon-accounting correctness claims.
- Keep examples deterministic, local-only, and reviewable unless the task
  explicitly scopes an opt-in integration path.

## Explicit Out Of Scope

The following are outside PH-001 and outside default Phase 2 execution unless a
future task explicitly scopes them:

- Implementing Phase 2 runtime code in this roadmap task.
- Adding new source parsers or source-specific ingestion in this roadmap task.
- Adding production credentials, secret-store integration, or raw connection
  string handling.
- Calling live source endpoints or proving live source availability.
- Executing database operations, migrations, DDL, DML, rollback, or cleanup.
- Enabling production database writes.
- Adding scheduler, distributed lock, queue, cron, replay, or dead-letter
  runtime behavior.
- Publishing production daemon or worker-service packaging.
- Claiming complete source coverage, carbon-accounting correctness, compliance
  readiness, legal correctness, or production data quality correctness.
- Changing Phase 1 production behavior, release candidate assumptions, or
  operator safety rules.

## Initial Phase 2 Backlog Proposal

The first backlog should separate planning, implementation, parity review, and
production-readiness review:

| Proposed task | Type | Purpose | Dependencies |
| --- | --- | --- | --- |
| PH-002 Source onboarding readiness plan | Planning | Define source selection, fixture capture, metadata, live-call controls, and review gates. | PH-001 |
| PH-003 Data quality validation plan | Planning | Define validation layers, issue taxonomy expansion, fixture matrix, and summary expectations. | PH-001 |
| PH-004 Parser/runtime hardening plan | Planning | Define first parser/source hardening slice and runtime failure semantics. | PH-001 |
| PH-005 Python/.NET parity review protocol | Review | Define reusable parity checklist for Phase 2 shared contracts and fixtures. | PH-001 |
| PH-006 Source onboarding fixture policy | Implementation | Add docs/tests for deterministic fixture requirements without adding live ingestion. | PH-002, PH-005 |
| PH-007 First source-family hardening slice | Implementation | Improve one existing source-family parser or acquisition boundary using local fixtures. | PH-003, PH-004, PH-006 |
| PH-008 First Phase 2 parity review | Review | Compare changed Python/.NET contracts, docs, and fixtures after PH-007. | PH-005, PH-007 |
| PH-009 PostgreSQL runtime execution hardening plan | Planning | Define opt-in execution, transaction, conflict, migration, rollback, and recovery boundaries. | PH-001 |
| PH-010 Operational packaging and scheduling plan | Planning | Define worker packaging, health probes, scheduler identity, leases, cancellation, retry, and replay boundaries. | PH-001 |
| PH-011 Release-gate promotion plan | Planning | Define how full Python, .NET, public-safety, integration, and RC checks become stable default gates. | PH-001 |
| PH-012 Phase 2 production-readiness review | Review | Consolidate validation evidence, accepted risks, and release recommendation for the first Phase 2 slice. | PH-008, PH-009, PH-010, PH-011 as applicable |

Task identifiers are proposals, not claims that the tasks already exist.

## Risk Register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Phase 2 implementation disturbs Phase 1 release assumptions. | Regression in accepted production candidate behavior. | Require small tasks, focused tests, docs updates, parity review, and production-readiness review for runtime changes. |
| Source onboarding expands faster than fixture and validation evidence. | Unsupported correctness claims or brittle parser behavior. | Require fixture-first onboarding, explicit source selection criteria, and local-only validation before live behavior. |
| Python and .NET contracts drift. | Broken consumers or inconsistent operational semantics. | Assign parity mode per task and run parity reviews for shared status, issue, and wire-name changes. |
| PostgreSQL execution is enabled before transaction/recovery rules are mature. | Data loss, duplicate persistence, or unsafe operational behavior. | Keep writes fail-closed until opt-in execution, transaction, conflict, migration, rollback, and recovery boundaries are reviewed. |
| Release gates become slow or flaky. | Teams bypass validation or lose confidence in release evidence. | Promote only deterministic checks into default gates; keep integration/live checks explicitly opt-in until stable. |
| Operational packaging couples scheduler, downloader, parser, and persistence too early. | Hard-to-review runtime failures and larger blast radius. | Define packaging and scheduling boundaries before implementation; keep coupling task-scoped. |
| Validation summaries hide row-level issues. | Reviewers miss parser or data quality regressions. | Preserve structured issue details and fixture-level assertions alongside summaries. |
| Documentation and implementation diverge. | Review decisions rely on stale boundaries. | Require docs/index updates and focused tests for changed public behavior. |

## Dependency Map

- PH-001 is the root Phase 2 roadmap and execution-boundary task.
- PH-002, PH-003, and PH-004 are unblocked by PH-001 and should remain
  planning-first.
- Source onboarding implementation depends on source onboarding planning,
  fixture policy, and parity protocol.
- Parser/runtime hardening depends on data quality expectations and source
  onboarding readiness for the affected source family.
- PostgreSQL runtime execution depends on a separate hardening plan and must
  remain independent of source onboarding until opt-in execution is reviewed.
- Operational packaging depends on service-host and orchestration boundaries,
  but must not enable scheduler/runtime coupling without its own task.
- Release-gate promotion depends on deterministic checks and should not depend
  on live endpoints or production databases by default.
- Production-readiness review depends on implementation evidence, parity review
  results, validation evidence, and updated risk acceptance.

## Review Boundary

This document is a planning artifact. It does not implement Phase 2 runtime
code, add source parsers, change production configuration, enable live calls,
execute database operations, or change Phase 1 production behavior.

Task-ID: PH-001
Task-Issue: #558
