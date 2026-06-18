# Maintainer Release And Sync Checklist

This checklist is for maintainers preparing CarbonOps-Parser branch synchronization, public repository cleanup, or a first alpha/review tag. It does not authorize automatic release creation, issue closure, or branch merges.

## Branch State

- Verify `develop` contains the current accepted project state for the Python operator path, PostgreSQL-backed source-specific persistence, supported Phase 1 source families, and .NET parity evidence.
- Confirm the working tree is clean before any branch sync, release tag, or public handoff.
- Merge or sync `develop` to `main` only after review approval and repository state confirmation.
- Confirm the README on the default branch no longer contains stale baseline-status wording that contradicts the accepted project state.

## Pull Requests And Issues

- Review open pull requests for stale duplicates, especially duplicate documentation polish or baseline-cleanup PRs that are superseded by the accepted branch state.
- Close or supersede stale duplicate PRs only after confirming their useful changes are already represented or intentionally rejected.
- Review open issues whose GitHub state and labels disagree, such as issues that remain open while carrying a `status:merged` label.
- Update issue labels or close issues only through the normal maintainer workflow; do not use this checklist as automatic closure authority.

## Release Readiness

- Create a first alpha/review tag only after branch state, duplicate PRs, issue labels, README status, and validation evidence are clean.
- Confirm release notes describe the narrow project-level production-ready scope without expanding into carbon-accounting, legal, compliance, source-owner, or package-publication claims.
- Confirm package publication status is accurate before mentioning any install channel beyond repository-local or editable installs.
- Confirm release validation references exact commands and does not rely on private infrastructure.

## Repository Hygiene

- Confirm no secrets, DSNs, API keys, local database credentials, private source files, or environment-specific values are committed.
- Confirm no generated artifacts, caches, `.venv`, `__pycache__`, `.pytest_cache`, coverage outputs, screenshots, binaries, database dumps, or downloaded source files are committed.
- Confirm docs and templates still require scoped PRs, validation evidence, no production credentials, no generated artifacts, and no production-ready claim expansion without an explicit review task.
- Confirm public examples remain deterministic and local-only unless a reviewed task explicitly changes that boundary.

## Handoff Notes

Record the final branch, commit, validation commands, skipped checks with reasons, open maintainer follow-ups, and tag decision in the release or sync handoff.
