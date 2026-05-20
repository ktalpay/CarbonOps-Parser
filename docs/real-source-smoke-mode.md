# Real-Source Smoke Mode

Real-source smoke mode is the controlled Python path for checking configured
GHG Protocol, DEFRA/DESNZ, and IPCC EFDB artifacts against the PostgreSQL
source-family master/detail tables. It uses the same adapters as the configured
cycle runner and keeps the local fixture path unchanged.

This mode does not add credentials, scheduler behavior, .NET parity,
production factor correctness claims, compliance claims, legal claims, or
source-owner correctness claims.

## Command

Use the dedicated command with an explicit JSON config:

```bash
carbonops-parser real-source-smoke --config config/carbonops.ingestion.example.json --cycles 1
```

The command supports local files by default. Local artifact references may be
plain paths, `file:` URIs, or `local:` paths. HTTPS source access is blocked
unless the operator opts in with either:

```bash
carbonops-parser real-source-smoke --config path/to/real-source-smoke.json --allow-live-source-access
```

or a config flag:

```json
{
  "real_source_smoke": {
    "allow_live_source_access": true
  }
}
```

## Config Shape

Each live or local artifact must be configured explicitly under `source_years`.
The runner supports the canonical source families `ghg_protocol`,
`defra_desnz`, and `ipcc_efdb`.

```json
{
  "archive_root": "./data/raw",
  "enabled_source_families": ["ghg_protocol", "defra_desnz", "ipcc_efdb"],
  "initial_year": 2024,
  "cycle": {"max_cycles": 1},
  "real_source_smoke": {"allow_live_source_access": false},
  "source_years": {
    "ghg_protocol": {
      "2024": {
        "artifact_url": "examples/fixtures/ingestion/ghg_protocol_2024.csv",
        "publication_url": "examples/fixtures/ingestion/ghg_protocol_2024.csv",
        "title": "Configured GHG Protocol artifact 2024",
        "version_label": "configured-2024",
        "content_type": "text/csv",
        "format_hint": "csv"
      }
    }
  }
}
```

For HTTPS artifacts, set `artifact_url` to the reviewed artifact URL and opt in
to live access. DEFRA/DESNZ can use configured artifact URLs directly; when the
reviewed DEFRA/DESNZ publication fallback is used, live access is also required.

## Output

Each source line reports:

- `download_status`: `downloaded`, `failed`, or `not_run`.
- `parse_status`: `parsed`, `failed`, `not_run`, or `no_rows`.
- `master_inserted` and `detail_inserted`.
- `master_skipped` and `detail_skipped` for idempotent duplicate rows.

The summary line reports aggregate `no_available_source_year`, parsed row,
inserted, and skipped duplicate counts. Error messages are user-readable and
redacted before they are printed.

## Docker PostgreSQL Smoke

Start PostgreSQL as described in
[Python Ingestion Local Runbook](python-ingestion-local-runbook.md), export the
PostgreSQL environment variables, then run:

```bash
carbonops-parser real-source-smoke --config config/carbonops.ingestion.example.json --cycles 1
```

Verify source-specific master/detail rows:

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

Re-running the same smoke against the same database should report skipped
duplicates instead of duplicate inserts for already persisted source rows.
