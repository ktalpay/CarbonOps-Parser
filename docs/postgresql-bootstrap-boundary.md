# PostgreSQL Bootstrap Boundary Contract (Phase 1)

This document defines the **documentation-only** startup/bootstrap boundary contract for PostgreSQL in CarbonOps-Parser.

It does **not** add runtime code, migrations, SQL execution, database connection code, downloader behavior, parser execution, scheduler behavior, fixture data, fake data, sample data, test data, or manual JSON-first input flow.

## 1) Scope and Intent

- Scope: future **service startup/bootstrap boundary** only.
- Phase target: **PostgreSQL only**.
- Runtime implementations: Python and .NET must follow equivalent lifecycle and fail-fast semantics.
- Cross-reference: this boundary complements (and does not replace) the Phase 1 schema contract in [PostgreSQL Phase 1 Schema Contract](postgresql-phase1-schema-contract.md).

## 2) Startup Configuration Inputs

At service startup, the implementation must read and normalize configuration needed for bootstrap checks, including:

- database provider
- PostgreSQL connection settings
- enabled source families
- bootstrap mode / schema initialization setting
- service/runtime identity where relevant for logs/trace context

This contract does not prescribe exact key names or config-file format.

## 3) Provider Constraint (Phase 1)

Phase 1 accepts **PostgreSQL only** for bootstrap validation and schema presence checks.

- Valid provider values conceptually include `postgres` and `postgresql`.
- `mysql` and `mssql` may appear only as future conceptual values in shared config models.
- This task does not design or define MySQL/MSSQL bootstrap behavior.

## 4) Mandatory Pre-Execution Validation Order

Bootstrap validation must happen **before** any downloader, parser, normalization, or persistence execution path.

Required order at startup:

1. Read startup configuration.
2. Validate provider and required PostgreSQL settings.
3. Validate bootstrap mode/schema initialization setting.
4. Check configured PostgreSQL database for required table families.
5. Resolve startup outcome (ready, fail-fast, or create-missing-if-enabled).

No source acquisition or parser activity may begin before this sequence is complete.

## 5) Required PostgreSQL Table Families

Startup checks must verify that required table families exist for Phase 1:

- shared ingestion/system metadata tables
- GHG master/detail tables
- DEFRA master/detail tables
- IPCC master/detail tables

This contract intentionally defines **family-level requirements** rather than implementation-specific SQL names.

## 6) Missing-Table Handling Contract

If required tables are missing:

- Missing tables may be created only when bootstrap/schema initialization is **explicitly enabled**.
- If bootstrap/schema initialization is **disabled**, startup must **fail fast** with a clear error before downloader/parser execution.

This document does not define DDL statements or migration tooling.

## 7) Strict Non-Execution Rules for Bootstrap

Bootstrap must not:

- download source files
- parse source files
- seed fake data
- insert test data
- execute source acquisition

Bootstrap is limited to startup validation and (optionally enabled) schema presence remediation for required tables.

## 8) Idempotency Contract

Bootstrap behavior must be idempotent across repeated service startup attempts:

- it must not recreate tables that already exist
- it must not corrupt existing tables
- it must not insert duplicate metadata rows unless a later explicit contract permits it

This contract sets the rule; implementation mechanics are deferred.

## 9) Observability Contract

Bootstrap must produce observable startup outcomes that can be surfaced in logs/telemetry without exposing secrets:

- startup check result
- missing table list
- created table list (only when creation is enabled)
- skipped/no-op result when schema is already present
- failure reason

## 10) Safety Contract

Phase 1 bootstrap must avoid destructive or unsafe schema behavior:

- no drop/truncate operations
- no automatic incompatible schema rewrite
- no destructive schema operation in Phase 1
- no credential logging
- no raw connection string logging

## 11) Python/.NET Parity Requirements

Python and .NET implementations must preserve the same conceptual bootstrap behavior:

- same startup validation lifecycle
- same fail-fast rules when required tables are missing and initialization is disabled
- same idempotency expectations
- same observability/safety expectations

Language-specific naming, dependency wiring, and diagnostics formatting may differ.

## 12) Out of Scope for CO-105A

This task does not implement:

- runtime bootstrap code
- SQL execution paths
- migration execution
- database connection adapters
- downloader/parser/scheduler integration
- production/compliance/certification claims

## 13) Related Documentation

- [PostgreSQL Phase 1 Schema Contract](postgresql-phase1-schema-contract.md)
- [PostgreSQL Config Contract Boundary](postgresql-config-contract-boundary.md)
- [Database Startup](database-startup.md)
- [Documentation Index](index.md)
