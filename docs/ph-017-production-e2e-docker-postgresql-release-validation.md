# PH-017 Production E2E Docker PostgreSQL Release Validation

## Verdict

production-ready with accepted risks

PH-017 requires final production E2E validation against Docker PostgreSQL on the
user's Apple M3 machine. M3 Docker PostgreSQL validation is now complete.

This verdict is limited to the PH-017 release-validation decision. It does not
claim source-owner correctness, factor correctness, legal correctness, or
compliance correctness.

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

Required PH-017 Docker PostgreSQL validation status: passed.

```bash
CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1 \
CARBONOPS_POSTGRESQL_TEST_DSN='<external test DSN supplied by the runner>' \
python -m pytest -m postgresql_integration \
  tests/test_ghg_protocol_production_e2e.py \
  tests/test_defra_desnz_production_e2e.py \
  tests/test_ipcc_efdb_production_e2e.py \
  tests/test_postgresql_runtime_year_state.py
# 4 passed, 22 deselected
```

M3 validation evidence:

- Docker PostgreSQL E2E integration passed on the user's Apple M3 machine.
- The focused opt-in PostgreSQL integration run reported `4 passed, 22
  deselected`.
- The run used the canonical external controls and did not record a DSN,
  password, credential, token, or secret value.
- Docker PostgreSQL evidence covers all three PH-017 production E2E source
  families and the runtime year-state path.

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
dotnet restore
# completed

python scripts/release_validation_gate.py
# passed

focused .NET production-safety contract tests
# 17 passed

python scripts/production_rc_verification.py
# Passed true

python -m pytest
# 2062 passed

git diff --check
# passed
```

The executable release gate, production RC verifier, default Python test suite,
focused .NET production-safety contract tests, and whitespace check passed.

## Required Behavior Assessment

| Required PH-017 behavior | Assessment |
| --- | --- |
| First run checks/creates database schema safely | Implemented by additive runtime schema bootstrap and verified by focused Docker PostgreSQL integration evidence. |
| No data targets 2024 per source family | Covered by local orchestrator and per-family E2E tests, with Docker PostgreSQL evidence for the opt-in production E2E path. |
| Existing 2024 targets 2025 | Covered by local orchestrator and per-family E2E tests, with Docker PostgreSQL evidence for the opt-in production E2E path. |
| Existing 2025 targets 2026 | Covered by local orchestrator tests and release validation evidence. |
| Existing 2026 targets 2027 | Covered by local orchestrator tests and release validation evidence. |
| 2027 unavailable no-ops with `no_available_source_year` | Covered by local orchestrator behavior and release validation evidence. |
| Available target year downloads, archives metadata, parses, validates, inserts, then updates latest year only after successful insert | Covered by local per-family E2E tests, orchestrator ordering, and Docker PostgreSQL opt-in evidence. |
| Repeated runs are idempotent and do not duplicate records | Covered by local per-family duplicate replay tests and Docker PostgreSQL opt-in evidence. |
| DB errors and config errors are safe/redacted | Covered by release gate, RC verifier, and repository error-shaping tests. |

## Source Family Assessment

### GHG Protocol

Local evidence exists for `2024` first-run ingestion, `2025` next-year
selection, future-year unavailable no-op handling, archive metadata creation,
parse/validate/insert handoff, and duplicate replay idempotency.

PH-017 Docker PostgreSQL evidence now includes the focused GHG Protocol
production E2E integration path on the required M3 Docker PostgreSQL
environment.

### DEFRA/DESNZ

Local evidence exists for `2024` first-run ingestion, `2025` next-year
selection, `2026` and `2027` unavailable no-op handling, archive metadata
creation, CSV/XLSX parse support, validation/insert handoff, and duplicate
replay idempotency.

PH-017 Docker PostgreSQL evidence now includes the focused DEFRA/DESNZ
production E2E integration path on the required M3 Docker PostgreSQL
environment.

### IPCC EFDB

Local evidence exists for `2024` first-run ingestion, `2025` next-year
selection, future-year unavailable no-op handling, archive metadata creation,
parse/validate/insert handoff, and duplicate replay idempotency.

PH-017 Docker PostgreSQL evidence now includes the focused IPCC EFDB production
E2E integration path on the required M3 Docker PostgreSQL environment.

## Accepted Risks

The PH-017 release verdict accepts these explicit risks:

- Live source URL/default discovery remains a release risk.
- No source-owner correctness claim is made.
- No factor correctness claim is made.
- No legal correctness claim is made.
- No compliance correctness claim is made.

## Release Decision

The repository has local, opt-in Docker PostgreSQL, release-gate, production RC,
focused .NET production-safety contract, and default Python test evidence for
the PH-017 behavior. The release decision for PH-017 is therefore:

production-ready with accepted risks

Merge readiness evidence:

1. Docker PostgreSQL E2E integration: `4 passed, 22 deselected`.
2. `dotnet restore`: completed.
3. `python scripts/release_validation_gate.py`: passed.
4. Focused .NET production-safety contract tests: `17 passed`.
5. `python scripts/production_rc_verification.py`: `Passed true`.
6. `python -m pytest`: `2062 passed`.
7. `git diff --check`: passed.

## PR Body Footer

The pull request body must end with:

```text
Task-ID: PH-017
Task-Issue: #584
```

Task-ID: PH-017
Task-Issue: #584
