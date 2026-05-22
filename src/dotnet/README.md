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
dotnet run --project src/dotnet/CarbonOps.Parser.Service -- preview-source-cycle --config /etc/carbonops-parser/dotnet.production.json
dotnet run --project src/dotnet/CarbonOps.Parser.Service -- validate-source-cycle --config /etc/carbonops-parser/dotnet.production.json
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
primitives exist and that the source-specific master/detail insert baseline is
available through `source_specific_master_detail_insert_baseline=True`. It also
reports `master_detail_insert_e2e_validated=False` and
`production_ingestion_ready=False` because Docker PostgreSQL E2E,
idempotency/rerun E2E, and Python/.NET persisted parity validation remain
incomplete. Production source download, full parser orchestration E2E, .NET
production readiness, and project-level production readiness are still false in
this PostgreSQL validation command.

`preview-source-cycle` and `validate-source-cycle` provide the PROD-006 safe
source-cycle orchestration baseline. They select enabled source families from
the optional JSON config, calculate each target year through the year-state
contract with default initial year `2024`, check configured local artifacts, and
hand supported local CSV/text artifacts to the existing normalized parser
contracts. The commands do not open PostgreSQL, run SQL, insert source-specific
master/detail records, update year-state, print secrets, or make uncontrolled
network calls. Missing configured target-year artifacts report
`no_available_source_year`; unsupported artifact shapes report
`parser_not_available`; completed parser handoff reports `parsed` and
`persistence_not_implemented`.

The optional .NET source-cycle config extension is intentionally narrow:

```json
{
  "enabled_source_families": ["ghg_protocol", "defra_desnz", "ipcc_efdb"],
  "source_artifacts": {
    "ghg_protocol": {
      "2024": {
        "path": "/var/lib/carbonops-parser/sources/ghg_protocol_2024.csv",
        "content_type": "text/csv",
        "extension": ".csv",
        "version_label": "v1"
      }
    }
  }
}
```

The .NET contracts project now includes an explicit Npgsql runtime boundary for
additive schema bootstrap and source-family year-state behavior. Construction
and validation do not connect to PostgreSQL. DB connections are opened only by
explicit runtime methods, and diagnostics redact passwords and connection
strings. The schema bootstrap DDL is limited to `CREATE TABLE IF NOT EXISTS`
and `CREATE INDEX IF NOT EXISTS` style statements for the shared/source-family
Phase 1 tables.

The .NET contracts project also includes a PROD-007 source-specific
master/detail insert boundary. It maps normalized parser output into
`ghg_emission_factor_masters/details`, `defra_emission_factor_masters/details`,
and `ipcc_emission_factor_masters/details`, uses additive
`INSERT ... ON CONFLICT DO NOTHING` SQL, returns explicit inserted/skipped
duplicate/validation-failed counts, and updates source-family year-state only
inside the successful source-family persistence transaction. This is a baseline
only; Docker PostgreSQL E2E, idempotency/rerun E2E, and Python/.NET persisted
parity validation remain blockers.

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
PostgreSQL schema bootstrap/year-state item from the production parity map.
PROD-006 adds only the .NET source discovery/load/parsing orchestration item.
PROD-007 adds only the .NET source-specific master/detail insert runtime item.
It does not complete .NET production ingestion.
