# PostgreSQL Integration Test Container Strategy

This document defines the container strategy for future PostgreSQL integration
tests.

It is documentation and test-strategy guidance only. It does not create
PostgreSQL containers, connect to PostgreSQL, execute SQL, write records, start
transactions, roll back transactions, create tables, run migrations, load
environment variables in library code, load configuration files in library
code, load credentials, perform HTTP or network calls, schedule work, or claim
production persistence readiness.

## Purpose

Future PostgreSQL integration tests need a repeatable database target that is
isolated from production, staging, shared development, and developer-default
databases.

The approved direction is an ephemeral local or CI-owned PostgreSQL test
service. The service should be created for an explicitly opted-in test run,
used only by that run, and discarded after the run. It must not point at an
external production or staging database.

## Strategy

Future integration tests should use a containerized PostgreSQL service owned by
the test runner. Acceptable future implementations include:

- a local Docker or Podman container started by a documented manual runbook.
- a CI service container declared inside a scoped CI job.
- a future test harness wrapper that starts an ephemeral container only after
  explicit integration-test opt-in controls are present.

The container is a test fixture, not product runtime infrastructure. Repository
code must not start, stop, inspect, or depend on containers from normal library
paths.

The container lifecycle should be:

1. Confirm the explicit PostgreSQL integration-test marker and opt-in controls.
2. Start a PostgreSQL test container with an isolated database and role.
3. Wait for readiness using container health or a scoped connection check.
4. Run only the opted-in PostgreSQL integration tests.
5. Stop and remove the container or CI service after the run.

Default `python -m pytest` must skip PostgreSQL integration tests and must not
start a container.

## Opt-In Controls

Container-backed tests must continue to use the existing PostgreSQL integration
test boundary controls:

- marker name: `postgresql_integration`
- opt-in control name: `CARBONOPS_RUN_POSTGRESQL_INTEGRATION`
- test connection input name: `CARBONOPS_POSTGRESQL_TEST_DSN`

These names are external test-runner inputs only. Library code must not read
them implicitly. A future test harness may read them inside an explicitly
opted-in test path, but normal parser, persistence, and CLI behavior must remain
DB-free by default.

## Container Isolation Requirements

Container-backed PostgreSQL tests must satisfy these isolation rules:

- use a disposable container or CI service owned by the current test run.
- use a generated or local-only test database name.
- use a generated or local-only test role.
- bind only to loopback or CI-internal networking.
- avoid production, staging, shared development, customer, or private source
  data.
- avoid committed DSNs, passwords, tokens, or connection strings.
- avoid reusing long-lived volumes unless a future task documents a safe reset
  procedure.
- prefer discarding the whole container over running broad cleanup against a
  shared database target.

Any future cleanup must be visibly scoped to the disposable test database or
container volume. Cleanup must never target production, staging, shared
development, or unlabeled databases.

## Image And Version Policy

Future container-backed tests should pin a public PostgreSQL major version in
the test-runner configuration or runbook. The initial default should remain in
the currently supported PostgreSQL family used by the repository's manual smoke
documentation, unless a later task updates the runtime compatibility target.

The exact image tag is test infrastructure metadata. It must not imply
production database support, migration support, or runtime persistence
readiness.

## Schema And Data Policy

Container-backed tests may prepare schema only inside the disposable test
database and only when a future runtime task explicitly adds that setup. Until a
runtime task approves SQL execution, container strategy remains planning
documentation only.

Future schema setup must:

- use deterministic repository-owned schema fixtures or migrations approved by
  a dedicated task.
- run only after the explicit integration-test opt-in path is active.
- avoid source-specific ingestion data unless the task explicitly requests it.
- avoid confidential, customer, production, or private source data.
- keep test records minimal, deterministic, and local-only.

## CI Policy

CI must keep PostgreSQL integration tests isolated from the default validation
job. A future CI job may run container-backed tests only when it is explicitly
named and configured for PostgreSQL integration validation.

The default CI test job should continue to run without PostgreSQL, without
database credentials, without external services, and without container startup.

## Review Checklist

Reviewers should reject future PostgreSQL integration-test container changes if
they:

- make default `python -m pytest` require PostgreSQL or Docker.
- connect to production, staging, shared development, or implicit local
  databases.
- commit DSNs, passwords, tokens, or connection strings.
- add runtime database execution outside an explicitly approved runtime task.
- hide container startup inside product library code.
- run broad cleanup against a database that is not clearly disposable.
- claim production persistence readiness from container test coverage alone.

## Non-Goals

This strategy does not add:

- Docker Compose files.
- CI workflow files.
- Testcontainers or Docker SDK dependencies.
- PostgreSQL container startup code.
- Runtime PostgreSQL repository behavior.
- Database connections.
- SQL execution.
- Database writes.
- Migrations or table creation.
- External database configuration.
- Production credentials or production readiness claims.

## Related Documents

- [PostgreSQL Integration Test Boundary](postgresql-integration-test-boundary.md)
- [PostgreSQL Opt-In Integration Runbook](postgresql-opt-in-integration-runbook.md)
- [PostgreSQL Runtime Persistence Implementation Plan](postgresql-runtime-persistence-implementation-plan.md)
- [PostgreSQL Runtime Integration Boundary](postgresql-runtime-integration-boundary.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [Public Safety](public-safety.md)
