# RV-043 DEFRA Download Execution Readiness Review

## Executive Summary

This review covers DEFRA/DESNZ source download execution readiness after the
PT-048 parity checkpoint. The reviewed surface remains documentation and
contract oriented: DEFRA/DESNZ download execution is explicit, caller-driven,
and guarded against parser execution, scheduler behavior, SQL generation, and
runtime database writes.

No blocker was found for the next review checkpoint. The DEFRA/DESNZ download
execution boundary is ready to proceed with the accepted limitation that this
review does not validate production live-source availability, production
downloader behavior, or runtime database execution.

## Scope Reviewed

- PT-048 DEFRA source download execution parity review.
- Python DEFRA source download execution request, validation, execution result,
  artifact, issue, and transport-response contracts.
- Python contract API exports for the DEFRA download execution boundary.
- Focused Python tests covering explicit opt-in behavior, non-downloadable
  discovery candidates, unsafe input blocking, injected transport behavior,
  checksum handling, path safety, side-effect flags, and runtime-passive import
  behavior.
- .NET DEFRA source download execution contract and focused parity test surface
  as summarized by PT-048.

This review did not modify product or runtime source code.

## DEFRA/DESNZ Download Execution Readiness Assessment

The DEFRA/DESNZ download execution boundary is ready for the next review
checkpoint within its current contract scope.

The boundary requires explicit request flags before execution:

- `allow_download_execution`
- `allow_file_write`
- `allow_network` for HTTPS references
- `allow_overwrite` when replacing an existing target is intended

The execution path is caller-driven through an injected transport callback. The
boundary does not own source-specific HTTP clients, production retry behavior,
authentication, release scheduling, parser execution, normalization, or
database persistence. Successful execution produces local artifact metadata
with source identity, candidate identity, local path, checksum, size, content
metadata, and version/year metadata where available.

Validation remains fail-closed for missing required fields, non-DEFRA source
identity, non-downloadable candidates, discovery references, insecure or unsafe
URI schemes, missing network opt-in, unsafe target paths, symlink escapes,
existing targets without overwrite opt-in, failed transport responses, empty
content, blank response metadata, checksum mismatches, and write failures.

## Contract And Boundary Consistency Notes

- Source identity is consistently scoped to `defra_desnz`.
- The public status model remains `blocked`, `downloaded`, and `failed`.
- Blocked and failed results require diagnostic issues.
- Downloaded results require artifact metadata.
- Non-downloaded results must not include artifact metadata.
- Result side-effect guard flags preserve no parser execution, no database
  writes, no SQL behavior, and no scheduler behavior.
- Python and .NET contract surfaces are aligned by PT-048 for request shape,
  result shape, artifact metadata, issue diagnostics, status vocabulary,
  transport-response validation, malformed URI diagnostics, and observable
  target-path safety behavior.
- The contract API exports the DEFRA download execution boundary without adding
  a broader ingestion, parser, scheduler, or database dependency.

## Safety Assessment

No production credentials are introduced or required by this review. The
DEFRA/DESNZ download execution request does not contain raw connection strings,
database credentials, source credentials, or environment-backed secret loading.

No live source endpoint calls were made for this review. The reviewed execution
boundary uses caller-provided transport and the focused tests use local,
deterministic mock-style payloads.

No runtime database execution was performed or added. The boundary exposes
`allow_database_writes` only as a forbidden side-effect flag and validates that
it remains disabled.

No destructive database operations were performed or added. The reviewed
boundary does not generate SQL, open database sessions, run migrations,
truncate tables, delete records, or otherwise mutate runtime database state.

## Remaining Risks

- This review confirms readiness only for the current DEFRA/DESNZ download
  execution contract and review checkpoint; it does not validate production
  live-source availability, endpoint stability, retry behavior, rate limiting,
  caching, or authentication.
- The boundary can write local files when explicitly opted in, so future callers
  still need integration-level controls for target roots, retention policy,
  operator approval, and artifact lifecycle.
- Parser execution, normalization, scheduler integration, and persistence
  remain outside this review and require their own readiness checks before any
  production workflow claim.
- Python and .NET use language-specific filesystem hardening mechanisms; PT-048
  found the observable contract aligned, but future changes can reintroduce
  cross-runtime drift without synchronized tests.
- The review did not execute live network, parser, scheduler, or database
  workflows by design, so operational readiness for those systems remains
  unproven.

## Verdict

ready for next review checkpoint

Task-ID: RV-043
Task-Issue: #388
