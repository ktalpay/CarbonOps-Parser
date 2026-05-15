# PH-017 Production E2E Docker PostgreSQL Release Validation

## Verdict

not production-ready

PH-017 requires final production E2E validation against Docker PostgreSQL on the
user's Apple M3 machine. That required validation did not complete in this
session. The current execution environment reports `x86_64`, not Apple Silicon,
and Docker socket access is unavailable to this process.

This verdict is limited to the PH-017 release-validation decision. It does not
claim that the implementation is unusable; it says the required production
release evidence is incomplete.

## Scope Reviewed

This review assessed the production E2E path for:

- GHG Protocol: `ghg_protocol`.
- DEFRA/DESNZ: `defra_desnz`.
- IPCC EFDB: `ipcc_efdb`.

The review covered the year-based orchestrator, source-family production E2E
adapters, parser boundaries, validation boundaries, PostgreSQL schema bootstrap,
PostgreSQL year-state storage, normalized factor insert behavior, release gate,
production RC verifier, and Docker PostgreSQL runbook.

No production credentials, production DSNs, live customer data, destructive
database operations, PR merge, PR approval, issue closure, branch deletion, or
worktree deletion were used.

## Docker PostgreSQL Evidence

Required PH-017 Docker PostgreSQL validation status: blocked.

Observed local environment:

```bash
uname -m
# x86_64

docker --version
# Docker version 29.4.0, build 9d7ad9ff18

docker image ls postgres:16
# permission denied while trying to connect to the docker API
```

Impact:

- The validation did not run on the required Apple M3 machine.
- A Docker PostgreSQL container could not be inspected or started from this
  session.
- The opt-in PostgreSQL integration suite could not be run against Docker
  PostgreSQL here.
- No passed Docker PostgreSQL production E2E result is claimed by this review.

## Repository Evidence Found

Existing focused tests and runtime boundaries support the intended production
E2E behavior:

- `tests/test_production_e2e_year_orchestrator.py` covers all three canonical
  source families, default `2024` selection when no year exists, `2024 -> 2025`,
  `2025 -> 2026`, `2026 -> 2027`, and `no_available_source_year` safe no-op
  behavior.
- `tests/test_ghg_protocol_production_e2e.py` covers GHG Protocol local
  download/archive metadata, parse, validation, insert handoff, next-year
  targeting, future-year no-op behavior, idempotent duplicate replay, and an
  opt-in Docker PostgreSQL integration test.
- `tests/test_defra_desnz_production_e2e.py` covers DEFRA/DESNZ local
  download/archive metadata, parse, validation, insert handoff, next-year
  targeting, future-year no-op behavior, idempotent duplicate replay, XLSX flat
  file parsing, and an opt-in Docker PostgreSQL integration test.
- `tests/test_ipcc_efdb_production_e2e.py` covers IPCC EFDB local
  download/archive metadata, parse, validation, insert handoff, next-year
  targeting, future-year no-op behavior, idempotent duplicate replay, and an
  opt-in Docker PostgreSQL integration test.
- `src/carbonfactor_parser/persistence/postgresql_runtime_schema_bootstrap.py`
  uses additive `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`
  statements for required Phase 1 tables.
- `src/carbonfactor_parser/persistence/postgresql_year_state_repository.py`
  returns `2024` for no existing year by default and otherwise computes
  `latest_year + 1`.
- `src/carbonfactor_parser/persistence/postgresql_normalized_factor_repository.py`
  inserts normalized factor records with idempotent conflict handling and
  returns safe structured database/config errors with redacted messages.
- `scripts/release_validation_gate.py` redacts password, token, secret, and
  PostgreSQL DSN-shaped output.
- `scripts/production_rc_verification.py` validates production-like config,
  passive schema readiness, service entrypoint wiring, dry-run orchestration,
  diagnostics redaction, and release-gate status without default database
  connections or live source calls.

## Local Validation Run

Commands run in this session:

```bash
python -m pytest
# blocked: No module named pytest

python scripts/release_validation_gate.py
# blocked during focused Python tests: No module named pytest

python scripts/release_validation_gate.py --check-only
# passed

python scripts/production_rc_verification.py --output-format json
# passed

git diff --check
# passed
```

The executable release gate did not pass because the active Python environment
does not have `pytest` installed. The static release gate and production RC
verifier did pass. This is another reason the PH-017 release verdict remains
`not production-ready` for this run.

## Required Behavior Assessment

| Required PH-017 behavior | Assessment |
| --- | --- |
| First run checks/creates database schema safely | Implemented by additive runtime schema bootstrap and covered by opt-in integration tests, but not verified against Docker PostgreSQL in this session. |
| No data targets 2024 per source family | Covered by local orchestrator and per-family E2E tests. Not verified against Docker PostgreSQL in this session. |
| Existing 2024 targets 2025 | Covered by local orchestrator and per-family E2E tests. Not verified against Docker PostgreSQL in this session. |
| Existing 2025 targets 2026 | Covered by local orchestrator tests. Not verified against Docker PostgreSQL in this session. |
| Existing 2026 targets 2027 | Covered by local orchestrator tests. Not verified against Docker PostgreSQL in this session. |
| 2027 unavailable no-ops with `no_available_source_year` | Covered by local orchestrator behavior. Not verified against Docker PostgreSQL in this session. |
| Available target year downloads, archives metadata, parses, validates, inserts, then updates latest year only after successful insert | Covered by local per-family E2E tests and orchestrator ordering. Not verified against Docker PostgreSQL in this session. |
| Repeated runs are idempotent and do not duplicate records | Covered by local per-family duplicate replay tests and opt-in per-family Docker tests exist. Not verified against Docker PostgreSQL in this session. |
| DB errors and config errors are safe/redacted | Covered by release gate, RC verifier, and repository error-shaping tests. |

## Source Family Assessment

### GHG Protocol

Local evidence exists for `2024` first-run ingestion, `2025` next-year
selection, future-year unavailable no-op handling, archive metadata creation,
parse/validate/insert handoff, and duplicate replay idempotency.

PH-017 blocker: the GHG Protocol Docker PostgreSQL integration test was not run
against the required M3 Docker PostgreSQL environment.

### DEFRA/DESNZ

Local evidence exists for `2024` first-run ingestion, `2025` next-year
selection, `2026` and `2027` unavailable no-op handling, archive metadata
creation, CSV/XLSX parse support, validation/insert handoff, and duplicate
replay idempotency.

PH-017 blocker: the DEFRA/DESNZ Docker PostgreSQL integration test was not run
against the required M3 Docker PostgreSQL environment.

### IPCC EFDB

Local evidence exists for `2024` first-run ingestion, `2025` next-year
selection, future-year unavailable no-op handling, archive metadata creation,
parse/validate/insert handoff, and duplicate replay idempotency.

PH-017 blocker: the IPCC EFDB Docker PostgreSQL integration test was not run
against the required M3 Docker PostgreSQL environment.

## Release Decision

The repository has meaningful local and opt-in integration coverage for the
PH-017 behavior, but the required final Docker PostgreSQL validation evidence is
missing. The release decision for PH-017 is therefore:

not production-ready

Required before changing this verdict:

1. Run the PH-017 Docker PostgreSQL validation command from
   `docs/postgresql-opt-in-integration-runbook.md` on the user's Apple M3
   machine.
2. Capture sanitized evidence for all three source families.
3. Confirm year-state behavior through `2024`, `2025`, `2026`, `2027`, and
   `no_available_source_year` against PostgreSQL.
4. Confirm repeated-run idempotency against PostgreSQL.
5. Re-run the release validation gate and `git diff --check`.

## PR Body Footer

The pull request body must end with:

```text
Task-ID: PH-017
Task-Issue: #584
```

Task-ID: PH-017
Task-Issue: #584
