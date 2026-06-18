# Production E2E Year Orchestrator Boundary

PH-013 adds a Python runtime boundary for one production E2E source-year step.
The boundary is implemented in
`carbonfactor_parser.pipeline.production_e2e_year_orchestrator`.

The orchestrator is dependency-injected. It coordinates:

- PostgreSQL source-family year state.
- Canonical source-family selection for `ghg_protocol`, `defra_desnz`, and
  `ipcc_efdb`.
- Initial-year and next-year target calculation.
- Source-family target-year discovery and download interfaces.
- Parser execution through an injected parser boundary.
- Validation through an injected validation boundary.
- PostgreSQL normalized-factor insert through an injected insert repository.

The implementation does not add live source adapters, source-specific parser
details, network calls, credentials, scheduling, or carbon-accounting
correctness claims.

## Year Selection

For each enabled source family:

- If PostgreSQL has no latest ingested year, the target year is the configured
  initial year. The default is `2024`.
- If PostgreSQL returns a latest ingested year, the target year is
  `latest_year + 1`.

The run selects exactly one target year per source family. It does not backfill,
skip ahead, or scan multiple years.

## No Available Source Year

If the source-family adapter reports `no_available_source_year`, the family is a
safe no-op:

- no download is required,
- parser execution is skipped,
- validation is skipped,
- PostgreSQL insert is skipped,
- year state is not advanced, and
- the whole run may still complete successfully.

## Adapter Scope

The source-family adapter contract intentionally has only two runtime methods:

- `discover_target_year(request)`
- `download_target_year(discovery_result)`

Real source integrations for GHG Protocol, DEFRA/DESNZ, and IPCC EFDB remain
deferred to source-specific implementation tasks.
