# PT-053 Parity Review: IPCC Source Download Execution

Task-ID: PT-053

Task-Issue: #478

## Scope

Parity review for IPCC EFDB source download execution across the Python and
.NET contract surfaces.

Reviewed files:

- `src/carbonfactor_parser/source_acquisition/ipcc_source_download_execution_boundary.py`
- `tests/test_ipcc_source_download_execution_boundary.py`
- `src/dotnet/CarbonOps.Parser.Contracts/IpccSourceDownloadExecutionBoundary.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/IpccSourceDownloadExecutionRequest.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/IpccSourceDownloadExecutionResult.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/IpccSourceDownloadExecutionStatus.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/IpccSourceDownloadedArtifact.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/IpccSourceDownloadExecutionIssue.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/IpccSourceDownloadExecutionValidationResult.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/IpccSourceDownloadTransportResponse.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/ContractWireNames.cs`
- `tests/dotnet/CarbonOps.Parser.Contracts.Tests/IpccSourceDownloadExecutionBoundaryTests.cs`
- `tests/fixtures/parity/ipcc_source_download_execution_expectations.json`

This review did not add live network calls, production database credentials,
parser execution, scheduler behavior, runtime database execution, destructive
database operations, branch cleanup, or worktree cleanup.

## Fixture Coverage

Python and .NET now read the same deterministic fixture:

- `tests/fixtures/parity/ipcc_source_download_execution_expectations.json`

The shared fixture covers:

- successful download metadata and checksum capture
- existing known document idempotency
- checksum mismatch failure before file persistence
- default discovery candidate blocked before transport
- blank transport response metadata failure

The fixture is local-only and uses injected mock transport payloads.

## Parity Findings

Python and .NET are aligned for the shared IPCC EFDB download execution
contract shape:

- explicit request creation from IPCC discovery candidate metadata
- explicit opt-in for download execution and file writes
- injected transport callback instead of owned downloader behavior
- validation before transport execution
- fail-closed blocking for unsafe or non-opted-in requests
- checksum calculation before file persistence
- artifact metadata capture on successful or already-known local documents
- side-effect guard flags for parse, SQL, database writes, and scheduler work

The status vocabulary is aligned for blocked, downloaded, and failed outcomes.
.NET additionally exposes `already_known` for idempotent existing documents.
Python preserves its existing public API by returning `downloaded` with
`reused_existing=true` on the artifact. The shared fixture documents and tests
that as an intentional current difference.

## Metadata And Naming

Common metadata expectations are aligned:

- source family/key: `ipcc_efdb`
- candidate id/title
- source reference URI
- artifact kind
- content type and extension
- document year, reporting year, and version label
- checksum SHA-256 and size in bytes
- local path/original filename semantics
- issue code diagnostics

Language-specific representation differences remain non-blocking:

- Python uses string source-family values; .NET uses `SourceFamily.IpccEfdb`.
- Python records `retrieved_at_label`; .NET records `RetrievedAtUtc`.
- Python records `storage_identity` and `reused_existing`; .NET records an
  `AlreadyKnown` result property/status.

## Error Semantics

The shared fixture confirms aligned issue codes for:

- `IPCC_SOURCE_DOWNLOAD_CANDIDATE_NOT_DOWNLOADABLE`
- `IPCC_SOURCE_DOWNLOAD_DISCOVERY_REFERENCE_NOT_DOWNLOADABLE`
- `IPCC_SOURCE_DOWNLOAD_CHECKSUM_MISMATCH`
- `IPCC_SOURCE_DOWNLOAD_RESPONSE_BLANK_CONTENT_TYPE`
- `IPCC_SOURCE_DOWNLOAD_RESPONSE_BLANK_FINAL_URI`

Existing dedicated tests in both runtimes also cover unsafe URI schemes,
target path validation, symlink safety, transport failure, missing/empty
transport responses, side-effect flag validation, and result validation.

## Remaining Risks

- This review confirms the current IPCC EFDB source download execution boundary
  only. It does not validate parser execution, scheduler behavior, production
  database writes, or future source-specific ingestion.
- Python and .NET use different target-path hardening mechanisms. The covered
  observable contract is aligned, but implementation-level equivalence is not
  expected across runtimes.
- Existing-document idempotency remains intentionally represented differently:
  Python returns `downloaded` plus `reused_existing=true`; .NET returns
  `already_known`.
- Cross-language drift remains possible if future IPCC download changes update
  only one runtime without synchronized fixture coverage.

## Verdict

Commit-ready for parity-review scope.

Task-ID: PT-053

Task-Issue: #478
