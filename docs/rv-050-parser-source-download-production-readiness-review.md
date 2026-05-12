# RV-050 Parser And Source Download Production Readiness Review

## Summary

This review covers the completed parser/source-download expansion for GHG
Protocol, DEFRA/DESNZ, and IPCC EFDB normalized output paths. The reviewed
contract surface is coherent enough for the next persistence-integration task:
source acquisition can describe discovered/downloaded artifacts, those artifacts
can be bridged into parser input metadata, the parser content boundaries produce
source identity and provenance fields, and persistence input already requires
normalized records to carry source identity before database execution.

No blocking contract mismatch was found that requires a code fix in this review
scope.

## Reviewed Scope

- Source discovery and download boundaries for GHG Protocol, DEFRA/DESNZ, and
  IPCC EFDB.
- Source download artifact metadata and source-artifact to parser-input bridge
  contracts.
- Phase 1 parser adapter registry and parser input artifact contracts.
- GHG Protocol, DEFRA/DESNZ, and IPCC EFDB content parser normalized output
  paths.
- Parser execution to normalization handoff and normalization input boundaries.
- Persistence input boundary and PostgreSQL preview/runtime safety gates.
- Existing parity notes for PT-046, PT-048, and PT-053.

## Readiness Findings

The source families use stable source identities across acquisition, parser
input, parser execution, normalized raw fields, and persistence preparation:

- `ghg_protocol`
- `defra_desnz`
- `ipcc_efdb`

The source-download execution boundaries remain explicitly opt-in and
side-effect guarded. They reject unsafe paths and non-opted-in network/file
write behavior, preserve checksum/provenance metadata on successful artifact
creation, and keep parser execution, SQL, database writes, and scheduler
behavior out of the download boundary.

The source-artifact to parser-input bridge preserves local artifact reference,
source family/key, parser key, content metadata, checksum, document year, and
reporting year without reading files or calling external systems. That is enough
metadata for persistence integration to identify source lineage and artifact
provenance after parser execution.

The parser content boundaries for GHG Protocol, DEFRA/DESNZ normalized
extraction rows, and IPCC EFDB produce deterministic normalized raw fields with
`source_family`, `source_id`, source year/version, factor identity/value/unit,
source-specific categorization fields, provenance artifact reference, checksum
metadata, row number, and stable master/detail external keys.

The persistence input boundary is appropriately fail-closed for this stage: it
requires normalized records to include `source_family` and `source_id`, rejects
mixed source identities in a single persistence input, and does not connect to
or write to a database.

## Known Limitations

- The reviewed source-download paths are contract and local-test ready; they do
  not prove live-source availability, live network reliability, or production
  downloader scheduling.
- GHG Protocol and IPCC EFDB have parser normalized content paths and parity
  fixtures, but no source-specific normalization mapper to convert their parser
  raw payloads into `NormalizationResult` records for persistence input yet.
- DEFRA/DESNZ has a local dry-run path through normalization and persistence
  input, but the existing mapper is still scoped as a minimal fixture/extraction
  mapper and does not claim source correctness.
- The normalized parser outputs are deterministic local CSV-style extraction
  contracts, not complete production parsers for arbitrary upstream workbooks,
  PDFs, web pages, or downloaded archives.
- The download execution boundaries use injected transport/local fixtures in
  tests; they do not own production HTTP retry, rate limiting, authentication,
  caching, or release packaging behavior.
- Persistence integration remains preview/contract oriented. Runtime database
  execution is guarded separately and was not executed in this review.
- Cross-language drift remains possible if Python and .NET source-download or
  parser contracts are changed without synchronized parity fixtures/tests.

## Verdict

Merge-ready for RV-050 review scope.

The parser/source-download contracts are coherent enough for persistence
integration to proceed, with the limitations above treated as follow-on scope
rather than blockers for this review.

Task-ID: RV-050
Task-Issue: #479
