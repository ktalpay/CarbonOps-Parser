# Governance Smoke Test Checkpoint

This checkpoint summarizes the current governance smoke tests that help keep documentation references and the lightweight task queue consistent.

## Purpose

The repository now has small filesystem-local tests for documentation maps, related-document references, and task queue status notes. These tests are intentionally conservative: they protect common review surfaces without turning documentation governance into a rigid schema.

This document summarizes what the smoke tests protect, what they intentionally do not protect, and safe future hardening directions. It adds no code, tests, contracts, examples, or runtime behavior.

## Current Smoke Tests

The current governance smoke tests are:

- `tests/test_documentation_map_references.py`
- `tests/test_task_queue_consistency.py`

`tests/test_documentation_map_references.py` checks local Markdown file references in the public documentation maps and exact `Related Documents` sections.

`tests/test_task_queue_consistency.py` checks basic consistency in `docs/codex-runs/task-queue.md`.

## Protected Areas

The documentation reference smoke test currently protects:

- `README.md` local `.md` references.
- `docs/index.md` local `.md` references.
- Local `.md` references in exact `Related Documents` sections across `docs/*.md`.
- File existence validation only.
- Deterministic filesystem-local validation.

The task queue consistency smoke test currently protects:

- `docs/codex-runs/task-queue.md` file presence.
- Task identifier extraction.
- Duplicate task identifier detection.
- Recent completed task presence.
- Completed-line status wording.

Together, these tests help catch broken local documentation links and accidental task queue identifier conflicts before PR review.

## Intentional Non-Coverage

The governance smoke tests intentionally do not check:

- External URL validation.
- Heading anchor validation.
- Full-document link crawling.
- Documentation style enforcement.
- Strict task queue schema.
- Task number contiguity.
- Complete chronological ordering.
- Git history parsing.
- PR number validation.
- Remote or GitHub checks.

These items can become future tasks only when the scope is explicit and the checks are likely to remain stable.

## Safe Future Hardening

Safe future hardening directions include:

- Narrow additional smoke tests for high-value public review surfaces.
- Documentation-only coverage notes when a test boundary changes.
- Conservative checks before stricter rules.
- Small test updates that avoid brittle schema enforcement unless explicitly scoped.
- Separate behavior-changing tasks from governance smoke-test tasks.

Future checks should stay deterministic, filesystem-local, and easy to diagnose.

## Review Checklist

When updating governance smoke tests, reviewers should confirm:

- The test scope is narrow and named in the task.
- The test does not call remote services.
- The test does not depend on Git history, PR numbers, or external state.
- The test does not enforce broad style preferences unless explicitly scoped.
- Documentation coverage notes are updated when the test boundary changes.
- The public safety script passes.
- Source adapter, parser, and normalization behavior remain unchanged.

## Deferred Items

The following items remain deferred:

- External URL validation.
- Heading anchor validation.
- Full-document link crawling.
- Documentation style enforcement.
- Strict task queue schema.
- Task number contiguity.
- Complete chronological ordering.
- Git history parsing.
- PR number validation.
- Remote or GitHub checks.
- Real source acquisition.
- Parser behavior changes.
- Normalization behavior changes.
- Database or persistence behavior.
- Scheduler behavior.
- Retry or cancel behavior.
- Downloading or remote access.
- Config loading.

## Non-Goals

This checkpoint does not claim:

- Real source acquisition coverage.
- Parser correctness for real external sources.
- Normalization correctness.
- Unit conversion correctness.
- Factor correctness.
- Legal or compliance interpretation.
- Carbon accounting correctness.
- Operational readiness.

It only documents current governance smoke-test coverage and safe future hardening boundaries.

## Related Documents

- [Documentation Map Consistency Checklist](documentation-map-consistency-checklist.md)
- [Review Readiness Checklist](review-readiness-checklist.md)
- [Milestone Checkpoint CO-037 To CO-049](milestone-checkpoint-co-037-to-co-049.md)
- [Public Roadmap Checkpoint](public-roadmap-checkpoint.md)
- [Repository Navigation Guide](repository-navigation-guide.md)
- [Normalization Test Coverage Recap](normalization-test-coverage-recap.md)
