# Ingestion Contracts

## Purpose

`carbonfactor_parser.contracts` defines shared, runtime-passive contract types for future ingestion orchestration work. The module provides a stable metadata boundary for:

- source acquisition outcomes,
- parsed factor payload handoff,
- ingestion run snapshots, and
- persistence bootstrap readiness snapshots.

These contracts are type-only data containers and must remain deterministic and import-safe.

## Public Symbols

- `SourceType`: stable source identifiers (`ghg_protocol`, `defra_desnz`, `ipcc_efdb`).
- `SourceDocument`: metadata-only representation of an acquired source document.
- `SourceAcquisitionResult`: acquisition metadata snapshot plus acquired documents.
- `ParsedFactorRecord`: normalized parsed emission factor record contract.
- `IngestionStatus`: shared run/bootstrap status identifiers.
- `IngestionRun`: ingestion run metadata snapshot.
- `PersistenceBootstrapResult`: persistence bootstrap readiness metadata snapshot.

## Boundary Rules (Forbidden Behavior)

This contract layer intentionally forbids runtime behavior:

- no HTTP,
- no DB connections,
- no parser execution,
- no scheduler behavior,
- no credential loading,
- no environment variable loading.

Contracts must not perform file reads, downloads, migrations, or side effects at import time.

## SourceType Naming and Compatibility

`SourceType` enum values should follow a stable three-part naming convention:

- source family,
- publisher/program, and
- dataset identifier.

Use lowercase snake case with `_` separators (for example, `defra_desnz`). Published enum values are part of the shared contract and are expected to remain stable over time.

Compatibility expectations:

- additive enum members are backward-compatible additions,
- enum removals or renames are breaking changes, and
- downstream parser and persistence agents must treat published contract symbols as stable interfaces.

## Guidance for Parallel Agents

Future parallel agents should use these contracts as shared interfaces:

1. Acquisition-oriented tasks should emit `SourceDocument` and `SourceAcquisitionResult` only.
2. Parser-oriented tasks should emit `ParsedFactorRecord` without persistence coupling.
3. Ingestion coordination tasks should capture state using `IngestionRun` and `IngestionStatus`.
4. Persistence-boundary tasks should report readiness through `PersistenceBootstrapResult` without establishing real DB sessions.

If a task requires execution behavior, that behavior must live outside `carbonfactor_parser.contracts` and reference these data contracts passively.
