# PostgreSQL Phase 1 Schema Contract

This document defines the **documentation-only** Phase 1 PostgreSQL schema contract for CarbonOps-Parser.

It is a planning contract and does **not** add runtime code, migrations, SQL execution, database connections, downloader behavior, parser execution, scheduler behavior, or any fixture/sample/temp/manual data flow.

## 1) Scope, Status, and Phase Constraint

- Phase 1 source families in scope:
  - GHG
  - DEFRA
  - IPCC
- Database target in scope: **PostgreSQL only**.
- Status: **contract-only architecture documentation**.

Conceptual future portability may mention `postgres/mysql/mssql` in configuration discussions, but this contract defines PostgreSQL table responsibilities only and does not define MySQL/MSSQL DDL.

## 2) Explicit Non-Goals

This document does not:

- implement schema creation logic
- implement startup bootstrap code
- implement downloader/parser/persistence agents
- implement SQL statements or transaction flows
- implement parser execution against source files
- introduce hardcoded JSON, temporary files, fake data, hand-authored fixtures, or manual input-data flow
- claim production readiness or carbon-accounting correctness

## 3) Shared Ingestion/System Metadata Contract

Phase 1 requires shared ingestion/system metadata tables (names may vary by implementation) that can represent:

- ingestion run identity
- source family and source type
- acquisition status
- parse status
- source URL **or** source document identity
- local document identity when applicable
- checksum/hash metadata
- created/updated timestamps
- error code and error message
- retry and correlation metadata when applicable

These shared tables are the system-of-record for ingestion/provenance lifecycle state and must be linkable from each source-family master/detail pair.

## 4) Source-Family Master/Detail Contracts

Each source family must have dedicated master/detail tables. No cross-family merged "one-size-fits-all" factor table is required in Phase 1.

### 4.1 GHG Contract

**GHG master table responsibilities:**

- source family (`GHG`) and source type identity
- year/reporting period context
- short description
- source document identity
- source document version if available
- acquisition metadata reference
- lifecycle/status fields
- timestamps

**GHG detail table responsibilities:**

- parsed calculation parameters/factors derived from downloaded/acquired GHG source documents
- row-level linkage back to GHG master
- row-level provenance linkage to shared ingestion/system metadata as needed

### 4.2 DEFRA Contract

**DEFRA master table responsibilities:**

- source family (`DEFRA`) and source type identity
- year/reporting period context
- short description
- source document identity
- source document version if available
- acquisition metadata reference
- lifecycle/status fields
- timestamps

**DEFRA detail table responsibilities:**

- parsed calculation parameters/factors derived from downloaded/acquired DEFRA source documents
- row-level linkage back to DEFRA master
- row-level provenance linkage to shared ingestion/system metadata as needed

### 4.3 IPCC Contract

**IPCC master table responsibilities:**

- source family (`IPCC`) and source type identity
- year/reporting period context
- short description
- source document identity
- source document version if available
- acquisition metadata reference
- lifecycle/status fields
- timestamps

**IPCC detail table responsibilities:**

- parsed calculation parameters/factors derived from downloaded/acquired IPCC source documents
- row-level linkage back to IPCC master
- row-level provenance linkage to shared ingestion/system metadata as needed

## 5) Startup Bootstrap Expectations (Future Runtime Behavior)

Future service implementations (Python and .NET) must follow this startup expectation:

1. Check the configured PostgreSQL database at service startup.
2. Validate required shared system tables and required GHG/DEFRA/IPCC master-detail tables.
3. If required tables are missing, create missing tables before runtime ingestion/parse persistence proceeds.

This section defines required behavior only; it does not implement bootstrap logic in this task.

## 6) Downloader → Parser → Persistence Boundary

Phase 1 architecture requires strict sequencing:

1. **Download/acquire source documents first.**
2. **Parse second** using acquired documents.
3. **Persist third** into source-family master/detail tables with shared metadata linkage.

Why download-before-parse is mandatory:

- ensures parser inputs are real acquired source artifacts, not hand-authored substitutes
- ensures checksum/document identity can be attached before parse output persistence
- ensures reproducible provenance and correlation across retries/runs
- keeps runtime behavior aligned with future operational ingestion controls

Parser agents must consume downloaded/acquired source documents and must not rely on hardcoded JSON, temp data, fake data, or fixtures.

## 7) Python/.NET Parity Expectations

Python and .NET implementations must remain conceptually equivalent for:

- source-family master/detail contract boundaries
- shared ingestion/system metadata contract
- startup bootstrap expectations
- downloader-before-parser sequencing
- provenance and status lifecycle semantics

Language/runtime differences are acceptable at implementation detail level, but contract semantics must remain aligned.

## 8) Documentation Map / Related References

- [Documentation Index](index.md)
- [Database Model](database-model.md)
- [Database Startup](database-startup.md)
- [Ingestion Metadata Model](ingestion-metadata-model.md)
- [Source Acquisition Parser Handoff Contract](source-acquisition-parser-handoff-contract.md)
- [PostgreSQL Persistence Schema Boundary](postgresql-persistence-schema-boundary.md)
