# PT-046 Parity Review: GHG Source Download Execution

Task-ID: PT-046

Task-Issue: #375

## Scope

Parity review for GHG source download execution across the Python and .NET
contract surfaces.

Reviewed files:

- `src/carbonfactor_parser/source_acquisition/ghg_source_download_execution_boundary.py`
- `tests/test_ghg_source_download_execution_boundary.py`
- `src/carbonfactor_parser/source_acquisition/contract_api.py`
- `src/dotnet/CarbonOps.Parser.Contracts/GhgSourceDownloadExecutionBoundary.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/GhgSourceDownloadExecutionRequest.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/GhgSourceDownloadExecutionResult.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/GhgSourceDownloadExecutionStatus.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/GhgSourceDownloadedArtifact.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/GhgSourceDownloadExecutionIssue.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/GhgSourceDownloadExecutionValidationResult.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/GhgSourceDownloadTransportResponse.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/ContractWireNames.cs`
- `tests/dotnet/CarbonOps.Parser.Contracts.Tests/GhgSourceDownloadExecutionBoundaryTests.cs`

This review did not add runtime database execution, production credentials,
source-specific ingestion outside the existing GHG boundary, parser coupling,
scheduler behavior, destructive database operations, or new source acquisition
runtime behavior.

## Post-OPS-032 Status

The original PT-046 review found blocking parity drift. OPS-032 / PR #512 was
merged to address that drift in the Python and .NET GHG source download
execution boundaries and focused tests.

After OPS-032, no remaining blocking parity mismatch was found for the current
runtime-passive GHG source download execution contract.

## Parity Findings

### Behavior And Contracts

Python and .NET expose the same high-level execution boundary:

- an explicit request created from a GHG discovery candidate
- an injected transport callback rather than an owned downloader client
- validation before transport execution
- fail-closed blocking for unsafe or non-opted-in requests
- checksum calculation before file persistence
- local artifact metadata on successful downloads
- result side-effect flags that keep parsing, SQL, database writes, and
  scheduler execution out of this boundary

The public status vocabulary is aligned:

| Concept | Python | .NET | Wire name |
| --- | --- | --- | --- |
| Blocked before execution | `BLOCKED` | `Blocked` | `blocked` |
| Download persisted | `DOWNLOADED` | `Downloaded` | `downloaded` |
| Execution failed | `FAILED` | `Failed` | `failed` |

The request, response, artifact, issue, validation-result, and execution-result
records are aligned by concept, with language-appropriate casing differences.

### Naming And Schema Alignment

The request fields align by intent:

| Concept | Python | .NET |
| --- | --- | --- |
| Source family | `source_family` | `SourceFamily` |
| Source key | `source_key` | `SourceKey` |
| Candidate identity | `candidate_id`, `candidate_title` | `CandidateId`, `CandidateTitle` |
| Source URI | `source_reference_uri` | `SourceReferenceUri` |
| Artifact kind | `artifact_kind` | `ArtifactKind` |
| Target path | `target_root`, `target_relative_path` | `TargetRoot`, `TargetRelativePath` |
| Explicit execution flags | `allow_download_execution`, `allow_file_write`, `allow_network`, `allow_overwrite` | `AllowDownloadExecution`, `AllowFileWrite`, `AllowNetwork`, `AllowOverwrite` |
| Forbidden side-effect flags | `allow_parse`, `allow_database_writes`, `allow_scheduler` | `AllowParse`, `AllowDatabaseWrites`, `AllowScheduler` |
| Optional metadata | `content_type`, `extension`, `expected_checksum_sha256`, `document_year`, `reporting_year`, `version_label` | `ContentType`, `Extension`, `ExpectedChecksumSha256`, `DocumentYear`, `ReportingYear`, `VersionLabel` |

The result and artifact fields align by intent:

| Concept | Python | .NET |
| --- | --- | --- |
| Status | `status` | `Status` |
| Original request | `request` | `Request` |
| Artifact metadata | `artifact` | `Artifact` |
| Issues | `issues` | `Issues` |
| Downloaded convenience property | `downloaded` | `Downloaded` |
| Side-effect guards | `no_parse`, `no_database_writes`, `no_sql`, `no_scheduler` | `NoParse`, `NoDatabaseWrites`, `NoSql`, `NoScheduler` |
| Artifact id and local path | `artifact_id`, `local_path` | `ArtifactId`, `LocalPath` |
| Checksum and size | `checksum_sha256`, `size_bytes` | `ChecksumSha256`, `SizeBytes` |

The GHG source identity is conceptually aligned, but represented through
different type systems:

- Python uses string values: `ghg_protocol`.
- .NET uses `SourceFamily.GhgProtocol` plus a string source key of
  `ghg_protocol`.

### State Transitions

The primary transition model is aligned:

- invalid requests return `blocked` without invoking transport
- unsafe target paths return `blocked`
- transport exceptions return `failed`
- missing transport responses return `failed`
- missing transport content returns `failed`
- non-byte transport content is rejected in Python and unrepresentable through
  the .NET `byte[]` contract except through null-content validation
- blank transport metadata is rejected consistently
- empty transport content returns `failed`
- checksum mismatch returns `failed` before writing a file
- successful writes return `downloaded` with artifact metadata
- blocked and failed result validation requires diagnostic issue metadata
- successful results expose no issues and preserve side-effect guard flags

Both implementations block existing targets when overwrite is not explicitly
allowed, reject direct parser/database/scheduler opt-in flags, reject insecure
HTTP, require network opt-in for HTTPS references, and require target paths to
stay under an absolute target root.

### Error Semantics

Validation issue codes are aligned for the shared observable contract,
including:

- `GHG_SOURCE_DOWNLOAD_MISSING_SOURCE_KEY`
- `GHG_SOURCE_DOWNLOAD_MISSING_CANDIDATE_ID`
- `GHG_SOURCE_DOWNLOAD_MISSING_CANDIDATE_TITLE`
- `GHG_SOURCE_DOWNLOAD_MISSING_SOURCE_REFERENCE_URI`
- `GHG_SOURCE_DOWNLOAD_MISSING_ARTIFACT_KIND`
- `GHG_SOURCE_DOWNLOAD_MISSING_TARGET_ROOT`
- `GHG_SOURCE_DOWNLOAD_MISSING_TARGET_RELATIVE_PATH`
- `GHG_SOURCE_DOWNLOAD_SOURCE_FAMILY_MISMATCH`
- `GHG_SOURCE_DOWNLOAD_SOURCE_KEY_MISMATCH`
- `GHG_SOURCE_DOWNLOAD_CANDIDATE_NOT_DOWNLOADABLE`
- `GHG_SOURCE_DOWNLOAD_DISCOVERY_REFERENCE_NOT_DOWNLOADABLE`
- `GHG_SOURCE_DOWNLOAD_EXECUTION_NOT_ALLOWED`
- `GHG_SOURCE_DOWNLOAD_FILE_WRITE_NOT_ALLOWED`
- `GHG_SOURCE_DOWNLOAD_PARSE_NOT_ALLOWED`
- `GHG_SOURCE_DOWNLOAD_DATABASE_WRITES_NOT_ALLOWED`
- `GHG_SOURCE_DOWNLOAD_SCHEDULER_NOT_ALLOWED`
- `GHG_SOURCE_DOWNLOAD_NETWORK_NOT_ALLOWED`
- `GHG_SOURCE_DOWNLOAD_INSECURE_HTTP_NOT_ALLOWED`
- `GHG_SOURCE_DOWNLOAD_UNSAFE_SOURCE_REFERENCE_URI`
- `GHG_SOURCE_DOWNLOAD_SOURCE_REFERENCE_URI_MISSING_SCHEME`
- `GHG_SOURCE_DOWNLOAD_MALFORMED_SOURCE_REFERENCE_URI`
- `GHG_SOURCE_DOWNLOAD_TARGET_ROOT_NOT_ABSOLUTE`
- `GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_ABSOLUTE`
- `GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_URI`
- `GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_UNSAFE`
- `GHG_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE`
- `GHG_SOURCE_DOWNLOAD_TARGET_EXISTS`
- `GHG_SOURCE_DOWNLOAD_TRANSPORT_FAILED`
- `GHG_SOURCE_DOWNLOAD_RESPONSE_MISSING`
- `GHG_SOURCE_DOWNLOAD_RESPONSE_MISSING_CONTENT`
- `GHG_SOURCE_DOWNLOAD_RESPONSE_EMPTY_CONTENT`
- `GHG_SOURCE_DOWNLOAD_RESPONSE_BLANK_CONTENT_TYPE`
- `GHG_SOURCE_DOWNLOAD_RESPONSE_BLANK_FINAL_URI`
- `GHG_SOURCE_DOWNLOAD_CHECKSUM_MISMATCH`
- `GHG_SOURCE_DOWNLOAD_WRITE_FAILED`
- `GHG_SOURCE_DOWNLOAD_RESULT_SIDE_EFFECT_FLAG_ENABLED`
- `GHG_SOURCE_DOWNLOAD_RESULT_MISSING_ARTIFACT`
- `GHG_SOURCE_DOWNLOAD_RESULT_UNEXPECTED_ARTIFACT`
- `GHG_SOURCE_DOWNLOAD_RESULT_MISSING_ISSUES`

OPS-032 specifically addressed the prior blocking drift around discovery
reference diagnostics, blocked/failed result diagnostics, transport response
validation, blank response metadata validation, and malformed URI diagnostics.

### Target-Path Safety Semantics

Both implementations reject parent traversal, absolute relative paths, URI-like
target paths, existing final symlinks, and existing target files unless
overwrite is allowed.

Python continues to use directory-relative write hardening with `O_NOFOLLOW`
where platform support allows it. .NET performs containment and symlink checks
before and after transport and now has focused coverage for parent symlink swap
during transport. The runtime hardening mechanisms are language-specific, but
the observable contract remains fail-closed for the covered escape scenarios.

## Validation Performed

- Reviewed Python GHG source download request creation, request validation,
  execution, safe target preparation, transport response validation, artifact
  validation, result validation, and dedicated tests.
- Reviewed .NET GHG source download request creation, request validation,
  execution, target path validation, transport response validation, result
  validation, wire-name mapping, record shapes, and dedicated tests.
- Compared behavior, contracts, naming, schema alignment, state transitions,
  error semantics, side-effect guard flags, source identity, URI handling,
  target path safety, checksum failure behavior, overwrite behavior, and public
  test coverage after OPS-032.

## Remaining Risks

- This review confirms parity for the current GHG source download execution
  boundary only. It does not validate future source-specific ingestion,
  parser execution, scheduler behavior, or runtime database writes.
- Python and .NET use different platform mechanisms for target-path hardening;
  the covered observable contract is aligned, but absolute implementation
  equivalence is not expected across runtimes.
- Cross-language drift remains possible if future GHG download execution
  changes update one runtime without synchronized tests and parity review.

## Verdict

Merge-ready for parity-review scope.

The Python and .NET GHG source download execution surfaces are aligned for the
current runtime-passive contract shape, naming intent, status vocabulary,
explicit opt-in flow, state transitions, diagnostic issue semantics,
transport-response validation, malformed URI diagnostics, and side-effect
boundaries after OPS-032.

Task-ID: PT-046

Task-Issue: #375
