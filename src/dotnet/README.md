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
dotnet run --project src/dotnet/CarbonOps.Parser.Service -- run-once
```

`validate-config` now loads production configuration through the shared .NET
production config loader. It accepts an optional explicit JSON config file and
the process environment, then deterministically lets `CARBONOPS_PARSER_*`
environment values override file values. The command validates required key
presence and basic shape, reports secret presence, and redacts diagnostics. It
does not open PostgreSQL, run SQL, or print secret values.

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
top of the scheduled-worker command surface. It does not add source ingestion
logic, database runtime behavior, or external dependencies.
