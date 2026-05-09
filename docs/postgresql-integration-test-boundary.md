# PostgreSQL Integration Test Boundary

This document defines the PostgreSQL integration test policy.

PostgreSQL integration tests are disabled by default. This boundary does not
connect to PostgreSQL, execute SQL, write records, run migrations, load config
files, load credentials, read environment variables, add database dependencies,
perform HTTP or network calls, or schedule work.

## Purpose

Future PostgreSQL repository tests need an explicit boundary so local and CI test
runs cannot accidentally target a database.

The persistence package exposes a passive helper:

- `POSTGRESQL_INTEGRATION_TEST_MARKER`
- `POSTGRESQL_INTEGRATION_TEST_SKIP_REASON`
- `PostgreSQLIntegrationTestBoundary`
- `create_postgresql_integration_test_boundary()`
- `should_skip_postgresql_integration_tests()`

The default boundary is disabled and returns a skip decision. It is metadata
only; it does not inspect the runtime environment.

## Opt-In Policy

Future PostgreSQL integration tests may be enabled only by explicit test-runner
wiring in a later task. That wiring must:

- require an explicit marker, option, or isolated test configuration.
- keep default `python -m pytest` runs skipped.
- avoid committed credentials, DSNs, passwords, or connection strings.
- target an isolated test database only.
- prove that no production or implicit local database target can be selected.
- keep SQL execution and write behavior scoped to a future runtime task.

This task does not add that runtime wiring. It provides only the marker name,
skip reason, and default-disabled boundary helper that future tests can consume.

Future container-backed PostgreSQL tests should follow the
[PostgreSQL Integration Test Container Strategy](postgresql-integration-test-container-strategy.md),
which keeps test databases ephemeral, local or CI-owned, and isolated from
production or staging targets.

## Default Behavior

`create_postgresql_integration_test_boundary()` returns:

- `enabled=False`
- marker name `postgresql_integration`
- a skip reason explaining that PostgreSQL integration tests are disabled by
  default

`should_skip_postgresql_integration_tests()` returns `True` unless a caller
passes an explicitly enabled boundary.

## Non-Goals

This boundary does not add:

- PostgreSQL repository runtime behavior.
- Database connections.
- Database writes.
- SQL execution.
- SQL generation.
- Table creation.
- Migrations.
- Database driver or ORM dependencies.
- Environment variable loading.
- Config file loading.
- Credential or secret loading.
- DSNs, passwords, or connection strings.
- HTTP or network behavior.
- Scheduler, retry, cancel, or background job behavior.

## Related Documents

- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Integration Test Container Strategy](postgresql-integration-test-container-strategy.md)
- [PostgreSQL Config Contract Boundary](postgresql-config-contract-boundary.md)
- [PostgreSQL Repository Skeleton Boundary](postgresql-repository-skeleton-boundary.md)
- [PostgreSQL Repository Implementation Planning Boundary](postgresql-repository-implementation-planning-boundary.md)
- [Persistence Repository Boundary](persistence-repository-boundary.md)
- [Public Safety](public-safety.md)
