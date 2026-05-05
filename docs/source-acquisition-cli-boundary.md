# Source Acquisition CLI Boundary

## Scope

The source acquisition CLI defaults to offline no-op behavior and requires an explicit flag to use live HTTP acquisition.

## Commands

The source acquisition CLI is available through both module invocation and package console script entrypoint.

- `python -m carbonfactor_parser.source_acquisition.cli list`
- `carbonops-source-acquisition list`
  - Lists default source descriptors from `create_default_source_acquisition_registry()`.
  - Default output format is deterministic text lines containing `source_id`, `source_family`, `display_name`, `expected_format`, and `enabled`.
- `python -m carbonfactor_parser.source_acquisition.cli list --output-format json`
- `carbonops-source-acquisition list --output-format json`
  - Emits deterministic, timestamp-free JSON with a `sources` array in default descriptor order.
- `python -m carbonfactor_parser.source_acquisition.cli run`
- `carbonops-source-acquisition run`
  - Runs `run_source_acquisition()` with `NoopSourceAcquisitionClient` by default (`--client noop`).
  - Default output format is deterministic text summary counts.
- `python -m carbonfactor_parser.source_acquisition.cli run --client http`
- `carbonops-source-acquisition run --client http`
  - Uses `HttpSourceAcquisitionClient` with `StandardLibraryHttpAcquisitionTransport` from the Python standard library.
  - Client construction occurs in the CLI run command path, so default mode remains noop unless this flag is explicitly provided.
  - Tests remain offline by mocking transport behavior; no live network calls are required in tests.
- `python -m carbonfactor_parser.source_acquisition.cli run --client http --persist-content --base-directory <PATH>`
- `carbonops-source-acquisition run --client http --persist-content --base-directory <PATH>`
  - Persists acquired HTTP bytes to planned local target paths under `<PATH>`.
  - `--persist-content` requires `--base-directory` in HTTP mode.
- `python -m carbonfactor_parser.source_acquisition.cli run --client http --timeout-seconds <FLOAT>`
- `carbonops-source-acquisition run --client http --timeout-seconds <FLOAT>`
  - Passes timeout configuration to `StandardLibraryHttpAcquisitionTransport`.
  - Timeout configuration is rejected in noop mode so default offline behavior is not misleading.
- `python -m carbonfactor_parser.source_acquisition.cli run --manifest-path <PATH>`
- `carbonops-source-acquisition run --manifest-path <PATH>`
  - Same no-op run behavior.
  - Optionally writes a local JSON acquisition manifest at the provided path.
- `python -m carbonfactor_parser.source_acquisition.cli run --output-format json`
- `carbonops-source-acquisition run --output-format json`
  - Emits deterministic, timestamp-free JSON summary counts and per-source results in descriptor order.
- `python -m carbonfactor_parser.source_acquisition.cli run --dry-run --base-directory <PATH>`
- `carbonops-source-acquisition run --dry-run --base-directory <PATH>`
  - Plans deterministic local target paths from default descriptors using `plan_source_acquisition_targets(...)`.
  - Does not acquire content, write source files, write manifests, or use HTTP transport.
  - Requires `--base-directory` and rejects `--manifest-path`, `--persist-content`, and `--timeout-seconds`.
  - Text output prints planned targets in descriptor order with `source_id` and `local_path`.
- `python -m carbonfactor_parser.source_acquisition.cli run --dry-run --base-directory <PATH> --output-format json`
- `carbonops-source-acquisition run --dry-run --base-directory <PATH> --output-format json`
  - Emits deterministic, timestamp-free JSON: `{"dry_run": true, "targets": [...]}` where each target contains `source_id`, `source_family`, `expected_format`, and `local_path`.
- `python -m carbonfactor_parser.source_acquisition.cli run --manifest-path <PATH> --output-format json`
- `carbonops-source-acquisition run --manifest-path <PATH> --output-format json`
  - Writes the local manifest file and returns the manifest path in the JSON payload.

## Deferred Behavior

The `carbonops-source-acquisition` console script points to `carbonfactor_parser.source_acquisition.cli:main`, so it runs the same command boundary and behavior as module invocation.

Default runs remain offline/no-op unless `--client http` is explicitly provided. Parser execution, scheduler logic, retry/cancel flows, and database persistence remain deferred.

When `--client noop` is selected (including the default), HTTP-only flags (`--persist-content`, `--base-directory`, and `--timeout-seconds`) are rejected with clear argument errors.
