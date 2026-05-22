# Branch And Pull Request Workflow

CarbonOps-Parser uses small, reviewable contribution units:

```text
one task -> one branch -> one commit -> one pull request
```

Contributors may open issues, work from branches in their own forks, and submit
pull requests. The upstream maintainer reviews and merges pull requests.
Contributors should not assume that an open pull request expands the supported
production scope or changes the project verdict.

## Issue First

Use the most specific issue template:

- Bug report for reproducible defects.
- Feature request for scoped improvements.
- Documentation request for corrections or discoverability gaps.
- Production-readiness question for supported-scope or readiness-evidence
  questions.
- Source mapping for source discovery or parser mapping notes.

Keep issue descriptions local, deterministic, and public. Do not attach
credentials, private source files, confidential customer data, or
environment-specific configuration.

## Branch Naming

Use a short task-oriented branch name. Examples:

```text
feature/docs-001-repository-contribution-and-discoverability-polish
fix/local-dry-run-validation-message
docs/python-runtime-runbook-clarity
```

Fork branches are welcome. Upstream branch creation is reserved for maintainers
and trusted automation.

## Pull Request Expectations

Before opening a pull request:

- Keep the pull request focused on the issue.
- Preserve the public API unless the issue explicitly changes it.
- Avoid source-specific ingestion, parser, database, scheduler, or downloader
  coupling unless the issue explicitly requests it.
- Avoid production, compliance, legal, carbon-accounting correctness, or
  source-owner correctness claims.
- Update docs when behavior, scope, validation, or operator expectations change.
- Run `python -m pytest` when Python package behavior or examples are affected.
- Run `git diff --check`.

Use the pull request template and list the validation commands with pass/fail
results. If a check is not applicable, say why.

## Review And Merge

The maintainer owns final review, branch protection decisions, and merging.
Pull requests should remain open until review feedback is resolved and required
validation is complete. Do not merge, approve, close issues, delete branches, or
delete worktrees unless the maintainer explicitly asks for that action.
