"""# Source Acquisition CLI Boundary

## Scope

The source acquisition CLI is currently an offline-only boundary for default source descriptors and no-op orchestration runs.

## Commands

- `python -m carbonfactor_parser.source_acquisition.cli list`
  - Lists default source descriptors from `create_default_source_acquisition_registry()`.
  - Default output format is deterministic text lines containing `source_id`, `source_family`, `display_name`, `expected_format`, and `enabled`.
- `python -m carbonfactor_parser.source_acquisition.cli list --output-format json`
  - Emits deterministic, timestamp-free JSON with a `sources` array in default descriptor order.
- `python -m carbonfactor_parser.source_acquisition.cli run`
  - Runs `run_source_acquisition()` with `NoopSourceAcquisitionClient`.
  - Default output format is deterministic text summary counts.
- `python -m carbonfactor_parser.source_acquisition.cli run --manifest-path <PATH>`
  - Same no-op run behavior.
  - Optionally writes a local JSON acquisition manifest at the provided path.
- `python -m carbonfactor_parser.source_acquisition.cli run --output-format json`
  - Emits deterministic, timestamp-free JSON summary counts and per-source results in descriptor order.
- `python -m carbonfactor_parser.source_acquisition.cli run --manifest-path <PATH> --output-format json`
  - Writes the local manifest file and returns the manifest path in the JSON payload.

## Deferred Behavior

The CLI remains offline/no-op only and does not run live HTTP acquisition. It does not use `HttpSourceAcquisitionClient`, parser execution, scheduler logic, retry/cancel flows, or database persistence in this phase. HTTP/live mode remains deferred.
"""
