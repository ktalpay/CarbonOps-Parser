# PT-044 Parity Review: Source-Family Master/Detail Repository Contract

Task-ID: PT-044

Task-Issue: #369

## Scope

Parity review for the source-family master/detail repository contract across
the Python and .NET contract surfaces.

Reviewed files:

- `src/carbonfactor_parser/persistence/source_family_repository.py`
- `tests/test_source_family_repository_contract.py`
- `src/carbonfactor_parser/persistence/postgresql_schema_catalog.py`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceFamily.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceFamilyRegistry.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceFamilyMasterRecord.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceFamilyDetailRecord.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceFamilyRepository.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceFamilyRepositoryIssue.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceFamilyRepositoryPersistResult.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceFamilyRepositoryPersistStatus.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceFamilyRepositoryRegistry.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceFamilyRepositoryTableNames.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceFamilyRepositoryValidationResult.cs`
- `tests/dotnet/CarbonOps.Parser.Contracts.Tests/SourceFamilyRepositoryContractTests.cs`

This review did not add runtime database execution, source-specific ingestion,
parser coupling, downloader coupling, scheduler behavior, production
configuration, credentials, destructive database operations, or source/test
changes.

## Parity Findings

No blocking parity mismatch was found.

### Behavior And Contracts

Python and .NET expose the same metadata-only repository contract shape:

- a repository interface/protocol with a human-readable provider name
- a persist operation that accepts source-family master and detail records
- a persist result that reports provider name, status, persisted master count,
  persisted detail count, and issues
- a validation result that reports issue collections and validity
- a pure helper/registry function that validates inputs before producing the
  persist result
- a helper for source-family-owned master/detail table names

Both implementations stay runtime-passive. The public contract surface does not
open database connections, execute SQL, fetch remote resources, read files,
calculate factors, run parsers, or perform source-specific ingestion.

### Naming And Schema Alignment

The language-specific casing differs, but the repository concepts align:

| Concept | Python | .NET |
| --- | --- | --- |
| Provider name | `provider_name` | `ProviderName` |
| Persist operation | `persist_source_family_records` | `PersistSourceFamilyRecords` |
| Master records input | `master_records` | `MasterRecords` |
| Detail records input | `detail_records` | `DetailRecords` |
| Persist status | `status` | `Status` |
| Persisted master count | `persisted_master_count` | `PersistedMasterCount` |
| Persisted detail count | `persisted_detail_count` | `PersistedDetailCount` |
| Issues | `issues` | `Issues` |
| Issue field name | `field_name` | `FieldName` |
| Repository type | `SourceFamilyRepository` | `ISourceFamilyRepository` |
| Table names helper | `source_family_repository_table_names` | `GetTableNames` |

The source-family record shapes align by concept:

| Concept | Python | .NET |
| --- | --- | --- |
| Source family | `source_family` | `SourceFamily` |
| Master id | `source_family_master_id` | `SourceFamilyMasterId` |
| Source document id | `source_document_id` | `SourceDocumentId` |
| Master external key | `master_external_key` | `MasterExternalKey` |
| Effective range | `effective_from`, `effective_to` | `EffectiveFrom`, `EffectiveTo` |
| Detail id | `source_family_detail_id` | `SourceFamilyDetailId` |
| Detail external key | `detail_external_key` | `DetailExternalKey` |
| Factor value and unit | `factor_value`, `factor_unit` | `FactorValue`, `FactorUnit` |
| Lifecycle status | `lifecycle_status` | `LifecycleStatus` |
| Record checksum | `record_checksum_sha256` | `RecordChecksumSha256` |
| Timestamps | `created_at`, `updated_at` | `CreatedAt`, `UpdatedAt` |

The source-family vocabulary is aligned to the same Phase 1 families:

- GHG Protocol: Python `ghg`, .NET `GhgProtocol`
- DEFRA/DESNZ: Python `defra`, .NET `DefraDesnz`
- IPCC EFDB: Python `ipcc`, .NET `IpccEfdb`

The table-name mapping is aligned:

| Source family | Master table | Detail table |
| --- | --- | --- |
| GHG Protocol | `ghg_emission_factor_masters` | `ghg_emission_factor_details` |
| DEFRA/DESNZ | `defra_emission_factor_masters` | `defra_emission_factor_details` |
| IPCC EFDB | `ipcc_emission_factor_masters` | `ipcc_emission_factor_details` |

The issue record shape is aligned in both implementations:

- `code`
- `message`
- `field_name` or `FieldName`
- `severity` with default value `error`

The persist result shape is also aligned:

- provider name is echoed back unchanged
- status is deterministic
- persisted master and detail counts are zero on validation failure
- successful declaration counts are based on the supplied master/detail inputs
- issues are snapshotted into the result rather than exposed as a mutable
  caller-owned collection

### State Transitions

The persist-result transition semantics match:

- valid provider name plus valid master/detail records returns `declared` or
  `Declared`
- any validation issue returns `failed_validation` or `FailedValidation`
- validation failure forces both persisted counts to `0`
- a successful declaration sets persisted counts to the supplied master and
  detail record counts

Both implementations combine validation issues with any caller-supplied issues
before determining the final status.

The master/detail relationship rule is also aligned: each detail record must
reference a declared master record in the same source family.

### Error Semantics

The validation issue codes are aligned:

- `SOURCE_FAMILY_REPOSITORY_MISSING_PROVIDER_NAME`
- `SOURCE_FAMILY_REPOSITORY_INVALID_MASTER_RECORD`
- `SOURCE_FAMILY_REPOSITORY_INVALID_DETAIL_RECORD`
- `SOURCE_FAMILY_REPOSITORY_INVALID_SOURCE_FAMILY`
- `SOURCE_FAMILY_REPOSITORY_MISSING_REQUIRED_FIELD`
- `SOURCE_FAMILY_REPOSITORY_DETAIL_MASTER_NOT_DECLARED`

The invalid input semantics also align:

- blank or whitespace provider names are rejected
- invalid master and detail entries are rejected per index
- unsupported source-family values are rejected
- required master/detail fields must be non-empty strings
- detail records cannot point at a missing or cross-family master record
- the field path format matches conceptually as `master_records[0]` /
  `detail_records[0]` in Python and `MasterRecords[0]` /
  `DetailRecords[0]` in .NET

The validation messages are equivalent aside from identifier casing and
language-specific type-system wording. .NET validates null entries explicitly,
while Python validates non-contract objects generically; the observable contract
outcome is aligned.

## Validation Performed

- Reviewed the Python repository protocol, master/detail record contracts,
  result helper, validation helper, table-name helper, and dedicated tests.
- Reviewed the .NET repository interface, master/detail records, registry
  helper, source-family enum, table-name record, validation result, and
  dedicated tests.
- Compared repository shape, master/detail record naming, source-family
  vocabulary, table-name mapping, persist-result structure, validation rules,
  default issue severity, persisted-count behavior, master/detail reference
  checks, state transitions, and runtime-passive constraints.

## Remaining Risks

- The review confirms parity for the repository contract only. It does not
  prove parity for future runtime repository implementations because those
  implementations are intentionally outside this task.
- Cross-language drift remains possible if future changes update one repository
  contract surface without synchronized tests or review artifacts.
- Python accepts string source-family values that coerce into the `SourceFamily`
  enum, while .NET accepts enum values and rejects undefined enum values. The
  supported source-family vocabulary and validation outcome are aligned, but
  the language runtimes reach that outcome through different type systems.

## Verdict

Merge-ready for parity-review scope.

The Python and .NET source-family master/detail repository contract surfaces are
aligned for behavior, contract shape, naming intent, schema/table mapping, state
transitions, and error semantics. No source code change is required for PT-044.

Task-ID: PT-044

Task-Issue: #369
