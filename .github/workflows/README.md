# GitHub Workflows

CI includes a Phase 1 release validation gate in
`release-validation.yml`.

The release gate validates a focused Phase 1 Python release-validation test set,
local static safety boundaries, local source acquisition dry-run behavior, local
parser fixture dry-run behavior, focused stable .NET production-safety contract
tests, parity fixture presence, sample config safety, runbook consistency, and
whitespace cleanliness.

The full Python test suite, full .NET contract suite, and full repository
public-safety validation are intentionally outside the default release gate. The
full .NET contract suite is outside the default release gate until known
deterministic parser assertion failures are resolved. They remain separate
tracked hardening items until baseline/noise cleanup, allowlist support, and
parser fixture determinism cleanup are available.

The default workflow path is local-only. PostgreSQL integration validation is
manual and opt-in through the workflow input plus the
`CARBONOPS_RELEASE_GATE_RUN_INTEGRATION`,
`CARBONOPS_RUN_POSTGRESQL_INTEGRATION`, and externally supplied
`CARBONOPS_POSTGRESQL_TEST_DSN` controls.
