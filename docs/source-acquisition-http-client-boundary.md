# Source Acquisition HTTP Client Boundary

## Scope

This increment keeps an injected-transport HTTP acquisition client and adds optional local file persistence for successful acquisitions.

## Boundary

- `HttpSourceAcquisitionClient` accepts a transport dependency and uses it to request `descriptor.acquisition_url`.
- Tests provide fake transport callables so coverage is deterministic and fully offline.
- By default (`persist_content=False`), acquired content remains in-memory and is represented through `SourceAcquisitionResult` metadata only.
- For successful 2xx responses, the client computes a deterministic lowercase SHA-256 checksum from in-memory bytes and sets `checksum_sha256`.
- Optional persistence is enabled with `persist_content=True` and a `base_directory`.
- When persistence is enabled, the client uses `plan_source_acquisition_target(...)` to determine `local_path` and writes the acquired bytes to that planned path.
- Parent directories are created only during successful persisted acquisitions.
- Existing files at the planned target path are overwritten in this increment.
- For non-2xx responses and transport exceptions, the client does not write files and returns `local_path=None` with `checksum_sha256=None`.

## Deferred Work

Future tasks may add acquisition audit storage and additional persistence controls while preserving the same injected-transport client boundary. This increment does not introduce parser execution or database persistence.

## Standard-Library Transport Increment

- `StandardLibraryHttpAcquisitionTransport` provides a concrete `HttpAcquisitionTransport` implementation using `urllib.request.urlopen` from the Python standard library.
- Transport-focused tests remain fully offline by mocking standard-library URL open behavior; no live network requests are required.
- CLI live mode is opt-in via `--client http`; default CLI behavior remains `NoopSourceAcquisitionClient` offline mode.
- HTTP status errors (`HTTPError`) are represented as `HttpAcquisitionTransportResponse` values with the error status code and available response metadata/body.
- Network-level exceptions such as `URLError` are left to propagate so `HttpSourceAcquisitionClient` can map transport exceptions into failed acquisition results.
