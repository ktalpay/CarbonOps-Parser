# Release Notes Draft

## CarbonOps-Parser Public Alpha/Review Release

Status: draft for first public alpha/review release.

This draft is for a public review release of CarbonOps-Parser, a climate-tech data infrastructure project for auditable carbon accounting emission factor ingestion and validation. The release is intended to make the repository understandable and inspectable for reviewers interested in GHG Protocol, DEFRA/DESNZ, IPCC EFDB, Python, .NET, and PostgreSQL boundaries.

## Highlights

- Public project positioning for auditable carbon factor ingestion, validation, diagnostics, and PostgreSQL readiness.
- Phase 1 documentation for supported source families: GHG Protocol, DEFRA/DESNZ, and IPCC EFDB.
- Python implementation slices for local source acquisition boundaries, parser contracts, normalization handoff, persistence input preparation, PostgreSQL previews, and local dry-run composition.
- .NET contract records and tests for shared Phase 1 concepts, including parser, acquisition, validation, diagnostics, and PostgreSQL readiness boundaries.
- PostgreSQL schema descriptors, DDL preview, bootstrap/readiness contracts, disabled execution adapters, and opt-in integration boundaries.
- Deterministic local examples and fixtures, including a DEFRA/DESNZ-style dry-run fixture that requires no network, database, credentials, or production services.

## What Reviewers Can Try Safely

From a local checkout, reviewers can install the Python package, run the Python tests, and execute the local dry-run fixture described in the README:

```bash
python -m pip install -e .
python -m pytest
carbonops-parser local-dry-run \
  --local-path examples/fixtures/defra_desnz_minimal.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-minimal-fixture \
  --content-type text/csv \
  --format-hint csv
```

The quickstart is non-destructive. It does not execute SQL, connect to PostgreSQL, perform source downloads, call live source endpoints, run a scheduler, or require credentials.

## Known Limits

- No production carbon-accounting correctness, compliance correctness, legal correctness, source-owner correctness, or factor correctness is claimed.
- Live source availability and full upstream source coverage are not proven by the default local checks.
- PostgreSQL runtime writes remain disabled, preview-only, or opt-in depending on the boundary being exercised.
- Scheduler and production deployment behavior are documented as boundaries and roadmap items, not promoted production guarantees.
- GHG Protocol, DEFRA/DESNZ, and IPCC EFDB support should be read as Phase 1 ingestion and parser boundary support, not complete source-owner coverage.

## Suggested Public Release Notes Summary

CarbonOps-Parser is ready for public alpha/review as a local-safe, documentation-forward repository for carbon emissions data ingestion infrastructure. It provides searchable public documentation, deterministic examples, Python and .NET contract surfaces, PostgreSQL readiness boundaries, and a conservative roadmap for expanding carbon accounting emission factor ingestion without overclaiming production correctness.
