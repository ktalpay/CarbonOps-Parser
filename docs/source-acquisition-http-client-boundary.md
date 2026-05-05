# Source Acquisition HTTP Client Boundary

## Scope

This increment adds a source acquisition HTTP client skeleton that uses an injected transport callable.

## Boundary

- `HttpSourceAcquisitionClient` accepts a transport dependency and uses it to request `descriptor.acquisition_url`.
- Tests provide fake transport callables so coverage is deterministic and fully offline.
- Acquired content is currently represented only through `SourceAcquisitionResult` metadata.
- The client does not write content to disk, create directories, or compute checksums in this increment.

## Deferred Work

Future tasks may add checksum computation and file persistence while preserving the same injected-transport client boundary.
