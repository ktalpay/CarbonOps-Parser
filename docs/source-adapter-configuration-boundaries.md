# Source Adapter Configuration Boundaries

Source adapter configuration should describe discovery inputs for an adapter instance. It should not define ingestion runtime behavior, parser behavior, persistence behavior, schedules, downloads, or secret handling.

## Purpose

Configuration boundaries keep source adapters small and explicit.

Adapter construction may accept the values needed to discover source document references. Future runtime orchestration should own wider concerns such as database connection settings, scheduler cadence, retry behavior, parser selection, and persistence integration.

## Adapter-Level Configuration

Conservative adapter-level configuration may include:

- Local directory path.
- Allowed file extensions.
- Source family, source name, or source key when represented by existing contracts.
- Artificial fixture paths for examples and tests.

`LocalFileSourceAdapter` currently performs non-recursive discovery. A recursive discovery flag is a future option only if a later task explicitly adds it.

Adapter-level configuration should stay deterministic and local unless a later task explicitly adds another boundary.

## Outside Adapter Scope

These concerns belong outside source adapter construction:

- Database connection settings.
- Scheduler cadence.
- Retry and cancellation policy.
- Remote download endpoints.
- Authentication secrets.
- Parser selection.
- Normalization rules.
- Persistence logging.
- Notification or observability integration.

Those concerns should be handled by future ingestion, runtime, or operations boundaries rather than the adapter package.

## Registry Boundary

`SourceAdapterRegistry` composes already-created adapters.

It should not:

- Load configuration files.
- Read environment variables.
- Auto-wire adapters.
- Auto-discover runtime adapters.
- Manage secrets.
- Create database, scheduler, downloader, parser, or persistence objects.

The registry remains a small lookup mechanism keyed by `SourceFamily`.

## Example Table

| Configuration item | Belongs to adapter? | Reason |
| --- | --- | --- |
| Local source directory | Yes | Needed for local file discovery |
| Allowed extensions | Yes | Limits local discovery inputs without parsing files |
| Database connection string | No | Persistence/runtime concern |
| Schedule interval | No | Scheduler concern |
| Parser format mapping | No | Parser or ingestion boundary concern |
| Remote access secret | No | Secret handling belongs outside this package |
| Recursive discovery | Deferred | Not implemented; may be explicit adapter option later |
| Source display name | Sometimes | Adapter option only when used as source metadata |

## Non-Goals

This document does not define:

- A configuration file format.
- Runtime configuration loader behavior.
- Dependency injection or autowiring.
- Secret management.
- Source-specific runtime setup.
- Compliance or legal determinations.

## Future Extension Points

Future tasks may add:

- Typed adapter options dataclasses if constructor parameters grow.
- A separate ingestion/runtime configuration boundary.
- A separate scheduler configuration boundary.
- Secret handling outside this package.
- Source-specific adapter options after source structure review.

Each extension should keep adapter construction separate from parser, persistence, scheduler, downloader, and operations concerns.
