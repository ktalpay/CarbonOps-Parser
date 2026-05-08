# Agent Operating Model

## Purpose

This document defines the operating model for coordinating Python, .NET, review, parity, and ops agents in this repository.

The source of truth for agent work is GitHub issues, pull requests, and the repository task/issue metadata. Agents must operate through explicit tasks and must not infer or start unrelated work.

## Agent Roles

### python-agent

Responsible for Python implementation tasks.

Allowed scope is limited to Python-side files explicitly listed by the task.

### dotnet-agent

Responsible for .NET implementation tasks.

Allowed scope is limited to .NET-side files explicitly listed by the task.

### review-agent

Responsible for reviewing pull requests against their original task scope.

The review-agent must not:

- modify code
- create commits
- create new branches
- rewrite the implementation
- expand the original scope

The review-agent must return one of these verdicts:

- `merge-ready`
- `needs-fix`
- `blocked`

### parity-agent

Responsible for comparing Python and .NET behavior, contracts, naming, schema alignment, state transitions, and error semantics.

The parity-agent must not modify code unless explicitly requested in a dedicated implementation task.

### ops-agent

Responsible for repository workflow, issue templates, labels, watcher workflow, and agent coordination infrastructure.

The ops-agent must not modify product implementation code unless explicitly requested.

## Task Lifecycle

Allowed task statuses:

- `blocked`
- `ready`
- `in-progress`
- `in-review`
- `needs-fix`
- `merged`

### blocked

The task cannot start because one or more dependencies are incomplete.

### ready

The task is eligible to be picked up by the assigned lane agent.

### in-progress

The assigned agent is actively working on the task.

### in-review

A PR exists and is waiting for review.

### needs-fix

The review-agent or human reviewer found issues that must be fixed in the existing PR.

### merged

The PR has been merged and the task is complete.

## Queue Progression Rules

Agents must not automatically start the next task unless the queue state marks that task as `ready`.

Agents must only pick tasks from their assigned lane.

A lane agent must not start a new task while it has another active task in `in-progress`, `in-review`, or `needs-fix`.

A task may become `ready` only when all declared dependencies are `merged`.

A merged PR alone is not sufficient to start arbitrary next work. The queue state must explicitly allow it.

## Branch Naming

Use deterministic branch names.

Recommended patterns:

- `feature/py-xxx-short-task-name`
- `feature/dn-xxx-short-task-name`
- `feature/rv-xxx-short-task-name`
- `feature/pt-xxx-short-task-name`
- `feature/ops-xxx-short-task-name`

Examples:

- `feature/py-004-source-acquisition-run-contract`
- `feature/dn-004-source-acquisition-run-contract`
- `feature/ops-004-agent-task-watcher`

## Pull Request Requirements

Every PR must include:

- Task ID
- linked GitHub issue
- summary
- files changed
- validation performed
- remaining risks
- explicit merge readiness statement

Recommended PR metadata:

```text
Task-ID: DN-004
Closes #123
Review Requirements

The review-agent must review the PR against:

task scope
non-goals
forbidden changes
allowed files
runtime side effects
dependency changes
test/check output
Python/.NET contract drift when relevant

The review-agent must not fix code directly. If fixes are required, the implementation agent updates the existing PR.

Needs-Fix Flow

When a PR is marked needs-fix:

The original coder agent continues on the same branch.
The agent addresses only the review comments.
The agent must not start a new issue.
The agent must not create a new branch unless explicitly instructed.
The same PR is updated and sent back to review.
Worktree Preservation

Codex agent worktrees must not be deleted.

After PR merge:

clean merged branches when appropriate
preserve long-lived agent worktrees
do not remove local agent workspaces unless explicitly instructed
Merge Cleanup

After a PR is merged:

mark the task as merged
unblock dependent tasks only if all dependencies are merged
mark eligible dependent tasks as ready
do not auto-start work unless the assigned lane is free and the task is explicitly ready
Safety Boundaries

Unless explicitly requested by the task, agents must not:

modify unrelated files
add migrations
execute database operations
add runtime database connectivity
add network behavior
add broad refactoring
modify public contracts outside the task scope
change parser/download/runtime behavior
modify tests or documentation outside the requested scope
delete or clean Codex worktrees
Final Report Format

Agents must return:

Summary
Files changed
Validation performed
Remaining risks
Commit-ready or merge-ready verdict

## Agent PR Footer Metadata

Agent-created pull requests must end with a deterministic metadata footer.

Required footer:

```text
Task-ID: <TASK_ID>
Task-Issue: #<ISSUE_NUMBER>

The watcher uses Task-Issue as the canonical GitHub issue target for label updates.

The final matching Task-ID and Task-Issue lines in the PR body are treated as authoritative. This avoids accidentally parsing example metadata from earlier markdown code blocks.
