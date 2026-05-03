# Source Adapter Package Recap

The Python source adapter package is a contract and helper foundation for source-aware ingestion work. It lives under `src/carbonfactor_parser/source_adapters` and exposes intentional public symbols through `carbonfactor_parser.source_adapters`.

## Purpose

This document summarizes the current package structure and boundaries.

The package is intended to make source document traceability, adapter handoffs, ingestion run summaries, and execution result metadata explicit before real source-family adapters are added.

## Current Package Responsibilities

The package currently provides:

- Source family and source document contracts.
- Adapter discovery and parse result contracts.
- No-op adapter for package smoke tests.
- Local file adapter skeleton for deterministic non-recursive file discovery.
- In-memory adapter registry behavior.
- SHA-256 hashing helpers for bytes, text, and local files.
- Source document construction from explicit local file metadata.
- Source document metadata validation.
- Ingestion run status and summary contracts.
- Ingestion run summary factory and validation helpers.
- Source adapter execution result contracts, factory, and validation helpers.
- Explicit public API exports from `carbonfactor_parser.source_adapters`.

## Current Module Map

| Module | Responsibility |
| --- | --- |
| `contracts.py` | Source family, source document, discovery result, parse result, and adapter protocol contracts |
| `registry.py` | Minimal in-memory registration and lookup by source family |
| `hashing.py` | Deterministic SHA-256 helpers for bytes, text, and local files |
| `document_builder.py` | Helper for constructing `SourceDocument` values from explicit local file metadata |
| `document_validation.py` | Structural source document metadata validation |
| `ingestion_run.py` | Ingestion run status and summary contracts |
| `ingestion_run_factory.py` | Helper for creating ingestion run summaries with safe defaults |
| `ingestion_run_validation.py` | Structural ingestion run summary validation |
| `execution_result.py` | Source adapter execution result contract and small status helpers |
| `execution_result_factory.py` | Helper for creating execution result values with safe tuple defaults |
| `execution_result_validation.py` | Structural execution result validation |
| `noop_adapter.py` | No-op adapter for contract smoke tests and registry examples |
| `local_file_adapter.py` | Local file adapter skeleton for non-recursive directory discovery |
| `__init__.py` | Intentional public API exports |

## Contract Layer

The contract layer defines data shapes and adapter boundaries only.

`SourceFamily`, `SourceDocument`, `AdapterDiscoveryResult`, `AdapterParseResult`, and `SourceAdapter` describe the source-family-specific adapter boundary without adding concrete adapter behavior.

`IngestionRunStatus`, `IngestionRunSummary`, and `SourceAdapterExecutionResult` describe run and result metadata that can be shared across later implementation slices.

## Helper Layer

The helper layer reduces repeated construction and hashing boilerplate.

Hashing helpers calculate deterministic SHA-256 values from bytes, text, or local files. The source document builder connects explicit local file metadata to `SourceDocument` without reading source contents beyond hashing the file.

Factory helpers create ingestion run summaries and execution results with safe default containers and timestamps where applicable.

## Validation Layer

Validation helpers return deterministic issue strings instead of raising metadata quality exceptions.

The current validation helpers check structure, required fields, enum values, timestamps, hash shape, warning and error containers, and nested source document or ingestion summary issues.

They do not check file existence beyond helper behavior, reach remote locations, parse source files, enforce lifecycle transitions, or compare record counts across layers.

## Registry Layer

`SourceAdapterRegistry` is an in-memory registry for explicit adapter instances.

It supports registration, lookup, containment checks, and stable source family listing. It does not auto-discover plugins, import source-specific adapter modules, instantiate adapters, or hold process-wide singleton state.

The registry is a lightweight composition point for examples and tests. It is not a dependency injection container or framework boundary.

The example at `examples/source_adapter_registry_example.py` shows how to register `NoOpSourceAdapter` and `LocalFileSourceAdapter`, resolve an adapter by `SourceFamily`, and call `discover()` through the existing adapter contract.

See [Source Adapter Execution Flow](source-adapter-execution-flow.md) for the intended flow from registry resolution to discovered source document handoff.

See [Source Adapter Configuration Boundaries](source-adapter-configuration-boundaries.md) for adapter construction and runtime configuration boundaries.

See [Source-Specific Adapter Skeleton Guidance](source-specific-adapter-skeleton-guidance.md) before adding future source-specific adapter skeletons.

## Execution Result Layer

The execution result layer connects a source document, adapter parse result, and ingestion run summary into one immutable contract.

It is intentionally passive. It does not execute adapters, calculate counts, enforce status transitions, persist records, or retry failed work.

## Public API Boundary

The public API is the set of names exported by `carbonfactor_parser.source_adapters.__all__`.

Public exports include current contracts, helper functions, validation helpers, factories, hashing helpers, registry behavior, and small execution result status helpers.

`NoOpSourceAdapter` is also exported for contract smoke tests and registry examples. It does not represent a real source family implementation.

`LocalFileSourceAdapter` is exported as a skeleton for local file discovery. It lists files from one directory and emits `SourceDocument` references without parsing source contents.

Module names and private implementation details are not part of the public API. README examples should import from `carbonfactor_parser.source_adapters` unless a later task documents a narrower module-level need.

## Test-Only Utilities Boundary

Test fake utilities live under `tests/`.

`FakeSourceAdapter` and test object builders support the repository test suite only. They are not exported from the runtime package and should not be used as source adapter implementations.

## Explicit Non-Goals

The current package does not:

- Add real GHG Protocol, DEFRA / DESNZ, or IPCC EFDB adapters.
- Discover source files.
- Download source files.
- Parse source-specific document formats.
- Persist records.
- Define database schema or ORM models.
- Schedule background jobs.
- Implement retry or cancellation processing.
- Perform network calls.
- Provide emissions advice or reporting claims.

## Suggested Next Steps

Future tasks may add:

- Source-specific adapter skeletons with no real parsing behavior.
- Source discovery notes or fixtures for one source family.
- A first concrete source adapter once source file structure has been reviewed.

Each next step should keep source-specific behavior isolated from shared validation, normalization, metadata, and storage boundaries.
