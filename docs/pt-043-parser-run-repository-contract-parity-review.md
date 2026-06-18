# PT-043 Parity Review: Parser Run Repository Contract

Task-ID: PT-043  
Task-Issue: #366

## Scope

Parity review for the parser run repository contract across the Python and .NET
contract surfaces.

Reviewed files:

- `src/carbonfactor_parser/parsers/run_repository_contract.py`
- `tests/test_parser_run_repository_contract.py`
- `src/carbonfactor_parser/parsers/parser_run_contract.py`
- `src/dotnet/CarbonOps.Parser.Contracts/ParserRunRepository.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/ParserRunRepositoryIssue.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/ParserRunRepositoryPersistResult.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/ParserRunRepositoryPersistStatus.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/ParserRunRepositoryRegistry.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/ParserRunRepositoryValidationResult.cs`
- `tests/dotnet/CarbonOps.Parser.Contracts.Tests/ParserRunRepositoryContractTests.cs`

This review did not add runtime database execution, source-specific ingestion,
parser execution, downloader coupling, scheduler behavior, production
configuration, credentials, or destructive database operations.

## Parity Findings

No blocking parity mismatch was found.

### Behavior And Contracts

Python and .NET expose the same metadata-only repository contract shape:

- a repository interface/protocol with a human-readable provider name
- a persist operation that accepts parser run result metadata
- a persist result that reports provider name, status, persisted count, and
  issues
- a validation result that reports issue collections and validity
- a pure helper/registry function that validates inputs before producing the
  persist result

Both implementations stay runtime-passive. The public contract surface does not
open database connections, execute SQL, fetch remote resources, read files,
execute parsers, calculate factors, or perform source-specific ingestion.

### Naming And Schema Alignment

The language-specific casing differs, but the repository concepts align:

| Concept | Python | .NET |
| --- | --- | --- |
| Provider name | `provider_name` | `ProviderName` |
| Persist operation | `persist_runs` | `PersistRuns` |
| Persist status | `status` | `Status` |
| Persisted count | `persisted_count` | `PersistedCount` |
| Issues | `issues` | `Issues` |
| Issue field name | `field_name` | `FieldName` |
| Repository type | `ParserRunRepository` | `IParserRunRepository` |

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

The repository input is aligned on parser run result metadata. Python validates
`ParserRunResult` dataclass instances, while .NET accepts `ParserRunResult`
instances and rejects null entries through its nullable enumerable contract.

### State Transitions

The persist-result transition semantics match:

- valid provider name plus valid parser run results returns `declared` or
  `Declared`
- any validation issue returns `failed_validation` or `FailedValidation`
- validation failure forces persisted count to `0`
- a successful declaration sets persisted count to the number of supplied runs

Both implementations combine validation issues with any caller-supplied issues
before determining the final status.

### Error Semantics

The validation issue codes are aligned:

- `PARSER_RUN_REPOSITORY_MISSING_PROVIDER_NAME`
- `PARSER_RUN_REPOSITORY_INVALID_RUN`

The invalid input semantics also align:

- blank or whitespace provider names are rejected
- invalid run entries are rejected per index
- the field path format matches conceptually as `runs[0]` in Python and
  `Runs[0]` in .NET

The provider-name validation messages are equivalent aside from identifier
casing:

- Python: `provider_name must be a non-empty string.`
- .NET: `ProviderName must be a non-empty string.`

The invalid-run validation messages are aligned in meaning:

- Python: `runs must contain ParserRunResult instances.`
- .NET: `Runs must contain ParserRunResult instances.`

## Validation Performed

- Reviewed the Python repository protocol, result helper, validation helper, and
  dedicated tests.
- Reviewed the .NET repository interface, records, registry helper, and
  dedicated tests.
- Compared repository shape, persist-result structure, validation rules,
  default issue severity, persisted-count behavior, parser-run input
  expectations, and runtime-passive constraints.

## Remaining Risks

- The review confirms parity for the repository contract only. It does not
  prove parity for future runtime repository implementations because those
  implementations are intentionally outside this task.
- Cross-language drift remains possible if future changes update one repository
  contract surface without synchronized tests or review artifacts.
- .NET currently validates null run entries while Python validates non-contract
  objects generically; the resulting contract outcome is aligned, but the
  language runtimes reach that outcome through different type systems.

## Verdict

Merge-ready for parity-review scope.

The Python and .NET parser run repository contract surfaces are aligned for
behavior, contract shape, naming intent, state transitions, and error semantics.
No source code change is required for PT-043.

Task-ID: PT-043  
Task-Issue: #366
