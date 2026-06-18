# PostgreSQL Opt-In Integration Runbook

This runbook defines how PostgreSQL integration tests should be prepared and
run safely. The default test suite remains deterministic and DB-free; real
PostgreSQL checks require explicit opt-in controls and an externally supplied
test DSN.

The current Python production runtime is documented in
[Production Packaging And Operator Runbook](production-packaging-operator-runbook.md).
This integration runbook is test-harness guidance; it must not be used to store
production DSNs, passwords, tokens, or database dumps.

## Why Integration Tests Are Opt-In

The default test suite must remain deterministic and local-only. Normal
`python -m pytest` runs must not require PostgreSQL, credentials, network
access, a local database, migrations, or table setup.

PostgreSQL integration tests are opt-in because they can open external
connections, create isolated schemas, bootstrap Phase 1 tables, and write test
rows. They must not run unless the operator provides the canonical controls
described below.

## Existing Boundary

Use the existing PostgreSQL integration test boundary:

- marker name: `postgresql_integration`
- opt-in control name: `CARBONOPS_RUN_POSTGRESQL_INTEGRATION`
- test connection input name: `CARBONOPS_POSTGRESQL_TEST_DSN`
- helper: `create_postgresql_integration_test_boundary()`
- skip helper: `should_skip_postgresql_integration_tests()`
- skip reason: `POSTGRESQL_INTEGRATION_TEST_SKIP_REASON`

The helper is disabled by default. It does not inspect the runtime environment,
read config files, load credentials, connect to PostgreSQL, create cursors,
execute SQL, or write records.

Do not introduce a competing marker name. Future integration tests should align
with `postgresql_integration`. The control names are passive boundary metadata;
the library does not read their values.

## Opt-In Controls For Future Tests

Future PostgreSQL integration tests should require all of these explicit
test-runner controls:

- Pytest marker: `postgresql_integration`.
- Opt-in runner flag: `CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1`.
- Caller-provided test connection input: `CARBONOPS_POSTGRESQL_TEST_DSN`.

These names are external test-runner inputs only. Library code must not read
them implicitly. A future test harness may read them inside an opt-in test path,
but only after a scoped task adds that behavior and proves default test runs
remain DB-free.

The marker is registered in pytest configuration only to make future marked
tests explicit and discoverable. Registration does not enable DB tests by
default.

## psycopg Binary/Libpq Packaging Decision

CO-103L keeps the core project dependency as `psycopg>=3,<4` and adds an
explicit PostgreSQL opt-in extra for local smoke users:

```bash
python -m pip install -e ".[postgresql]"
```

The `postgresql` extra installs `psycopg[binary]>=3,<4`. This keeps the base
editable install small while giving local Docker PostgreSQL smoke runs a clear
binary-wrapper path when the host does not provide libpq. Local users who manage
libpq separately may continue to use the base editable install.

This is a packaging/installability decision only. It does not create PostgreSQL
connections, execute SQL, write records, enable repository persistence, change
the default test suite, or claim production persistence readiness. DSNs and
credentials remain external test-runner inputs and must stay redacted.

## Fresh Clone Install Smoke

Use this checklist to validate the public install path from a clean clone or a
clean checkout. It is local install verification only; it does not require
PostgreSQL, DSNs, credentials, or secrets.

Prerequisites:

- Start from a fresh clone or a clean checkout with `git status --short`.
- Create and activate a local virtual environment, for example:

```bash
python -m venv .venv
source .venv/bin/activate
```

Base install and CLI smoke:

```bash
python -m pip install -e .
carbonops-parser --help
carbonops-parser local-dry-run \
  --local-path examples/fixtures/defra_desnz_minimal.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-minimal-fixture \
  --content-type text/csv \
  --format-hint csv
carbonops-parser local-dry-run \
  --local-path examples/fixtures/defra_desnz_minimal.csv \
  --source-family defra_desnz \
  --source-id defra-desnz-minimal-fixture \
  --content-type text/csv \
  --format-hint csv \
  --json
```

Optional PostgreSQL packaging smoke:

```bash
python -m pip install -e ".[postgresql]"
python -c "import psycopg; print(psycopg.__version__)"
```

The optional PostgreSQL extra install does not enable repository persistence.
`PostgreSQLPersistenceRepository.persist()` remains unsupported/no-execution.
Default `python -m pytest` runs remain DB-free. The PostgreSQL connection smoke
is still manual and opt-in only through the `postgresql_integration` marker and
the canonical external controls. No DSN, password, credential, or secret is
required for this fresh-clone install smoke.

## Fresh Clone Install Smoke Execution Record

Use this record to capture a sanitized fresh-clone install smoke attempt. Do not
record absolute private paths, DSNs, passwords, tokens, or machine-specific
sensitive values.

Allowed status values:

- `not_run`
- `passed`
- `failed_sanitized`
- `blocked_environment` for historical environment-unavailable smoke attempts
  only; completed release records should use `passed` or `failed_sanitized`.

Current execution record:

- status: `passed`
- date: `2026-05-06`
- environment: temporary clean local clone with an isolated virtual
  environment.
- package metadata: `pyproject.toml` unchanged in this task.
- commands covered:
  - `python -m pip install -e .`
  - `carbonops-parser --help`
  - `carbonops-parser local-dry-run`
  - `carbonops-parser local-dry-run --json`
  - `python -m pip install -e ".[postgresql]"`
  - `python -c "import psycopg; print(psycopg.__version__)"`
- result summary:
  - editable install passed.
  - CLI help passed.
  - local dry-run passed with `status=success`.
  - JSON local dry-run passed with `status` set to `success`.
  - PostgreSQL extra install passed.
  - `psycopg` import passed and reported version `3.3.4`.
- DB behavior:
  - no PostgreSQL connection was performed.
  - no SQL execution was performed.
  - no DB write was performed.
  - no repository persistence was performed.
  - no migration or table creation was performed.
- secret handling:
  - no DSN was required.
  - no password was required.
  - no credential or secret value was recorded.
- post-run cleanup: temporary clone and virtual environment were removed after
  the smoke.

## Public Install Smoke Closure Checkpoint

CO-103O closes the public install smoke checkpoint with the verified paths
below:

- `python -m pip install -e .` passed in a fresh clone.
- `carbonops-parser --help` passed.
- `carbonops-parser local-dry-run` passed with text output.
- `carbonops-parser local-dry-run --json` passed with JSON output.
- `python -m pip install -e ".[postgresql]"` passed.
- `python -c "import psycopg; print(psycopg.__version__)"` passed.
- The fresh clone install smoke passed.
- The Docker PostgreSQL connection smoke passed as a manual opt-in smoke.
- Default `python -m pytest` remains DB-free.
- PostgreSQL smoke remains manual/opt-in through `postgresql_integration` and
  the canonical external controls.
- `PostgreSQLPersistenceRepository.persist()` remains unsupported/no-execution.

Deferred runtime and production work remains out of scope:

- real SQL execution
- DB writes
- repository runtime persistence
- migrations and table lifecycle
- transaction behavior
- idempotency/conflict runtime behavior
- production release hardening
- real source/parser coverage beyond the fixture/minimal path

This checkpoint does not claim production persistence readiness. It records
install and smoke evidence only, with no DSN, password, credential, or secret
values.

## Connection Smoke Skeleton

CO-103C adds a default-skipped connection smoke skeleton for future local
validation. The skeleton is test-only and guarded by:

- `postgresql_integration`
- `CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1`
- `CARBONOPS_POSTGRESQL_TEST_DSN`

Without both external controls, the smoke test is skipped and does not attempt a
connection. When explicitly enabled, it opens and closes a caller-provided
PostgreSQL connection only. It does not execute SQL, write records, create
tables, run migrations, commit, roll back, or call repository persistence.

## Suggested Local Test Environment

Future local validation should use an isolated PostgreSQL database created
outside the library:

- Suggested database name: `carbonops_parser_integration_test`.
- Suggested role model: a dedicated local test role with access only to the
  test database.
- Suggested schema ownership: pre-created test schema or tables owned by the
  test role, documented before runtime execution is enabled.

Do not use production, staging, shared development, or customer databases for
these tests. Do not commit database names that reveal private infrastructure.

## Credential Handling

Credentials must be supplied externally by the test runner or developer shell.
They must not be committed to docs, tests, fixtures, logs, examples, exceptions,
or result metadata.

Future test output should show only redacted connection metadata, such as test
database label, host label, or credential-present flags. It must not print DSNs,
user secrets, SQL parameter values, or password values.

## Future Manual Run Shape

When a future task adds real opt-in integration tests, the intended manual shape
is:

```bash
CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1 \
CARBONOPS_POSTGRESQL_TEST_DSN='<external test DSN supplied by the runner>' \
python -m pytest -m postgresql_integration tests/test_postgresql_connection_smoke_boundary.py
```

This command is a future/manual integration path. It is not part of the default
test suite and does not exist as runtime persistence enablement.

## PH-011 Docker Runtime Schema And Year-State Integration

PH-011 adds an opt-in integration test that proves runtime schema bootstrap and
source-family year-state behavior against Docker PostgreSQL. The default test
suite remains DB-free. Run this only against an isolated local test container on
the user's M3 test machine.

Start PostgreSQL locally:

```bash
docker run --rm --name carbonops-ph011-postgres \
  -e POSTGRES_PASSWORD=carbonops_local_test \
  -e POSTGRES_USER=carbonops \
  -e POSTGRES_DB=carbonops_parser_integration_test \
  -p 54329:5432 \
  postgres:16
```

In a second shell, run the focused integration test with an externally supplied
local DSN:

```bash
CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1 \
CARBONOPS_POSTGRESQL_TEST_DSN='<external test DSN supplied by the runner>' \
python -m pytest -m postgresql_integration tests/test_postgresql_runtime_year_state.py
```

The test creates a unique `carbonops_ph011_<uuid>` schema, creates missing Phase
1 tables with `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`,
records minimal GHG Protocol year-state rows, verifies latest-year and next-year
behavior, and verifies DEFRA/DESNZ no-data behavior returns the default initial
year `2024`.

Do not use production, staging, shared development, customer, or confidential
databases. Do not commit DSNs, passwords, container logs, or machine-specific
paths. After the run, unset both integration controls:

```bash
unset CARBONOPS_RUN_POSTGRESQL_INTEGRATION
unset CARBONOPS_POSTGRESQL_TEST_DSN
```

## PH-017 Production E2E Docker PostgreSQL Validation

PH-017 is the final production E2E release-validation pass for the source
families `ghg_protocol`, `defra_desnz`, and `ipcc_efdb`. Run it only on the
user's isolated Apple M3 Docker PostgreSQL test machine with an externally
supplied local test DSN.

Start PostgreSQL locally:

```bash
docker run --rm --name carbonops-ph017-postgres \
  -e POSTGRES_PASSWORD=carbonops_local_test \
  -e POSTGRES_USER=carbonops \
  -e POSTGRES_DB=carbonops_parser_integration_test \
  -p 54329:5432 \
  postgres:16
```

In a second shell, run the focused PH-017 integration tests:

```bash
CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1 \
CARBONOPS_POSTGRESQL_TEST_DSN='<external test DSN supplied by the runner>' \
python -m pytest -m postgresql_integration \
  tests/test_ghg_protocol_production_e2e.py \
  tests/test_defra_desnz_production_e2e.py \
  tests/test_ipcc_efdb_production_e2e.py \
  tests/test_postgresql_runtime_year_state.py
```

Then run the default release checks:

```bash
python scripts/release_validation_gate.py
python scripts/production_rc_verification.py
git diff --check
```

PH-017 M3 execution record:

- status: `passed`
- Docker PostgreSQL E2E integration: `4 passed, 22 deselected`.
- `dotnet restore`: completed.
- `python scripts/release_validation_gate.py`: passed.
- focused .NET production-safety contract tests: `17 passed`.
- `python scripts/production_rc_verification.py`: `Passed true`.
- `python -m pytest`: `2062 passed`.
- `git diff --check`: passed.
- result: PH-017 source-family Docker PostgreSQL E2E validation passed.
- secret handling: no DSN, password, credential, token, or secret value is
  recorded in this runbook.

Accepted risks remain explicit:

- Live source URL/default discovery remains a release risk.
- No source-owner correctness claim is made.
- No factor correctness claim is made.
- No legal correctness claim is made.
- No compliance correctness claim is made.

Expected PH-017 evidence shape:

- GHG Protocol, DEFRA/DESNZ, and IPCC EFDB are all explicitly reported.
- Schema bootstrap creates or verifies required tables additively.
- No existing data selects target year `2024`.
- Existing `2024` selects `2025`.
- Existing `2025` selects `2026`.
- Existing `2026` selects `2027`.
- Unavailable target-year source data reports `no_available_source_year`
  without inserts or year-state advancement.
- Available target-year runs download, archive metadata, parse, validate,
  insert, and advance latest year only after successful insert.
- Repeated execution does not duplicate normalized factor records.
- DB/config failures are sanitized and do not expose DSNs, passwords, tokens, or
  raw configured values.

Current PH-017 execution record:

- status: `passed`
- date: `2026-05-15`
- environment: user's Apple M3 Docker PostgreSQL machine.
- opt-in PostgreSQL E2E command: `4 passed, 22 deselected`.
- release validation gate: passed.
- production RC verification: `Passed true`.
- default Python test suite: `2062 passed`.
- focused .NET production-safety contract tests: `17 passed`.
- `dotnet restore`: completed.
- `git diff --check`: passed.
- validation record:
  [PH-017 Production E2E Docker PostgreSQL Release Validation](ph-017-production-e2e-docker-postgresql-release-validation.md).
- boundaries: live source URL/default discovery remains operator-reviewed; no
  source-owner, factor, legal, or compliance correctness claim is made.

After the manual run, unset both integration controls:

```bash
unset CARBONOPS_RUN_POSTGRESQL_INTEGRATION
unset CARBONOPS_POSTGRESQL_TEST_DSN
```

## Verifying Default Tests Remain DB-Free

Before and after future integration-test work, reviewers should run:

```bash
python -m pytest
python scripts/check_public_safety.py
git diff --check
```

The default suite must pass without PostgreSQL installed or running, without
database credentials, without an opt-in flag, and without a test DSN.

Reviewers should also confirm that default code paths do not contain
`psycopg.connect`, `connect(`, `cursor(`, `execute(`, `commit(`, `rollback(`, or
`begin(` calls.

## Connection Smoke Verification

Reviewers can verify the default-skipped connection smoke skeleton with:

```bash
python -m pytest tests/test_postgresql_connection_smoke_boundary.py tests/test_postgresql_integration_test_boundary.py
```

The expected default behavior is that the connection smoke skipped path is
reported and the default test suite remains DB-free. The smoke must not attempt
a PostgreSQL connection unless both `CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1` and
`CARBONOPS_POSTGRESQL_TEST_DSN` are provided externally by the test runner.

The explicit opt-in command shape remains:

```bash
CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1 \
CARBONOPS_POSTGRESQL_TEST_DSN='<external test DSN supplied by the runner>' \
python -m pytest -m postgresql_integration tests/test_postgresql_connection_smoke_boundary.py
```

The connection smoke does not execute SQL and does not write records. It should
only open and close the external test connection when explicitly enabled. Test
failures and troubleshooting output must not log DSNs, credentials, or secret
values. Because the smoke is connection-only, there should be no database write
cleanup for this task.

## Manual Connection Smoke Checklist

Use this checklist only for a local, explicitly opted-in connection smoke run:

- Confirm the working tree is clean with `git status --short`.
- Confirm the default suite remains DB-free with `python -m pytest`.
- Confirm local PostgreSQL is prepared outside the library.
- Use an isolated test database placeholder such as `<local-test-database>`.
- Use an isolated test role placeholder such as `<local-test-role>`.
- Set the canonical opt-in control:
  `CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1`.
- Set the canonical test DSN input externally:
  `CARBONOPS_POSTGRESQL_TEST_DSN='<external test DSN supplied by the runner>'`.
- Run the opt-in smoke command:

```bash
CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1 \
CARBONOPS_POSTGRESQL_TEST_DSN='<external test DSN supplied by the runner>' \
python -m pytest -m postgresql_integration tests/test_postgresql_connection_smoke_boundary.py
```

Expected result shape:

- With both controls present, the smoke may open and close the external test
  connection.
- Without those controls, the smoke remains skipped by default.
- The smoke performs no SQL execution.
- The smoke performs no DB writes.
- The smoke performs no migrations or table creation.
- Repository persistence remains disabled/no-execution.
- Logs and failures must not expose DSNs, credentials, or secret values.

After the manual run, reset any local test database state outside this project
if your local setup requires it. The connection-only smoke should not leave DB
writes to clean up. Then unset the opt-in controls:

```bash
unset CARBONOPS_RUN_POSTGRESQL_INTEGRATION
unset CARBONOPS_POSTGRESQL_TEST_DSN
```

## Manual Connection Smoke Execution Record

Use this template to record a local opt-in connection smoke run. If no manual
smoke was performed, keep `status` set to `not_run` or a truthful blocked
status, and do not record a passed result.

Allowed status values:

- `not_run`
- `blocked_missing_local_postgresql`
- `blocked_missing_dsn`
- `passed`
- `failed_sanitized`

Current execution record:

- status: `passed`
- date/time: `<manual-run-timestamp-redacted>`
- local environment: Docker-based local PostgreSQL container.
- PostgreSQL image: `postgres:16`.
- PostgreSQL version: PostgreSQL 16.11.
- container name: `carbonops-postgres-test`.
- test database: `<redacted-test-database>`
- readiness evidence: PostgreSQL container logs reported that the database
  system was ready to accept connections.
- system-level smoke evidence: manual `psql --version` smoke succeeded inside
  the container.
- opt-in smoke result: 1 passed, 15 deselected.
- marker: `postgresql_integration`
- opt-in control: `CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1`
- test DSN control: `CARBONOPS_POSTGRESQL_TEST_DSN`
- opt-in command:

```bash
CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1 \
CARBONOPS_POSTGRESQL_TEST_DSN='<external test DSN supplied by the runner>' \
python -m pytest -m postgresql_integration tests/test_postgresql_connection_smoke_boundary.py
```

Expected result shape:

- The connection smoke either passes or fails with sanitized output.
- This record claims a passed smoke result only for the sanitized Docker-based
  manual run evidence above.
- The project opt-in smoke performed no SQL execution.
- The project opt-in smoke performed no DB writes.
- Repository persistence remained disabled/no-execution.
- The default test suite remains DB-free.
- No migration, table creation, or project-managed database setup occurs.

Deferred local setup issues:

- The earlier editable-install metadata blocker from this smoke setup was
  resolved by adding the minimum required `project.name` and `project.version`
  metadata in CO-103K.
- The declared `psycopg>=3,<4` local import path failed because the local
  environment lacked the required libpq or binary wrapper.
- The manual smoke was unblocked locally with `psycopg[binary]>=3,<4`.
- CO-103L resolves the libpq/binary packaging decision by keeping
  `psycopg>=3,<4` in the core dependency list and adding the explicit
  `postgresql` extra with `psycopg[binary]>=3,<4` for local opt-in smoke users.

Redaction checklist:

- DSN redacted.
- Password redacted.
- Host, user, and database names redacted when needed.
- No secrets in logs, issues, PRs, examples, fixtures, or test output.

Post-run cleanup checklist:

- Unset `CARBONOPS_RUN_POSTGRESQL_INTEGRATION`.
- Unset `CARBONOPS_POSTGRESQL_TEST_DSN`.
- Confirm default `python -m pytest` still remains DB-free.
- Confirm no migration, table creation, DB write, or repository persistence
  happened.

## Local PostgreSQL Setup Checklist

This setup checklist is manual shell guidance only. It does not add project code
execution, repository persistence, SQL execution from project code, migrations,
or database writes from the default test suite.

- Install PostgreSQL on macOS with Homebrew using an explicit local version
  placeholder:

```bash
brew install postgresql@<major-version>
```

- Manage the local service outside this project:

```bash
brew services status postgresql@<major-version>
brew services start postgresql@<major-version>
brew services stop postgresql@<major-version>
```

- Use placeholder-only local database guidance:
  - database placeholder: `<local-test-database>`
  - role placeholder: `<local-test-role>`
  - host placeholder: `<local-host>`
  - port placeholder: `<local-port>`
  - credential placeholder: `<external-local-test-credential>`
- Create or reset the local test database and role manually outside project
  code, using tools such as `createdb <local-test-database>` and
  `createuser <local-test-role>` if that matches your local PostgreSQL setup.
- Construct `CARBONOPS_POSTGRESQL_TEST_DSN` only from placeholder values owned by
  the local test runner. Do not commit the DSN or credentials.
- Do not paste a DSN with a password or credential into logs, issues, PRs,
  examples, fixtures, or test output.
- Remember that default `python -m pytest` remains DB-free and does not require
  local PostgreSQL.
- Remember that local setup alone does not enable repository persistence;
  `PostgreSQLPersistenceRepository.persist()` remains unsupported/no-execution.
- Use the [Manual Connection Smoke Checklist](#manual-connection-smoke-checklist)
  before running the opt-in smoke.
- Roll back local setup manually outside project code if needed:

```bash
dropdb --if-exists <local-test-database>
dropuser --if-exists <local-test-role>
```

## System-Level PostgreSQL Install Smoke

These checks are external manual shell checks. They are not executed by project
code, are not part of default `python -m pytest`, do not enable repository
persistence, and do not change the explicitly gated project connection smoke.

Manual system-level shell checks may include:

```bash
brew services status postgresql@<major-version>
psql --version
psql -lqt | grep '<local-test-database>'
psql -c "\\du" | grep '<local-test-role>'
psql '<external test DSN supplied by the runner>' -c '<manual read-only check>'
```

Keep these commands separate from project test commands. Project test commands
remain limited to default DB-free validation and the explicitly opted-in smoke:

```bash
python -m pytest
CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1 \
CARBONOPS_POSTGRESQL_TEST_DSN='<external test DSN supplied by the runner>' \
python -m pytest -m postgresql_integration tests/test_postgresql_connection_smoke_boundary.py
```

Project library behavior remains unchanged: library code does not create
PostgreSQL connections, execute SQL, create tables, run migrations, write
records, load credentials, or enable repository persistence. DSNs and
credentials must stay local to the manual test runner and must be redacted from
logs, issues, PRs, examples, fixtures, and test output.

## Cleanup And Reset Guidance

Future opt-in integration tests should document cleanup before they are added:

- Use an isolated test database.
- Prefer disposable databases or schemas.
- Reset only the test database or schema.
- Never run cleanup against production, staging, shared development, or
  unlabelled databases.
- Document any table or schema expectations before executing SQL.
- Keep cleanup commands manual and visibly scoped to the test database.

This task does not add cleanup scripts, migrations, table creation, or SQL
execution.

## Troubleshooting

Troubleshooting should avoid exposing secrets:

- Report whether opt-in was requested, not the secret value used.
- Report missing test connection input as a missing external input.
- Report connection failures with sanitized host/database labels only.
- Do not print DSNs, passwords, tokens, or SQL parameter values.
- If default `python -m pytest` attempts to reach PostgreSQL, treat that as a
  blocker.
- If enabling integration tests requires weakening public safety checks, treat
  that as a blocker.

## Non-Goals

This runbook does not add:

- Repository runtime persistence.
- Default PostgreSQL connections.
- Cursor creation.
- SQL execution.
- Database writes.
- Transactions.
- Migrations.
- Table creation.
- Default integration test execution.
- Library environment loading.
- Library config loading.
- Credential or secret loading.
- HTTP or network behavior.
- Scheduler or background behavior.
- Production persistence readiness.

## Related Documents

- [PostgreSQL Integration Test Boundary](postgresql-integration-test-boundary.md)
- [PostgreSQL Runtime Readiness Checklist](postgresql-runtime-readiness-checklist.md)
- [PostgreSQL Implementation Safety Gate](postgresql-implementation-safety-gate.md)
- [PostgreSQL Runtime Persistence Implementation Plan](postgresql-runtime-persistence-implementation-plan.md)
- [PostgreSQL Runtime Execution Gate Boundary](postgresql-runtime-execution-gate-boundary.md)
- [PostgreSQL Repository Disabled Execution Preview Boundary](postgresql-repository-disabled-execution-preview-boundary.md)
