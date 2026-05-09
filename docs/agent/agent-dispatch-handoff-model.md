# Agent Dispatch Handoff Model

## Purpose

This document defines the OPS-014 handoff model for turning one safe `status:ready` GitHub issue into a deterministic local agent handoff package.

The model builds on the lane queue readiness and dispatcher design in [Lane Queue Readiness Report And Local Dispatcher Design](lane-queue-readiness-report-design.md). OPS-014 narrows that design to the handoff artifact: what is selected, what prompt is produced, what safety checks are preserved, and what remains manual for now.

This is a design document only. It does not implement live Codex invocation, auto-start Codex agents, auto-merge pull requests, auto-approve pull requests, delete branches, delete worktrees, or close issues.

## Dispatch Handoff Responsibility

The dispatch handoff component is not the Agent Task Watcher.

The watcher owns merged-PR processing:

- detect merged agent PRs;
- read PR footer metadata;
- mark task issues `status:merged`;
- unblock dependent tasks when every dependency is merged.

The dispatch handoff component owns ready-task preparation:

- consume open task issues with `status:ready`;
- select exactly one safe task per dispatch cycle;
- verify dependencies and queue blockers before handoff;
- generate the correct lane-specific prompt;
- produce a concrete handoff package for a human or future local automation;
- eventually bridge queue readiness to local Codex execution after the handoff model is proven.

It must not process merged PR events or write `status:merged`; that remains watcher-owned.

## Handoff Package Contents

The handoff package should be a deterministic artifact that can be reviewed, archived, or passed to a supported local Codex invocation mechanism later.

Required fields:

| Field | Description |
| --- | --- |
| `selected_issue_number` | GitHub issue number selected for this dispatch cycle. |
| `task_id` | Canonical task identifier parsed from the issue body, such as `OPS-014`. |
| `lane` | Lane label without the `lane:` prefix, such as `ops`, `python`, `dotnet`, `parity`, or `review`. |
| `agent_label` | Agent label from the issue, such as `agent:ops`. |
| `issue_title` | Exact selected issue title. |
| `issue_body` | Exact selected issue body used to generate the prompt. |
| `dependency_summary` | Parsed `Depends on` and `Unblocks` values plus resolved dependency issue numbers and statuses. |
| `selected_prompt_template` | Template category chosen for the issue and lane. |
| `generated_prompt` | Complete lane-specific Codex prompt. |
| `expected_branch_name_pattern` | Expected branch pattern, for example `feature/ops-014-agent-dispatch-handoff`. |
| `expected_pr_title` | Expected PR title derived from task ID and issue title. |
| `required_pr_footer` | Final two PR body lines required by watcher metadata. |
| `validation_checklist` | Task and repository validation commands or manual checks. |
| `safety_constraints` | Non-goals and forbidden actions that the executing agent must preserve. |
| `human_action_needed` | Manual next step, such as review the prompt, start Codex manually, review PR, or merge PR. |

Suggested artifact shape:

```yaml
selected_issue_number: 344
task_id: OPS-014
lane: ops
agent_label: agent:ops
issue_title: "[OPS-014] Agent dispatch handoff model"
issue_body: "<verbatim issue body>"
dependency_summary:
  depends_on:
    - task_id: OPS-013
      issue_number: 343
      status: merged
  unblocks: []
selected_prompt_template: ops workflow/automation
generated_prompt: "<complete prompt text>"
expected_branch_name_pattern: feature/ops-014-agent-dispatch-handoff
expected_pr_title: "OPS-014: Agent dispatch handoff model"
required_pr_footer: |
  Task-ID: OPS-014
  Task-Issue: #344
validation_checklist:
  - markdown/content sanity review
  - git diff --check
  - confirm no workflow/source/test/runtime files were modified unless explicitly justified
  - confirm no branch/worktree cleanup logic was added
safety_constraints:
  - no auto-merge
  - no auto-approval
  - no branch deletion
  - no worktree deletion
human_action_needed: "Review the generated prompt and start the local Codex lane task manually."
```

The exact serialization can be Markdown, YAML, JSON, or a combined Markdown report with fenced structured metadata. OPS-015 should choose one format and keep it stable enough for later automation.

## Selection Rules

The dispatcher must select deterministically and conservatively:

- Dispatch exactly one task per dispatch cycle.
- Select only open issues with `status:ready`.
- Do not dispatch if an open PR exists for any active task awaiting review or fixes.
- Do not dispatch if any issue has `status:in-progress`.
- Parse the selected issue's `Depends on` list before prompt generation.
- Every dependency task must resolve to exactly one issue.
- Every dependency issue must have `status:merged`.
- Prefer lanes in this order when multiple safe ready issues exist:
  1. `ops`
  2. `python`
  3. `dotnet`
  4. `parity`
  5. `review`
- Within the same lane, choose the lowest issue number unless declared dependency order requires a different selection.
- Do not dispatch `parity` or `review` tasks before all implementation dependencies are `status:merged`.

Multiple ready tasks should be reported with the deterministic winner. Multiple ready tasks do not permit parallel dispatch.

## Handoff Modes

### Report-Only Mode

Report-only mode is read-only. It explains what would be selected and why.

It may:

- list ready candidates;
- list blockers such as open PRs, `status:in-progress` issues, dependency gaps, dirty repo state, or watcher failures;
- show the deterministic selected issue when dispatch would be safe;
- summarize which prompt template would be used.

It must not write files, labels, comments, branches, commits, PRs, or local Codex invocations.

### Prompt-Only Mode

Prompt-only mode generates the handoff artifact but does not change GitHub state.

It may:

- perform all report-only checks;
- generate the prompt artifact for the selected task;
- include the validation checklist, safety constraints, expected branch name, expected PR title, and required footer.

It must not change issue labels, add comments, create branches, invoke Codex, push commits, open PRs, or close issues.

### Claim-And-Prompt Mode

Claim-and-prompt mode is a future mode. It may mark the selected issue `status:in-progress` and produce the handoff artifact only after all preflight checks pass.

It may write:

- removal of existing active status labels from the selected issue;
- addition of `status:in-progress` to the selected issue;
- an optional issue comment containing the handoff summary and artifact reference.

It must not write `status:merged`, invoke Codex, auto-approve, auto-merge, delete branches, delete worktrees, or close issues.

### Live-Run Mode

Live-run mode is a later future mode. It may invoke Codex only if a supported local CLI or app invocation mechanism exists and has been validated.

It must:

- complete all claim-and-prompt checks first;
- produce the handoff artifact before invocation;
- invoke only one local lane task;
- stop with a handoff report if invocation support is missing or ambiguous;
- preserve the same PR footer, validation, fallback report, and no-cleanup constraints as prompt-only mode.

Live-run mode is explicitly out of scope for OPS-014 and should not be implemented before the read-only reporter and prompt artifact are reviewed.

## Prompt Template Contract

Prompt templates are selected from issue metadata, lane label, and task scope. Each template must produce a complete prompt that can be handed to a local Codex agent without requiring the user to rewrite it.

Every template must include:

- narrow scope tied to the selected task;
- explicit non-goals;
- allowed files;
- forbidden changes;
- validation requirements;
- required PR body footer;
- PR fallback report requirement;
- no branch cleanup;
- no worktree cleanup;
- no production secrets;
- no destructive database operations;
- final report requirements.

Required template categories:

### Python Source Discovery Boundary

Use for Python tasks that define or refine source discovery contracts, boundaries, metadata, examples, or tests.

The generated prompt must limit changes to the Python files, tests, examples, and docs allowed by the issue. It must not add source-specific ingestion, downloader execution, scheduler behavior, database writes, production claims, or network behavior unless explicitly requested.

### Python Source Download Execution

Use for Python tasks that implement or validate controlled source download execution boundaries.

The generated prompt must require explicit local/offline test behavior unless the issue authorizes network behavior. It must forbid production credentials, destructive file operations, database writes, scheduler coupling, and branch/worktree cleanup.

### .NET Source Discovery Boundary

Use for .NET tasks that define source discovery contracts, metadata, examples, or test boundaries.

The generated prompt must limit changes to the allowed .NET project, test, and documentation files. It must forbid Python drift unless parity work is explicitly requested, and it must require validation commands appropriate to the .NET scope.

### .NET Repository Contract

Use for .NET tasks that define repository, persistence, or contract boundaries.

The generated prompt must preserve public API expectations unless explicitly changed, forbid destructive database operations, forbid production credentials, and require clear validation of contract behavior.

### Parity Review

Use for tasks that compare Python and .NET behavior, naming, schema alignment, state transitions, error semantics, or public contract drift.

The generated prompt must frame the work as review or report generation unless the issue explicitly allows implementation. It must not modify code, create unrelated branches, or start follow-up implementation tasks.

### Ops Workflow/Automation

Use for tasks that modify or document repository workflow, issue templates, labels, watcher behavior, dispatcher behavior, PR metadata, or agent coordination.

The generated prompt must forbid product implementation changes unless explicitly requested. It must not add auto-merge, auto-approval, branch deletion, worktree deletion, issue closing, live Codex invocation, or label changes beyond the task's normal PR flow.

## Safety Guards

Dispatch must be blocked or limited by these guards:

- no auto-merge;
- no auto-approval;
- no branch deletion;
- no worktree deletion;
- no issue closing;
- no production secrets;
- no destructive database operations;
- no parallel execution;
- no task dispatch if repo state is dirty;
- no task dispatch if watcher has recent failures;
- no task dispatch if dependency graph is inconsistent;
- no task dispatch if prompt generation cannot include the required PR footer;
- no task dispatch if the selected lane has no template.

The dispatcher must report guard failures rather than repairing them destructively.

## GitHub State Interaction

The dispatcher reads GitHub state through issue and PR metadata.

It should read:

- open issues labeled `status:ready`;
- open issues labeled `status:in-progress`;
- open PRs for task branches or PR bodies containing task metadata;
- selected task issue title and body;
- lane and agent labels;
- `Depends on` and `Unblocks` fields from issue bodies;
- dependency issue status labels, especially `status:merged`;
- recent watcher workflow health when available.

It may write only in future modes:

- `status:in-progress` label on the selected issue in claim-and-prompt or live-run mode;
- removal of conflicting `status:*` labels from the selected issue when claiming;
- an optional issue comment with the handoff summary and artifact reference.

It must not write:

- `status:merged`, because the watcher owns that transition;
- labels on dependency issues;
- issue close state;
- PR approval state;
- PR merge state;
- branch or worktree cleanup changes.

## Failure Modes

The handoff reporter should make failures explicit and non-destructive:

- No ready task: report that no `status:ready` issue is available.
- Multiple ready tasks: list candidates, show deterministic ordering, and select no more than one.
- Dependency missing: block dispatch when `Depends on` is empty, malformed, or missing for a task that requires dependencies.
- Dependency issue not found: block dispatch and identify the unresolved dependency task ID.
- Open PR blocks dispatch: report the PR number, title, head branch, and task metadata if available.
- Dirty worktree: block dispatch and report dirty paths without deleting, reverting, or cleaning them.
- Codex invocation unsupported: produce the handoff package and stop before claim or live invocation, depending on mode.
- PR creation failed after Codex run: report branch, commit hash, push status, intended PR title/body, files changed, validation, and the observed error.
- Generated prompt missing footer: block handoff until the footer can be generated exactly.
- Selected task lane has no template: block prompt generation and report the unsupported lane.
- Watcher recent failure: block claim/live dispatch until queue health is verified.
- Dependency graph inconsistency: block dispatch when dependencies are duplicated, cyclic, missing status labels, or have conflicting status labels.

## Manual Steps For Now

Until OPS-015 or later implements the reporter, the human still manually:

- reviews the selected issue and generated prompt;
- starts the local Codex lane task;
- verifies the implementation PR was opened;
- reviews or assigns review for the PR;
- merges the PR when it is ready.

The handoff model should reduce prompt-writing and selection ambiguity first. It should not remove human review or merge control.

## OPS-015 Proposal

OPS-015 should implement a read-only dispatch handoff reporter.

Recommended scope:

1. Read GitHub issues and PRs for the repository.
2. Apply the deterministic selection rules from this document.
3. Produce a report for exactly one selected safe `status:ready` task, or explain why no dispatch is safe.
4. Generate a prompt artifact using the selected template category.
5. Include the required PR footer, fallback report requirement, validation checklist, and safety constraints in the artifact.
6. Do not start Codex.
7. Do not invoke live-run behavior.
8. Do not change labels unless an explicit later configuration enables claim mode.
9. Do not auto-merge, auto-approve, delete branches, delete worktrees, or close issues.

OPS-015 should leave claim-and-prompt and live-run modes disabled by default until the read-only reporter output is reviewed.
