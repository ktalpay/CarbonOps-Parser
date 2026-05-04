# Review Readiness Checklist

This checklist helps reviewers confirm that future CarbonOps-Parser tasks are scoped, public-safe, and ready for PR review.

It is a review readiness guide only. It is not a launch, certification, legal, compliance, or carbon accounting checklist.

## Purpose

The repository uses small documentation, contract, skeleton, example, and test tasks to keep boundary changes easy to review.

This document gives contributors and reviewers a common checklist for confirming that each task stays inside its stated scope, avoids unsafe public wording, and documents deferred work clearly.

## Review Checklist

Before a task is ready for PR review, confirm:

- The branch name matches the scoped task.
- The change is limited to the files and behavior described by the task.
- Documentation-only tasks add no code, contracts, examples, tests, or runtime behavior.
- Contract or model tasks do not add execution behavior unless explicitly scoped.
- Artificial skeleton and example tasks stay deterministic, in-memory, and artificial unless local fixture use is explicitly scoped.
- Public wording avoids confidential information and unsupported claims.
- No real data, credential material, external source references, or copied source tables are added unless explicitly scoped.
- No operational-readiness claim is made.
- No compliance or legal correctness claim is made.
- No source-owner or carbon accounting correctness claim is made.
- No unit conversion or factor correctness logic is added unless explicitly scoped.
- Source adapter, parser, and normalization behavior are unchanged unless the task explicitly scopes a behavior change.
- Tests and checks listed in the task were run.
- New documents are linked from `docs/index.md` and, when consistent with the existing documentation map, `README.md`.
- Deferred items are documented instead of being quietly implemented.
- The work stays to one branch, one focused commit, and one PR.

## Checklist By Task Type

### Documentation-Only Task

- Adds or updates documentation only.
- Adds links to the documentation index where appropriate.
- Does not add code, contracts, examples, tests, fixtures, or runtime behavior.
- States current status and deferred areas without implying correctness or operational coverage.

### Contract Or Model Task

- Adds source-agnostic contracts or models only when scoped.
- Keeps models deterministic and easy to instantiate in tests.
- Avoids hidden I/O, config loading, network access, persistence, and scheduler behavior.
- Uses generic artificial fields unless a task explicitly scopes source-specific metadata.
- Adds focused tests for construction, immutability or caller-mutation safety, counts, flags, and public API exports.

### Artificial Skeleton Task

- Demonstrates implementation shape without real source processing.
- Uses artificial in-memory inputs or explicitly scoped local fixture references only.
- Returns existing contract types where the boundary requires them.
- Does not read file contents, download sources, persist data, schedule jobs, retry work, or load config.
- Does not perform unit conversion, factor correctness checks, or carbon accounting decisions.

### Artificial Usage Example Task

- Is importable and deterministic.
- Returns a stable dictionary or similarly testable structure.
- Avoids print-only behavior.
- Uses artificial records, artificial issues, or existing local fixture references only when scoped.
- Adds tests that confirm output shape and that no real source behavior is required.

### Test-Only Task

- Adds or adjusts tests for an existing boundary without changing behavior.
- Keeps tests deterministic and local.
- Avoids expanding test fixtures into real source data.
- Documents any residual gaps when the task calls for a recap or checklist update.

### Real Implementation Task With Explicit Scope

- Has a separate boundary document or task statement that names the real behavior being added.
- States what remains out of scope before implementation starts.
- Keeps source acquisition, parsing, normalization, persistence, scheduling, and reporting concerns separate.
- Adds focused tests for the scoped behavior only.
- Avoids correctness, compliance, legal, or operational claims unless a future task explicitly defines and reviews that language.

## Required Local Checks

Run the repository checks before the final commit:

- `python -m pytest`
- `python scripts/check_public_safety.py`
- `git diff --check`
- Local docs or link check if an established command is available.

If a check cannot be run, the PR notes should say which check was skipped and why.

## Public Safety Review

Public safety review should confirm:

- No confidential company, customer, or personal material is present.
- No real source data, real factor values, copied source tables, or unsupported source references are introduced.
- No credential material or auth behavior is introduced.
- No language implies legal, compliance, source-owner, carbon accounting, unit conversion, or factor correctness.
- No language implies operational readiness.
- The local public safety validation script passes.

## Scope Review

Scope review should confirm:

- The task does not mix unrelated documentation, contract, skeleton, example, and real behavior changes.
- Source adapter changes do not alter parser or normalization behavior unless explicitly scoped.
- Parser changes do not alter source adapter or normalization behavior unless explicitly scoped.
- Normalization changes do not alter source adapter or parser behavior unless explicitly scoped.
- Persistence, scheduling, retry/cancel, remote access, and config loading remain deferred unless explicitly scoped.

## Deferred Item Review

Each task should either leave these items untouched or explicitly document why they are in scope:

- Real source acquisition.
- Real parser-to-normalization integration behavior.
- Real normalization correctness.
- Executor integration beyond current artificial skeleton behavior.
- Aggregation semantics beyond output-shape counting.
- Unit conversion.
- Factor correctness.
- Carbon accounting correctness.
- Compliance or legal interpretation.
- Real source data.
- File reading beyond existing local and artificial examples.
- Source adapter behavior change.
- Parser behavior change.
- Database or persistence behavior.
- Scheduler behavior.
- Retry or cancel behavior.
- Downloading or remote access.
- Config loading.

## Non-Goals

This checklist does not claim:

- Real source acquisition coverage.
- Parser correctness for real external sources.
- Normalization correctness.
- Unit conversion correctness.
- Factor correctness.
- Legal or compliance interpretation.
- Carbon accounting correctness.
- Operational readiness.

It is only a PR review checklist for keeping future work scoped, public-safe, and easy to review.

## Related Documents

- [Repository Navigation Guide](repository-navigation-guide.md)
- [Public Roadmap Checkpoint](public-roadmap-checkpoint.md)
- [Source To Normalization Pipeline Recap](source-to-normalization-pipeline-recap.md)
- [Normalization Deferred Implementation Roadmap](normalization-deferred-implementation-roadmap.md)
- [Normalization Test Coverage Recap](normalization-test-coverage-recap.md)
- [Codex-Assisted Runs](codex-runs/README.md)
- [Codex Reviewer Checklist](codex-runs/reviewer-checklist.md)
- [Local Public Safety Validation](codex-runs/local-public-safety-validation.md)
