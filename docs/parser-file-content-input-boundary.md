# Parser File Content Input Boundary

This document defines the parser file content input boundary for future parsing tasks.

It is a content contract boundary only. It does not read files, perform HTTP or network calls, execute parser logic, execute normalization, write to a database, schedule work, use credentials, or add real source-specific parsing.

## Purpose

`ParserInputContract` carries source acquisition and artifact metadata prepared for parser selection and execution planning. It can include source identity, artifact references, checksums, content type hints, acquisition status, and run or manifest metadata.

`ParserFileContentInput` carries already-loaded parseable content for a future parser task. It is separate from acquisition output so file loading, parsing, normalization, and persistence responsibilities do not collapse into one boundary.

## Contract Shape

`ParserFileContentInput` includes:

- `source_family`
- `source_id`
- `content` as already-loaded text or bytes
- optional `content_type`
- optional `format_hint`
- optional `artifact_reference`
- optional `checksum_sha256`

`artifact_reference` and `checksum_sha256` are metadata only. They may preserve traceability to acquisition output, but this contract does not open paths, resolve references, or verify hashes.

## Validation

`validate_parser_file_content_input()` checks shape only:

- source family must be present.
- source id must be present.
- content must be non-empty already-loaded text or bytes.
- optional text metadata must be non-empty when provided.

Validation does not parse content, inspect file paths, make network calls, execute normalization, or write to persistence.

## File Loading Separation

File loading remains deferred to a future loader task. That future task must explicitly own how artifact references are opened, streamed, decoded, size-checked, and converted into `ParserFileContentInput`.

Parser adapters should receive content contracts only after loading is complete. They must not rediscover sources, download artifacts, mutate acquisition manifests, or write parsed results to a database.

## Parser Adapter Relationship

Future source-specific parser adapters may use `ParserInputContract` for metadata-only routing and planning. When real parsing is explicitly scoped, parser logic should consume an already-loaded content boundary such as `ParserFileContentInput`.

`ParserFileContentInput` is not parser output. Parser output remains represented by `ParserExecutionResult`, and normalization remains downstream of parser execution.

## Minimal DEFRA/DESNZ Content Path

`parse_defra_desnz_file_content()` accepts `ParserFileContentInput` and parses a tiny deterministic in-memory DEFRA/DESNZ CSV-like fixture format with the header `factor_id,factor_name,unit`.

This helper counts parsed in-memory rows and returns `ParserExecutionResult`. Empty content returns `no_records` with an issue, and invalid header or row shape returns `failed` with an issue.

This is not full DEFRA/DESNZ parsing. It does not read `artifact_reference`, open files, perform HTTP calls, normalize values, persist records, or claim real source support.

## Non-Goals

This boundary does not add:

- Real parser execution.
- DEFRA/DESNZ parser implementation.
- File reading or decoding.
- HTTP or network calls.
- Normalization execution.
- Database persistence.
- Scheduler, retry, cancel, or background job behavior.
- Credentials or secrets.
- Production parser correctness claims.

## Related Documents

- [Parser Adapter Boundary](parser-adapter-boundary.md)
- [Source-Specific Parser Adapter Boundary](source-specific-parser-adapter-boundary.md)
- [Parser Execution Result Boundary](parser-execution-result-boundary.md)
- [Source Acquisition Parser Handoff Contract](source-acquisition-parser-handoff-contract.md)
- [Parser To Normalization Handoff Boundary](parser-to-normalization-handoff-boundary.md)
- [Public Safety](public-safety.md)
