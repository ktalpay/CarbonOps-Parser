# PostgreSQL Runtime Integration Boundary

This document defines the boundary for future PostgreSQL runtime integration in
CarbonOps-Parser.

It is boundary documentation only. It does not create PostgreSQL connections,
execute SQL, write records, create schema objects, run migrations, load
configuration from environment variables or files, read credentials, perform
network operations, or claim production persistence readiness.

## Purpose

The PostgreSQL runtime integration boundary exists to keep the transition from
preview-only persistence planning to runtime execution controlled, explicit, and
reviewable.

The boundary separates:

- deterministic persistence planning and preview behavior
- runtime execution behavior that can modify database state

## In Scope

Runtime integration foundation includes:

- explicit contracts that describe runtime handoff points
- gate checks that keep runtime execution disabled by default
- driver/session adapter boundaries that isolate database dependencies
- deterministic metadata and diagnostics that can be validated without a
  database connection

## Out of Scope

Unless a future task explicitly enables runtime execution, the following remain
out of scope:

- inserting rows into PostgreSQL
- creating databases, schemas, tables, or indexes
- running migrations or bootstrap SQL against a real database
- implicit connection/session construction in library code
- environment/config-based credential loading in library code
- production configuration or production-readiness claims

## Integration Flow (No-Execution Foundation)

A future runtime-enabled path must continue to preserve this control flow
boundary:

1. `PersistenceInput` is produced from deterministic parser + normalization
   outputs.
2. `build_postgresql_insert_statement()` builds deterministic SQL metadata.
3. Runtime gate evaluation determines whether execution is allowed.
4. If execution remains disabled, repository-level diagnostics are returned with
   no side effects.
5. If a future task enables execution, the repository must call only through an
   explicit execution adapter/session boundary.

## Required Runtime Safety Constraints

Any future runtime integration task must preserve these constraints:

- explicit opt-in execution; no implicit default execution path
- caller-provided session/connection ownership
- sanitized diagnostics and error surfaces that never expose secrets
- transaction behavior defined and tested before broad enablement
- integration tests remain opt-in and isolated from the default test suite

## Foundation Deliverables For DB-040

DB-040 is satisfied by defining this boundary artifact so that later runtime
execution tasks can be implemented in small, scoped increments without
broadening behavior unintentionally.

This task does not modify repository runtime behavior.
