# .NET Implementation

The .NET implementation is an independent Worker Service implementation option for CarbonOps-Parser.

It should follow the same conceptual ingestion workflow as the Python implementation while using .NET-appropriate project structure and typed application architecture.

## Current Entry Point

`CarbonOps.Parser.Service` is the first scheduled-worker entrypoint baseline for
the .NET runtime. It is a console-style executable intended for direct operator
execution and cron/manual scheduling of a single cycle.

Command shape:

```bash
dotnet run --project src/dotnet/CarbonOps.Parser.Service -- help
dotnet run --project src/dotnet/CarbonOps.Parser.Service -- validate-config
dotnet run --project src/dotnet/CarbonOps.Parser.Service -- validate-config --config /etc/carbonops-parser/dotnet.production.json
dotnet run --project src/dotnet/CarbonOps.Parser.Service -- validate-postgresql-runtime --config /etc/carbonops-parser/dotnet.production.json
dotnet run --project src/dotnet/CarbonOps.Parser.Service -- run-once
```

`validate-config` now loads production configuration through the shared .NET
production config loader. It accepts an optional explicit JSON config file and
the process environment, then deterministically lets `CARBONOPS_PARSER_*`
environment values override file values. The command validates required key
presence and basic shape, reports secret presence, and redacts diagnostics. It
does not open PostgreSQL, run SQL, or print secret values.

`validate-postgresql-runtime` validates the same explicit configuration and
reports the .NET PostgreSQL schema/year-state baseline without opening
PostgreSQL or running SQL. It reports that schema bootstrap and year-state
primitives exist, and also reports that source download, parser orchestration,
master/detail inserts, .NET production readiness, and project-level production
readiness are still false.

The .NET contracts project now includes an explicit Npgsql runtime boundary for
additive schema bootstrap and source-family year-state behavior. Construction
and validation do not connect to PostgreSQL. DB connections are opened only by
explicit runtime methods, and diagnostics redact passwords and connection
strings. The schema bootstrap DDL is limited to `CREATE TABLE IF NOT EXISTS`
and `CREATE INDEX IF NOT EXISTS` style statements for the shared/source-family
Phase 1 tables.

`run-once` is intentionally fail-closed. It may reuse the same config
validation boundary, but it reports
`ingestion_status=not_implemented`, opens no PostgreSQL connection, inserts no
records, and returns a non-zero exit code until later .NET parity tasks
implement PostgreSQL orchestration, source behavior, and inserts.

This entrypoint does not make the .NET runtime production-ready.

## Role

The .NET path should focus on:

- Configuration loading.
- PostgreSQL startup checks.
- Schema availability checks.
- Background worker service execution.
- Source-specific schedules.
- Source version/hash checks.
- Raw file download and archive.
- Source-specific parsing.
- Parsed record validation.
- Persistence of shared ingestion metadata and source-specific records.
- Import summaries and validation issues.

The .NET implementation should not depend on the Python implementation.

PROD-004 adds only the .NET production config loader and redaction baseline on
top of the scheduled-worker command surface. PROD-005 adds only the .NET
PostgreSQL schema bootstrap/year-state item from the production parity map. It
does not add source discovery, source download, parser orchestration, or
source-family master/detail insert execution.
