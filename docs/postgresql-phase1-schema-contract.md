# PostgreSQL Phase 1 Schema Contract

This document defines a documentation-only PostgreSQL Phase 1 schema contract for CarbonOps-Parser.

It records intended table-shape boundaries before any runtime persistence implementation. It does not implement persistence behavior.

## Scope And Status

This contract describes intended PostgreSQL table responsibilities for:

- shared ingestion/source metadata
- GHG Protocol source-family master/detail storage
- DEFRA/DESNZ source-family master/detail storage
- IPCC EFDB source-family master/detail storage

Status: planning contract only. Runtime persistence remains unsupported/no-execution.

## Explicit Non-Goals

This task does not add:

- runtime repository persistence
- SQL execution
- DB writes
- migrations or runtime table creation behavior
- transaction behavior
- environment/config/credential loading in library code
- parser execution changes
- source downloading behavior
- production persistence readiness claims

## Contract Principles

- Keep source-family-specific data separated by family-specific master/detail tables.
- Keep shared ingestion and provenance metadata normalized into dedicated shared tables.
- Preserve source-native traceability without forcing all source-native fields into one canonical payload shape.
- Keep idempotency/conflict handling at contract intent level only in this phase.
- Keep schema initialization and data persistence as separate future implementation concerns.

## Shared Ingestion/Source Metadata Contract

Intended shared contract responsibilities:

- register ingestion runs as immutable ingestion events
- register source artifacts and source identity/version metadata
- record checksum/hash metadata for artifact-level integrity tracking
- attach parser-version and pipeline provenance metadata to ingestion events
- provide references that source-family tables can link back to

Intended shared entities (names illustrative, not implemented):

- ingestion run record entity
- source artifact record entity
- parser/provenance metadata entity
- optional normalized-factor reference catalog entity

## Source-Family Master/Detail Contract

### GHG Protocol Contract

Intended split:

- GHG Protocol master entity stores source-level record identity and source-version context.
- GHG Protocol detail entity stores granular factor rows/segments tied to a master row.

Intent:

- preserve GHG Protocol source-native semantics
- support one-to-many record decomposition when source-native structures require row expansion
- preserve reference linkage to shared ingestion/source metadata

### DEFRA/DESNZ Contract

Intended split:

- DEFRA/DESNZ master entity stores source publication/version context and grouping identity.
- DEFRA/DESNZ detail entity stores factor-level rows from the source-native tabular payload.

Intent:

- preserve DEFRA/DESNZ source-native structure and row-level traceability
- support deterministic linkage to shared ingestion/source metadata
- preserve mapping references used by normalization/dry-run boundaries

### IPCC EFDB Contract

Intended split:

- IPCC EFDB master entity stores source entry grouping identity and version/date context.
- IPCC EFDB detail entity stores source-native factor components tied to each master entry.

Intent:

- preserve IPCC EFDB source-native structure
- support one-to-many detail row expansion tied to each source entry
- preserve provenance linkage through shared ingestion/source metadata references

## Field Contract (Required Intent)

The following field intents are required at contract level across shared and family-specific entities.

### Common/Shared Field Intents

- **provenance identifiers**: stable references linking records to ingestion run and source artifact identity.
- **source identity**: source family + source identifier values used for deterministic record lineage.
- **source version/date**: publication/release identifiers or effective dates from the source.
- **checksum/hash**: source artifact hash values for change detection and lineage.
- **ingestion timestamp**: ingestion event timestamp metadata.
- **parser version**: parser implementation/version marker used during parsing.
- **normalized factor references**: optional reference identifiers linking source-native rows to normalized factor projections.
- **idempotency/conflict intent metadata**: deterministic keys/fields declared for future conflict strategy wiring (contract only; not runtime behavior).

### Source-Native Field Intents

- **raw/source-specific payload traceability**: source-native fields remain recoverable through detail records or explicit source payload metadata references.
- **master/detail separation markers**: each source-family contract must define master identity fields and detail row identity fields.
- **source-specific attributes**: family-specific factor attributes stay in family-specific detail structures and are not flattened into one generic canonical table in this phase.

## Future Implementation Gates

The following gates remain mandatory for later tasks:

1. **DDL generation is a separate future task.**
2. **Schema initialization must be explicit/manual/opt-in.**
3. **Repository data persistence must remain separate from schema initialization.**
4. **Integration tests remain default-off unless explicitly opt-in and safety-gated.**
5. **Runtime SQL execution/write behavior requires dedicated runtime implementation tasks and safety validation.**

## Related Documents

- [PostgreSQL Persistence Schema Boundary](postgresql-persistence-schema-boundary.md)
- [PostgreSQL DDL Preview Boundary](postgresql-ddl-preview-boundary.md)
- [PostgreSQL Repository Skeleton Boundary](postgresql-repository-skeleton-boundary.md)
- [PostgreSQL Runtime Execution Gate Boundary](postgresql-runtime-execution-gate-boundary.md)
- [PostgreSQL Integration Test Boundary](postgresql-integration-test-boundary.md)
- [PostgreSQL Opt-In Integration Runbook](postgresql-opt-in-integration-runbook.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [Public Safety](public-safety.md)
