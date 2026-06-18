# DEFRA/DESNZ Production E2E Ingestion

PH-014 adds the DEFRA/DESNZ year-based production E2E path behind explicit
runtime dependencies.

## Runtime Behavior

- PostgreSQL year state selects the target year: no DEFRA state targets 2024,
  otherwise the latest ingested DEFRA year plus one.
- The DEFRA/DESNZ source adapter discovers the GOV.UK flat-file publication for
  the selected target year.
- If the selected year is not configured or a flat-file link cannot be found,
  the orchestrator returns `no_available_source_year` and performs no parse,
  insert, or year-state update.
- Downloaded artifacts are archived under the configured target root with a
  sidecar metadata JSON file containing source metadata, local path, size, and
  SHA-256 checksum.
- The parser reads CSV or XLSX flat-file artifacts into normalized parser output
  rows without making DEFRA/DESNZ factor correctness claims.
- Phase 2 data-quality validation runs before PostgreSQL insertion.
- Validated rows are inserted through the existing PostgreSQL normalized factor
  runtime repository, which uses idempotent conflict handling.
- The DEFRA year-state row is recorded only after a successful insert result.

## Docker PostgreSQL Integration Test

The PH-014 integration test is opt-in and uses the existing repository
environment contract:

```bash
CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1 \
CARBONOPS_POSTGRESQL_TEST_DSN=postgresql://user:password@localhost:5432/carbonops \
python -m pytest tests/test_defra_desnz_production_e2e.py -m postgresql_integration
```

The integration test creates an isolated schema, bootstraps the Phase 1 runtime
tables, runs the DEFRA/DESNZ 2024 path against Docker PostgreSQL, reruns the
same source with reset year state, and asserts that normalized factor insertion
is idempotent.
