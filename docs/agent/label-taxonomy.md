# Agent Label Taxonomy

## Purpose

This document defines the GitHub issue and pull request labels used by the agent coordination workflow.

Labels are used by humans, agents, and the future GitHub Actions watcher to determine task lane, lifecycle state, review state, and automation eligibility.

## Status Labels

Use exactly one `status:*` label per task issue.

| Label | Meaning |
|---|---|
| `status:blocked` | Task cannot start because dependencies are incomplete. |
| `status:ready` | Task is eligible for the assigned lane agent. |
| `status:in-progress` | Assigned agent is actively working on the task. |
| `status:in-review` | A PR exists and is waiting for review. |
| `status:needs-fix` | Review found issues that must be fixed in the existing PR. |
| `status:merged` | Task PR has been merged and the task is complete. |

## Lane Labels

Use exactly one `lane:*` label per task issue.

| Label | Meaning |
|---|---|
| `lane:python` | Python implementation lane. |
| `lane:dotnet` | .NET implementation lane. |
| `lane:review` | PR review lane. |
| `lane:parity` | Python/.NET parity review lane. |
| `lane:ops` | Workflow, issue, watcher, or repository automation lane. |

## Agent Labels

Use exactly one `agent:*` label per task issue.

| Label | Meaning |
|---|---|
| `agent:python` | Task is assigned to python-agent. |
| `agent:dotnet` | Task is assigned to dotnet-agent. |
| `agent:review` | Task is assigned to review-agent. |
| `agent:parity` | Task is assigned to parity-agent. |
| `agent:ops` | Task is assigned to ops-agent. |

## Type Labels

Use one or more `type:*` labels when useful.

| Label | Meaning |
|---|---|
| `type:implementation` | Product or platform implementation task. |
| `type:review` | Review-only task. |
| `type:parity` | Python/.NET parity validation task. |
| `type:ops` | Agent workflow or repository automation task. |
| `type:docs` | Documentation-only task. |
| `type:cleanup` | Cleanup or correction task. |

## Priority Labels

Priority labels are optional.

| Label | Meaning |
|---|---|
| `priority:high` | Should be handled before normal ready tasks. |
| `priority:normal` | Default priority. |
| `priority:low` | Can wait behind other ready work. |

## Review Verdict Labels

Use these on PRs or review issues when useful.

| Label | Meaning |
|---|---|
| `verdict:merge-ready` | Review found no blocking issue. |
| `verdict:needs-fix` | Review found issues that must be fixed before merge. |
| `verdict:blocked` | Review cannot complete or PR cannot proceed. |
| `verdict:drift-found` | Parity review found Python/.NET contract or behavior drift. |
| `verdict:aligned` | Parity review found Python/.NET behavior aligned. |

## Label Consistency Rules

- Each task issue must have exactly one `status:*` label.
- Each task issue must have exactly one `lane:*` label.
- Each task issue must have exactly one `agent:*` label.
- A task issue may have multiple `type:*` labels only when the task genuinely spans categories.
- `status:ready` must not be used when dependencies are incomplete.
- `status:merged` must only be applied after the linked PR is merged.
- `status:needs-fix` must point back to the same PR and branch, not a new task, unless the reviewer explicitly requests a follow-up task.

## Watcher Expectations

The future GitHub Actions watcher may use these labels to:

- identify merged task issues
- detect tasks eligible to become `status:ready`
- avoid starting blocked tasks
- avoid multiple active tasks in the same lane
- distinguish implementation, review, parity, and ops work

The watcher must not infer task readiness from label names alone. It must also check declared dependencies.

## Non-Goals

This document does not:

- create labels in GitHub
- add GitHub Actions workflows
- add watcher scripts
- modify issue templates
- modify source code
