# Reviewer Checklist

Use this checklist for Codex-assisted pull requests.

## Scope Review

- Confirm the PR matches the task.
- Confirm unrelated refactors are not included.
- Confirm scope creep is called out as a blocker.

## Public Wording Review

- Check for confidential data.
- Check for production, compliance, legal, or carbon-accounting correctness claims.
- Check that examples remain generic unless the task explicitly requires source-specific content.

## Architecture Boundary Review

- Confirm parser, database, scheduler, downloader, and source-specific ingestion boundaries are preserved unless requested.
- Confirm public API changes are intentional and tested.
- Confirm examples are deterministic and local-only unless requested.

## Test And Validation Review

- Confirm requested tests/checks were run.
- Confirm `git diff --check` passed.
- Confirm missing validation is treated as a blocker.

## Documentation Link Review

- Confirm new documentation is linked from existing indexes when appropriate.
- Confirm local Markdown links resolve when practical.

## One-Commit Review

- Confirm the PR contains one task commit.
- Confirm the commit message matches the task.

## Merge Recommendation Levels

- `approve`: Scope is correct, validation is listed, and no blockers remain.
- `request changes`: Fixable issues exist before merge.
- `block`: Scope, safety, confidential data, missing validation, or architecture boundary issues prevent merge.
