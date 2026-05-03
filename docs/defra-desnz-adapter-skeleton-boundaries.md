# DEFRA/DESNZ Adapter Skeleton Boundaries

`DefraDesnzSourceAdapter` is a local fixture-based discovery skeleton only. This document makes that boundary explicit so the adapter is not confused with real ingestion, downloading, parsing, source-owner data handling, or correctness validation.

## Purpose

The boundary document exists because `DefraDesnzSourceAdapter` carries a real source-family identity while its behavior is intentionally minimal.

The adapter currently demonstrates how a source-specific adapter can identify a source family, filter local artificial fixture filenames, and emit `SourceDocument` references. It does not process real source material.

## Current Behavior

The skeleton currently:

- Represents DEFRA/DESNZ source identity in the adapter layer through `SourceFamily.DEFRA_DESNZ`.
- Discovers artificial local fixture files from a caller-provided directory.
- Uses deterministic prefix filtering for `defra_desnz_` fixture names by default.
- Uses deterministic extension filtering for `.csv` and `.json` fixture files by default.
- Emits `SourceDocument` references with source family, source name, and file reference metadata.
- Participates in explicit `SourceAdapterRegistry` tests.
- Works with the source adapter summary helper in tests.

The adapter remains non-recursive and does not inspect file contents.

`DefraDesnzFixtureManifest` describes already-discovered local fixture documents before any later parser or ingestion handoff. It is a model-only manifest and does not read fixture contents.

See `examples/defra_desnz_fixture_manifest_example.py` for a fixture-only example that discovers local artificial documents and builds the manifest.

See [Parser Handoff Boundary](parser-handoff-boundary.md) for the separation between fixture manifests and future parser execution.

## Not Implemented

The skeleton does not provide:

- Real ingestion.
- Source-owner data.
- Real emission factor values.
- Real source URLs.
- Downloading or remote access.
- Authentication or sensitive access handling.
- Parser execution.
- Normalization.
- Persistence.
- Scheduler, retry, or cancellation behavior.
- Compliance, legal, or correctness determination.

## Fixture Policy

DEFRA/DESNZ adapter fixtures must remain artificial and tiny.

Fixture files exist only to test deterministic local discovery, source identity metadata, prefix filtering, extension filtering, registry compatibility, and summary helper behavior.

Fixture contents must not include source-owner data or real factor values. Fixture names may use `defra_desnz_` prefixes only to test source identity filtering.

## Review Checklist

Before approving future `DefraDesnzSourceAdapter` changes, reviewers should confirm:

- No real URLs are added.
- No real factor values are added.
- No parser assumptions are introduced.
- No downloading or remote access is added.
- No correctness claims are added.
- No database, persistence, scheduler, retry, or cancellation coupling is added.
- Tests remain deterministic and local.
- Fixtures remain artificial and small.

## Future Extension Boundaries

Future work should remain split into separate tasks:

- Real source discovery should be a separate task.
- Downloading should be a separate task.
- Parser implementation should be a separate task.
- Persistence should stay behind a separate ingestion boundary.
- Scheduler and retry behavior should remain outside the adapter package unless a later task explicitly scopes that boundary.

Each future task should keep source discovery, retrieval, parsing, normalization, persistence, and runtime orchestration reviewable as separate changes.

## Related Docs

- [Source-Specific Adapter Skeleton Guidance](source-specific-adapter-skeleton-guidance.md)
- [Source Adapter Execution Flow](source-adapter-execution-flow.md)
- [Source Adapter Configuration Boundaries](source-adapter-configuration-boundaries.md)
- [Source Adapter Error And Warning Handling](source-adapter-error-warning-handling.md)
