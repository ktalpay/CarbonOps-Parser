# PT-049 Parity Review: IPCC Source Discovery Runtime Boundary

Task-ID: PT-049

Task-Issue: #384

## Scope

Parity review for the IPCC source discovery runtime boundary across the
Python and .NET contract surfaces.

Reviewed files:

- `src/carbonfactor_parser/source_acquisition/ipcc_source_discovery_boundary.py`
- `tests/test_ipcc_source_discovery_boundary.py`
- `src/carbonfactor_parser/source_acquisition/contract_api.py`
- `src/dotnet/CarbonOps.Parser.Contracts/IpccSourceDiscoveryBoundary.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/IpccSourceDiscoveryRequest.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/IpccSourceDocumentCandidate.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/IpccSourceDiscoveryResult.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/IpccSourceDiscoveryIssue.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/IpccSourceDiscoveryValidationResult.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/IpccSourceDiscoveryMode.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/IpccSourceDiscoveryStatus.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/ContractWireNames.cs`
- `tests/dotnet/CarbonOps.Parser.Contracts.Tests/IpccSourceDiscoveryBoundaryTests.cs`

This review did not add source-specific ingestion, parser execution,
downloader execution, scheduler behavior, runtime database execution,
production configuration, credentials, destructive database operations, or
source discovery network access.

Allowed files for this implementation were constrained to:

- `src/carbonfactor_parser/source_acquisition/ipcc_source_discovery_boundary.py`
- `tests/test_ipcc_source_discovery_boundary.py`
- `docs/pt-049-ipcc-source-discovery-runtime-boundary-parity-review.md`

## Parity Findings

Python-side result-validation gaps were found and fixed during this review:

- Python now rejects declared IPCC discovery results that include issue
  metadata, matching the .NET
  `IPCC_SOURCE_DISCOVERY_RESULT_DECLARED_WITH_ISSUES` validation rule.
- Python now rejects undefined result statuses with
  `IPCC_SOURCE_DISCOVERY_RESULT_INVALID_STATUS`, matching the .NET result
  validation rule.

No remaining blocking parity mismatch was found.

### Behavior And Contracts

Both implementations expose the same runtime-passive boundary shape:

- deterministic request creation
- deterministic metadata-only result creation
- an IPCC-only source document candidate declaration
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
| Source family/source key | `ipcc_efdb` |
| Discovery mode | `runtime_passive` |
| Declared status | `declared` |
| Invalid status | `invalid` |
| Discovery reference URI | `discovery://ipcc_efdb/homepage` |
| Artifact kind | `discovery` |

The deterministic candidate id aligns as
`ipcc_source_discovery_candidate_001_ipcc_efdb`.

Python and .NET use different implementation provenance labels in
`version_label`/`VersionLabel` (`py049_ipcc_discovery_boundary` and
`dn049_ipcc_discovery_boundary`). The field shape and validation semantics are
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

- `IPCC_SOURCE_DISCOVERY_MISSING_SOURCE_KEY`
- `IPCC_SOURCE_DISCOVERY_MISSING_REFERENCE_URI`
- `IPCC_SOURCE_DISCOVERY_SOURCE_FAMILY_MISMATCH`
- `IPCC_SOURCE_DISCOVERY_SOURCE_KEY_MISMATCH`
- `IPCC_SOURCE_DISCOVERY_UNSUPPORTED_MODE`
- `IPCC_SOURCE_DISCOVERY_NETWORK_NOT_ALLOWED`
- `IPCC_SOURCE_DISCOVERY_DOWNLOAD_NOT_ALLOWED`
- `IPCC_SOURCE_DISCOVERY_PARSE_NOT_ALLOWED`
- `IPCC_SOURCE_DISCOVERY_DATABASE_WRITES_NOT_ALLOWED`
- `IPCC_SOURCE_DISCOVERY_SCHEDULER_NOT_ALLOWED`

Candidate validation issue codes align:

- `IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_SOURCE_KEY`
- `IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_CANDIDATE_ID`
- `IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_TITLE`
- `IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_REFERENCE_URI`
- `IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_ARTIFACT_KIND`
- `IPCC_SOURCE_DISCOVERY_CANDIDATE_BLANK_CONTENT_TYPE`
- `IPCC_SOURCE_DISCOVERY_CANDIDATE_BLANK_EXTENSION`
- `IPCC_SOURCE_DISCOVERY_CANDIDATE_BLANK_CHECKSUM_SHA256`
- `IPCC_SOURCE_DISCOVERY_CANDIDATE_BLANK_VERSION_LABEL`
- `IPCC_SOURCE_DISCOVERY_CANDIDATE_BLANK_DISCOVERED_AT_LABEL`
- `IPCC_SOURCE_DISCOVERY_CANDIDATE_INVALID_DOCUMENT_YEAR`
- `IPCC_SOURCE_DISCOVERY_CANDIDATE_INVALID_REPORTING_YEAR`
- `IPCC_SOURCE_DISCOVERY_CANDIDATE_SOURCE_FAMILY_MISMATCH`
- `IPCC_SOURCE_DISCOVERY_CANDIDATE_SOURCE_KEY_MISMATCH`
- `IPCC_SOURCE_DISCOVERY_CANDIDATE_ARTIFACT_KIND_MISMATCH`
- `IPCC_SOURCE_DISCOVERY_CANDIDATE_UNSUPPORTED_STATUS`
- `IPCC_SOURCE_DISCOVERY_CANDIDATE_DOWNLOAD_NOT_ALLOWED`

Result validation issue codes align for the shared observable contract:

- `IPCC_SOURCE_DISCOVERY_RESULT_INVALID_STATUS`
- `IPCC_SOURCE_DISCOVERY_RESULT_SIDE_EFFECT_FLAG_ENABLED`
- `IPCC_SOURCE_DISCOVERY_RESULT_DECLARED_WITH_ISSUES`
- `IPCC_SOURCE_DISCOVERY_RESULT_STATUS_MISMATCH`
- `IPCC_SOURCE_DISCOVERY_RESULT_MISSING_INVALID_ISSUES`

.NET additionally validates null request/candidate/result inputs and undefined
`SourceFamily` enum values. Python reaches the same supported contract outcome
through dataclass and string-field validation, so that difference is
language-runtime-specific rather than a blocking parity issue.

## Validation Performed

- Reviewed the Python IPCC source discovery boundary and dedicated tests.
- Reviewed the .NET IPCC source discovery boundary, record types, enum wire
  names, and dedicated tests.
- Compared contract shape, deterministic metadata, field naming, wire values,
  side-effect gates, state transitions, validation issue codes, and
  runtime-passive constraints.

## Remaining Risks

- The review confirms parity for the runtime-passive discovery boundary only.
  It does not validate future runtime discovery, downloader, parser,
  scheduler, or persistence implementations.
- Cross-language drift remains possible if future changes update one IPCC
  boundary without synchronized tests and parity review.
- Python and .NET preserve different implementation provenance labels in the
  candidate version metadata.

## Verdict

Commit-ready for parity-review scope.

The Python and .NET IPCC source discovery runtime boundary contract surfaces
are aligned for behavior, contract shape, naming intent, schema alignment,
state transitions, and error semantics after the Python result-validation
parity fix.

Task-ID: PT-049

Task-Issue: #384
