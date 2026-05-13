# RV-052 Phase 1 Ingestion Orchestrator Production Readiness Review

## Summary

This review covers the Phase 1 ingestion orchestrator contracts across Python
and .NET before service and scheduler hardening. The reviewed contract surface
is coherent enough for service/runtime integration planning to proceed:
source-family selection is explicit, execution is runtime-injected and
sequential by default, run state is captured in top-level and per-family
results, partial failures are reported deterministically, and PostgreSQL runtime
readiness remains fail-closed before source execution.

No blocking contract mismatch was found that requires a code fix in this review
scope.

## Reviewed Scope

- Python Phase 1 ingestion orchestrator request, dependency, runtime, result,
  summary, and failure contracts.
- Python orchestrator tests for source-family selection, duplicate selection,
  sequential execution, PostgreSQL readiness blocking, deterministic stage
  failures, and partial family failure semantics.
- .NET Phase 1 ingestion orchestrator request, dependency, runtime, result, and
  failure contracts.
- .NET orchestrator tests for explicit source selection, duplicate selection,
  sequential execution, bounded-parallel blocking, PostgreSQL runtime config
  blocking, and partial family failure semantics.
- Related persistence, parser, source acquisition, and PostgreSQL runtime safety
  contracts used by the orchestrator boundary.

## Readiness Findings

Source-family selection is explicit and limited to the Phase 1 source families:
`ghg_protocol`, `defra_desnz`, and `ipcc_efdb`. Python accepts stable aliases
such as `ghg`, `defra`, and `ipcc` before normalizing to canonical family keys;
.NET accepts the `SourceFamily` enum and filters duplicate selections. Both
surfaces require at least one valid family and avoid running unselected
families.

Run state is structured enough for a service adapter to observe orchestration
outcomes. Python records top-level run status, selected families, per-family
stage-specific statuses, summary counts, persisted counts, and structured
failure details. .NET records top-level run status, selected families,
per-family completed/failed status, aggregate counts, persisted counts, and
structured stage failures.

Retry and idempotency posture is intentionally conservative. The orchestrators
do not implement retry loops, background scheduling, queue claims, distributed
locks, or automatic replay. Duplicate source-family selections collapse to one
execution in both languages. Repository and parsed-factor persistence contracts
remain responsible for attempted/persisted counts and validation failures, while
database idempotency, conflict policy, transaction retry, and rollback behavior
remain deferred to scoped runtime persistence work.

Partial failure semantics are deterministic. A failing family produces a
per-family failure result and does not prevent later selected families from
running in sequential order. Top-level status becomes
`completed_with_failures`/`CompletedWithFailures` when at least one family
completes and at least one fails, and `failed`/`Failed` when no selected family
completes. Repository, parser, acquisition, and runtime exception stages are
reported through structured failure records.

Runtime readiness remains guarded. Python can block before source execution
when PostgreSQL runtime config is not ready or schema bootstrap reports missing
required tables. .NET blocks before source execution when PostgreSQL runtime
configuration is requested but not enabled. Both surfaces keep production
credentials, environment loading, scheduler behavior, and destructive database
operations outside this orchestrator review.

## Known Limitations

- The orchestrators are contract/runtime-injection boundaries, not production
  services. No scheduler, worker lifecycle, service installer, queue consumer,
  cancellation, lease, distributed lock, or deployment packaging behavior is
  added or validated here.
- Retry behavior is not implemented. Production retry policy, backoff,
  dead-letter handling, and replay safety remain future service/runtime scope.
- End-to-end idempotency is not proven at the orchestrator level. Duplicate
  family selection is idempotent, but database conflict policy, transaction
  rollback, version/hash replay handling, and source document uniqueness remain
  persistence/runtime responsibilities.
- Python and .NET have different internal runtime shapes: Python separates
  discovery, download, and parse calls; .NET combines discovery/download before
  normalization. This is acceptable for the current review because both expose
  equivalent observable orchestration outcomes, but future parity work should
  preserve cross-language stage semantics when runtime adapters harden.
- Python has a schema-bootstrap readiness input on the orchestrator request;
  .NET currently gates PostgreSQL runtime config but does not model the same
  schema-bootstrap report on the orchestrator request. This is a known runtime
  integration gap, not a merge blocker for the contract review because .NET
  schema bootstrap execution is still separately scoped.
- .NET per-family status is coarser than Python's stage-specific family status.
  Stage details are still present in structured failure records, so service
  integration can classify failures, but exact enum parity is not present.
- Parser/source/downloader implementations remain fixture or boundary scoped in
  tests. This review does not prove live upstream availability, source
  correctness, carbon-accounting correctness, or arbitrary production document
  handling.

## Verdict

Merge-ready for RV-052 review scope.

The Phase 1 ingestion orchestrator behavior is coherent enough for
service/runtime integration to proceed, with the limitations above treated as
follow-on hardening scope rather than blockers for this review.

Task-ID: RV-052
Task-Issue: #488
