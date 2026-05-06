# PostgreSQL Config Contract Boundary

This document defines the explicit PostgreSQL persistence options contract.

The contract is caller-provided only. It does not load environment variables,
read config files, read credentials, connect to PostgreSQL, add database
dependencies, generate SQL, execute SQL, create tables, run migrations, perform
HTTP or network calls, or schedule work.

## Purpose

`PostgreSQLPersistenceOptions` records the future connection-shaped values that a
runtime PostgreSQL repository may need after the safety gate is satisfied.

The options include:

- `host`
- `port`
- `database`
- `username`
- `password_set`
- `ssl_mode`
- `application_name`
- `connect_timeout_seconds`

The contract uses `password_set` as a marker instead of storing a password
value. This keeps object representation, string rendering, and public test
fixtures free of secret values.

## Validation

`validate_postgresql_persistence_options()` checks only option shape. It does not
attempt a connection or load missing values from the environment.

Validation reports structured issues for:

- missing `host`
- invalid `port`
- missing `database`
- missing `username`
- invalid `password_set` marker
- blank optional text fields when provided
- invalid `connect_timeout_seconds`

`password_set=False` is valid. Future credential requirements remain part of the
PostgreSQL implementation safety gate and explicit runtime configuration work.

## Repository Relationship

`PostgreSQLPersistenceRepository` may accept `PostgreSQLPersistenceOptions`, but
the skeleton still returns `unsupported` from `persist()`.

Providing options does not cause a database connection, SQL generation, SQL
execution, migrations, configuration loading, credential loading, or writes.

## Non-Goals

This boundary does not add:

- Environment variable loading.
- Config file loading.
- Credential or secret loading.
- Password storage.
- Database driver or ORM dependencies.
- Database connections.
- Database writes.
- SQL generation or execution.
- Table creation.
- Migrations.
- HTTP or network behavior.
- Scheduler, retry, cancel, or background job behavior.

## Related Documents

- [PostgreSQL Repository Skeleton Boundary](postgresql-repository-skeleton-boundary.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Repository Implementation Planning Boundary](postgresql-repository-implementation-planning-boundary.md)
- [Persistence Repository Boundary](persistence-repository-boundary.md)
- [PostgreSQL Persistence Schema Boundary](postgresql-persistence-schema-boundary.md)
- [Public Safety](public-safety.md)
