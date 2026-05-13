# GitHub Workflows

CI includes a Phase 1 release validation gate in
`release-validation.yml`.

The release gate validates Python tests, local static safety boundaries, local
source acquisition dry-run behavior, local parser fixture dry-run behavior,
.NET contract tests, parity fixture presence, sample config safety, runbook
consistency, and whitespace cleanliness.

Full repository public-safety validation is intentionally outside the default
release gate until existing fixture noise has baseline support.

The default workflow path is local-only. PostgreSQL integration validation is
manual and opt-in through the workflow input plus the
`CARBONOPS_RELEASE_GATE_RUN_INTEGRATION`,
`CARBONOPS_RUN_POSTGRESQL_INTEGRATION`, and externally supplied
`CARBONOPS_POSTGRESQL_TEST_DSN` controls.
