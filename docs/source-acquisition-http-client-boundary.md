# Source Acquisition HTTP Client Boundary

## Scope

This increment adds a source acquisition HTTP client skeleton that uses an injected transport callable.

## Boundary

- `HttpSourceAcquisitionClient` accepts a transport dependency and uses it to request `descriptor.acquisition_url`.
- Tests provide fake transport callables so coverage is deterministic and fully offline.
- Acquired content remains in-memory and is represented through `SourceAcquisitionResult` metadata.
- For successful 2xx responses, the client computes a deterministic lowercase SHA-256 checksum from in-memory bytes and sets `checksum_sha256`.
- The client does not write content to disk, create directories, or persist artifacts in this increment.

## Deferred Work

Future tasks may add file persistence and acquisition audit storage while preserving the same injected-transport client boundary.
