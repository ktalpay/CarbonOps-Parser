# Production Packaging And Operator Runbook

This runbook is the supported operator path for the Python ingestion runtime.
It documents the commands an operator can run today to install, configure,
validate, execute, rerun, stop, and troubleshoot CarbonOps-Parser without
editing Python source files.

The production ingestion runtime path is Python only. The .NET solution now has
a scheduled-worker executable baseline, production config validation, a
PostgreSQL schema bootstrap/year-state runtime baseline, and a .NET
source-specific master/detail insert baseline. It also has a safe source-cycle
preview for target-year selection and configured local parser handoff, but its
ingestion command is a safe not-yet-implemented placeholder and is not a
production ingestion path.

This runbook does not make the whole project production-ready. Project-level
production-ready requires Python and .NET runtime parity as defined in
[Production Parity Contract](production-parity-contract.md). The .NET runtime is
not production-ready yet.

PROD-010 adds an opt-in persisted PostgreSQL parity validation baseline for
Python and .NET fixture-backed source-specific output. PROD-011 records the
final project-level verdict in
[Final Project Production-Ready Verdict](final-project-production-ready-verdict.md):
project-level production-ready remains no.

The .NET contract/test solution remains available at `src/dotnet/CarbonOps.Parser.sln`.

## Runtime Surface

| Surface | Current entrypoint | Production operation status |
| --- | --- | --- |
| Python package | `carbonops-parser` from `pyproject.toml` | Supported for configured PostgreSQL ingestion |
| Source acquisition CLI | `carbonops-source-acquisition` | Supported for local dry-run/source planning checks |
| .NET scheduled-worker baseline | `dotnet run --project src/dotnet/CarbonOps.Parser.Service -- <command>` | Entrypoint/config-validation, PostgreSQL schema/year-state baseline, source-specific master/detail insert baseline, and safe source-cycle preview only; ingestion parity incomplete |

Supported scheduling is cron or manual scheduled execution of the packaged
Python command. There is no daemon, long-running service installer, distributed
lock, or system service wrapper in this repository.

The .NET scheduled-worker command surface added by PROD-003 is directly
runnable and suitable for future cron/manual scheduling, but `run-once` returns
`ingestion_status=not_implemented` and a non-zero exit code until later .NET
production parity tasks complete service execution and the final verdict task.
PROD-009 adds an opt-in Docker PostgreSQL contract-test baseline for all three
local fixture-backed Phase 1 source families. PROD-010 adds an opt-in persisted
PostgreSQL parity baseline for Python and .NET output from the same fixture
families.

## Safety Modes

| Mode | Command shape | Purpose | External mutation |
| --- | --- | --- | --- |
| Local fixture/dry-run | `carbonops-parser local-dry-run ...` | Parse deterministic checked-in fixture data and render preview metadata | No |
| Local PostgreSQL smoke | `carbonops-parser real-source-smoke --config config/carbonops.ingestion.example.json --cycles 1` | Validate the packaged Python runtime against an operator-owned local PostgreSQL database | Yes, local DB only |
| Production PostgreSQL | `carbonops-parser run-ingestion --config /etc/carbonops-parser/ingestion.production.json --cycles 1` | Run configured source-family ingestion against the approved production PostgreSQL database | Yes, production DB |

HTTPS source access is blocked unless the operator explicitly sets
`real_source_smoke.allow_live_source_access` or passes
`--allow-live-source-access` to the smoke command. Production configs must use
reviewed artifact URLs or local artifact paths under `source_years`.

## Install

From a clean checkout or packaged deployment directory:

```bash
python -m pip install -e ".[postgresql]"
carbonops-parser --help
```

The `postgresql` extra installs the psycopg binary wrapper used by the runtime.
Do not commit virtual environments, package caches, or machine-local install
artifacts.

## Configure

Use JSON for the Python ingestion runtime. Production configuration is split:
non-secret ingestion settings live in an operator-managed JSON file, while
PostgreSQL credentials and connection fields are supplied by environment or the
deployment secret mechanism.

Example production JSON file:

```json
{
  "archive_root": "/var/lib/carbonops-parser/raw-archive",
  "enabled_source_families": ["ghg_protocol", "defra_desnz", "ipcc_efdb"],
  "initial_year": 2024,
  "cycle": {
    "interval_seconds": 0,
    "max_cycles": 1
  },
  "real_source_smoke": {
    "allow_live_source_access": false
  },
  "source_years": {
    "ghg_protocol": {
      "2024": {
        "artifact_url": "/var/lib/carbonops-parser/sources/ghg_protocol_2024.csv",
        "publication_url": "https://<reviewed-publication-url>",
        "title": "GHG Protocol reviewed artifact 2024",
        "version_label": "<reviewed-version-label>",
        "content_type": "text/csv",
        "format_hint": "csv"
      }
    },
    "defra_desnz": {
      "2024": {
        "artifact_url": "/var/lib/carbonops-parser/sources/defra_desnz_2024.csv",
        "publication_url": "https://<reviewed-publication-url>",
        "title": "DEFRA/DESNZ reviewed artifact 2024",
        "version_label": "<reviewed-version-label>",
        "content_type": "text/csv",
        "format_hint": "csv"
      }
    },
    "ipcc_efdb": {
      "2024": {
        "artifact_url": "/var/lib/carbonops-parser/sources/ipcc_efdb_2024.csv",
        "publication_url": "https://<reviewed-publication-url>",
        "title": "IPCC EFDB reviewed artifact 2024",
        "version_label": "<reviewed-version-label>",
        "content_type": "text/csv",
        "format_hint": "csv"
      }
    }
  }
}
```

A placeholder copy of this shape is checked in at
[../config/carbonops.ingestion.production.example.json](../config/carbonops.ingestion.production.example.json).
It contains no credentials and is not directly runnable until the operator
replaces placeholder artifact paths and source metadata.

Required runtime environment:

| Name | Required | Secret | Purpose |
| --- | --- | --- | --- |
| `CARBONOPS_POSTGRESQL_HOST` | Yes, unless DSN is used | No | PostgreSQL host |
| `CARBONOPS_POSTGRESQL_PORT` | Yes | No | PostgreSQL port, normally `5432` |
| `CARBONOPS_POSTGRESQL_DATABASE` | Yes, unless DSN is used | No | Database name |
| `CARBONOPS_POSTGRESQL_USERNAME` | Yes, unless DSN is used | No | Runtime database role |
| `CARBONOPS_POSTGRESQL_PASSWORD` | Yes, unless DSN is used | Yes | Runtime database password supplied externally |
| `CARBONOPS_POSTGRESQL_APPLICATION_NAME` | Yes for production operations | No | PostgreSQL application name, for example `carbonops-parser-prod` |
| `CARBONOPS_POSTGRESQL_SSL_MODE` | Deployment-specific | No | psycopg SSL mode, for example `require` |
| `CARBONOPS_POSTGRESQL_INITIAL_YEAR` | Yes for production operations | No | Initial year for empty year-state tables; keep aligned with JSON `initial_year` |
| `CARBONOPS_POSTGRESQL_DSN` | No | Yes if it embeds credentials | Alternative connection input; avoid in production because it is easier to leak |

Required JSON keys:

| Key | Required | Purpose |
| --- | --- | --- |
| `archive_root` | Yes | Operator-managed raw archive directory |
| `enabled_source_families` | Yes | Explicit subset of `ghg_protocol`, `defra_desnz`, `ipcc_efdb` |
| `initial_year` | Yes | First target year when no year-state exists |
| `cycle.max_cycles` | Yes | Use `1` for cron/manual scheduled production runs |
| `cycle.interval_seconds` | Yes | Use `0` for cron/manual scheduled production runs |
| `real_source_smoke.allow_live_source_access` | Yes | Must be explicit; default production recommendation is `false` with staged local artifacts |
| `source_years.<family>.<year>.artifact_url` | Yes for each enabled family/year | Local path, `file:` URI, `local:` URI, or reviewed HTTPS URL |
| `source_years.<family>.<year>.publication_url` | Yes | Source publication reference for audit metadata |
| `source_years.<family>.<year>.title` | Yes | Human-readable source artifact title |
| `source_years.<family>.<year>.version_label` | Yes | Reviewed version label |
| `source_years.<family>.<year>.content_type` | Yes | Usually `text/csv` |
| `source_years.<family>.<year>.format_hint` | Yes | Usually `csv` |

The only required secret in the split environment path is
`CARBONOPS_POSTGRESQL_PASSWORD`. Provide it through the deployment secret
manager or protected shell environment. Do not put passwords, tokens, private
DSNs, or real credentials in repository files, runbooks, tickets, command
history examples, or logs.

## Validate

Run local package and fixture checks first:

```bash
python -m pytest
git diff --check
python scripts/production_rc_verification.py
carbonops-source-acquisition validate
carbonops-source-acquisition run --dry-run --base-directory ./data/source-acquisition
carbonops-parser local-dry-run \
  --local-path examples/fixtures/defra_desnz_minimal.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-minimal-fixture \
  --content-type text/csv \
  --format-hint csv
dotnet test tests/dotnet/CarbonOps.Parser.Contracts.Tests/CarbonOps.Parser.Contracts.Tests.csproj \
  --configuration Release \
  --no-restore \
  --filter "FullyQualifiedName~ProductionConfigBoundaryTests|FullyQualifiedName~Phase1OperationalDiagnosticsTests|FullyQualifiedName~PostgreSQLRuntimeConfigGateContractTests|FullyQualifiedName~CarbonOpsParserServiceCommandTests"
dotnet test tests/dotnet/CarbonOps.Parser.Contracts.Tests/CarbonOps.Parser.Contracts.Tests.csproj \
  --configuration Release \
  --no-restore \
  --filter "FullyQualifiedName~PostgreSQLRuntimeSchemaAndYearStateTests|FullyQualifiedName~CarbonOpsParserServiceCommandTests"
dotnet test tests/dotnet/CarbonOps.Parser.Contracts.Tests/CarbonOps.Parser.Contracts.Tests.csproj \
  --configuration Release \
  --no-restore \
  --filter "FullyQualifiedName~PostgreSQLSourceSpecificFactorPersistenceTests|FullyQualifiedName~PostgreSQLRuntimeSchemaAndYearStateTests|FullyQualifiedName~CarbonOpsParserServiceCommandTests"
dotnet run --project src/dotnet/CarbonOps.Parser.Service -- help
```

The commands above must not require production configuration or credentials.
The focused .NET command is the default release-gate contract subset; the full .NET contract suite is outside the default release gate and remains a separate reviewer/operator validation choice when broader parity evidence is needed.

Validate production configuration without opening PostgreSQL:

```bash
export CARBONOPS_POSTGRESQL_HOST='<postgresql-host>'
export CARBONOPS_POSTGRESQL_PORT='5432'
export CARBONOPS_POSTGRESQL_DATABASE='<postgresql-database>'
export CARBONOPS_POSTGRESQL_USERNAME='<postgresql-runtime-role>'
export CARBONOPS_POSTGRESQL_PASSWORD='<external-secret-value>'
export CARBONOPS_POSTGRESQL_APPLICATION_NAME='carbonops-parser-prod'
export CARBONOPS_POSTGRESQL_SSL_MODE='require'
export CARBONOPS_POSTGRESQL_INITIAL_YEAR='2024'

carbonops-parser validate-ingestion-config \
  --config /etc/carbonops-parser/ingestion.production.json \
  --cycles 1
```

The .NET entrypoint has a separate validation command. It now loads a flat JSON
config file when `--config <path>` is supplied, loads the process environment,
and lets `CARBONOPS_PARSER_*` environment values override file values. It
validates presence and basic value shape for the expected `.NET`
`CARBONOPS_PARSER_*` keys, reports required key and password presence, does not
connect to PostgreSQL, and does not print secret values:

```bash
dotnet run --project src/dotnet/CarbonOps.Parser.Service -- validate-config --config /etc/carbonops-parser/dotnet.production.json
```

Validate the .NET PostgreSQL runtime baseline without opening PostgreSQL:

```bash
dotnet run --project src/dotnet/CarbonOps.Parser.Service -- validate-postgresql-runtime --config /etc/carbonops-parser/dotnet.production.json
```

Expected baseline result includes `schema_bootstrap_available=True`,
`year_state_available=True`,
`source_specific_master_detail_insert_baseline=True`,
`master_detail_insert_e2e_validated=False`,
`production_ingestion_ready=False`,
`postgresql_connection_opened=False`,
`.net_runtime_production_ready=False`, and
`project_level_production_ready=False`. This PostgreSQL validation command is
not the source-cycle preview command, so it still reports production ingestion
source download and parser orchestration as incomplete.

Optionally validate the .NET Docker PostgreSQL E2E/idempotency baseline against
a disposable Docker PostgreSQL database. This path is disabled by default and
must use externally supplied credentials:

```bash
export CARBONOPS_RUN_DOTNET_POSTGRESQL_INTEGRATION=1
export CARBONOPS_DOTNET_POSTGRESQL_TEST_DSN='<redacted-postgresql-dsn>'

dotnet test tests/dotnet/CarbonOps.Parser.Contracts.Tests/CarbonOps.Parser.Contracts.Tests.csproj \
  --configuration Release \
  --no-restore \
  --filter "FullyQualifiedName~DotNetPostgreSQLIntegrationE2ETests"
```

The tests may also use split `CARBONOPS_PARSER_POSTGRES_*` settings. They do
not print passwords, DSNs, or connection strings. They validate additive schema
bootstrap, GHG Protocol, DEFRA/DESNZ, and IPCC EFDB local fixture parsing,
source-specific master/detail insert, same-year rerun duplicate skips,
successful year-state progression, `no_available_source_year`, failure
rollback, and redacted diagnostics. They do not make `.NET run-once` a
production ingestion command and do not prove Python/.NET persisted parity.

Optionally validate Python/.NET persisted PostgreSQL parity against a
disposable database. This path is disabled by default and must use externally
supplied credentials:

```bash
export CARBONOPS_RUN_PERSISTED_PARITY_VALIDATION=1
export CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1
export CARBONOPS_POSTGRESQL_TEST_DSN='<redacted-postgresql-dsn>'

dotnet restore src/dotnet/CarbonOps.Parser.sln
python -m pytest -q tests/test_postgresql_persisted_parity_validation.py
```

The parity test creates isolated generated schemas, persists the same GHG
Protocol, DEFRA/DESNZ, and IPCC EFDB checked-in fixtures through the Python and
.NET paths, reruns same-year inserts to verify duplicate skips, records
successful `2024` year-state, and compares stable source-specific
master/detail output. It compares source-family identifiers, row counts,
source years, source versions, deterministic external keys, factor fields,
statuses, latest successful year, and next target year. It does not compare
volatile timestamps or generated UUIDs, does not print DSNs or credentials, and
does not perform destructive DB cleanup.

Preview the .NET source-cycle orchestration baseline without opening PostgreSQL
or writing source-family records:

```bash
dotnet run --project src/dotnet/CarbonOps.Parser.Service -- preview-source-cycle --config /etc/carbonops-parser/dotnet.production.json
```

The preview selects enabled source families from the optional JSON config,
calculates each target year from the year-state contract using the default
initial year `2024` when no successful year exists, checks configured local
artifacts under the narrow `source_artifacts.<family>.<year>` config shape, and
hands supported local CSV/text artifacts to the existing normalized parser
contracts. It does not make live network calls, open PostgreSQL, insert
records, or advance year-state. Missing target-year artifacts report
`no_available_source_year`; unsupported artifact shapes report
`parser_not_available`; successful parser handoff reports `parsed` plus
`persistence_not_implemented`.

Expected validation result:

```text
status=ready
postgresql_password_configured=True
postgresql_connection_opened=False
secret_values_printed=False
```

If validation prints `status=blocked`, fix the named field before opening a DB
connection.

Raw PostgreSQL connection strings are rejected by the committed configuration
boundary. Use split `.NET` `CARBONOPS_PARSER_*` fields for the .NET entrypoint
and keep production secret values in environment or an operator-managed secret
source rather than committed files. The PROD-004 .NET boundary satisfies only
the config loader/redaction item from the production parity map. The PROD-005
.NET boundary satisfies only the PostgreSQL schema bootstrap/year-state item.
The PROD-006 .NET boundary satisfies only the source discovery/load/parsing
orchestration item from the production parity map. The PROD-007 .NET boundary
satisfies only the source-specific master/detail insert runtime item from the
production parity map. PROD-010 satisfies the opt-in fixture-backed persisted
parity baseline. .NET production ingestion remains incomplete until service
run-once ingestion execution and the separate final project-level verdict task
are complete.

Validate DB connectivity and schema bootstrap with an isolated local or
pre-production database before production. The integration-test DSN is external
test-runner input and must not be printed:

```bash
CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1 \
CARBONOPS_POSTGRESQL_TEST_DSN='<external test DSN supplied by operator>' \
python -m pytest -q \
  tests/test_postgresql_connection_smoke_boundary.py::test_postgresql_opt_in_connection_open_close_smoke \
  tests/test_postgresql_runtime_year_state.py::test_docker_postgresql_schema_bootstrap_and_year_state_integration \
  tests/test_postgresql_source_family_repository.py::test_docker_postgresql_source_specific_master_detail_tables_integration
```

## Run

Local fixture/dry-run mode:

```bash
carbonops-parser local-dry-run \
  --local-path examples/fixtures/defra_desnz_minimal.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-minimal-fixture \
  --content-type text/csv \
  --format-hint csv \
  --include-postgresql-preview
```

Local PostgreSQL smoke mode:

```bash
export CARBONOPS_POSTGRESQL_HOST='127.0.0.1'
export CARBONOPS_POSTGRESQL_PORT='5432'
export CARBONOPS_POSTGRESQL_DATABASE='carbonops'
export CARBONOPS_POSTGRESQL_USERNAME='carbonops'
export CARBONOPS_POSTGRESQL_PASSWORD='<local-test-password>'
export CARBONOPS_POSTGRESQL_APPLICATION_NAME='carbonops-parser-local'
export CARBONOPS_POSTGRESQL_INITIAL_YEAR='2024'

carbonops-parser real-source-smoke \
  --config config/carbonops.ingestion.example.json \
  --cycles 1
```

Production PostgreSQL mode:

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

Use `--cycles 1` for production scheduling. The command creates missing Phase 1
tables additively, ingests the next target year per source family, records
year-state after successful source-family inserts, and reports inserted/skipped
counts. Re-running safely skips duplicate master/detail records and does not
advance year-state for `no_available_source_year` runs.

.NET scheduled-worker placeholder:

```bash
dotnet run --project src/dotnet/CarbonOps.Parser.Service -- run-once
```

Expected behavior remains fail-closed: `status=blocked`,
`ingestion_status=not_implemented`, `postgresql_connection_opened=False`, and
`records_inserted=0`. This command must not be treated as production ingestion
until later tasks complete .NET service run-once ingestion execution and the
separate final project-level verdict. The .NET runtime is still not
production-ready.

## PostgreSQL Readiness

Minimum database privileges for the runtime role:

- `CONNECT` on the configured database.
- `USAGE` on the target schema.
- `CREATE` on the target schema for additive schema bootstrap.
- `SELECT`, `INSERT`, and `UPDATE` on Phase 1 tables created or owned by the
  runtime schema.
- Sequence privileges if the deployment changes table definitions to use
  sequences.

Schema bootstrap is additive and idempotent. It uses `CREATE TABLE IF NOT
EXISTS` and `CREATE INDEX IF NOT EXISTS` for required Phase 1 tables; it does
not drop, truncate, or destructively migrate existing tables.

Before the first production run, the operator must verify:

- The target database and schema are correct.
- A backup/restore point exists according to the operator's production policy.
- Monitoring, alerting, retention, and credential rotation are owned outside
  this repository.
- The runtime role has the minimum privileges listed above.
- The archive root exists, is writable by the runtime user, and has enough
  storage.
- The configured source artifacts exist or reviewed live access is explicitly
  enabled.

After the first run, verify required tables:

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

Verify GHG Protocol master/detail counts:

```sql
SELECT 'ghg_emission_factor_masters' AS table_name, count(*) AS records
FROM ghg_emission_factor_masters
UNION ALL
SELECT 'ghg_emission_factor_details', count(*)
FROM ghg_emission_factor_details;
```

Verify DEFRA/DESNZ master/detail counts:

```sql
SELECT 'defra_emission_factor_masters' AS table_name, count(*) AS records
FROM defra_emission_factor_masters
UNION ALL
SELECT 'defra_emission_factor_details', count(*)
FROM defra_emission_factor_details;
```

Verify IPCC EFDB master/detail counts:

```sql
SELECT 'ipcc_emission_factor_masters' AS table_name, count(*) AS records
FROM ipcc_emission_factor_masters
UNION ALL
SELECT 'ipcc_emission_factor_details', count(*)
FROM ipcc_emission_factor_details;
```

Verify latest ingested year / year-state:

```sql
SELECT source_family, max(ingested_year) AS latest_ingested_year
FROM source_family_year_states
GROUP BY source_family
ORDER BY source_family;
```

Production database backup/restore, database monitoring, storage monitoring,
credential rotation, and audit-log retention are operator responsibilities
unless a future repository task implements a specific supported integration.

## Scheduling

Supported production scheduling is cron or manual scheduled execution of a
single-cycle command. Do not run overlapping production invocations for the same
database/schema unless an external scheduler lock is in place.

Safe cron shape:

```cron
SHELL=/bin/sh
CARBONOPS_POSTGRESQL_HOST=<postgresql-host>
CARBONOPS_POSTGRESQL_PORT=5432
CARBONOPS_POSTGRESQL_DATABASE=<postgresql-database>
CARBONOPS_POSTGRESQL_USERNAME=<postgresql-runtime-role>
CARBONOPS_POSTGRESQL_PASSWORD_FILE=/run/secrets/carbonops-postgresql-password
CARBONOPS_POSTGRESQL_APPLICATION_NAME=carbonops-parser-prod
CARBONOPS_POSTGRESQL_SSL_MODE=require
CARBONOPS_POSTGRESQL_INITIAL_YEAR=2024

15 4 * * * CARBONOPS_POSTGRESQL_PASSWORD="$(cat "$CARBONOPS_POSTGRESQL_PASSWORD_FILE")" /opt/carbonops-parser/.venv/bin/carbonops-parser run-ingestion --config /etc/carbonops-parser/ingestion.production.json --cycles 1 >> /var/log/carbonops-parser/ingestion.log 2>&1
```

The cron example uses placeholders and an external secret file. Ensure the
secret file and log file permissions are managed by the operator. Logs must not
include the password value.

## Stop And Rerun

Stop a running command with the process supervisor, scheduler cancellation, or
terminal interrupt. Normal stop/cancel must not delete archives, schemas,
tables, branches, worktrees, or source artifacts.

Rerun the same command after fixing an operator-visible issue. Duplicate
master/detail rows are skipped by the source-family repositories. If a run
reports `no_available_source_year`, add the missing configured year artifact or
reviewed live source access before rerunning.

## Troubleshooting

Common failures and operator actions:

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `POSTGRESQL_RUNTIME_CONFIG_MISSING_HOST` or related config issue | Missing DB env | Set the named `CARBONOPS_POSTGRESQL_*` value through the deployment environment |
| Connection failure before startup summary | Bad DB credentials, host, port, SSL mode, network route, or database name | Verify externally with `psql` using redacted operator procedures; rotate secrets if exposure is suspected |
| `archive_root could not be created` or `archive_root must be a directory path` | Missing or invalid archive root | Create the directory and set runtime-user permissions |
| `Unsupported enabled source family` | Unsupported family key | Use only `ghg_protocol`, `defra_desnz`, or `ipcc_efdb` |
| `requires artifact_url` | Missing configured source artifact | Add `source_years.<family>.<year>.artifact_url` |
| Live HTTPS source access error | HTTPS artifact configured without explicit live opt-in | Stage the artifact locally or explicitly enable reviewed live access |
| `no_available_source_year` | No configured artifact for the target year | Add the target year artifact or confirm the no-op is expected |
| Duplicate rows skipped | Idempotent rerun | Confirm skipped counts match prior successful run |

When reporting failures, include run ID, source family, target year, status,
issue code, and sanitized message. Do not include passwords, DSNs, tokens, or
private artifact URLs with credentials.

## Production Validation Checklist

A Python runtime deployment is ready for the supported operator path only when
every item is pass/fail recorded:

- PASS/FAIL: Clean install completed with `python -m pip install -e ".[postgresql]"`.
- PASS/FAIL: `carbonops-parser validate-ingestion-config --config <production-json> --cycles 1` reports `status=ready`.
- PASS/FAIL: DB connectivity passed against an isolated pre-production or approved production target.
- PASS/FAIL: Schema bootstrap created or verified all required Phase 1 tables.
- PASS/FAIL: One source-family smoke passed, or the full three-source smoke passed.
- PASS/FAIL: Idempotent rerun skipped duplicate master/detail rows.
- PASS/FAIL: Redaction check found no passwords, tokens, private DSNs, or secrets in logs and tickets.
- PASS/FAIL: Full Python test baseline passed with `python -m pytest`.
- PASS/FAIL: `git diff --check` passed.
- PASS/FAIL: `git status --short` is clean or contains only the reviewed deployment change.

Historical release-gate trace retained for reviewer continuity:
Task-ID: OPS-033
Task-Issue: #500

## Related Documents

- [Python Ingestion Local Runbook](python-ingestion-local-runbook.md)
- [Production Parity Contract](production-parity-contract.md)
- [Final Project Production-Ready Verdict](final-project-production-ready-verdict.md)
- [Real-Source Smoke Mode](real-source-smoke-mode.md)
- [PostgreSQL Runtime Readiness Checklist](postgresql-runtime-readiness-checklist.md)
- [PostgreSQL Opt-In Integration Runbook](postgresql-opt-in-integration-runbook.md)
- [PostgreSQL Phase 1 Schema Contract](postgresql-phase1-schema-contract.md)
