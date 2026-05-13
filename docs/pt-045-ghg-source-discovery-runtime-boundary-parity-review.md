# PT-045 Parity Review: GHG Source Discovery Runtime Boundary

Task-ID: PT-045

Task-Issue: #372

## Scope

Parity review for the GHG source discovery runtime boundary across the Python
and .NET contract surfaces.

Reviewed files:

- `src/carbonfactor_parser/source_acquisition/ghg_source_discovery_boundary.py`
- `tests/test_ghg_source_discovery_boundary.py`
- `src/carbonfactor_parser/source_acquisition/contract_api.py`
- `src/dotnet/CarbonOps.Parser.Contracts/GhgSourceDiscoveryBoundary.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/GhgSourceDiscoveryRequest.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/GhgSourceDocumentCandidate.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/GhgSourceDiscoveryResult.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/GhgSourceDiscoveryIssue.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/GhgSourceDiscoveryValidationResult.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/GhgSourceDiscoveryMode.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/GhgSourceDiscoveryStatus.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/ContractWireNames.cs`
- `tests/dotnet/CarbonOps.Parser.Contracts.Tests/GhgSourceDiscoveryBoundaryTests.cs`

This review did not add source-specific ingestion, parser execution, downloader
execution, scheduler behavior, runtime database execution, production
configuration, credentials, destructive database operations, or source
discovery network access.

## Parity Findings

One Python-side result-validation gap was found and fixed during this review:

- Python now rejects declared GHG discovery results that include issue metadata,
  matching the .NET `GHG_SOURCE_DISCOVERY_RESULT_DECLARED_WITH_ISSUES`
  validation rule.
- Python now rejects undefined result statuses, matching the .NET
  `GHG_SOURCE_DISCOVERY_RESULT_INVALID_STATUS` validation rule.

No remaining blocking parity mismatch was found.

### Behavior And Contracts

Both implementations expose the same runtime-passive boundary shape:

- deterministic request creation
- deterministic metadata-only result creation
- a GHG-only source document candidate declaration
- request, candidate, and result validation helpers
- structured issue metadata with code, message, field name, and default error
  severity
- result-level runtime guard flags for network, download, parse, database
  writes, SQL, and scheduler behavior

The public boundary remains declarative. Neither implementation fetches
references, downloads files, opens databases, executes SQL, schedules work,
starts parser execution, or performs production source discovery.

### Naming And Schema Alignment

The language-specific casing differs, but the contract concepts align:

| Concept | Python | .NET |
| --- | --- | --- |
| Source family | `source_family` | `SourceFamily` |
| Source key | `source_key` | `SourceKey` |
| Discovery reference | `discovery_reference_uri` | `DiscoveryReferenceUri` |
| Mode | `mode` | `Mode` |
| Runtime side-effect gates | `allow_*` / `no_*` | `Allow*` / `No*` |
| Candidate id | `candidate_id` | `CandidateId` |
| Reference URI | `reference_uri` | `ReferenceUri` |
| Artifact kind | `artifact_kind` | `ArtifactKind` |
| Candidate ids projection | `candidate_ids` | `CandidateIds` |
| Issue field name | `field_name` | `FieldName` |

The canonical wire values align:

| Concept | Wire value |
| --- | --- |
| Source family/source key | `ghg_protocol` |
| Discovery mode | `runtime_passive` |
| Declared status | `declared` |
| Invalid status | `invalid` |
| Discovery reference URI | `discovery://ghg_protocol/acquisition` |
| Artifact kind | `discovery` |

The deterministic candidate id aligns as
`ghg_source_discovery_candidate_001_ghg_protocol`.

Python and .NET use different implementation provenance labels in
`version_label`/`VersionLabel` (`py045_ghg_discovery_boundary` and
`dn045_ghg_discovery_boundary`). The field shape and validation semantics are
aligned, and the label difference is non-blocking because the runtime boundary
uses it only as metadata.

### State Transitions

The state transitions now match:

- valid runtime-passive request plus valid candidate returns `declared`
- invalid request returns `invalid`, zero candidates, and request validation
  issues
- invalid candidate metadata returns `invalid`, zero candidates, and candidate
  validation issues
- result validation rejects enabled side-effect flags
- result validation rejects declared results with issue metadata
- result validation rejects undefined result status values
- invalid results require issue metadata

### Error Semantics

Request validation issue codes align:

- `GHG_SOURCE_DISCOVERY_MISSING_SOURCE_KEY`
- `GHG_SOURCE_DISCOVERY_MISSING_REFERENCE_URI`
- `GHG_SOURCE_DISCOVERY_SOURCE_FAMILY_MISMATCH`
- `GHG_SOURCE_DISCOVERY_SOURCE_KEY_MISMATCH`
- `GHG_SOURCE_DISCOVERY_UNSUPPORTED_MODE`
- `GHG_SOURCE_DISCOVERY_NETWORK_NOT_ALLOWED`
- `GHG_SOURCE_DISCOVERY_DOWNLOAD_NOT_ALLOWED`
- `GHG_SOURCE_DISCOVERY_PARSE_NOT_ALLOWED`
- `GHG_SOURCE_DISCOVERY_DATABASE_WRITES_NOT_ALLOWED`
- `GHG_SOURCE_DISCOVERY_SCHEDULER_NOT_ALLOWED`

Candidate validation issue codes align:

- `GHG_SOURCE_DISCOVERY_CANDIDATE_MISSING_SOURCE_KEY`
- `GHG_SOURCE_DISCOVERY_CANDIDATE_MISSING_CANDIDATE_ID`
- `GHG_SOURCE_DISCOVERY_CANDIDATE_MISSING_TITLE`
- `GHG_SOURCE_DISCOVERY_CANDIDATE_MISSING_REFERENCE_URI`
- `GHG_SOURCE_DISCOVERY_CANDIDATE_MISSING_ARTIFACT_KIND`
- `GHG_SOURCE_DISCOVERY_CANDIDATE_BLANK_CONTENT_TYPE`
- `GHG_SOURCE_DISCOVERY_CANDIDATE_BLANK_EXTENSION`
- `GHG_SOURCE_DISCOVERY_CANDIDATE_BLANK_CHECKSUM_SHA256`
- `GHG_SOURCE_DISCOVERY_CANDIDATE_BLANK_VERSION_LABEL`
- `GHG_SOURCE_DISCOVERY_CANDIDATE_BLANK_DISCOVERED_AT_LABEL`
- `GHG_SOURCE_DISCOVERY_CANDIDATE_INVALID_DOCUMENT_YEAR`
- `GHG_SOURCE_DISCOVERY_CANDIDATE_INVALID_REPORTING_YEAR`
- `GHG_SOURCE_DISCOVERY_CANDIDATE_SOURCE_FAMILY_MISMATCH`
- `GHG_SOURCE_DISCOVERY_CANDIDATE_SOURCE_KEY_MISMATCH`
- `GHG_SOURCE_DISCOVERY_CANDIDATE_ARTIFACT_KIND_MISMATCH`
- `GHG_SOURCE_DISCOVERY_CANDIDATE_UNSUPPORTED_STATUS`
- `GHG_SOURCE_DISCOVERY_CANDIDATE_DOWNLOAD_NOT_ALLOWED`

Result validation issue codes align for the shared observable contract:

- `GHG_SOURCE_DISCOVERY_RESULT_INVALID_STATUS`
- `GHG_SOURCE_DISCOVERY_RESULT_SIDE_EFFECT_FLAG_ENABLED`
- `GHG_SOURCE_DISCOVERY_RESULT_DECLARED_WITH_ISSUES`
- `GHG_SOURCE_DISCOVERY_RESULT_STATUS_MISMATCH`
- `GHG_SOURCE_DISCOVERY_RESULT_MISSING_INVALID_ISSUES`

.NET additionally validates null request/candidate/result inputs and undefined
`SourceFamily` enum values. Python reaches the same supported contract outcome
through dataclass and string-field validation, so that difference is
language-runtime-specific rather than a blocking parity issue.

## Validation Performed

- Reviewed the Python GHG source discovery boundary and dedicated tests.
- Reviewed the .NET GHG source discovery boundary, record types, enum wire
  names, and dedicated tests.
- Compared contract shape, deterministic metadata, field naming, wire values,
  side-effect gates, state transitions, validation issue codes, and
  runtime-passive constraints.

## Remaining Risks

- The review confirms parity for the runtime-passive discovery boundary only.
  It does not validate future runtime discovery, downloader, parser, scheduler,
  or persistence implementations.
- Cross-language drift remains possible if future changes update one GHG
  boundary without synchronized tests and parity review.
- Python and .NET preserve different implementation provenance labels in the
  candidate version metadata.

## Verdict

Commit-ready for parity-review scope.

The Python and .NET GHG source discovery runtime boundary contract surfaces are
aligned for behavior, contract shape, naming intent, schema alignment, state
transitions, and error semantics after the Python result-validation parity fix.

Task-ID: PT-045

Task-Issue: #372
