# Database Startup

Both implementation paths must make the database schema available before any source ingestion starts.

## Required Startup Sequence

The required startup sequence is:

1. Read configuration.
2. Validate the configured database provider.
3. Connect to PostgreSQL.
4. Check whether required tables exist.
5. Create missing tables if needed.
6. Initialize source schedules.
7. Start scheduled ingestion checks.

Parsing, downloading, and importing must not start before the database schema is available.

## Provider Validation

The conceptual configuration model allows these provider names:

- `postgres`
- `mysql`
- `mssql`

Phase 1 implements only `postgres`. Any other provider should fail fast with a clear message:

```text
Unsupported database provider. Phase 1 supports postgres only.
```

## Schema Availability

The startup check should cover shared ingestion metadata tables and source-specific table groups. Missing tables should be created before schedules are allowed to run.

This startup rule applies to both:

- `src/python`
- `src/dotnet`
