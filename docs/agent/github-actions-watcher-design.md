# GitHub Actions Watcher Design

## Purpose

This document defines the first version of the GitHub Actions watcher for the agent coordination workflow.

The watcher coordinates issue and PR state after pull requests are merged. It does not execute agent work, write product code, create branches, or start Codex tasks.

## Scope

The first watcher version is responsible for:

- detecting merged pull requests
- reading the task identity from the PR body
- finding the related task issue
- marking the completed task as `status:merged`
- checking dependent tasks
- marking eligible dependent tasks as `status:ready`
- leaving traceable comments on affected issues

## Non-Goals

The watcher must not:

- start Codex agents
- create branches
- create pull requests
- modify source code
- modify task documents
- delete or clean worktrees
- execute local commands
- infer task readiness without dependency checks
- start the next task automatically

## Trigger Model

The watcher may run on these triggers:

- `pull_request` closed event
- scheduled polling
- manual workflow dispatch

The first implementation should support:

```yaml
on:
  pull_request:
    types: [closed]
  workflow_dispatch:

Scheduled polling can be added later if needed.

PR Requirements

Each agent PR must include a machine-readable task identifier in the body:

Task-ID: DN-004

A PR should also link the GitHub issue:

Closes #123

The watcher should prefer Task-ID as the canonical task identity.

Task Issue Requirements

Each task issue should have:

one status:* label
one lane:* label
one agent:* label
a Task ID field from the issue form
optional dependency fields:
Depends on
Unblocks

Example:

Task ID: DN-004
Depends on: DN-003
Unblocks: DN-005, PT-004
Completed Task Flow

When a PR is merged:

Confirm the PR was actually merged.
Read Task-ID from the PR body.
Find the matching task issue.
Remove active status labels from the issue:
status:ready
status:in-progress
status:in-review
status:needs-fix
status:blocked
Add:
status:merged
Add an issue comment explaining:
merged PR number
detected task ID
watcher action taken
Dependency Unblock Flow

After marking the completed task as merged:

Read the completed task issue's Unblocks field.
For each unblocked task:
find the task issue by Task ID
read its Depends on field
verify every dependency task has status:merged
If all dependencies are merged:
remove status:blocked
add status:ready
add a comment explaining why the task became ready
If dependencies are still incomplete:
keep status:blocked
add no ready label
Label Rules

The watcher must follow docs/agent/label-taxonomy.md.

A task issue must not end up with multiple status:* labels.

When changing status, the watcher must remove all existing status:* labels before applying the new one.

Safety Rules

The watcher must be conservative.

If any required field is missing or ambiguous, it must:

leave labels unchanged
add a comment explaining the blocker
exit successfully unless the workflow itself failed

The watcher must not guess task identity from branch names alone.

The watcher must not infer readiness from a merged PR alone. It must check declared dependencies.

Error Handling

The watcher should treat these as non-destructive blockers:

missing Task-ID in PR body
no matching issue found
multiple matching issues found
missing dependency metadata
dependency issue not found
insufficient GitHub token permissions

In these cases, the watcher should comment where possible and avoid label changes.

Permissions

The future workflow will need permissions for:

permissions:
  issues: write
  pull-requests: read
  contents: read
Implementation Preference

The first implementation should prefer GitHub CLI commands inside GitHub Actions where practical.

The first implementation should avoid introducing a custom application, external service, or OpenAI API dependency.

Expected First Implementation

The first workflow implementation should be limited to:

.github/workflows/agent-task-watcher.yml
simple shell or GitHub CLI logic
no product code changes
no source code execution
Out of Scope for First Implementation

The following are intentionally out of scope:

automatic Codex task creation
agent auto-start
branch creation
PR creation
local worktree cleanup
task queue file mutation
cross-repository orchestration
scheduled polling
