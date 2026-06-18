# PT-042 Parity Review: Source Document Repository Contract

Task-ID: PT-042  
Task-Issue: #363

## Scope

Parity review for the source document repository contract across the Python and
.NET contract surfaces.

Reviewed files:

- `src/carbonfactor_parser/persistence/source_document_repository.py`
- `tests/test_source_document_repository_contract.py`
- `src/carbonfactor_parser/source_acquisition/models.py`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceDocumentRepository.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceDocumentRepositoryIssue.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceDocumentRepositoryPersistResult.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceDocumentRepositoryPersistStatus.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceDocumentRepositoryRegistry.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceDocumentRepositoryValidationResult.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceDocumentPersistenceRecord.cs`
- `tests/dotnet/CarbonOps.Parser.Contracts.Tests/SourceDocumentRepositoryContractTests.cs`

This review did not add runtime database execution, source-specific ingestion,
parser coupling, downloader coupling, scheduler behavior, production
configuration, credentials, or destructive database operations.

## Parity Findings

No blocking parity mismatch was found.

### Behavior And Contracts

Python and .NET expose the same metadata-only repository contract shape:

- a repository interface/protocol with a human-readable provider name
- a persist operation that accepts source document persistence records
- a persist result that reports provider name, status, persisted count, and
  issues
- a validation result that reports issue collections and validity
- a pure helper/registry function that validates inputs before producing the
  persist result

Both implementations stay runtime-passive. The public contract surface does not
open database connections, execute SQL, fetch remote resources, read files,
perform checksum calculation, or start parser execution.

### Naming And Schema Alignment

The language-specific casing differs, but the repository concepts align:

| Concept | Python | .NET |
| --- | --- | --- |
| Provider name | `provider_name` | `ProviderName` |
| Persist operation | `persist_source_documents` | `PersistSourceDocuments` |
| Persist status | `status` | `Status` |
| Persisted count | `persisted_count` | `PersistedCount` |
| Issues | `issues` | `Issues` |
| Issue field name | `field_name` | `FieldName` |
| Repository type | `SourceDocumentRepository` | `ISourceDocumentRepository` |

The issue record shape is aligned in both implementations:

- `code`
- `message`
- `field_name` or `FieldName`
- `severity` with default value `error`

The persist result shape is also aligned:

- provider name is echoed back unchanged
- status is deterministic
- persisted count is zero on validation failure
- issues are snapshotted into the result rather than exposed as a mutable
  caller-owned collection

The source document persistence record carried by the repository is intentionally
language-specific in detail because the Python side models the broader local
database mapping shape while the .NET side carries the compact cross-contract
source document reference and checksum shape. For this repository contract, both
sides still align on accepting source document persistence records as metadata
inputs without performing runtime persistence.

### State Transitions

The persist-result transition semantics match:

- valid provider name plus valid source document persistence records returns
  `declared` or `Declared`
- any validation issue returns `failed_validation` or `FailedValidation`
- validation failure forces persisted count to `0`
- a successful declaration sets persisted count to the number of supplied
  records

Both implementations combine validation issues with any caller-supplied issues
before determining the final status.

### Error Semantics

The validation issue codes are aligned:

- `SOURCE_DOCUMENT_REPOSITORY_MISSING_PROVIDER_NAME`
- `SOURCE_DOCUMENT_REPOSITORY_INVALID_RECORD`

The invalid input semantics also align:

- blank or whitespace provider names are rejected
- invalid record entries are rejected per index
- the field path format matches conceptually as `records[0]` in Python and
  `Records[0]` in .NET

The provider-name validation messages are equivalent aside from identifier
casing:

- Python: `provider_name must be a non-empty string.`
- .NET: `ProviderName must be a non-empty string.`

The invalid-record validation messages are aligned in meaning:

- Python: `records must contain SourceDocumentPersistenceRecord instances.`
- .NET: `Records must contain SourceDocumentPersistenceRecord instances.`

## Validation Performed

- Reviewed the Python repository protocol, result helper, validation helper, and
  dedicated tests.
- Reviewed the .NET repository interface, records, registry helper, and
  dedicated tests.
- Compared repository shape, persist-result structure, validation rules,
  default issue severity, persisted-count behavior, record-input expectations,
  and runtime-passive constraints.

## Remaining Risks

- The review confirms parity for the repository contract only. It does not
  prove parity for future runtime repository implementations because those
  implementations are intentionally outside this task.
- Cross-language drift remains possible if future changes update one repository
  contract surface without synchronized tests or review artifacts.
- .NET currently validates null record entries while Python validates
  non-contract objects generically; the resulting contract outcome is aligned,
  but the language runtimes reach that outcome through different type systems.

## Verdict

Merge-ready for parity-review scope.

The Python and .NET source document repository contract surfaces are aligned for
behavior, contract shape, naming intent, state transitions, and error semantics.
No source code change is required for PT-042.

Task-ID: PT-042  
Task-Issue: #363
