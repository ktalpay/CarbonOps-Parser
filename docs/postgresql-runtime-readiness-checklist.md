# PostgreSQL Runtime Readiness Checklist

This document defines the go/no-go checklist before any future task enables real
PostgreSQL runtime execution.

It is checklist documentation only. It does not create a PostgreSQL connection,
create a cursor, run SQL, write records, start a transaction, finish a
transaction, roll back a transaction, create tables, run migrations, load
environment variables, load configuration files, load credentials, perform HTTP
or network calls, schedule work, or claim production persistence readiness.

## Current Boundary

Runtime PostgreSQL execution remains disabled. The current implementation
supports planning, preview, and diagnostic metadata only:

- `PostgreSQLPersistenceRepository.persist()` remains unsupported/no-execution.
- The insert SQL builder produces deterministic parameterized metadata only.
- The persistence preview and local dry-run preview are deterministic and
  no-execution.
- The disabled runtime execution adapter returns no-execution metadata.
- The repository disabled execution preview composes diagnostics only.
- The runtime execution gate is disabled by default and does not enable
  persistence when requested.

## Go/No-Go Criteria

A future real runtime execution task is blocked until all of these are true:

- Dependency boundary verified: `psycopg` is the approved PostgreSQL driver and
  no competing driver or ORM is introduced for Phase 1.
- `psycopg` imports isolated: pure preview/domain modules, local dry-run code,
  insert builder, schema descriptor, and repository skeleton remain driver-free.
- Caller-provided session contract ready: future execution consumes a
  caller-provided session boundary and does not create implicit connections.
- psycopg session adapter skeleton isolated: the dedicated skeleton remains the
  only psycopg-specific boundary until a scoped runtime adapter task.
- Transaction policy agreed: single-batch, caller-provided-session,
  no-partial-success policy is explicitly accepted or replaced by a reviewed
  policy.
- Idempotency/conflict strategy agreed: Phase 1 duplicate handling is explicit
  and not ambiguous.
- Runtime execution gate default disabled: default gate decision remains
  disabled/no-execution.
- Repository disabled preview available: repository-level diagnostics can be
  reviewed without runtime persistence.
- Disabled runtime execution result available: future execution metadata can be
  inspected without connecting or running SQL.
- Public safety checks pass without weakening rules.
- Integration test opt-in plan exists and normal test runs do not touch
  PostgreSQL.
- No credentials, config files, or environment variables are loaded by library
  code.
- No secrets appear in docs, tests, logs, fixtures, examples, exceptions, or
  result metadata.
- No production persistence readiness claim is made.
- Repository `persist()` remains unsupported until an explicit future runtime
  task changes it with tests and safety review.

## Must Not Proceed If

Do not begin a real execution task if any of these are true:

- DB credentials are not isolated.
- Schema, table creation, or migration lifecycle ownership is unclear.
- PostgreSQL integration tests are not opt-in and disabled by default.
- Duplicate or conflict policy is ambiguous.
- Transaction rollback policy is ambiguous.
- The public safety script would need weakening to pass.
- Repository `persist()` would imply success without integration and rollback
  tests.
- Real source parser correctness is assumed but unverified.
- Local dry-run default behavior would change.
- Preview output would become nondeterministic.

## Future Task Sequence

Suggested follow-up sequence after this checklist:

1. CO-103A: opt-in PostgreSQL integration test environment and runbook, with no
   default execution.
2. CO-103B: runtime session adapter execution smoke behind an explicit test
   fixture, opt-in only.
3. CO-103C: repository execution adapter implementation behind the runtime
   execution gate, opt-in only.
4. CO-103D: transaction rollback integration tests.
5. CO-103E: conflict and idempotency runtime behavior tests.
6. CO-103F: CLI/config ownership for local PostgreSQL validation if needed.

Each task should remain separately scoped, reviewed, and validated. None should
silently convert default repository behavior into runtime persistence.

## First Real Execution Task Acceptance Criteria

The first task that adds real PostgreSQL execution must satisfy all of these:

- It is opt-in.
- It uses a caller-provided session.
- It does not read environment variables or config files in library code.
- It does not run in the default test suite.
- It reports sanitized errors.
- It proves secrets do not appear in logs, docs, fixtures, exceptions, or result
  metadata.
- It proves rollback behavior or explicitly defers rollback to a named
  follow-up before any broad execution path exists.
- It shows the exact PostgreSQL table and schema expectation.
- It does not change local dry-run default behavior.
- It keeps preview behavior deterministic.
- It keeps `PostgreSQLPersistenceRepository.persist()` unsupported unless the
  task explicitly changes repository runtime behavior with gate checks and
  opt-in tests.

## Risk Register

- Credential leakage: require redacted metadata, no committed credentials, and
  no secret values in logs or exceptions.
- Accidental default execution: keep the runtime execution gate disabled by
  default and require explicit opt-in.
- Partial writes: start with one batch transaction policy and deterministic
  rollback reporting.
- Schema drift: compare schema descriptor, DDL review text, and insert builder
  columns before runtime execution.
- Duplicate inserts: require an approved conflict policy and explicit counts.
- Placeholder incompatibility: verify psycopg placeholder behavior against
  insert-builder output before runtime execution.
- Test DB pollution: isolate opt-in test databases and document cleanup.
- Production misuse: avoid default DB targets and production-readiness claims.
- Dependency footprint: keep database imports inside runtime adapter boundaries.
- Unclear operational ownership: document who owns migrations, config, rollback,
  logging, and audit metadata.

## Related Documents

- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Runtime Execution Gate Boundary](postgresql-runtime-execution-gate-boundary.md)
- [PostgreSQL Runtime Persistence Implementation Plan](postgresql-runtime-persistence-implementation-plan.md)
- [PostgreSQL Driver Dependency Decision](postgresql-driver-dependency-decision.md)
- [PostgreSQL Connection Session Contract Boundary](postgresql-connection-session-contract-boundary.md)
- [PostgreSQL psycopg Session Adapter Boundary](postgresql-psycopg-session-adapter-boundary.md)
- [PostgreSQL Disabled Runtime Execution Adapter Boundary](postgresql-disabled-runtime-execution-adapter-boundary.md)
- [PostgreSQL Repository Disabled Execution Preview Boundary](postgresql-repository-disabled-execution-preview-boundary.md)
- [PostgreSQL Integration Test Boundary](postgresql-integration-test-boundary.md)
