# Source Acquisition Target Planning

## Purpose

The source acquisition target planning layer defines deterministic local file targets from source acquisition descriptor metadata.

This layer is metadata-only. It does not perform network access, file downloads, directory creation, file writes, checksum computation, parser invocation, persistence, scheduling, retry behavior, cancellation behavior, or background job execution.

## Planned Target Shape

`SourceAcquisitionTarget` represents one deterministic planned file target with:

- `source_id`
- `source_family`
- `expected_format`
- `target_directory`
- `target_filename`
- `local_path`

## Deterministic Filename Planning

`plan_source_acquisition_target(descriptor, base_directory)` produces a stable filename from descriptor metadata.

- Filename shape: `{source_id}.{extension}` after defensive filename token sanitization.
- Extension mapping:
  - `csv` -> `.csv`
  - `json` -> `.json`
  - `xlsx` -> `.xlsx`
  - `zip` -> `.zip`
  - `pdf` -> `.pdf`
  - unknown or unmapped values -> `.dat`

For values like `discovery`, `html`, or `unknown`, the mapping remains `.dat`.

`plan_source_acquisition_targets(descriptors, base_directory)` plans targets in descriptor input order and returns an immutable tuple.

## Validation

Planning rejects empty required values:

- descriptor `source_id`
- descriptor `source_family`
- descriptor `expected_format`
- `base_directory`

The planner raises clear `ValueError` messages for these conditions.

## Intended Future Integration

Future downloader implementations should use this planning layer first to choose deterministic local target metadata before any explicit file system write step is introduced.
