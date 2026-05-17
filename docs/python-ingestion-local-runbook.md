# Python Ingestion Local Runbook

This runbook packages the Python ingestion path for a local PostgreSQL run. It
uses checked-in local CSV fixtures for GHG Protocol, DEFRA/DESNZ, and IPCC EFDB
so a user can clone the repository, start Docker PostgreSQL, and run the
3-source ingestion cycle without writing or editing Python files.

This document does not add .NET parity, production credentials, production
source URLs, legal/compliance claims, carbon-accounting correctness claims, or
source-owner correctness claims.

## Install

From a fresh checkout:

```bash
git clone <REPOSITORY_URL> CarbonOps-Parser
cd CarbonOps-Parser
python -m pip install -e ".[postgresql]"
```

The package installs the `carbonops-parser` command from
[pyproject.toml](../pyproject.toml). The PostgreSQL extra installs the local
`psycopg` driver dependency used by the runtime.

## Start Docker PostgreSQL

Start an isolated local PostgreSQL container:

```bash
docker run --name carbonops-postgres \
  -e POSTGRES_USER=carbonops \
  -e POSTGRES_PASSWORD=carbonops_local_password \
  -e POSTGRES_DB=carbonops \
  -p 5432:5432 \
  -d postgres:16
```

If you need to restart a stopped container:

```bash
docker start carbonops-postgres
```

If you need a clean database after a previous local test run:

```bash
docker rm -f carbonops-postgres
```

Then run the `docker run` command again.

## Configure

Use the checked-in example config:
[config/carbonops.ingestion.example.json](../config/carbonops.ingestion.example.json).

The config file contains archive settings, enabled source families, cycle
settings, and local fixture paths for source years `2024`, `2025`, and `2026`.
It does not contain a PostgreSQL password or any other secret. Runtime
PostgreSQL settings come from environment variables.

Set local environment variables:

```bash
export CARBONOPS_POSTGRESQL_HOST=127.0.0.1
export CARBONOPS_POSTGRESQL_PORT=5432
export CARBONOPS_POSTGRESQL_DATABASE=carbonops
export CARBONOPS_POSTGRESQL_USERNAME=carbonops
export CARBONOPS_POSTGRESQL_PASSWORD=carbonops_local_password
export CARBONOPS_POSTGRESQL_APPLICATION_NAME=carbonops-parser-local
```

## Run Ingestion

Run the packaged Python ingestion command:

```bash
carbonops-parser run-ingestion --config config/carbonops.ingestion.example.json
```

For a single-line shell command without exported variables:

```bash
CARBONOPS_POSTGRESQL_HOST=127.0.0.1 CARBONOPS_POSTGRESQL_PORT=5432 CARBONOPS_POSTGRESQL_DATABASE=carbonops CARBONOPS_POSTGRESQL_USERNAME=carbonops CARBONOPS_POSTGRESQL_PASSWORD=carbonops_local_password CARBONOPS_POSTGRESQL_APPLICATION_NAME=carbonops-parser-local carbonops-parser run-ingestion --config config/carbonops.ingestion.example.json
```

The example config sets `max_cycles` to `4`, so one command demonstrates the
full local cycle behavior:

- Cycle 1 targets `2024` for all three source families.
- Cycle 2 reads the latest ingested year from PostgreSQL and targets `2025`.
- Cycle 3 targets `2026`.
- Cycle 4 targets `2027`; because the example config has no `2027` source
  artifact, each family returns `no_available_source_year`.

The `2027` cycle is a safe no-op. It does not insert source records and does not
advance `source_family_year_states`.

## Verify Records

Use `psql` inside the Docker container.

Check source-specific master/detail table counts:

```bash
docker exec -e PGPASSWORD=carbonops_local_password carbonops-postgres \
  psql -U carbonops -d carbonops -c "
SELECT 'ghg_emission_factor_masters' AS table_name, count(*) AS records FROM ghg_emission_factor_masters
UNION ALL SELECT 'ghg_emission_factor_details', count(*) FROM ghg_emission_factor_details
UNION ALL SELECT 'defra_emission_factor_masters', count(*) FROM defra_emission_factor_masters
UNION ALL SELECT 'defra_emission_factor_details', count(*) FROM defra_emission_factor_details
UNION ALL SELECT 'ipcc_emission_factor_masters', count(*) FROM ipcc_emission_factor_masters
UNION ALL SELECT 'ipcc_emission_factor_details', count(*) FROM ipcc_emission_factor_details
ORDER BY table_name;"
```

After a clean 4-cycle run, each source-specific table should have local fixture
records for `2024`, `2025`, and `2026`.

Check year state:

```bash
docker exec -e PGPASSWORD=carbonops_local_password carbonops-postgres \
  psql -U carbonops -d carbonops -c "
SELECT source_family, max(ingested_year) AS latest_ingested_year
FROM source_family_year_states
GROUP BY source_family
ORDER BY source_family;"
```

Expected latest ingested year after a clean 4-cycle run:

```text
defra | 2026
ghg   | 2026
ipcc  | 2026
```

Confirm that the unavailable `2027` cycle did not insert source-specific
records:

```bash
docker exec -e PGPASSWORD=carbonops_local_password carbonops-postgres \
  psql -U carbonops -d carbonops -c "
SELECT 'ghg_masters_2027' AS check_name, count(*) AS records FROM ghg_emission_factor_masters WHERE source_year = 2027
UNION ALL SELECT 'defra_masters_2027', count(*) FROM defra_emission_factor_masters WHERE source_year = 2027
UNION ALL SELECT 'ipcc_masters_2027', count(*) FROM ipcc_emission_factor_masters WHERE source_year = 2027
UNION ALL SELECT 'ghg_details_2027', count(*) FROM ghg_emission_factor_details d JOIN ghg_emission_factor_masters m USING (ghg_emission_factor_master_id) WHERE m.source_year = 2027
UNION ALL SELECT 'defra_details_2027', count(*) FROM defra_emission_factor_details d JOIN defra_emission_factor_masters m USING (defra_emission_factor_master_id) WHERE m.source_year = 2027
UNION ALL SELECT 'ipcc_details_2027', count(*) FROM ipcc_emission_factor_details d JOIN ipcc_emission_factor_masters m USING (ipcc_emission_factor_master_id) WHERE m.source_year = 2027
ORDER BY check_name;"
```

Each `2027` count should be `0`.

## Accepted Risks And Non-Claims

- The example source artifacts are deterministic local fixtures, not official
  source-owner files.
- The Docker password is a local example value only. Do not use it for shared,
  hosted, or production databases.
- The command creates and writes Phase 1 tables in the connected local
  PostgreSQL database. Use an isolated database or reset the Docker container
  before repeat demos.
- Re-running against the same database is idempotent for duplicate source
  rows, but the latest-year state will already be advanced from the previous
  run.
- The Python runner is the only packaged ingestion path covered here. This task
  does not implement .NET runtime parity.
- The local run demonstrates packaging, configuration, source-specific
  master/detail persistence, and cycle behavior. It does not claim production
  readiness, compliance correctness, legal correctness, carbon-accounting
  correctness, or source-owner correctness.

## Related Documents

- [Production E2E Ingestion Readiness Contract](production-e2e-ingestion-readiness-contract.md)
- [PH-018 Real Production-Ready Ingestion Contract](ph-018-real-production-ready-ingestion-contract.md)
- [PostgreSQL Phase 1 Schema Contract](postgresql-phase1-schema-contract.md)
