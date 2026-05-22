# Roadmap

This roadmap organizes the path from the documentation baseline to a `v0.1.0` reference release.

## Sprint 1: Documentation Baseline

- Add public project positioning.
- Document architecture, configuration, database model, background job model, and source support.
- Document limitations and public wording rules.
- Add README files for PostgreSQL, Python, and .NET paths.

## Sprint 2: PostgreSQL Schema Baseline

- Add initial PostgreSQL schema scripts.
- Define shared ingestion metadata tables.
- Define initial source-specific table groups.
- Add schema setup notes and reviewable examples.

## Sprint 3: Python Source Discovery Baseline

- Add Python project skeleton.
- Add configuration loading placeholder.
- Add source discovery command structure.
- Inspect DEFRA/DESNZ source structure first.

## Sprint 4: Python Startup and Archive Baseline

- Add PostgreSQL startup check.
- Add schema availability check.
- Add raw archive path handling.
- Add hash calculation and idempotency planning.

## Sprint 5: First DEFRA/DESNZ Ingestion Slice

- Add first parser mapping for discovered DEFRA/DESNZ structures.
- Validate parsed records.
- Persist source-specific records and import summaries.

## Sprint 6: .NET Worker Baseline

- Add independent .NET Worker Service structure.
- Add configuration model.
- Add database startup check design.
- Add background schedule skeleton.

## Production Parity Sequence

Project-level production-ready is not claimed in this roadmap. The Python
runtime has a production operator path; the .NET runtime is not
production-ready yet. The required .NET sequence is:

- Add .NET service/scheduled-worker entrypoint. Added by PROD-003 as a
  scheduled-worker command-surface baseline only.
- Add .NET production config loader and redaction.
- Add .NET PostgreSQL schema bootstrap and year-state.
- Add .NET source discovery/download/parsing orchestration.
- Add .NET source-specific master/detail insert.
- Add .NET idempotency and rerun behavior.
- Add .NET Docker PostgreSQL E2E tests.
- Add Python/.NET parity validation.
- Record the final project production-ready verdict.

## Sprint 7: GHG Protocol and IPCC Preparation

- Add source discovery outputs for GHG Protocol.
- Add source discovery outputs for IPCC EFDB.
- Refine source-specific table groups after inspection.

## Sprint 8: v0.1.0 Release Preparation

- Review documentation for consistency.
- Add release notes.
- Confirm Phase 1 scope and limitations are clear.
- Prepare `v0.1.0` tag notes after review.
