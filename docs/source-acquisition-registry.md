# Source Acquisition Registry (Metadata Boundary)

## Scope

This task introduces a metadata/configuration registry only for known Phase 1 source families:

- GHG Protocol
- DEFRA/DESNZ
- IPCC EFDB

The registry defines stable descriptor fields for source identity and acquisition discovery metadata.

## Explicit Non-Goals

This change does **not** implement:

- network download behavior
- filesystem writes
- parser execution
- database persistence
- scheduler or background execution
- retry/cancel workflow

## Contract Boundary

The registry is intended as a deterministic contract boundary for follow-on downloader work. Current acquisition URLs should be treated as discovery metadata placeholders unless later tasks replace them with verified direct acquisition links.

## Offline Acquisition Client Boundary

An offline-safe acquisition client contract is provided for deterministic execution flow testing.
The default no-op implementation returns `not_implemented` results and does not perform network access, file writes, checksum computation, or parser/persistence work.

Future HTTP downloader tasks should implement the same client contract and populate optional result metadata fields (`content_type`, `content_length`, `checksum_sha256`, and `local_path`) when real acquisition behavior is introduced.

## Descriptor Validation Boundary
Descriptor validation helpers (`validate_source_descriptors(...)`, `SourceDescriptorValidationReport`, and `serialize_descriptor_validation_report(...)`) are part of the `carbonfactor_parser.source_acquisition` public API for local-only metadata checks.


Descriptor validation reports are local metadata quality checks only.
They validate required descriptor fields, duplicate source IDs, and simple warning/error semantics without live URL verification or network access.
