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
scheduler behavior, destructive database operations, or source/test changes.

## Parity Findings

Blocking parity mismatches were found.

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

The result and artifact fields also align by intent:

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
- empty transport content returns `failed`
- checksum mismatch returns `failed` before writing a file
- successful writes return `downloaded` with artifact metadata
- successful results expose no issues and preserve side-effect guard flags

Both implementations block existing targets when overwrite is not explicitly
allowed, reject direct parser/database/scheduler opt-in flags, reject insecure
HTTP, require network opt-in for HTTPS references, and require target paths to
stay under an absolute target root.

### Error Semantics

Most validation issue codes are aligned:

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
- `GHG_SOURCE_DOWNLOAD_EXECUTION_NOT_ALLOWED`
- `GHG_SOURCE_DOWNLOAD_FILE_WRITE_NOT_ALLOWED`
- `GHG_SOURCE_DOWNLOAD_PARSE_NOT_ALLOWED`
- `GHG_SOURCE_DOWNLOAD_DATABASE_WRITES_NOT_ALLOWED`
- `GHG_SOURCE_DOWNLOAD_SCHEDULER_NOT_ALLOWED`
- `GHG_SOURCE_DOWNLOAD_NETWORK_NOT_ALLOWED`
- `GHG_SOURCE_DOWNLOAD_INSECURE_HTTP_NOT_ALLOWED`
- `GHG_SOURCE_DOWNLOAD_UNSAFE_SOURCE_REFERENCE_URI`
- `GHG_SOURCE_DOWNLOAD_TARGET_ROOT_NOT_ABSOLUTE`
- `GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_ABSOLUTE`
- `GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_URI`
- `GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_UNSAFE`
- `GHG_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE`
- `GHG_SOURCE_DOWNLOAD_TARGET_EXISTS`
- `GHG_SOURCE_DOWNLOAD_TRANSPORT_FAILED`
- `GHG_SOURCE_DOWNLOAD_RESPONSE_EMPTY_CONTENT`
- `GHG_SOURCE_DOWNLOAD_CHECKSUM_MISMATCH`
- `GHG_SOURCE_DOWNLOAD_WRITE_FAILED`
- `GHG_SOURCE_DOWNLOAD_RESULT_SIDE_EFFECT_FLAG_ENABLED`
- `GHG_SOURCE_DOWNLOAD_RESULT_MISSING_ARTIFACT`
- `GHG_SOURCE_DOWNLOAD_RESULT_UNEXPECTED_ARTIFACT`

However, the following differences are blocking for strict parity:

| Area | Python behavior | .NET behavior | Risk |
| --- | --- | --- | --- |
| Discovery references | `discovery://` references receive `GHG_SOURCE_DOWNLOAD_DISCOVERY_REFERENCE_NOT_DOWNLOADABLE`. | `discovery://` references receive `GHG_SOURCE_DOWNLOAD_UNSAFE_SOURCE_REFERENCE_URI`. | Error handling and tests cannot assert the same reason code for the same default discovery candidate path. |
| Result validation for blocked or failed results without issues | Rejects non-downloaded results with no issues using `GHG_SOURCE_DOWNLOAD_RESULT_MISSING_ISSUES`. | Does not require issues for blocked or failed results. | A .NET caller can construct a failed or blocked result with no diagnostic issue and still pass validation. |
| Transport response content type | Rejects non-`bytes` content with `GHG_SOURCE_DOWNLOAD_RESPONSE_CONTENT_NOT_BYTES`. | Uses `byte[]`; null content is reported as `GHG_SOURCE_DOWNLOAD_RESPONSE_MISSING_CONTENT`. | The invalid transport-response path is not code-aligned for null or wrong-typed content. |
| Transport response metadata | Does not validate blank response `content_type` or `final_uri`. | Rejects blank response metadata with `GHG_SOURCE_DOWNLOAD_RESPONSE_BLANK_CONTENT_TYPE` and `GHG_SOURCE_DOWNLOAD_RESPONSE_BLANK_FINAL_URI`. | Response metadata validation can diverge between runtimes. |
| Source reference missing scheme | Reports `GHG_SOURCE_DOWNLOAD_SOURCE_REFERENCE_URI_MISSING_SCHEME`. | Leaves unparseable absolute URI strings to the generic required-text checks and does not emit a matching missing-scheme code. | Malformed but non-empty URI inputs can produce different diagnostics. |
| Result status validation | Python enum typing does not include an explicit invalid-status result issue. | Emits `GHG_SOURCE_DOWNLOAD_RESULT_INVALID_STATUS` for undefined enum values. | Language-specific type-system handling differs; acceptable if documented, but not fully symmetric. |

### Target-Path Safety Semantics

Both implementations reject parent traversal, absolute relative paths, URI-like
target paths, existing final symlinks, and existing target files unless
overwrite is allowed.

Python has stronger directory-relative write hardening:

- opens the resolved parent directory with `O_NOFOLLOW`
- writes using a directory file descriptor
- rechecks the parent path against the open directory descriptor before writing
- rejects platforms without the required safe directory flags

.NET performs path containment and symlink checks before writing and repeats
safe-target preparation after transport, but it does not use an equivalent
directory descriptor mechanism. This is a runtime-hardening difference rather
than a public shape mismatch, but it matters for behavior parity under
concurrent path mutation.

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
  test coverage.

## Remaining Risks

- The review identifies blocking parity drift but does not correct it because
  PT-046 is a parity review and the issue does not authorize source/test
  implementation changes.
- The directory-relative write hardening difference may require a dedicated
  implementation task if strict runtime behavior parity is required across
  concurrent path mutation scenarios.
- Cross-language drift remains possible if future GHG download execution
  changes update one runtime without synchronized parity tests and review.

## Verdict

Not merge-ready for parity-review acceptance if strict Python/.NET behavior and
error-semantics parity is required.

The Python and .NET GHG source download execution surfaces are aligned in
overall contract shape, naming intent, status vocabulary, explicit opt-in flow,
state transitions, and side-effect boundaries. They are not fully aligned for
diagnostic issue codes, result validation requirements, transport-response
metadata validation, malformed URI diagnostics, and target-path race hardening.

Task-ID: PT-046

Task-Issue: #375
