# Background Job Model

CarbonOps-Parser is intended to run as a background ingestion service. The service evaluates source-specific schedules, checks whether source documents changed, and runs imports only when needed.

## Source-Specific Schedules

Each source family has its own schedule:

- GHG Protocol
- DEFRA/DESNZ
- IPCC EFDB

Schedules should support daily, weekly, and monthly periods with explicit time and timezone settings. A schedule for one source should not force another source to run.

## Job Lifecycle

At a high level, a scheduled job should:

1. Resolve the configured source.
2. Check the latest source version and raw file hash.
3. Skip the import if the same version/hash is already stored.
4. Download the file when a new version or hash is detected.
5. Archive the raw file.
6. Parse and validate records.
7. Persist source-specific records.
8. Store import run status, summary counts, and validation issues.

## Idempotency

Imports should be idempotent by source version and content hash.

The recommended duplicate policy is `skip_if_same_hash`. If a source version and file hash already exist, the job should record or report that no import was needed and avoid duplicate persistence.

## Locking Concept

The database model includes `carbon_job_locks` for a single-instance lock concept. The design goal is to prevent overlapping imports for the same source when a previous run is still active.

Phase 1 documentation defines the lock concept. Runtime lock behavior should be implemented in a later task with care for each implementation path.
