# Local Parser File Content Loader Boundary

This document defines the local parser file content loader boundary.

It is a local file loading boundary only. It may read an explicitly supplied local file path as UTF-8 text and create `ParserFileContentInput`. It does not perform HTTP or network calls, execute parser logic, execute normalization, write to a database, execute SQL, run migrations, schedule work, load configuration, or use credentials.

## Purpose

`load_parser_file_content_from_local_path()` loads already-acquired local files into `ParserFileContentInput` for future parser tasks.

The loader makes file content availability explicit. It does not discover sources, acquire sources, choose parser adapters, parse source formats, normalize records, or persist anything.

## Input Boundary

The loader accepts:

- `source_family`
- `source_id`
- an explicit `local_path`
- optional `content_type`
- optional `format_hint`
- optional `artifact_reference`
- optional `checksum_sha256`
- optional `max_bytes` guard

The path must point to a local regular file. The caller owns source acquisition and path selection before this boundary is called.

## Output Boundary

The loader returns `ParserFileContentLoadResult`.

On success, the result includes `ParserFileContentInput` with:

- preserved source identity
- loaded UTF-8 text content
- content type and format hint metadata when supplied
- `artifact_reference`, defaulting to the local path when no explicit reference is supplied
- checksum metadata when supplied

The loader does not compute parsed records. It produces parser input content only.

## Status And Issues

`ParserFileContentLoadStatus` includes:

- `success`
- `failed`
- `not_found`
- `unsupported`

Structured issues explain missing paths, nonexistent files, directory paths, non-regular paths, invalid UTF-8 content, binary-like NUL bytes, size guard failures, and other local I/O failures.

## Safety Boundaries

The loader performs only explicit local file reads. It does not:

- call parser adapters
- call `parse_defra_desnz_file_content()`
- execute normalization
- build persistence input
- connect to a database
- execute SQL
- generate migrations
- make HTTP or network calls
- load credentials or configuration
- schedule background work

## Dry-Run Pipeline Relationship

`run_local_file_normalized_persistence_dry_run()` may call this loader as its first step for local DEFRA/DESNZ fixture files. That pipeline remains a dry-run composition: it stops at `PersistenceInput` plus DDL preview metadata and does not connect to PostgreSQL, execute SQL, write to a database, or perform network calls.

## Related Documents

- [Local File Normalized Persistence Dry-Run Boundary](local-file-normalized-persistence-dry-run-boundary.md)
- [Parser File Content Input Boundary](parser-file-content-input-boundary.md)
- [Source Acquisition Parser Handoff Contract](source-acquisition-parser-handoff-contract.md)
- [Parser Adapter Boundary](parser-adapter-boundary.md)
- [Parser Execution Result Boundary](parser-execution-result-boundary.md)
- [Public Safety](public-safety.md)
