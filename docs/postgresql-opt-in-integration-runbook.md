# PostgreSQL Opt-In Integration Runbook

This runbook defines how future PostgreSQL integration tests should be prepared
and run safely.

It is documentation and test-harness guidance only. It does not create a
PostgreSQL connection, create a cursor, run SQL, write records, start a
transaction, finish a transaction, roll back a transaction, create tables, run
migrations, load environment variables in library code, load configuration
files in library code, load credentials, perform HTTP or network calls, schedule
work, or claim production persistence readiness.

## Why Integration Tests Are Opt-In

The default test suite must remain deterministic and local-only. Normal
`python -m pytest` runs must not require PostgreSQL, credentials, network
access, a local database, migrations, or table setup.

PostgreSQL integration tests are reserved for future runtime tasks that
explicitly add database behavior behind the runtime execution gate. Until then,
the repository remains unsupported/no-execution and integration test behavior is
represented only by metadata.

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
