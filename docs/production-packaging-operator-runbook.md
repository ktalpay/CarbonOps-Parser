# Production Packaging And Operator Runbook

This runbook defines the Phase 1 operator flow for installing, configuring,
validating, running, stopping, and diagnosing CarbonOps-Parser across the Python
and .NET implementation paths.

It is operator documentation and packaging guidance only. It does not add a
daemon installer, start a service, connect to PostgreSQL, run SQL, download real
sources, create tables, mutate deployed systems, load credentials, or claim
carbon-accounting correctness.

## Runtime Surface

| Surface | Current entrypoint | Packaging status | Production operation status |
| --- | --- | --- | --- |
| Python package | `carbonops-parser` and `carbonops-source-acquisition` from `pyproject.toml` | Editable install supported for local checks | Service-host contract exists, but no packaged daemon command is published yet |
| .NET package | `src/dotnet/CarbonOps.Parser.sln` | Contracts project can be restored, built, and tested | Service-host contract exists, but no Worker Service executable is published yet |

The two paths are intentionally aligned at the contract level: both use
PostgreSQL-only Phase 1 configuration, split non-secret database fields,
`CARBONOPS_PARSER_POSTGRES_PASSWORD` as the secret boundary, fail-closed startup
validation, schema-bootstrap readiness checks, sequential scheduled execution,
overlap skipping, and graceful stop semantics.

The current difference is packaging shape. Python exposes installed console
scripts for local validation and dry-run boundaries. .NET exposes a contracts
solution and tests, not a deployed Worker Service binary. Operators must not
invent a production wrapper that bypasses the documented validation gates.

## Safety Modes

Use these mode labels in operator notes, release checklists, and PR bodies:

| Mode | Purpose | Safe default | May mutate external systems |
| --- | --- | --- | --- |
| Dry-run | Plan targets or render preview metadata | Yes | No |
| Local fixture | Parse checked-in local fixture data | Yes | No |
| Isolated integration | Validate opt-in infrastructure using isolated local resources | No, explicit opt-in only | Only the isolated resource named by the operator |
| Production | Run the deployed service with approved environment configuration | No, requires release approval | Yes, within the approved deployment boundary |

Dry-run and local fixture commands must remain deterministic and credential-free.
Isolated integration and production commands must be documented separately from
safe defaults, with an explicit operator approval step before use.

## Install

### Python

From a clean checkout:

```bash
python -m pip install -e .
```

Optional PostgreSQL driver packaging smoke:

```bash
python -m pip install -e ".[postgresql]"
```

The optional extra validates installability only. It does not enable repository
persistence or open a PostgreSQL connection.

### .NET

From the repository root:

```bash
dotnet restore src/dotnet/CarbonOps.Parser.sln
dotnet build src/dotnet/CarbonOps.Parser.sln --configuration Release
```

This builds the contracts and tests projects. It does not publish or install a
Worker Service executable.

## Configure

Production configuration is supplied outside the repository. Do not commit
environment-specific host names, database names, usernames, raw connection
strings, or secret values.

Required Phase 1 keys:

- `CARBONOPS_PARSER_ENV`
- `CARBONOPS_PARSER_DATABASE_PROVIDER`
- `CARBONOPS_PARSER_POSTGRES_HOST`
- `CARBONOPS_PARSER_POSTGRES_PORT`
- `CARBONOPS_PARSER_POSTGRES_DATABASE`
- `CARBONOPS_PARSER_POSTGRES_USERNAME`
- `CARBONOPS_PARSER_POSTGRES_PASSWORD`
- `CARBONOPS_PARSER_POSTGRES_SCHEMA`
- `CARBONOPS_PARSER_RAW_ARCHIVE_PATH`
- `CARBONOPS_PARSER_LOG_LEVEL`

Operator rules:

- `CARBONOPS_PARSER_DATABASE_PROVIDER` must be `postgres`.
- `CARBONOPS_PARSER_POSTGRES_PORT` must be an integer from 1 to 65535.
- `CARBONOPS_PARSER_LOG_LEVEL` must be `debug`, `info`, `warning`, `error`, or
  `critical`.
- The password key may be checked for presence, but its value must not be
  printed, logged, copied into examples, or added to diagnostics.
- Raw PostgreSQL connection strings are rejected; use split non-secret fields
  plus the password key above.
- `CARBONOPS_PARSER_RAW_ARCHIVE_PATH` must point to an operator-managed
  directory with enough free space and backup policy for raw source archives.

The shared conceptual template is
[../config/carbonops.config.example.yaml](../config/carbonops.config.example.yaml).
It contains placeholders only.

## Validate

Run validation in this order before any production start attempt.

Combined CI/release gate:

```bash
python scripts/release_validation_gate.py
```

The combined gate runs Python tests, local source acquisition and parser
fixture checks, .NET contract checks, parity fixture presence checks, sample
config safety checks, static workflow/runbook safety checks, and whitespace
validation. Full repository public-safety validation is currently noisy because
of existing fixture strings and is tracked separately until baseline support is
available. PostgreSQL integration validation remains opt-in only through
`CARBONOPS_RELEASE_GATE_RUN_INTEGRATION=1`,
`CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1`, and an externally supplied
`CARBONOPS_POSTGRESQL_TEST_DSN`.

Default combined gate command coverage includes:

```bash
python -m pytest
git diff --check
```

Repository checks outside the default combined gate:

```bash
python scripts/check_public_safety.py
```

Python package smoke:

```bash
carbonops-source-acquisition validate
carbonops-source-acquisition run --dry-run --base-directory ./data/source-acquisition
carbonops-parser local-dry-run \
  --local-path examples/fixtures/defra_desnz_minimal.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-minimal-fixture \
  --content-type text/csv \
  --format-hint csv
```

Python preview-only persistence smoke:

```bash
carbonops-parser local-dry-run \
  --local-path examples/fixtures/defra_desnz_minimal.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-minimal-fixture \
  --content-type text/csv \
  --format-hint csv \
  --include-postgresql-preview
```

.NET packaging smoke:

```bash
dotnet test src/dotnet/CarbonOps.Parser.sln --configuration Release
```

The commands above must not require production configuration or credentials.
Treat any prompt for production values during these checks as a release blocker.

## Run

Current repository entrypoints are safe local boundaries, not deployed service
commands. A production service process may be started only after a future task
adds or approves an explicit host executable or deployment wrapper that preserves
the service-host gates.

Minimum run requirements for either implementation path:

1. Configuration validation succeeds before source checks, downloads, parsing,
   imports, or database execution.
2. PostgreSQL provider is `postgres`.
3. The password value is present through the deployment secret mechanism but is
   never stored in repository files or emitted in diagnostics.
4. Schema-bootstrap readiness is checked before scheduled source execution.
5. Scheduled execution remains sequential with one active run per host instance.
6. The selected source families are explicit.
7. Logs include run IDs and sanitized issue codes, not raw configured values.

For Linux service shape and a non-installing systemd template, see
[linux-service-setup.md](linux-service-setup.md).

## Stop

Use the process supervisor or hosting platform stop action for the deployed
process. The Phase 1 service-host contract treats stop as graceful:

- new scheduled triggers are skipped after shutdown is requested;
- an active run is allowed to unwind;
- the host reports stopped after the active runner exits;
- shutdown does not delete worktrees, branches, raw archives, or database data.

Do not use cleanup commands that delete branches, worktrees, archives, schemas,
tables, or production data as part of normal stop.

## Diagnose

Start with safe, non-mutating evidence:

```bash
carbonops-source-acquisition validate --output-format json
carbonops-source-acquisition list --output-format json
carbonops-source-acquisition run --dry-run --base-directory ./data/source-acquisition --output-format json
carbonops-parser local-dry-run \
  --local-path examples/fixtures/defra_desnz_minimal.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-minimal-fixture \
  --content-type text/csv \
  --format-hint csv \
  --json \
  --include-postgresql-preview
```

Troubleshooting checklist:

- Startup blocked: review issue codes and field names; do not paste configured
  values into tickets.
- Missing schema: compare the schema-bootstrap report with the PostgreSQL Phase
  1 schema contract before enabling any create-missing behavior.
- Already running: wait for the active run to finish; do not start a second host
  against the same production target without an approved lock strategy.
- Source acquisition failure: identify whether the run was noop, dry-run, HTTP
  without persistence, or HTTP with explicit content persistence.
- Parser or normalization issue: reproduce with the local fixture path first if
  the failure shape applies to checked-in deterministic data.
- Database execution issue: confirm that runtime execution was explicitly
  enabled by a reviewed future task; the current default repository boundary is
  no-execution.
- Suspected credential exposure: rotate the affected runtime credential through
  the deployment secret mechanism and remove the exposed diagnostic artifact
  from normal operator channels.

## Failure Recovery

Use least-mutating recovery first:

1. Stop or pause new triggers.
2. Capture sanitized run ID, source family, status, issue codes, and timestamps.
3. Preserve raw archive files for inspection unless an approved data-retention
   policy says otherwise.
4. Re-run dry-run or local fixture commands to separate packaging/config issues
   from source-specific runtime behavior.
5. If a production deployment changed, roll back the package or deployment
   pointer to the last known reviewed version.
6. If database writes were enabled by a future task, follow that task's
   transaction and rollback runbook; do not run ad hoc destructive SQL.
7. Resume triggers only after validation commands pass and the operator records
   the resolved cause.

Rollback must not delete Codex worktrees, delete branches, close issues, merge
pull requests, approve pull requests, or remove raw archives unless a separate
human-approved retention process requires it.

## PR Body Footer

OPS-032 pull request bodies must end with:

```text
Task-ID: OPS-032
Task-Issue: #499
```

OPS-036 pull request bodies must end with:

```text
Task-ID: OPS-036
Task-Issue: #498
```

## Related Documents

- [Configuration Model](configuration-model.md)
- [Linux Service Setup](linux-service-setup.md)
- [PostgreSQL Runtime Readiness Checklist](postgresql-runtime-readiness-checklist.md)
- [PostgreSQL Opt-In Integration Runbook](postgresql-opt-in-integration-runbook.md)
- [PostgreSQL Config Contract Boundary](postgresql-config-contract-boundary.md)
- [Local Dry-Run CLI Boundary](local-dry-run-cli-boundary.md)
- [Source Acquisition CLI Boundary](source-acquisition-cli-boundary.md)
- [Public Safety](public-safety.md)
