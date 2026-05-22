# PostgreSQL Runtime Readiness Checklist

This checklist defines the operator checks that must pass before a
CarbonOps-Parser Python ingestion deployment is treated as ready for the
supported production operator path.
It reflects the current packaged runtime: `carbonops-parser run-ingestion`
opens PostgreSQL, runs additive schema bootstrap, ingests configured source
families, and writes source-family master/detail tables.

This checklist does not claim project-level production-ready. The .NET runtime
is not production-ready yet, and project-level production-ready is blocked until
Python and .NET runtimes satisfy the same production parity contract.
PROD-005 adds the .NET PostgreSQL schema bootstrap/year-state baseline only; it
does not add .NET source discovery, source download, parser orchestration, or
source-family master/detail insert execution.

## Supported Runtime Boundary

Python production path:

- Entrypoint: `carbonops-parser run-ingestion --config <ingestion-json> --cycles 1`.
- Configuration validation: `carbonops-parser validate-ingestion-config --config <ingestion-json> --cycles 1`.
- Scheduling: cron or manual scheduled execution of a one-cycle command.
- Source families: `ghg_protocol`, `defra_desnz`, and `ipcc_efdb`.
- Source access: local paths, `file:` URIs, `local:` URIs, or reviewed HTTPS
  artifacts when live access is explicitly enabled.
- PostgreSQL driver: psycopg through the `postgresql` Python extra.

.NET non-production baseline:

- Entrypoint/status: `dotnet run --project src/dotnet/CarbonOps.Parser.Service -- validate-postgresql-runtime`.
- PostgreSQL driver boundary: Npgsql, opened only by explicit runtime methods.
- Schema baseline: additive `CREATE TABLE IF NOT EXISTS` and
  `CREATE INDEX IF NOT EXISTS` statements for the Phase 1 runtime catalog.
- Year-state baseline: latest successful year lookup, default initial year
  `2024`, next-year calculation, and idempotent successful-year recording.
- Unsupported in .NET today: source discovery, source download, parser
  orchestration, and source-family master/detail insert execution.

The older preview-only `PostgreSQLPersistenceRepository.persist()` boundary is
still unsupported. Production ingestion uses
`PostgreSQLSourceFamilyRuntimeRepository` through the configured cycle runner.

## Required PostgreSQL Privileges

The runtime role needs the minimum privileges below on the target database and
schema:

- `CONNECT` on the configured database.
- `USAGE` on the target schema.
- `CREATE` on the target schema for additive bootstrap.
- `SELECT`, `INSERT`, and `UPDATE` on the Phase 1 runtime tables.
- Sequence privileges if the operator changes table definitions to use
  sequences.

Do not grant destructive privileges just to run the parser. Backup/restore,
monitoring, retention, audit export, and credential rotation are owned by the
operator's production platform unless this repository later implements a
specific integration.

## Schema Bootstrap

Schema bootstrap is additive and idempotent:

- Tables use `CREATE TABLE IF NOT EXISTS`.
- Indexes use `CREATE INDEX IF NOT EXISTS`.
- Bootstrap commits after the DDL batch.
- Bootstrap reports required, present, created, and still-missing table names.
- Bootstrap does not drop, truncate, rename, or destructively migrate tables.

Required Phase 1 tables:

- `source_family_year_states`
- `ingestion_runs`
- `source_documents`
- `parser_runs`
- `schema_bootstrap_states`
- `normalized_factor_records`
- `ghg_emission_factor_masters`
- `ghg_emission_factor_details`
- `defra_emission_factor_masters`
- `defra_emission_factor_details`
- `ipcc_emission_factor_masters`
- `ipcc_emission_factor_details`

## Before First Run

Every item must be recorded as PASS or FAIL:

- PASS/FAIL: Clean install completed with `python -m pip install -e ".[postgresql]"`.
- PASS/FAIL: `carbonops-parser --help` works in the deployment environment.
- PASS/FAIL: Production JSON is present outside the repository and contains
  `archive_root`, `enabled_source_families`, `initial_year`, `cycle.max_cycles`,
  `cycle.interval_seconds`, `real_source_smoke.allow_live_source_access`, and
  explicit `source_years` entries for enabled families.
- PASS/FAIL: Required `CARBONOPS_POSTGRESQL_*` environment variables are
  supplied externally, including `CARBONOPS_POSTGRESQL_PASSWORD`.
- PASS/FAIL: `carbonops-parser validate-ingestion-config --config <production-json> --cycles 1`
  reports `status=ready`.
- PASS/FAIL: Archive root exists or can be created by the runtime user.
- PASS/FAIL: Source artifact paths exist, or reviewed HTTPS live source access
  is explicitly enabled.
- PASS/FAIL: The target database and schema are correct.
- PASS/FAIL: A backup/restore point exists according to operator policy.
- PASS/FAIL: Runtime role privileges match the minimum privilege list.
- PASS/FAIL: DB connectivity passed with an isolated/pre-production smoke.
- PASS/FAIL: Logs and validation output do not contain passwords, tokens, or
  private DSNs.

## First Run Command

Use one cycle for production scheduling:

```bash
export CARBONOPS_POSTGRESQL_HOST='<postgresql-host>'
export CARBONOPS_POSTGRESQL_PORT='5432'
export CARBONOPS_POSTGRESQL_DATABASE='<postgresql-database>'
export CARBONOPS_POSTGRESQL_USERNAME='<postgresql-runtime-role>'
export CARBONOPS_POSTGRESQL_PASSWORD='<external-secret-value>'
export CARBONOPS_POSTGRESQL_APPLICATION_NAME='carbonops-parser-prod'
export CARBONOPS_POSTGRESQL_SSL_MODE='require'
export CARBONOPS_POSTGRESQL_INITIAL_YEAR='2024'

carbonops-parser run-ingestion \
  --config /etc/carbonops-parser/ingestion.production.json \
  --cycles 1
```

## SQL Verification

Required schema/table presence:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = current_schema()
  AND table_name IN (
    'source_family_year_states',
    'ghg_emission_factor_masters',
    'ghg_emission_factor_details',
    'defra_emission_factor_masters',
    'defra_emission_factor_details',
    'ipcc_emission_factor_masters',
    'ipcc_emission_factor_details'
  )
ORDER BY table_name;
```

GHG Protocol counts:

```sql
SELECT 'ghg_emission_factor_masters' AS table_name, count(*) AS records
FROM ghg_emission_factor_masters
UNION ALL
SELECT 'ghg_emission_factor_details', count(*)
FROM ghg_emission_factor_details;
```

DEFRA/DESNZ counts:

```sql
SELECT 'defra_emission_factor_masters' AS table_name, count(*) AS records
FROM defra_emission_factor_masters
UNION ALL
SELECT 'defra_emission_factor_details', count(*)
FROM defra_emission_factor_details;
```

IPCC EFDB counts:

```sql
SELECT 'ipcc_emission_factor_masters' AS table_name, count(*) AS records
FROM ipcc_emission_factor_masters
UNION ALL
SELECT 'ipcc_emission_factor_details', count(*)
FROM ipcc_emission_factor_details;
```

Latest ingested year / year-state:

```sql
SELECT source_family, max(ingested_year) AS latest_ingested_year
FROM source_family_year_states
GROUP BY source_family
ORDER BY source_family;
```

## Idempotent Rerun Check

Run the same one-cycle command again against the same database/schema. PASS
requires:

- The command exits successfully, or reports only expected
  `no_available_source_year` outcomes.
- Duplicate source-family master/detail rows are reported as skipped, not
  inserted again.
- Latest-year state does not advance when the source year is unavailable.
- Logs remain redacted.

## Failure Blocks

Treat any item below as a production-readiness failure until resolved:

- Missing DB config such as `POSTGRESQL_RUNTIME_CONFIG_MISSING_HOST`,
  `POSTGRESQL_RUNTIME_CONFIG_MISSING_DATABASE`,
  `POSTGRESQL_RUNTIME_CONFIG_MISSING_USERNAME`, or
  `POSTGRESQL_RUNTIME_CONFIG_MISSING_PASSWORD`.
- Bad DB credentials, unreachable host, invalid port, wrong database, or
  rejected SSL mode.
- Missing or unwritable `archive_root`.
- Unsupported source family outside `ghg_protocol`, `defra_desnz`, and
  `ipcc_efdb`.
- Missing `source_years.<family>.<year>.artifact_url`.
- HTTPS artifact configured without explicit live source access.
- Unexpected `no_available_source_year` for a planned source family/year.
- Schema bootstrap reports missing required tables after execution.
- Any log, ticket, artifact, or test output exposes a password, token, private
  DSN, or real secret value.

## Production Checklist

All items must be PASS:

- PASS/FAIL: Clean install.
- PASS/FAIL: Config loaded and validated.
- PASS/FAIL: DB connectivity.
- PASS/FAIL: Schema bootstrap.
- PASS/FAIL: One source-family smoke or full three-source smoke.
- PASS/FAIL: Idempotent rerun.
- PASS/FAIL: Redaction check.
- PASS/FAIL: Full Python test baseline with `python -m pytest`.
- PASS/FAIL: `git diff --check`.
- PASS/FAIL: `git status --short` clean after validation.

## Related Documents

- [Production Packaging And Operator Runbook](production-packaging-operator-runbook.md)
- [Production Parity Contract](production-parity-contract.md)
- [Python Ingestion Local Runbook](python-ingestion-local-runbook.md)
- [Real-Source Smoke Mode](real-source-smoke-mode.md)
- [PostgreSQL Opt-In Integration Runbook](postgresql-opt-in-integration-runbook.md)
- [PostgreSQL Phase 1 Schema Contract](postgresql-phase1-schema-contract.md)
