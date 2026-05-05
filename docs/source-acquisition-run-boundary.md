# Source Acquisition Run Boundary

## Scope

The source acquisition run helper is a small synchronous orchestration utility. It runs acquisition for a provided descriptor sequence using a provided client and returns deterministic run metadata.

## Included Behavior

- deterministic descriptor ordering for acquisition results
- deterministic manifest-entry construction from acquisition results
- optional local JSON manifest writing when a manifest path is provided
- deterministic summary counts for acquired, failed, and skipped or not-implemented outcomes
- centralized source acquisition status constants and predicate helpers with preserved
  compatibility values (`"acquired"`, `"failed"`, `"skipped"`, and `"not_implemented"`)
- deterministic status counting helper behavior that ignores unknown statuses

## Explicit Non-Goals

- no scheduler or background job behavior
- no database persistence
- no parser execution
- no retry or cancellation flow
- no source-specific parsing assumptions
- no timestamps in run metadata (by design for this phase)

## Local Manifest Boundary

Manifest writing is optional. If enabled, the helper writes local JSON via the existing manifest writer boundary and returns the written local path.
