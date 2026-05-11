# PT-041 Parity Review: Source Acquisition Run Repository Contract

Task-ID: PT-041  
Task-Issue: #360

## Scope

Parity review for the source acquisition run repository contract across the
Python and .NET contract surfaces.

Reviewed files:

- `src/carbonfactor_parser/source_acquisition/run_repository_contract.py`
- `tests/test_source_acquisition_run_repository_contract.py`
- `src/carbonfactor_parser/source_acquisition/run_contract.py`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceAcquisitionRunRepository.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceAcquisitionRunRepositoryIssue.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceAcquisitionRunRepositoryPersistResult.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceAcquisitionRunRepositoryPersistStatus.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceAcquisitionRunRepositoryRegistry.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/SourceAcquisitionRunRepositoryValidationResult.cs`
- `tests/dotnet/CarbonOps.Parser.Contracts.Tests/SourceAcquisitionRunRepositoryContractTests.cs`

This review did not add runtime database execution, parser coupling, downloader
coupling, scheduler behavior, production configuration, or destructive
operations.

## Parity Findings

No blocking parity mismatch was found.

### Behavior And Contracts

Python and .NET expose the same metadata-only repository contract shape:

- a repository interface/protocol with a human-readable provider name
- a persist operation that accepts source acquisition run results
- a persist result that reports provider name, status, persisted count, and
  issues
- a validation result that reports issue collections and validity
- a pure helper/registry function that validates inputs before producing the
  persist result

Both implementations stay runtime-passive. The contract surface does not open
database connections, execute SQL, fetch remote resources, read files, or start
parser execution.

### Naming And Schema Alignment

The language-specific casing differs, but the schema concepts align:

| Concept | Python | .NET |
| --- | --- | --- |
| Provider name | `provider_name` | `ProviderName` |
| Persist status | `status` | `Status` |
| Persisted count | `persisted_count` | `PersistedCount` |
| Issues | `issues` | `Issues` |
| Issue field name | `field_name` | `FieldName` |
| Repository type | `SourceAcquisitionRunRepository` | `ISourceAcquisitionRunRepository` |

The issue record shape is aligned in both implementations:

- `code`
- `message`
- `field_name` or `FieldName`
- `severity` with default value `error`

The persist result shape is also aligned:

- provider name is echoed back unchanged
- status is deterministic
- persisted count is zero on validation failure
- issues are snapshot/copied into the result rather than exposed as a mutable
  caller-owned collection

### State Transitions

The persist-result transition semantics match:

- valid provider name plus valid run instances returns `declared` or
  `Declared`
- any validation issue returns `failed_validation` or `FailedValidation`
- validation failure forces persisted count to `0`
- a successful declaration sets persisted count to the number of supplied runs

Both implementations combine validation issues with any caller-supplied issues
before determining the final status.

### Error Semantics

The validation issue codes are aligned:

- `SOURCE_ACQUISITION_RUN_REPOSITORY_MISSING_PROVIDER_NAME`
- `SOURCE_ACQUISITION_RUN_REPOSITORY_INVALID_RUN`

The invalid input semantics also align:

- blank or whitespace provider names are rejected
- invalid run entries are rejected per index
- the field path format matches conceptually as `runs[0]` in Python and
  `Runs[0]` in .NET

The provider-name validation messages are equivalent aside from identifier
casing:

- Python: `provider_name must be a non-empty string.`
- .NET: `ProviderName must be a non-empty string.`

The invalid-run validation message is aligned exactly in meaning:

- `runs must contain SourceAcquisitionRunResult instances.`
- `Runs must contain SourceAcquisitionRunResult instances.`

## Validation Performed

- Reviewed the Python repository contract helper and its dedicated tests.
- Reviewed the .NET repository interface, records, registry helper, and its
  dedicated tests.
- Compared repository shape, persist-result structure, validation rules,
  default issue severity, persisted-count behavior, and runtime-passive
  constraints.

## Remaining Risks

- The review confirms parity for the repository contract only. It does not
  prove parity for downstream runtime repository implementations because those
  implementations are intentionally outside this task.
- Cross-language drift remains possible if future changes update one repository
  contract surface without synchronized tests or review artifacts.
- .NET currently validates null run entries while Python validates non-contract
  objects generically; the resulting contract outcome is still aligned, but the
  language runtimes reach that outcome through different type systems.

## Verdict

Merge-ready for parity-review scope.

The Python and .NET source acquisition run repository contract surfaces are
aligned for behavior, contract shape, naming intent, state transitions, and
error semantics. No code change is required for PT-041.

Task-ID: PT-041  
Task-Issue: #360
