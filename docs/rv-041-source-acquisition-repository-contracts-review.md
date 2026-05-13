# RV-041 Review: Source Acquisition Repository Contracts

Task-ID: RV-041
Task-Issue: #386

## Executive Summary

This review-only checkpoint covers the source acquisition repository contract
surface after the PT-041, PT-042, and PT-044 parity reviews. The reviewed
contracts remain metadata-only and runtime-passive. No blocker was found for the
next review checkpoint.

No product or runtime source code was changed. This task did not add
credentials, raw connection strings, live source endpoint calls, database
execution, destructive database operations, branch deletion, worktree deletion,
issue closure, PR merge activity, or source-specific ingestion behavior.

## Scope Reviewed

This review covered documentation and existing contract surfaces for repository
contracts related to source acquisition persistence boundaries:

- source acquisition run repository contract
- source document repository contract
- source-family master/detail repository contract
- cross-language Python and .NET parity-review conclusions for those contracts
- safety posture of the reviewed contracts as non-executing declarations

Out of scope:

- new runtime repository implementation
- source-specific downloader or parser behavior
- production database connectivity
- migrations or destructive database operations
- scheduler, retry, or orchestration execution behavior
- production readiness claims beyond this review checkpoint

## Source Acquisition Repository Contracts Reviewed

The following existing review artifacts were used as the primary contract
inputs:

- `docs/pt-041-source-acquisition-run-repository-contract-parity-review.md`
- `docs/pt-042-source-document-repository-contract-parity-review.md`
- `docs/pt-044-source-family-repository-contract-parity-review.md`

The corresponding contract areas are:

- Python source acquisition run repository:
  `src/carbonfactor_parser/source_acquisition/run_repository_contract.py`
- Python source document repository:
  `src/carbonfactor_parser/persistence/source_document_repository.py`
- Python source-family repository:
  `src/carbonfactor_parser/persistence/source_family_repository.py`
- .NET source acquisition run repository contract records and registry under
  `src/dotnet/CarbonOps.Parser.Contracts/SourceAcquisitionRunRepository*.cs`
- .NET source document repository contract records and registry under
  `src/dotnet/CarbonOps.Parser.Contracts/SourceDocumentRepository*.cs`
- .NET source-family repository contract records, registry, and table-name
  helper under `src/dotnet/CarbonOps.Parser.Contracts/SourceFamily*.cs`

The reviewed contracts share the same broad repository declaration model:

- provider-name validation
- persist-operation shape
- deterministic persist-result status
- persisted-count reporting
- validation issue collection
- failed-validation behavior that reports zero persisted records
- metadata-only registry/helper functions

## Python/.NET Readiness Observations

Python and .NET readiness is acceptable for this review checkpoint.

The parity reviews confirm aligned contract intent across the Python and .NET
surfaces for:

- repository interface/protocol shape
- issue record shape and default severity
- validation-result shape
- deterministic declaration vs failed-validation status transitions
- persisted-count handling
- source-family table-name mapping for Phase 1 source families
- runtime-passive behavior

Language-specific differences remain expected and accepted:

- Python uses snake_case identifiers while .NET uses PascalCase identifiers.
- Python validates non-contract objects generically while .NET validates null or
  invalid typed entries through its type system.
- Python can coerce supported source-family values into enum values while .NET
  receives enum values directly and rejects undefined values.

These differences do not block the review checkpoint because the observable
contract outcomes remain aligned.

## Contract Consistency Assessment

The reviewed repository contracts are consistent enough for the next review
checkpoint.

The source acquisition run, source document, and source-family repository
contracts all follow the same pattern:

- no runtime persistence is performed by the contract helper itself
- validation happens before declared persistence results are returned
- validation failure prevents nonzero persisted counts
- provider names are required and echoed in results
- issue collections are reported as contract data
- caller-supplied issues are preserved when determining final status

The PT-041, PT-042, and PT-044 reviews found no blocking parity mismatch across
Python and .NET. Their combined findings support a consistent repository
contract model for source acquisition persistence boundaries.

## Safety Assessment

### No Production Credentials

No production credentials were added, reviewed, required, or referenced. This
review document does not include secrets, tokens, passwords, usernames, or raw
connection strings.

### No Live Source Endpoint Calls

No live source endpoints were called. The reviewed repository contracts are
metadata-only persistence boundaries and do not fetch remote resources.

### No Runtime DB Execution

No runtime database execution was performed. The reviewed contracts define
declaration and validation shapes only; they do not open database connections or
execute SQL.

### No Destructive DB Operations

No destructive database operations were performed or added. This review did not
run migrations, truncate data, drop objects, delete records, or issue database
commands.

## Remaining Risks

- This review confirms repository contract consistency only; it does not prove
  future runtime repository implementation correctness.
- Cross-language drift remains possible if future changes update Python or .NET
  contract surfaces without synchronized tests and review artifacts.
- Execution-path behavior remains intentionally deferred until a separate scoped
  task introduces runtime persistence with explicit safety gates.
- Source-specific acquisition correctness, parser correctness, factor
  correctness, compliance interpretation, and carbon-accounting correctness are
  outside this review.

## Verdict

ready for next review checkpoint

The reviewed source acquisition repository contracts are consistent,
runtime-passive, and aligned with the safety boundaries required for RV-041.

Task-ID: RV-041
Task-Issue: #386
