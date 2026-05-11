# PT-048 Parity Review: DEFRA Source Download Execution

Task-ID: PT-048

Task-Issue: #381

## Scope

Parity review for DEFRA source download execution across the Python and .NET
contract surfaces.

Reviewed files:

- `src/carbonfactor_parser/source_acquisition/defra_source_download_execution_boundary.py`
- `tests/test_defra_source_download_execution_boundary.py`
- `src/carbonfactor_parser/source_acquisition/contract_api.py`
- `src/dotnet/CarbonOps.Parser.Contracts/DefraSourceDownloadExecutionBoundary.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/DefraSourceDownloadExecutionRequest.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/DefraSourceDownloadExecutionResult.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/DefraSourceDownloadExecutionStatus.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/DefraSourceDownloadedArtifact.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/DefraSourceDownloadExecutionIssue.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/DefraSourceDownloadExecutionValidationResult.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/DefraSourceDownloadTransportResponse.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/ContractWireNames.cs`
- `tests/dotnet/CarbonOps.Parser.Contracts.Tests/DefraSourceDownloadExecutionBoundaryTests.cs`

This review did not add source-specific ingestion beyond the existing DEFRA
download boundary, parser execution, scheduler behavior, runtime database
execution, production configuration, credentials, destructive database
operations, or source discovery network access.

Allowed files for this implementation were constrained to:

- `src/carbonfactor_parser/source_acquisition/defra_source_download_execution_boundary.py`
- `tests/test_defra_source_download_execution_boundary.py`
- `docs/pt-048-defra-source-download-execution-parity-review.md`

## Parity Findings

Python-side validation gaps were found and fixed during this review:

- Python now classifies malformed source reference URIs with
  `DEFRA_SOURCE_DOWNLOAD_MALFORMED_SOURCE_REFERENCE_URI`, matching .NET for
  malformed `://` inputs and hostless HTTP(S) references.
- Python now distinguishes a missing transport response from missing transport
  content with `DEFRA_SOURCE_DOWNLOAD_RESPONSE_MISSING` and
  `DEFRA_SOURCE_DOWNLOAD_RESPONSE_MISSING_CONTENT`.
- Python now rejects blank transport response `content_type` and `final_uri`
  metadata with the .NET-aligned response metadata issue codes.
- Python now rejects undefined result statuses with
  `DEFRA_SOURCE_DOWNLOAD_RESULT_INVALID_STATUS`, matching the .NET result
  validation rule.

No remaining blocking parity mismatch was found.

### Behavior And Contracts

Both implementations expose the same explicit execution boundary shape:

- a request created from DEFRA discovery candidate metadata
- explicit opt-in flags for download execution and file writes
- an injected transport callback instead of an owned downloader client
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

The request, transport response, artifact, issue, validation-result, and
execution-result records are aligned by concept, with language-appropriate
casing differences.

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

The DEFRA source identity is conceptually aligned:

- Python uses string values: `defra_desnz`.
- .NET uses `SourceFamily.DefraDesnz` plus a string source key of
  `defra_desnz`.

Python and .NET use different implementation provenance labels in test fixture
metadata (`py048_mock_download` and `dn048_mock_download`). The field shape and
validation semantics are aligned, and the label difference is non-blocking
because the boundary treats it only as metadata.

### State Transitions

The primary transition model is aligned:

- invalid requests return `blocked` without invoking transport
- default DEFRA discovery candidates are not downloadable and remain blocked
- unsafe target paths return `blocked`
- transport exceptions return `failed`
- missing transport responses return `failed`
- missing transport content returns `failed`
- non-byte transport content is rejected in Python and unrepresentable through
  the .NET `byte[]` contract except through null-content validation
- blank transport response metadata is rejected consistently
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

- `DEFRA_SOURCE_DOWNLOAD_MISSING_SOURCE_KEY`
- `DEFRA_SOURCE_DOWNLOAD_MISSING_CANDIDATE_ID`
- `DEFRA_SOURCE_DOWNLOAD_MISSING_CANDIDATE_TITLE`
- `DEFRA_SOURCE_DOWNLOAD_MISSING_SOURCE_REFERENCE_URI`
- `DEFRA_SOURCE_DOWNLOAD_MISSING_ARTIFACT_KIND`
- `DEFRA_SOURCE_DOWNLOAD_MISSING_TARGET_ROOT`
- `DEFRA_SOURCE_DOWNLOAD_MISSING_TARGET_RELATIVE_PATH`
- `DEFRA_SOURCE_DOWNLOAD_SOURCE_FAMILY_MISMATCH`
- `DEFRA_SOURCE_DOWNLOAD_SOURCE_KEY_MISMATCH`
- `DEFRA_SOURCE_DOWNLOAD_CANDIDATE_NOT_DOWNLOADABLE`
- `DEFRA_SOURCE_DOWNLOAD_DISCOVERY_REFERENCE_NOT_DOWNLOADABLE`
- `DEFRA_SOURCE_DOWNLOAD_EXECUTION_NOT_ALLOWED`
- `DEFRA_SOURCE_DOWNLOAD_FILE_WRITE_NOT_ALLOWED`
- `DEFRA_SOURCE_DOWNLOAD_PARSE_NOT_ALLOWED`
- `DEFRA_SOURCE_DOWNLOAD_DATABASE_WRITES_NOT_ALLOWED`
- `DEFRA_SOURCE_DOWNLOAD_SCHEDULER_NOT_ALLOWED`
- `DEFRA_SOURCE_DOWNLOAD_NETWORK_NOT_ALLOWED`
- `DEFRA_SOURCE_DOWNLOAD_INSECURE_HTTP_NOT_ALLOWED`
- `DEFRA_SOURCE_DOWNLOAD_UNSAFE_SOURCE_REFERENCE_URI`
- `DEFRA_SOURCE_DOWNLOAD_SOURCE_REFERENCE_URI_MISSING_SCHEME`
- `DEFRA_SOURCE_DOWNLOAD_MALFORMED_SOURCE_REFERENCE_URI`
- `DEFRA_SOURCE_DOWNLOAD_TARGET_ROOT_NOT_ABSOLUTE`
- `DEFRA_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_ABSOLUTE`
- `DEFRA_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_URI`
- `DEFRA_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_UNSAFE`
- `DEFRA_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE`
- `DEFRA_SOURCE_DOWNLOAD_TARGET_EXISTS`
- `DEFRA_SOURCE_DOWNLOAD_TRANSPORT_FAILED`
- `DEFRA_SOURCE_DOWNLOAD_RESPONSE_MISSING`
- `DEFRA_SOURCE_DOWNLOAD_RESPONSE_MISSING_CONTENT`
- `DEFRA_SOURCE_DOWNLOAD_RESPONSE_EMPTY_CONTENT`
- `DEFRA_SOURCE_DOWNLOAD_RESPONSE_BLANK_CONTENT_TYPE`
- `DEFRA_SOURCE_DOWNLOAD_RESPONSE_BLANK_FINAL_URI`
- `DEFRA_SOURCE_DOWNLOAD_CHECKSUM_MISMATCH`
- `DEFRA_SOURCE_DOWNLOAD_WRITE_FAILED`
- `DEFRA_SOURCE_DOWNLOAD_RESULT_INVALID_STATUS`
- `DEFRA_SOURCE_DOWNLOAD_RESULT_SIDE_EFFECT_FLAG_ENABLED`
- `DEFRA_SOURCE_DOWNLOAD_RESULT_MISSING_ARTIFACT`
- `DEFRA_SOURCE_DOWNLOAD_RESULT_UNEXPECTED_ARTIFACT`
- `DEFRA_SOURCE_DOWNLOAD_RESULT_MISSING_ISSUES`

.NET additionally validates null request/result inputs and undefined enum
values. Python reaches the same supported contract outcome through dataclass
construction and string-field validation, so that difference is
language-runtime-specific rather than a blocking parity issue.

### Target-Path Safety Semantics

Both implementations reject parent traversal, absolute relative paths, URI-like
target paths, existing final symlinks, and existing target files unless
overwrite is allowed.

Python uses directory-relative write hardening with `O_NOFOLLOW` and fails
closed when required platform flags are unavailable. .NET performs containment
and symlink checks around the write path and has focused coverage for parent
symlink swap during transport. The runtime hardening mechanisms are
language-specific, but the observable contract remains fail-closed for the
covered escape scenarios.

## Validation Performed

- Reviewed Python DEFRA source download request creation, request validation,
  execution, safe target preparation, transport response validation, artifact
  validation, result validation, public API export coverage, and dedicated
  tests.
- Reviewed .NET DEFRA source download request creation, request validation,
  execution, target path validation, transport response validation, result
  validation, wire-name mapping, record shapes, and dedicated tests.
- Compared behavior, contracts, naming, schema alignment, state transitions,
  error semantics, side-effect guard flags, source identity, URI handling,
  target path safety, checksum failure behavior, overwrite behavior, and public
  test coverage.

## Remaining Risks

- This review confirms parity for the current DEFRA source download execution
  boundary only. It does not validate future source-specific ingestion,
  parser execution, scheduler behavior, or runtime database writes.
- Python and .NET use different platform mechanisms for target-path hardening;
  the covered observable contract is aligned, but absolute implementation
  equivalence is not expected across runtimes.
- Cross-language drift remains possible if future DEFRA download execution
  changes update one runtime without synchronized tests and parity review.
- Local `pytest` execution was blocked because the active Python environment
  does not have `pytest` installed.

## Verdict

Commit-ready for parity-review scope.

The Python and .NET DEFRA source download execution surfaces are aligned for
the current explicit execution contract shape, naming intent, status
vocabulary, explicit opt-in flow, state transitions, diagnostic issue
semantics, transport-response validation, malformed URI diagnostics, and
side-effect boundaries after the Python parity fixes in this task.

Task-ID: PT-048

Task-Issue: #381
