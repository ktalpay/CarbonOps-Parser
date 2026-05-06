# Source Acquisition CLI Boundary

## Scope

The source acquisition CLI defaults to offline no-op behavior and requires an explicit flag to use live HTTP acquisition.

The examples in this document are command-surface examples only. They show CLI invocation patterns and guardrails, but they do not guarantee remote source availability.

## Commands

The source acquisition CLI is available through both module invocation and package console script entrypoint.

- `python -m carbonfactor_parser.source_acquisition.cli list`
- `carbonops-source-acquisition list`
  - Example: list all default registry sources.
  - If `--source-id` is omitted, all default source descriptors are included.
- `python -m carbonfactor_parser.source_acquisition.cli list --source-id ghg_protocol`
- `carbonops-source-acquisition list --source-id ghg_protocol`
  - Example: list one source by ID.
- `python -m carbonfactor_parser.source_acquisition.cli list --source-id defra_desnz --source-id ghg_protocol`
- `carbonops-source-acquisition list --source-id defra_desnz --source-id ghg_protocol`
  - Example: list multiple sources with repeated `--source-id` flags.
  - Filtered output preserves default registry order instead of input order.
- `python -m carbonfactor_parser.source_acquisition.cli list`
- `carbonops-source-acquisition list`
  - Lists default source descriptors from `create_default_source_acquisition_registry()`.
  - Default output format is deterministic text lines containing `source_id`, `source_family`, `display_name`, `expected_format`, and `enabled`.
  - Optional `--source-id <SOURCE_ID>` flag can be repeated to filter output to selected source IDs only.
  - If `--source-id` is omitted, all default source descriptors are included.
  - Filtered output always preserves the default registry order.
  - Unknown source IDs fail with a clear argument error.
  - Duplicate `--source-id` values are rejected with a clear argument error.
- `python -m carbonfactor_parser.source_acquisition.cli list --output-format json`
- `carbonops-source-acquisition list --output-format json`
  - Emits deterministic, timestamp-free JSON with a `sources` array in default descriptor order.
- `python -m carbonfactor_parser.source_acquisition.cli run`
- `carbonops-source-acquisition run`
  - Example: noop run using the default client.
  - Runs `run_source_acquisition()` with `NoopSourceAcquisitionClient` by default (`--client noop`).
  - Default output format is deterministic text summary counts.
  - Optional `--source-id <SOURCE_ID>` flag can be repeated to scope run targets to selected source IDs from the default registry.
  - If `--source-id` is omitted, all default source descriptors are included.
  - Filtering preserves default registry order across run outputs and manifest entries.
  - Unknown source IDs fail with a clear argument error.
  - Duplicate `--source-id` values are rejected with a clear argument error.
- `python -m carbonfactor_parser.source_acquisition.cli run --client http`
- `carbonops-source-acquisition run --client http`
  - Example: explicit HTTP mode.
  - Uses `HttpSourceAcquisitionClient` with `StandardLibraryHttpAcquisitionTransport` from the Python standard library.
  - Client construction occurs in the CLI run command path, so default mode remains noop unless this flag is explicitly provided.
  - Tests remain offline by mocking transport behavior; no live network calls are required in tests.
- `python -m carbonfactor_parser.source_acquisition.cli run --client http --persist-content --base-directory <PATH>`
- `carbonops-source-acquisition run --client http --persist-content --base-directory <PATH>`
  - Example: HTTP mode with local content persistence and planned base directory.
  - Persists acquired HTTP bytes to planned local target paths under `<PATH>`.
  - `--persist-content` requires `--base-directory` in HTTP mode.
- `python -m carbonfactor_parser.source_acquisition.cli run --client http --source-id defra_desnz --source-id ghg_protocol`
- `carbonops-source-acquisition run --client http --source-id defra_desnz --source-id ghg_protocol`
  - Example: source-filtered HTTP mode using repeated `--source-id` flags.
- `python -m carbonfactor_parser.source_acquisition.cli run --client http --timeout-seconds <FLOAT>`
- `carbonops-source-acquisition run --client http --timeout-seconds <FLOAT>`
  - Passes timeout configuration to `StandardLibraryHttpAcquisitionTransport`.
  - Timeout configuration is rejected in noop mode so default offline behavior is not misleading.
- `python -m carbonfactor_parser.source_acquisition.cli run --manifest-path <PATH>`
- `carbonops-source-acquisition run --manifest-path <PATH>`
  - Example: noop run that also writes a local manifest file.
  - Same no-op run behavior.
  - Optionally writes a local JSON acquisition manifest at the provided path.
- `python -m carbonfactor_parser.source_acquisition.cli run --output-format json`
- `carbonops-source-acquisition run --output-format json`
  - Example: noop run with deterministic JSON output.
  - Emits deterministic, timestamp-free JSON summary counts and per-source results in descriptor order.
- `python -m carbonfactor_parser.source_acquisition.cli run --dry-run --base-directory <PATH>`
- `carbonops-source-acquisition run --dry-run --base-directory <PATH>`
  - Example: dry-run planning mode with local target path planning only.
  - Plans deterministic local target paths from default descriptors using `plan_source_acquisition_targets(...)`.
  - Does not acquire content, write source files, write manifests, or use HTTP transport.
  - Requires `--base-directory` and rejects `--manifest-path`, `--persist-content`, and `--timeout-seconds`.
  - Text output prints planned targets in descriptor order with `source_id` and `local_path`.
- `python -m carbonfactor_parser.source_acquisition.cli run --dry-run --base-directory <PATH> --output-format json`
- `carbonops-source-acquisition run --dry-run --base-directory <PATH> --output-format json`
  - Example: dry-run planning mode with deterministic JSON output.
  - Emits deterministic, timestamp-free JSON: `{"dry_run": true, "targets": [...]}` where each target contains `source_id`, `source_family`, `expected_format`, and `local_path`.
- `python -m carbonfactor_parser.source_acquisition.cli run --manifest-path <PATH> --output-format json`
- `carbonops-source-acquisition run --manifest-path <PATH> --output-format json`
  - Writes the local manifest file and returns the manifest path in the JSON payload.
- `python -m carbonfactor_parser.source_acquisition.cli validate`
- `carbonops-source-acquisition validate`
  - Validates source descriptor metadata locally from `create_default_source_acquisition_registry()`.
  - No HTTP calls, file writes, manifest writes, parser execution, or database work are performed.
  - Text output prints deterministic summary counts and issue lines.
- `python -m carbonfactor_parser.source_acquisition.cli validate --output-format json`
The validate command uses deterministic descriptor validation report helpers exposed from `carbonfactor_parser.source_acquisition` so the CLI and package API stay consistent.

- `carbonops-source-acquisition validate --output-format json`
  - Emits deterministic JSON with `issue_count`, `warning_count`, `error_count`, and `issues`.
  - Exit code is `0` when no errors exist and non-zero when one or more errors are present; warnings alone do not fail the command.

## Deferred Behavior

The `carbonops-source-acquisition` console script points to `carbonfactor_parser.source_acquisition.cli:main`, so it runs the same command boundary and behavior as module invocation.

Default runs remain offline/no-op unless `--client http` is explicitly provided. Parser execution, scheduler logic, retry/cancel flows, and database persistence remain deferred.

When `--client noop` is selected (including the default), HTTP-only flags (`--persist-content`, `--base-directory`, and `--timeout-seconds`) are rejected with clear argument errors.

Unknown source IDs and duplicate `--source-id` values fail with clear argument errors in list/run/validate flows, including HTTP and dry-run mode.
