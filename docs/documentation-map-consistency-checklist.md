# Documentation Map Consistency Checklist

This checklist helps reviewers keep CarbonOps-Parser documentation maps, indexes, related-doc references, and task queue notes consistent across documentation-first tasks.

## Purpose

The repository has many boundary, recap, roadmap, and checklist documents. Small docs-only changes are easiest to review when every public-facing map points to the right place and related references stay accurate.

This document is a manual review aid. It adds no code, contracts, examples, tests, or runtime behavior.

## Consistency Checklist

For each new documentation task, confirm:

- The new document is added to `docs/index.md`.
- The new document is added to the README documentation map when it is comparable to existing public-facing entries.
- Related documents sections link only to documents that exist.
- Relative links follow the surrounding file style.
- `docs/codex-runs/task-queue.md` is updated for the completed task and the next conservative task.
- PR summaries use the same boundary and deferred-item wording as the changed docs.
- The [Review Readiness Checklist](review-readiness-checklist.md) remains the generic PR review reference.
- New docs do not duplicate or contradict existing boundary, recap, roadmap, or checklist docs.
- Deferred item wording stays consistent across related docs.
- The change does not add code, contracts, examples, tests, or behavior unless explicitly scoped.

## README Update Rule

Update `README.md` when the new document is comparable to existing entries in the README documentation map, such as:

- Boundary documents.
- Recap documents.
- Roadmap documents.
- Navigation guides.
- Review or consistency checklists.

Do not update `README.md` for narrow internal task notes unless the existing README pattern supports that level of detail.

When updating `README.md`, place the new link near related documents rather than at the end by default.

## docs/index.md Update Rule

Add every new public documentation file to `docs/index.md` using the existing flat list format.

When choosing placement:

- Keep source adapter docs near source adapter docs.
- Keep parser docs near parser docs.
- Keep normalization docs near normalization docs.
- Keep roadmap, navigation, and checklist docs near the existing roadmap and guide entries.
- Do not invent section headings unless the index format changes in a separate explicit task.

## Related Documents Review

Related-doc sections should help readers move to the next relevant boundary or recap.

Reviewers should confirm:

- Every linked file exists.
- Links are relative to the current document.
- Link labels match the document title closely.
- The list is useful rather than exhaustive.
- New references do not imply real source coverage, parser correctness, normalization correctness, unit conversion correctness, factor correctness, legal interpretation, or operational readiness.

## Task Queue Review

For `docs/codex-runs/task-queue.md`, confirm:

- The completed task is added to `Completed`.
- `Active` is updated to the next conservative task.
- `Next` and `Backlog` stay small.
- Existing completed entries are not rewritten without a clear reason.
- Task names match the actual work completed, not an older placeholder.

## Deferred Wording Review

Deferred item wording should remain consistent across related docs. Prefer explicit deferred lists when a task touches roadmap, review, or boundary material.

Common deferred items include:

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

## Documentation-Only Review

For documentation-only tasks, reviewers should confirm:

- Changed files are limited to the new or edited docs, `docs/index.md`, `docs/codex-runs/task-queue.md`, and `README.md` when the map pattern calls for it.
- No code, contract, example, fixture, or test files changed.
- No behavior is described as newly implemented unless the task actually added it.
- Local docs or reference checks are run when an established command exists.
- Public safety wording is checked with the repository script.

## Local Checks

Run the usual local checks before the final commit:

- `python -m pytest`
- `python scripts/check_public_safety.py`
- `git diff --check`
- `python -m pytest tests/test_documentation_map_references.py` when documentation map references change.
- Local docs or reference link check if an established command is available.

If no dedicated docs link-check script exists, use a small local reference check for the new document and its index entries, and mention that in the PR notes.

## Documentation Reference Smoke Test Coverage

`tests/test_documentation_map_references.py` currently checks:

- Local `.md` links in `README.md`.
- Local `.md` links in `docs/index.md`.
- Local `.md` links inside exact `Related Documents` sections across `docs/*.md`.
- Filesystem-local deterministic validation.
- File existence only.

The smoke test intentionally does not check:

- External URL availability.
- Anchors-only links.
- Heading anchor targets.
- Every Markdown link in every document.
- Documentation style preferences.
- Remote or network references.

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

It only helps keep documentation references consistent during PR review.

## Related Documents

- [Repository Navigation Guide](repository-navigation-guide.md)
- [Review Readiness Checklist](review-readiness-checklist.md)
- [Public Roadmap Checkpoint](public-roadmap-checkpoint.md)
- [Source To Normalization Pipeline Recap](source-to-normalization-pipeline-recap.md)
- [Normalization Deferred Implementation Roadmap](normalization-deferred-implementation-roadmap.md)
- [Codex-Assisted Runs](codex-runs/README.md)
- [Codex Task Queue](codex-runs/task-queue.md)
