# RV-051 Parsed Factor Persistence Production Readiness Review

## Summary

This review covers the parsed factor persistence writer contracts added after
PT-054. The reviewed path is coherent enough for full ingestion orchestration to
begin wiring parser output into the source-family repository boundary: Python
and .NET both map parsed normalized rows into source-family master/detail
records, preserve source document identity, validate required factor fields,
deduplicate identical identities, reject conflicting duplicates, and return
declared/failed/no-records outcomes without enabling PostgreSQL runtime writes.

One narrow contract fix was made during this review: the Python public API test
now explicitly covers the parsed factor persistence writer types and both build
and persist functions.

## Reviewed Scope

- Python parsed factor persistence writer boundary.
- .NET parsed factor persistence writer contract boundary.
- Shared parity fixture for fallback persistence identity and checksums.
- Source-family repository validation contracts used by the writer.
- PostgreSQL repository and runtime execution safety gates.
- Persistence package public exports.

## Readiness Findings

The writer has a stable in-memory command boundary. Both language surfaces build
source-family master/detail records with deterministic identifiers, external
keys, record checksums, lifecycle status, and timestamp labels.

The Python writer accepts both `ParsedRawRecordPayload` and
`ParserNormalizedOutputBatch`; the .NET writer accepts
`ParserNormalizedOutputBatch`. Both surfaces validate required source document
identity, factor value, and factor unit before calling the repository.

Duplicate handling is explicit. Identical master/detail identities are
deduplicated and counted; conflicting identities produce validation issues and
block repository submission.

The repository handoff remains protocol-level. The fake/source-family repository
tests verify attempted and persisted counts, while the concrete PostgreSQL
repository still returns unsupported and does not connect, run SQL, write
records, start transactions, or load credentials.

The shared parity fixture confirms cross-language fallback persistence intent
for source document id, master/detail ids, external keys, checksums, and default
timestamps.

## Known Limitations

- This is not an end-to-end ingestion orchestration path. No scheduler,
  downloader, parser runner, repository runtime execution, or database write path
  is added here.
- PostgreSQL runtime persistence remains intentionally disabled and unsupported.
- The writer maps only the current source-family master/detail contract fields;
  production database migrations, conflict actions, transaction behavior, retry
  policy, observability, and rollback verification remain future work.
- Python and .NET do not accept identical input shapes: Python also accepts raw
  parsed payloads, while .NET currently covers normalized output batches.
- The default timestamp label is deterministic review metadata, not a production
  clock value.
- Source correctness, carbon-accounting correctness, and upstream data coverage
  are not claimed by this review.

## Verdict

Merge-ready for RV-051 review scope.

The parsed factor persistence writer behavior is coherent enough for the next
full ingestion orchestration task, with the limitations above treated as
follow-on scope rather than blockers for this review.

Task-ID: RV-051
Task-Issue: #483
