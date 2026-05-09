# Lane Queue Readiness Report And Local Dispatcher Design

## Purpose

This document defines the OPS-013 design for lane queue readiness reporting and the future local agent dispatcher.

The design keeps GitHub issues and labels as the task queue/state machine, keeps the Agent Task Watcher responsible for PR-merge-driven transitions, and defines how a later local dispatcher can select at most one safe task for handoff.

This is a design document only. It does not implement the live dispatcher, start Codex agents, edit issue labels, delete branches, delete worktrees, or add any automation that merges pull requests.

## Current State

The Agent Task Watcher is responsible for the merge-side queue transition:

- detect a merged agent PR;
- read the task metadata footer from the PR body;
- find the related task issue;
- mark the completed task issue as `status:merged`;
- inspect dependency metadata for downstream issues;
- mark downstream issues as `status:ready` only when every declared dependency is `status:merged`.

The watcher intentionally does not start agents, create branches, create PRs, clean worktrees, or choose the next task. That boundary is defined in [GitHub Actions Watcher Design](github-actions-watcher-design.md) and keeps GitHub Actions conservative.

The current gap is queue management after an issue becomes `status:ready`. A human still checks ready issues, inspects dependencies, chooses the next task, writes the Codex prompt, starts the correct lane agent, and verifies the PR footer/review flow. This is useful while the process is maturing, but it is not the target operating model.

## Desired State

The target operating model is:

1. GitHub issues and labels act as the task queue/state machine.
2. The Agent Task Watcher handles PR-merge-driven state transitions.
3. A future Local Agent Dispatcher runs locally and selects one safe `status:ready` issue.
4. The dispatcher claims exactly one task by moving it to `status:in-progress` only after all preflight checks pass.
5. The dispatcher generates a lane/task-specific prompt artifact.
6. The dispatcher starts or hands off to the correct local Codex lane agent.
7. Codex completes the task and opens a PR.
8. A reviewer reviews the PR.
9. A human merges the PR.
10. The watcher transitions the completed task to `status:merged` and dependency-unblocks downstream work.

The human's normal role should become review and merge, not manual queue management.

## State Machine

The dispatcher and watcher should treat the task issue status labels as a single-state machine:

- `status:blocked`: task cannot start because at least one dependency is incomplete.
- `status:ready`: task is eligible for selection if queue and dependency checks pass.
- `status:in-progress`: exactly one local agent task is actively being worked.
- `status:in-review`: a PR exists and is awaiting review or human action.
- `status:needs-fix`: review found issues that must be fixed on the existing PR.
- `status:merged`: the task PR was merged and the watcher completed the task transition.

Expected transitions:

| From | To | Actor | Condition |
| --- | --- | --- | --- |
| `status:blocked` | `status:ready` | Watcher | All declared dependencies are `status:merged`. |
| `status:ready` | `status:in-progress` | Dispatcher | One selected task passes all preflight checks. |
| `status:in-progress` | `status:in-review` | Codex or dispatcher support tooling | A PR was created for the task. |
| `status:in-review` | `status:needs-fix` | Reviewer or human | Review requests changes. |
| `status:needs-fix` | `status:in-review` | Lane agent | Fixes are pushed to the existing PR. |
| `status:in-review` | `status:merged` | Watcher | The PR is merged by a human and watcher processing succeeds. |

The first live dispatcher implementation should not perform review, approval, merge, issue close, branch deletion, or worktree deletion transitions.

## Queue Selection Rules

The dispatcher must use deterministic selection rules:

- Never start more than one task per run.
- Never start if an open PR exists for any task awaiting review.
- Never start if any task has `status:in-progress`.
- Select only open GitHub issues with `status:ready`.
- Validate the selected issue's `Depends on` list before claiming it.
- Every declared dependency must resolve to exactly one task issue with `status:merged`.
- Prefer lanes in this order when multiple ready issues exist:
  1. `ops`
  2. `python`
  3. `dotnet`
  4. `parity`
  5. `review`
- If the same lane has multiple ready issues, choose the lowest issue number unless explicit task dependency order requires a different choice.
- Never start `parity` or `review` tasks unless all implementation dependencies are `status:merged`.

If multiple ready tasks exist, the dispatcher should report all eligible candidates and the deterministic winner. Multiple candidates are not an error by themselves, but the live run must still claim only the single selected task.

## Prompt Template Strategy

The dispatcher should generate prompts from lane/task template categories rather than free-form text.

Required template categories:

- `python source discovery boundary`
- `python source download execution`
- `dotnet source discovery boundary`
- `dotnet repository contract`
- `parity review`
- `ops workflow/automation`

Every generated prompt must enforce:

- narrow scope tied to the selected issue;
- allowed and forbidden files from the issue or dispatcher configuration;
- no branch deletion;
- no worktree cleanup;
- no production secrets or private source data;
- no destructive database operations;
- no auto-merge or auto-approval;
- no source-specific ingestion unless the issue explicitly requests it;
- no parser, database, scheduler, or downloader coupling unless the issue explicitly requests it;
- validation commands required by the task;
- exactly one task branch, one commit, and one PR unless the task explicitly says otherwise;
- a PR body that ends exactly with the required footer:

```text
Task-ID: <TASK_ID>
Task-Issue: #<ISSUE_NUMBER>
```

The prompt artifact should include the selected issue number, task ID, lane, dependencies, allowed files, forbidden changes, validation requirements, PR title/body requirements, and final-report requirements.

The footer format should remain aligned with [PR Footer Metadata](pr-footer-metadata.md).

## Dispatcher Modes

### Report-Only Mode

Report-only mode is read-only. It should:

- inspect repository identity and GitHub issue/PR state;
- list active, blocked, ready, in-review, needs-fix, and merged task counts;
- show dependency blockers for ready-looking tasks that are not actually safe;
- show the deterministic next selected task if the queue is safe;
- explain why no task can start when the queue is blocked.

Report-only mode must not edit labels, create prompt files, create branches, invoke Codex, push commits, or open PRs.

### Dry-Run Mode

Dry-run mode performs all report-only checks and may generate a local prompt artifact for the selected task.

Dry-run mode must not edit GitHub labels, create branches, invoke Codex, push commits, or open PRs. The generated prompt should be marked as dry-run output and should include the exact live-run checks that would be required before claiming the task.

### Live-Run Mode

Live-run mode may claim and hand off one task only when every preflight check passes.

Live-run requirements:

- mark the selected issue `status:in-progress` only after all preflight checks pass;
- create a prompt file or equivalent local artifact before invoking Codex;
- invoke local Codex only if a supported CLI or app mechanism exists and can be validated;
- stop with a handoff report if local Codex invocation is unsupported or ambiguous;
- never continue to a second task in the same run.

The first implementation should prefer report-only behavior. Live-run should be added only after the reporter and prompt dry-run are stable.

## Preflight Checks

The dispatcher must complete these checks before any live-run claim:

- Repository identity matches `ktalpay/CarbonOps-Parser`.
- Local checkout is on the expected base branch or a supported dispatcher control branch.
- Base branch is current with `origin/develop`; stale local `develop` blocks live-run.
- Git working tree is clean, with no unstaged, staged, or untracked changes.
- GitHub CLI or API authentication is available and scoped for issue/PR reads and label updates.
- Recent Agent Task Watcher runs are healthy enough to trust queue state.
- No open task PR is waiting for human review.
- No task issue currently has `status:in-progress`.
- The selected issue is open and has exactly one valid `Task-ID`.
- The selected issue has exactly one supported lane label.
- The selected issue has a matching agent label or an explicitly accepted lane-agent mapping.
- The selected issue's `Depends on` list parses successfully.
- Every dependency resolves to exactly one open or completed task issue.
- Every dependency issue has `status:merged`.
- The selected prompt template category can be resolved deterministically.
- The local Codex invocation mechanism is supported before any attempt to start an agent.

If any preflight fails, live-run must stop before changing labels.

## Failure Modes

The reporter and dispatcher should make failures explicit and non-destructive:

- PR creation failed: leave the task in its current label state, report branch/commit/push status, and require human handoff.
- Codex produced a commit but no PR: report the branch, commit hash, validation known so far, and exact command or API error.
- Task output is missing the required PR footer: block review handoff until the footer is corrected.
- Watcher run failed: block new live-run dispatch until queue health is restored or manually verified.
- Dependency graph inconsistency: block selection when a dependency task is missing, duplicated, cyclic, or lacks a single status label.
- Multiple ready tasks: report all candidates, select deterministically, and still start no more than one task.
- Unsupported local Codex invocation: produce a handoff report with the prompt artifact path and do not claim the task.
- Dirty worktree: block live-run and report the dirty paths without deleting, reverting, or cleaning them.
- Stale local `develop`: block live-run until the base branch is updated from `origin/develop`.

Failures should not cause branch deletion, worktree deletion, issue closing, auto-approval, auto-merge, or destructive database operations.

## Non-Goals

This design does not include:

- auto-merge;
- auto-approval;
- branch deletion;
- worktree deletion;
- issue closing;
- production credential handling;
- parallel agent execution in the first implementation;
- production, compliance, legal, or carbon-accounting correctness claims;
- source-specific ingestion not explicitly requested by a task;
- parser, database, scheduler, or downloader coupling not explicitly requested by a task.

## OPS-014 Proposal

OPS-014 should implement the dispatcher in conservative increments:

1. Implement a read-only lane queue readiness reporter first.
   - Read GitHub issues and PRs.
   - Summarize active queue state.
   - Validate dependency readiness.
   - Select at most one deterministic next task.
   - Produce a human-readable report without changing labels or files.

2. Optionally add dry-run prompt generation.
   - Generate the selected task prompt from a template category.
   - Write a local prompt artifact only in dry-run output location.
   - Include the exact PR footer requirement and validation checklist.
   - Keep GitHub labels, branches, commits, and PRs unchanged.

3. Add live-run task claiming only after report-only and dry-run behavior are reviewed.
   - Require all preflight checks.
   - Move exactly one selected issue to `status:in-progress`.
   - Create the prompt artifact.
   - Invoke local Codex only through a supported, validated CLI or app mechanism.
   - Stop with a handoff report when invocation support is missing.

4. Defer advanced behavior.
   - No parallel agent execution.
   - No automatic review assignment beyond explicit safe metadata updates.
   - No auto-approval or auto-merge.
   - No branch or worktree cleanup.
