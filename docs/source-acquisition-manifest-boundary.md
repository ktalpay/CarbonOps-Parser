# Source Acquisition Manifest Boundary

## Scope

This increment adds a deterministic local manifest layer for source acquisition outputs that are represented by `SourceAcquisitionResult` metadata.

## Boundary

- The manifest is local JSON metadata only.
- Manifest entries are generated from acquisition results and preserve acquisition result order.
- JSON serialization is deterministic (stable key ordering, indentation, and trailing newline).
- Manifest writing creates parent directories as needed and explicitly overwrites existing manifest files.
- No source content parsing is introduced.
- No parser execution is introduced.
- No scheduler or run lifecycle behavior is introduced.
- No database persistence is introduced.

## Deferred Work

Future tasks may attach run-level metadata, timestamps, and database persistence. This increment intentionally omits timestamps so tests remain deterministic while preparing a stable boundary for future audit/run metadata and PostgreSQL persistence.
