#!/usr/bin/env python3
"""Agent dispatch handoff reporter.

By default, the reporter inspects GitHub issue and PR state through read-only
`gh` CLI queries, selects one safe ready task, and prints a deterministic
handoff report. Explicit `--claim` mode may claim one selected issue by moving
`status:ready` to `status:in-progress`. Explicit `--lifecycle` and
`--review-status` modes inspect one claimed task and PR metadata without
mutating GitHub. The reporter never starts Codex, approves PRs, merges PRs,
closes issues, deletes branches, or deletes worktrees.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


DEFAULT_REPOSITORY = "ktalpay/CarbonOps-Parser"
BASE_BRANCH = "develop"
LANE_PRIORITY = ("ops", "python", "dotnet", "parity", "review")
TASK_ID_PATTERN = re.compile(r"^Task[- ]ID:\s*([A-Za-z]+-\d+)\s*$", re.MULTILINE)
FIELD_PATTERN_TEMPLATE = r"^{field}:\s*(.*)$"
TASK_REFERENCE_PATTERN = re.compile(r"\b(?:OPS|PY|DN|PT|RV)-\d+\b", re.IGNORECASE)
TASK_ISSUE_PATTERN = re.compile(r"^Task-Issue:\s*#?(\d+)\s*$", re.MULTILINE)

PROMPT_TEMPLATE_CATEGORIES = (
    "python source discovery boundary",
    "python source download execution",
    "dotnet source discovery boundary",
    "dotnet repository contract",
    "parity review",
    "ops workflow/automation",
)

VALIDATION_CHECKLIST = (
    "Run focused tests for the task if tests are added.",
    "Run python -m pytest if practical.",
    "Run python scripts/check_public_safety.py if applicable.",
    "Run git diff --check.",
    "Confirm dry-run did not modify GitHub labels/issues/PRs.",
    "In claim mode, confirm only the selected issue changed from status:ready to status:in-progress.",
)

SAFETY_CONSTRAINTS = (
    "Do not start Codex agents.",
    "Do not call Codex.",
    "Do not edit GitHub issues or labels.",
    "Do not approve or merge PRs.",
    "Do not close issues.",
    "Do not delete branches.",
    "Do not delete worktrees.",
    "Do not add branch/worktree cleanup logic.",
    "Do not add production credentials.",
    "Do not execute database operations.",
    "Do not modify Python package runtime behavior unless the task explicitly allows it.",
    "Do not modify .NET source behavior unless the task explicitly allows it.",
)

CommandRunner = Callable[[Sequence[str]], str]


@dataclass(frozen=True)
class Issue:
    number: int
    title: str
    body: str
    labels: tuple[str, ...]
    state: str


@dataclass(frozen=True)
class PullRequest:
    number: int
    title: str
    head_ref_name: str
    body: str
    state: str = "OPEN"
    is_draft: bool = False
    base_ref_name: str = ""
    review_decision: str = ""
    status_check_rollup: tuple[dict[str, object], ...] = ()
    mergeable: str = ""
    merge_state_status: str = ""


@dataclass(frozen=True)
class DependencySummary:
    task_id: str
    issue_number: int | None
    status: str | None
    title: str | None


@dataclass(frozen=True)
class QueueState:
    ready_issues: tuple[Issue, ...]
    in_progress_issues: tuple[Issue, ...]
    all_issues: tuple[Issue, ...]
    open_prs: tuple[PullRequest, ...]
    all_prs: tuple[PullRequest, ...] = ()


@dataclass(frozen=True)
class HandoffPackage:
    selected_issue_number: int
    task_id: str
    issue_title: str
    issue_body: str
    lane: str
    agent_label: str
    dependency_summary: tuple[DependencySummary, ...]
    selected_prompt_template: str
    generated_prompt: str
    expected_branch_name_pattern: str
    expected_pr_title_pattern: str
    required_pr_footer: str
    validation_checklist: tuple[str, ...]
    safety_constraints: tuple[str, ...]
    human_action_needed: str
    artifact_path: Path | None = None


@dataclass(frozen=True)
class ClaimResult:
    issue_number: int
    removed_label: str
    added_label: str
    command: tuple[str, ...]


@dataclass(frozen=True)
class SelectionOutcome:
    package: HandoffPackage | None
    blockers: tuple[str, ...]
    ready_candidates: tuple[Issue, ...]
    task_prs: tuple[PullRequest, ...]
    claim_result: ClaimResult | None = None


class ClaimFailedError(RuntimeError):
    """Raised when explicit claim mode fails after preflight succeeds."""


@dataclass(frozen=True)
class InvocationSupport:
    supported: bool
    message: str
    command: tuple[str, ...] = ()


@dataclass(frozen=True)
class HandoffOutcome:
    package: HandoffPackage | None
    blockers: tuple[str, ...]
    in_progress_candidates: tuple[Issue, ...]
    invocation_support: InvocationSupport
    invoke_requested: bool = False


@dataclass(frozen=True)
class PullRequestFooterEvaluation:
    pull_request: PullRequest
    footer_task_id: str | None
    footer_issue_number: int | None
    footer_errors: tuple[str, ...]
    matches_claimed_task: bool


@dataclass(frozen=True)
class LifecycleOutcome:
    lifecycle_status: str
    claimed_issue: Issue | None
    task_id: str | None
    pr_evaluations: tuple[PullRequestFooterEvaluation, ...]
    matching_prs: tuple[PullRequestFooterEvaluation, ...]
    blockers: tuple[str, ...]
    human_action_needed: str


@dataclass(frozen=True)
class CheckSummary:
    status: str
    summary: str


@dataclass(frozen=True)
class ReviewReadinessOutcome:
    readiness_status: str
    claimed_issue: Issue | None
    task_id: str | None
    pr_evaluations: tuple[PullRequestFooterEvaluation, ...]
    matching_prs: tuple[PullRequestFooterEvaluation, ...]
    check_summary: CheckSummary | None
    blockers: tuple[str, ...]
    human_action_needed: str


def subprocess_runner(command: Sequence[str]) -> str:
    completed = subprocess.run(
        list(command),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def run_json(command: Sequence[str], runner: CommandRunner) -> object:
    output = runner(command)
    return json.loads(output or "null")


def load_queue_state(
    repository: str,
    runner: CommandRunner = subprocess_runner,
    issue_limit: int = 500,
) -> QueueState:
    ready_issues = tuple(
        parse_issues(
            run_json(
                (
                    "gh",
                    "issue",
                    "list",
                    "--repo",
                    repository,
                    "--state",
                    "open",
                    "--label",
                    "status:ready",
                    "--limit",
                    str(issue_limit),
                    "--json",
                    "number,title,body,labels,state",
                ),
                runner,
            )
        )
    )
    in_progress_issues = tuple(
        parse_issues(
            run_json(
                (
                    "gh",
                    "issue",
                    "list",
                    "--repo",
                    repository,
                    "--state",
                    "open",
                    "--label",
                    "status:in-progress",
                    "--limit",
                    str(issue_limit),
                    "--json",
                    "number,title,body,labels,state",
                ),
                runner,
            )
        )
    )
    all_issues = tuple(
        parse_issues(
            run_json(
                (
                    "gh",
                    "issue",
                    "list",
                    "--repo",
                    repository,
                    "--state",
                    "all",
                    "--limit",
                    str(issue_limit),
                    "--json",
                    "number,title,body,labels,state",
                ),
                runner,
            )
        )
    )
    open_prs = tuple(
        parse_pull_requests(
            run_json(
                (
                    "gh",
                    "pr",
                    "list",
                    "--repo",
                    repository,
                    "--state",
                    "open",
                    "--limit",
                    str(issue_limit),
                    "--json",
                    "number,title,headRefName,body,state,isDraft",
                ),
                runner,
            )
        )
    )
    all_prs = tuple(
        parse_pull_requests(
            run_json(
                (
                    "gh",
                    "pr",
                    "list",
                    "--repo",
                    repository,
                    "--state",
                    "all",
                    "--limit",
                    str(issue_limit),
                    "--json",
                    (
                        "number,title,headRefName,baseRefName,body,state,isDraft,"
                        "reviewDecision,statusCheckRollup,mergeable,mergeStateStatus"
                    ),
                ),
                runner,
            )
        )
    )
    return QueueState(
        ready_issues=ready_issues,
        in_progress_issues=in_progress_issues,
        all_issues=all_issues,
        open_prs=open_prs,
        all_prs=all_prs,
    )


def parse_issues(raw_items: object) -> list[Issue]:
    if not isinstance(raw_items, list):
        return []
    return [
        Issue(
            number=int(item.get("number", 0)),
            title=str(item.get("title") or ""),
            body=str(item.get("body") or ""),
            labels=extract_label_names(item.get("labels")),
            state=str(item.get("state") or ""),
        )
        for item in raw_items
        if isinstance(item, dict)
    ]


def parse_pull_requests(raw_items: object) -> list[PullRequest]:
    if not isinstance(raw_items, list):
        return []
    return [
        PullRequest(
            number=int(item.get("number", 0)),
            title=str(item.get("title") or ""),
            head_ref_name=str(item.get("headRefName") or ""),
            body=str(item.get("body") or ""),
            state=str(item.get("state") or "OPEN"),
            is_draft=bool(item.get("isDraft", False)),
            base_ref_name=str(item.get("baseRefName") or ""),
            review_decision=str(item.get("reviewDecision") or ""),
            status_check_rollup=extract_status_check_rollup(item.get("statusCheckRollup")),
            mergeable=str(item.get("mergeable") or ""),
            merge_state_status=str(item.get("mergeStateStatus") or ""),
        )
        for item in raw_items
        if isinstance(item, dict)
    ]


def extract_status_check_rollup(raw_items: object) -> tuple[dict[str, object], ...]:
    if not isinstance(raw_items, list):
        return ()
    return tuple(dict(item) for item in raw_items if isinstance(item, dict))


def extract_label_names(raw_labels: object) -> tuple[str, ...]:
    if not isinstance(raw_labels, list):
        return ()

    labels: list[str] = []
    for label in raw_labels:
        if isinstance(label, dict):
            name = label.get("name")
            if isinstance(name, str):
                labels.append(name)
        elif isinstance(label, str):
            labels.append(label)
    return tuple(labels)


def parse_task_id(body: str) -> str | None:
    match = TASK_ID_PATTERN.search(body or "")
    if not match:
        return None
    return match.group(1).upper()


def parse_task_issue_number(body: str) -> int | None:
    match = TASK_ISSUE_PATTERN.search(body or "")
    if not match:
        return None
    return int(match.group(1))


def parse_field(body: str, field: str) -> str:
    pattern = re.compile(
        FIELD_PATTERN_TEMPLATE.format(field=re.escape(field)),
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(body or "")
    return match.group(1).strip() if match else ""


def parse_task_list(body: str, field: str) -> tuple[str, ...]:
    value = parse_field(body, field)
    if not value:
        return ()
    return tuple(match.group(0).upper() for match in TASK_REFERENCE_PATTERN.finditer(value))


def status_label(issue: Issue) -> str | None:
    statuses = sorted(label.removeprefix("status:") for label in issue.labels if label.startswith("status:"))
    if len(statuses) == 1:
        return statuses[0]
    return None


def lane_label(issue: Issue) -> str | None:
    lanes = sorted(label.removeprefix("lane:") for label in issue.labels if label.startswith("lane:"))
    if len(lanes) == 1:
        return lanes[0]
    return None


def agent_label(issue: Issue) -> str | None:
    agents = sorted(label for label in issue.labels if label.startswith("agent:"))
    if len(agents) == 1:
        return agents[0]
    return None


def is_task_pr(pull_request: PullRequest) -> bool:
    searchable = "\n".join(
        (pull_request.body, pull_request.title, pull_request.head_ref_name)
    )
    return bool(
        parse_task_id(pull_request.body)
        or TASK_ISSUE_PATTERN.search(pull_request.body)
        or TASK_REFERENCE_PATTERN.search(searchable)
    )


def select_handoff_package(
    state: QueueState,
    repository: str = DEFAULT_REPOSITORY,
) -> SelectionOutcome:
    blockers: list[str] = []
    task_prs = tuple(pr for pr in state.open_prs if is_task_pr(pr))
    if task_prs:
        blockers.append(
            "Open task PR blocks dispatch: "
            + ", ".join(f"#{pr.number} {pr.title}" for pr in task_prs)
        )

    if state.in_progress_issues:
        blockers.append(
            "status:in-progress issue blocks dispatch: "
            + ", ".join(f"#{issue.number} {issue.title}" for issue in state.in_progress_issues)
        )

    ready_candidates = tuple(
        sorted(
            (issue for issue in state.ready_issues if status_label(issue) == "ready"),
            key=issue_sort_key,
        )
    )
    if not ready_candidates:
        blockers.append("No status:ready issue is available.")

    task_index, duplicate_task_ids = build_task_index(state.all_issues)
    if duplicate_task_ids:
        blockers.append(
            "Dependency graph inconsistency: duplicate Task-ID entries: "
            + ", ".join(sorted(duplicate_task_ids))
        )

    if blockers:
        return SelectionOutcome(
            package=None,
            blockers=tuple(blockers),
            ready_candidates=ready_candidates,
            task_prs=task_prs,
        )

    selected_issue = ready_candidates[0]
    selected_blockers = validate_selected_issue(selected_issue, task_index)
    if selected_blockers:
        return SelectionOutcome(
            package=None,
            blockers=tuple(selected_blockers),
            ready_candidates=ready_candidates,
            task_prs=task_prs,
        )

    package = build_handoff_package(selected_issue, task_index, repository=repository)
    return SelectionOutcome(
        package=package,
        blockers=(),
        ready_candidates=ready_candidates,
        task_prs=task_prs,
    )


def issue_sort_key(issue: Issue) -> tuple[int, int]:
    lane = lane_label(issue)
    try:
        lane_rank = LANE_PRIORITY.index(lane or "")
    except ValueError:
        lane_rank = len(LANE_PRIORITY)
    return (lane_rank, issue.number)


def build_task_index(issues: Sequence[Issue]) -> tuple[dict[str, Issue], set[str]]:
    task_index: dict[str, Issue] = {}
    duplicates: set[str] = set()
    for issue in issues:
        task_id = parse_task_id(issue.body)
        if not task_id:
            continue
        if task_id in task_index:
            duplicates.add(task_id)
        else:
            task_index[task_id] = issue
    return task_index, duplicates


def validate_selected_issue(
    issue: Issue,
    task_index: dict[str, Issue],
) -> tuple[str, ...]:
    blockers: list[str] = []
    task_id = parse_task_id(issue.body)
    lane = lane_label(issue)

    if not task_id:
        blockers.append(f"Selected issue #{issue.number} has no valid Task-ID.")
    if lane not in LANE_PRIORITY:
        blockers.append(f"Selected issue #{issue.number} has no supported lane label.")
    if not agent_label(issue):
        blockers.append(f"Selected issue #{issue.number} has no single agent label.")

    template = select_prompt_template(issue)
    if template is None:
        blockers.append(f"Selected task lane has no known prompt template: {lane or 'missing'}.")

    dependencies = parse_task_list(issue.body, "Depends on")
    if lane in {"parity", "review"} and not dependencies:
        blockers.append(
            f"Selected {lane} task #{issue.number} has no implementation dependencies declared."
        )

    for dependency_id in dependencies:
        dependency_issue = task_index.get(dependency_id)
        if dependency_issue is None:
            blockers.append(f"Dependency issue not found for {dependency_id}.")
            continue
        dependency_status = status_label(dependency_issue)
        if dependency_status != "merged":
            blockers.append(
                f"Dependency {dependency_id} is status:{dependency_status or 'missing'}, not status:merged."
            )

    return tuple(blockers)


def select_prompt_template(issue: Issue) -> str | None:
    lane = lane_label(issue)
    text = f"{issue.title}\n{issue.body}".lower()

    if lane == "ops":
        return "ops workflow/automation"
    if lane == "python":
        if "download" in text:
            return "python source download execution"
        return "python source discovery boundary"
    if lane == "dotnet":
        if any(word in text for word in ("repository", "contract", "persistence")):
            return "dotnet repository contract"
        return "dotnet source discovery boundary"
    if lane == "parity":
        return "parity review"
    if lane == "review" and "parity" in text:
        return "parity review"
    return None


def build_handoff_package(
    issue: Issue,
    task_index: dict[str, Issue],
    repository: str = DEFAULT_REPOSITORY,
) -> HandoffPackage:
    task_id = require_value(parse_task_id(issue.body), "Task-ID")
    lane = require_value(lane_label(issue), "lane")
    agent = require_value(agent_label(issue), "agent label")
    template = require_value(select_prompt_template(issue), "prompt template")
    dependency_summary = tuple(
        summarize_dependency(task_id, task_index)
        for task_id in parse_task_list(issue.body, "Depends on")
    )
    branch_name = expected_branch_name(task_id, issue.title)
    pr_title = expected_pr_title(task_id, issue.title)
    footer = f"Task-ID: {task_id}\nTask-Issue: #{issue.number}"
    prompt = generate_prompt(
        repository=repository,
        issue=issue,
        task_id=task_id,
        lane=lane,
        agent=agent,
        template=template,
        branch_name=branch_name,
        pr_title=pr_title,
        footer=footer,
    )
    return HandoffPackage(
        selected_issue_number=issue.number,
        task_id=task_id,
        issue_title=issue.title,
        issue_body=issue.body,
        lane=lane,
        agent_label=agent,
        dependency_summary=dependency_summary,
        selected_prompt_template=template,
        generated_prompt=prompt,
        expected_branch_name_pattern=branch_name,
        expected_pr_title_pattern=pr_title,
        required_pr_footer=footer,
        validation_checklist=VALIDATION_CHECKLIST,
        safety_constraints=SAFETY_CONSTRAINTS,
        human_action_needed=(
            "Review this handoff report, then start the appropriate local Codex lane task manually."
        ),
    )


def build_handoff_package_for_issue(
    issue: Issue,
    all_issues: Sequence[Issue],
    repository: str = DEFAULT_REPOSITORY,
) -> tuple[HandoffPackage | None, tuple[str, ...]]:
    task_index, duplicate_task_ids = build_task_index(all_issues)
    blockers: list[str] = []
    if duplicate_task_ids:
        blockers.append(
            "Dependency graph inconsistency: duplicate Task-ID entries: "
            + ", ".join(sorted(duplicate_task_ids))
        )
    blockers.extend(validate_selected_issue(issue, task_index))
    if blockers:
        return None, tuple(blockers)
    return build_handoff_package(issue, task_index, repository=repository), ()


def require_value(value: str | None, name: str) -> str:
    if not value:
        raise ValueError(f"Missing {name}")
    return value


def summarize_dependency(task_id: str, task_index: dict[str, Issue]) -> DependencySummary:
    issue = task_index.get(task_id)
    if issue is None:
        return DependencySummary(task_id=task_id, issue_number=None, status=None, title=None)
    return DependencySummary(
        task_id=task_id,
        issue_number=issue.number,
        status=status_label(issue),
        title=issue.title,
    )


def expected_branch_name(task_id: str, title: str) -> str:
    title_without_task = re.sub(r"^\[[^\]]+\]\s*", "", title).strip()
    slug = slugify(title_without_task)
    return f"feature/{task_id.lower()}-{slug}" if slug else f"feature/{task_id.lower()}"


def expected_pr_title(task_id: str, title: str) -> str:
    title_without_task = re.sub(r"^\[[^\]]+\]\s*", "", title).strip()
    return f"{task_id}: {title_without_task or title}"


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-+", "-", slug)


def generate_prompt(
    repository: str,
    issue: Issue,
    task_id: str,
    lane: str,
    agent: str,
    template: str,
    branch_name: str,
    pr_title: str,
    footer: str,
) -> str:
    scope = parse_field(issue.body, "Scope") or "Use the selected issue body as the scope."
    non_goals = extract_section(issue.body, "Non-goals")
    allowed_files = extract_section(issue.body, "Allowed files")

    return "\n".join(
        (
            f"# Codex Handoff Prompt: {task_id}",
            "",
            f"Repository: {repository}",
            f"Base branch: {BASE_BRANCH}",
            f"Issue: #{issue.number}",
            f"Task-ID: {task_id}",
            f"Lane: {lane}",
            f"Agent label: {agent}",
            f"Prompt template category: {template}",
            "",
            "## Issue Title",
            issue.title,
            "",
            "## Issue Body Context",
            issue.body.strip(),
            "",
            "## Scope",
            scope,
            "",
            "## Non-Goals",
            non_goals or "- Follow the non-goals in the issue body.",
            "",
            "## Allowed Files Guidance",
            allowed_files or "- Modify only files explicitly allowed by the task.",
            "",
            "## Expected Branch And PR",
            f"- Branch pattern: `{branch_name}`",
            f"- PR title pattern: `{pr_title}`",
            "",
            "## Validation Requirements",
            bullet_list(VALIDATION_CHECKLIST),
            "",
            "## Safety Constraints",
            bullet_list(SAFETY_CONSTRAINTS),
            "",
            "## PR Footer Requirement",
            "The PR body must end exactly with:",
            "",
            "```text",
            footer,
            "```",
            "",
            "## PR Fallback Report Requirement",
            "If the PR cannot be created, report exactly:",
            "- Branch name",
            "- Base branch",
            "- Commit hash",
            "- Whether the branch was pushed to origin",
            "- Exact PR title",
            "- Exact PR body",
            "- Files changed",
            "- Validation performed",
            "- Any GitHub/API error message observed",
            "",
            "## Final Report Requirement",
            "Return summary, branch, files changed, validation performed, read-only, "
            "claim-mode, or invocation safety confirmation, remaining risks, PR URL if "
            "available, and a merge-ready or commit-ready verdict.",
        )
    )


def extract_section(body: str, heading: str) -> str:
    pattern = re.compile(
        rf"^{re.escape(heading)}:\s*(.*?)(?=^\S[^:\n]*:\s*|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body or "")
    return match.group(1).strip() if match else ""


def bullet_list(items: Sequence[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def build_report(outcome: SelectionOutcome) -> str:
    if outcome.claim_result is None:
        safety_line = (
            "Read-only safety: no Codex invocation, GitHub mutation, PR approval, "
            "PR merge, branch deletion, or worktree deletion was performed."
        )
    else:
        safety_line = (
            "Claim-mode safety: exactly one issue label mutation was performed; no Codex "
            "invocation, PR approval, PR merge, issue close, branch deletion, or worktree "
            "deletion was performed."
        )

    lines: list[str] = [
        "# Agent Dispatch Handoff Report",
        "",
        safety_line,
        "",
    ]

    if outcome.blockers:
        lines.extend(("## Dispatch Status", "blocked", "", "## Blockers"))
        lines.extend(f"- {blocker}" for blocker in outcome.blockers)
        lines.append("")
        append_ready_candidates(lines, outcome.ready_candidates)
        return "\n".join(lines).rstrip() + "\n"

    package = require_package(outcome.package)
    lines.extend(
        (
            "## Dispatch Status",
            "claimed" if outcome.claim_result is not None else "ready",
            "",
            "## Selected Task",
            f"- Selected issue number: #{package.selected_issue_number}",
            f"- Task-ID: {package.task_id}",
            f"- Issue title: {package.issue_title}",
            f"- Lane: {package.lane}",
            f"- Agent label: {package.agent_label}",
            f"- Selected prompt template category: {package.selected_prompt_template}",
            f"- Expected branch name pattern: `{package.expected_branch_name_pattern}`",
            f"- Expected PR title pattern: `{package.expected_pr_title_pattern}`",
            "",
            "## Dependency Summary",
        )
    )
    if package.dependency_summary:
        lines.extend(
            (
                f"- {dependency.task_id}: issue #{dependency.issue_number}, "
                f"status:{dependency.status}, {dependency.title}"
            )
            for dependency in package.dependency_summary
        )
    else:
        lines.append("- No dependencies declared.")

    lines.extend(
        (
            "",
            "## Required PR Footer",
            "```text",
            package.required_pr_footer,
            "```",
            "",
            "## Generated Prompt",
        )
    )

    if package.artifact_path is not None:
        lines.append(f"Prompt artifact: `{package.artifact_path.as_posix()}`")
    else:
        lines.extend(("```text", package.generated_prompt, "```"))

    lines.extend(
        (
            "",
            "## Validation Checklist",
            bullet_list(package.validation_checklist),
            "",
            "## Safety Constraints",
            bullet_list(package.safety_constraints),
            "",
            "## Human Action Needed",
            package.human_action_needed,
            "",
        )
    )
    if outcome.claim_result is not None:
        lines.extend(
            (
                "## Label Mutation Performed",
                f"- Selected issue: #{outcome.claim_result.issue_number}",
                f"- Removed label: `{outcome.claim_result.removed_label}`",
                f"- Added label: `{outcome.claim_result.added_label}`",
                "- Lane, agent, and type labels were left unchanged.",
                "",
            )
        )
    append_ready_candidates(lines, outcome.ready_candidates)
    return "\n".join(lines).rstrip() + "\n"


def build_handoff_report(outcome: HandoffOutcome) -> str:
    lines: list[str] = [
        "# Local Codex Handoff Report",
        "",
        "Invocation safety: no Codex invocation, GitHub mutation, PR approval, PR merge, "
        "issue close, branch deletion, or worktree deletion was performed.",
        "",
    ]

    if outcome.blockers:
        lines.extend(("## Handoff Status", "blocked", "", "## Blockers"))
        lines.extend(f"- {blocker}" for blocker in outcome.blockers)
        lines.append("")
        if outcome.package is not None:
            append_handoff_task_details(lines, outcome.package)
            lines.extend(
                (
                    "",
                    "## Invocation Support",
                    f"- Live invocation supported: {'yes' if outcome.invocation_support.supported else 'no'}",
                    f"- {outcome.invocation_support.message}",
                    "",
                    "## Recommended Human Action",
                    "- Open the prompt artifact.",
                    "- Start the correct local Codex lane task manually.",
                    "- Use the prompt artifact content as the task prompt.",
                    "",
                )
            )
        append_in_progress_candidates(lines, outcome.in_progress_candidates)
        return "\n".join(lines).rstrip() + "\n"

    package = require_package(outcome.package)
    prompt_summary = first_nonempty_line(package.generated_prompt)
    lines.extend(
        (
            "## Handoff Status",
            "ready-for-manual-handoff",
            "",
        )
    )
    append_handoff_task_details(lines, package)
    lines.extend(
        (
            f"- Generated prompt summary: {prompt_summary}",
            "",
            "## Invocation Support",
            f"- Live invocation supported: {'yes' if outcome.invocation_support.supported else 'no'}",
            f"- {outcome.invocation_support.message}",
        )
    )
    if outcome.invocation_support.command:
        lines.append(
            "- Proposed local Codex command: `"
            + " ".join(outcome.invocation_support.command)
            + "`"
        )
    lines.extend(
        (
            "",
            "## Recommended Human Action",
            "- Open the prompt artifact.",
            "- Start the correct local Codex lane task manually.",
            "- Use the prompt artifact content as the task prompt.",
            "- Do not merge, approve, close issues, delete branches, or delete worktrees from this handoff.",
            "",
            "## Manual Handoff Steps",
            f"1. Review `{artifact_path_text(package)}`.",
            f"2. Start the local Codex session for `{package.agent_label}`.",
            "3. Paste or attach the generated prompt artifact.",
            "4. Let the agent create the implementation PR through the normal review flow.",
            "",
            "## Safety Statement",
            "local Codex invocation unsupported; use generated prompt artifact manually.",
            "",
        )
    )
    append_in_progress_candidates(lines, outcome.in_progress_candidates)
    return "\n".join(lines).rstrip() + "\n"


def append_handoff_task_details(lines: list[str], package: HandoffPackage) -> None:
    lines.extend(
        (
            "## Claimed Task",
            f"- Selected issue number: #{package.selected_issue_number}",
            f"- Task-ID: {package.task_id}",
            f"- Issue title: {package.issue_title}",
            f"- Lane: {package.lane}",
            f"- Agent label: {package.agent_label}",
            f"- Prompt artifact path: `{artifact_path_text(package)}`",
        )
    )


def append_ready_candidates(lines: list[str], ready_candidates: Sequence[Issue]) -> None:
    lines.extend(("## Ready Candidates",))
    if ready_candidates:
        for issue in ready_candidates:
            task_id = parse_task_id(issue.body) or "missing-task-id"
            lane = lane_label(issue) or "missing-lane"
            lines.append(f"- #{issue.number} {task_id} lane:{lane} {issue.title}")
    else:
        lines.append("- None.")
    lines.append("")


def append_in_progress_candidates(lines: list[str], candidates: Sequence[Issue]) -> None:
    lines.extend(("## In-Progress Candidates",))
    if candidates:
        for issue in candidates:
            task_id = parse_task_id(issue.body) or "missing-task-id"
            lane = lane_label(issue) or "missing-lane"
            lines.append(f"- #{issue.number} {task_id} lane:{lane} {issue.title}")
    else:
        lines.append("- None.")
    lines.append("")


def first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return "Generated prompt artifact."


def artifact_path_text(package: HandoffPackage) -> str:
    if package.artifact_path is None:
        return ".agent-handoff/<missing-prompt-artifact>"
    return package.artifact_path.as_posix()


def require_package(package: HandoffPackage | None) -> HandoffPackage:
    if package is None:
        raise ValueError("Missing handoff package")
    return package


def write_prompt_artifact(package: HandoffPackage, artifact_dir: Path) -> HandoffPackage:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / f"{package.task_id}-{package.selected_issue_number}-prompt.md"
    artifact_path.write_text(package.generated_prompt + "\n", encoding="utf-8")
    return HandoffPackage(
        selected_issue_number=package.selected_issue_number,
        task_id=package.task_id,
        issue_title=package.issue_title,
        issue_body=package.issue_body,
        lane=package.lane,
        agent_label=package.agent_label,
        dependency_summary=package.dependency_summary,
        selected_prompt_template=package.selected_prompt_template,
        generated_prompt=package.generated_prompt,
        expected_branch_name_pattern=package.expected_branch_name_pattern,
        expected_pr_title_pattern=package.expected_pr_title_pattern,
        required_pr_footer=package.required_pr_footer,
        validation_checklist=package.validation_checklist,
        safety_constraints=package.safety_constraints,
        human_action_needed=package.human_action_needed,
        artifact_path=artifact_path,
    )


def locate_or_generate_prompt_artifact(
    package: HandoffPackage,
    artifact_dir: Path,
) -> HandoffPackage:
    artifact_path = artifact_dir / f"{package.task_id}-{package.selected_issue_number}-prompt.md"
    if artifact_path.exists():
        return HandoffPackage(
            selected_issue_number=package.selected_issue_number,
            task_id=package.task_id,
            issue_title=package.issue_title,
            issue_body=package.issue_body,
            lane=package.lane,
            agent_label=package.agent_label,
            dependency_summary=package.dependency_summary,
            selected_prompt_template=package.selected_prompt_template,
            generated_prompt=package.generated_prompt,
            expected_branch_name_pattern=package.expected_branch_name_pattern,
            expected_pr_title_pattern=package.expected_pr_title_pattern,
            required_pr_footer=package.required_pr_footer,
            validation_checklist=package.validation_checklist,
            safety_constraints=package.safety_constraints,
            human_action_needed=package.human_action_needed,
            artifact_path=artifact_path,
        )
    return write_prompt_artifact(package, artifact_dir)


def detect_invocation_support() -> InvocationSupport:
    return InvocationSupport(
        supported=False,
        message="local Codex invocation unsupported; use generated prompt artifact manually.",
    )


def select_handoff_issue(
    state: QueueState,
    issue_number: int | None = None,
) -> tuple[Issue | None, tuple[str, ...], tuple[Issue, ...]]:
    candidates = tuple(
        sorted(
            (issue for issue in state.in_progress_issues if status_label(issue) == "in-progress"),
            key=issue_sort_key,
        )
    )

    if not candidates:
        return None, ("No status:in-progress issue is available for handoff.",), candidates
    if len(candidates) > 1:
        return (
            None,
            (
                "Multiple status:in-progress issues exist; handoff requires exactly one claimed issue.",
            ),
            candidates,
        )

    selected = candidates[0]
    if issue_number is not None and selected.number != issue_number:
        return (
            None,
            (
                f"Explicit issue #{issue_number} does not match the single claimed "
                f"status:in-progress issue #{selected.number}.",
            ),
            candidates,
        )
    return selected, (), candidates


def build_local_handoff_outcome(
    state: QueueState,
    repository: str,
    artifact_dir: Path,
    issue_number: int | None = None,
    invoke_requested: bool = False,
) -> HandoffOutcome:
    selected_issue, blockers, candidates = select_handoff_issue(state, issue_number=issue_number)
    invocation_support = detect_invocation_support()
    if blockers:
        return HandoffOutcome(
            package=None,
            blockers=blockers,
            in_progress_candidates=candidates,
            invocation_support=invocation_support,
            invoke_requested=invoke_requested,
        )

    package, package_blockers = build_handoff_package_for_issue(
        require_issue(selected_issue),
        state.all_issues,
        repository=repository,
    )
    if package_blockers:
        return HandoffOutcome(
            package=None,
            blockers=package_blockers,
            in_progress_candidates=candidates,
            invocation_support=invocation_support,
            invoke_requested=invoke_requested,
        )

    if invoke_requested and not invocation_support.supported:
        return HandoffOutcome(
            package=None,
            blockers=(invocation_support.message,),
            in_progress_candidates=candidates,
            invocation_support=invocation_support,
            invoke_requested=invoke_requested,
        )

    package = locate_or_generate_prompt_artifact(require_package(package), artifact_dir)

    return HandoffOutcome(
        package=package,
        blockers=(),
        in_progress_candidates=candidates,
        invocation_support=invocation_support,
        invoke_requested=invoke_requested,
    )


def build_lifecycle_outcome(state: QueueState) -> LifecycleOutcome:
    claimed_issues = tuple(
        sorted(
            (issue for issue in state.in_progress_issues if status_label(issue) == "in-progress"),
            key=issue_sort_key,
        )
    )
    if not claimed_issues:
        return LifecycleOutcome(
            lifecycle_status="blocked_no_claimed_task",
            claimed_issue=None,
            task_id=None,
            pr_evaluations=(),
            matching_prs=(),
            blockers=("No status:in-progress issue exists.",),
            human_action_needed="Claim one ready task before expecting a task PR.",
        )
    if len(claimed_issues) > 1:
        return LifecycleOutcome(
            lifecycle_status="blocked_multiple_claimed_tasks",
            claimed_issue=None,
            task_id=None,
            pr_evaluations=(),
            matching_prs=(),
            blockers=(
                "Multiple status:in-progress issues exist; lifecycle monitoring requires exactly one claimed task.",
            ),
            human_action_needed="Resolve the queue so exactly one task is status:in-progress.",
        )

    claimed_issue = claimed_issues[0]
    task_id = parse_task_id(claimed_issue.body)
    if task_id is None:
        return LifecycleOutcome(
            lifecycle_status="pr_footer_invalid",
            claimed_issue=claimed_issue,
            task_id=None,
            pr_evaluations=(),
            matching_prs=(),
            blockers=(f"Claimed issue #{claimed_issue.number} has no valid Task-ID.",),
            human_action_needed="Fix the claimed issue metadata before matching PR lifecycle state.",
        )

    evaluations = tuple(
        evaluate_pr_footer(pull_request, task_id=task_id, issue_number=claimed_issue.number)
        for pull_request in sorted(state.open_prs, key=lambda pr: pr.number)
        if pr_is_candidate_for_claimed_task(
            pull_request,
            task_id=task_id,
            issue_number=claimed_issue.number,
        )
    )
    valid_matches = tuple(
        evaluation
        for evaluation in evaluations
        if evaluation.matches_claimed_task and not evaluation.footer_errors
    )
    invalid_candidates = tuple(evaluation for evaluation in evaluations if evaluation.footer_errors)

    if not evaluations:
        return LifecycleOutcome(
            lifecycle_status="waiting_for_pr",
            claimed_issue=claimed_issue,
            task_id=task_id,
            pr_evaluations=(),
            matching_prs=(),
            blockers=(),
            human_action_needed="Wait for the claimed task agent to open a PR with the required footer.",
        )
    if len(valid_matches) > 1:
        return LifecycleOutcome(
            lifecycle_status="pr_match_ambiguous",
            claimed_issue=claimed_issue,
            task_id=task_id,
            pr_evaluations=evaluations,
            matching_prs=valid_matches,
            blockers=("Multiple open PRs match the claimed task footer.",),
            human_action_needed="Ask a human to resolve the duplicate PRs before continuing review.",
        )
    if not valid_matches:
        return LifecycleOutcome(
            lifecycle_status="pr_footer_invalid",
            claimed_issue=claimed_issue,
            task_id=task_id,
            pr_evaluations=invalid_candidates,
            matching_prs=(),
            blockers=("Open PR candidate exists, but its required task footer is invalid.",),
            human_action_needed="Fix the PR body footer so it ends with the claimed Task-ID and Task-Issue.",
        )

    matched = valid_matches[0]
    if matched.pull_request.is_draft:
        return LifecycleOutcome(
            lifecycle_status="pr_draft_waiting",
            claimed_issue=claimed_issue,
            task_id=task_id,
            pr_evaluations=evaluations,
            matching_prs=valid_matches,
            blockers=(),
            human_action_needed="Wait for the task PR to be marked ready for review.",
        )

    return LifecycleOutcome(
        lifecycle_status="ready_for_human_review",
        claimed_issue=claimed_issue,
        task_id=task_id,
        pr_evaluations=evaluations,
        matching_prs=valid_matches,
        blockers=(),
        human_action_needed="Human reviewer should review the open non-draft task PR.",
    )


def pr_is_candidate_for_claimed_task(
    pull_request: PullRequest,
    task_id: str,
    issue_number: int,
) -> bool:
    footer_task_id = parse_task_id(pull_request.body)
    footer_issue_number = parse_task_issue_number(pull_request.body)
    if footer_task_id == task_id or footer_issue_number == issue_number:
        return True

    searchable = "\n".join((pull_request.title, pull_request.head_ref_name, pull_request.body))
    return task_id.lower() in searchable.lower() or f"#{issue_number}" in searchable


def evaluate_pr_footer(
    pull_request: PullRequest,
    task_id: str,
    issue_number: int,
) -> PullRequestFooterEvaluation:
    footer_task_id = parse_task_id(pull_request.body)
    footer_issue_number = parse_task_issue_number(pull_request.body)
    errors: list[str] = []

    if footer_task_id is None:
        errors.append("missing Task-ID footer")
    elif footer_task_id != task_id:
        errors.append(f"Task-ID footer mismatch: expected {task_id}, found {footer_task_id}")

    if footer_issue_number is None:
        errors.append("missing Task-Issue footer")
    elif footer_issue_number != issue_number:
        errors.append(
            f"Task-Issue footer mismatch: expected #{issue_number}, found #{footer_issue_number}"
        )

    expected_footer = f"Task-ID: {task_id}\nTask-Issue: #{issue_number}"
    if footer_task_id == task_id and footer_issue_number == issue_number:
        if not pull_request.body.strip().endswith(expected_footer):
            errors.append("required PR footer is not the final body content")

    return PullRequestFooterEvaluation(
        pull_request=pull_request,
        footer_task_id=footer_task_id,
        footer_issue_number=footer_issue_number,
        footer_errors=tuple(errors),
        matches_claimed_task=footer_task_id == task_id and footer_issue_number == issue_number,
    )


def build_lifecycle_report(outcome: LifecycleOutcome) -> str:
    lines: list[str] = [
        "# In-Progress Task PR Lifecycle Report",
        "",
        "Lifecycle safety: read-only mode; no GitHub mutation, PR approval, PR merge, "
        "issue or PR comment, issue or PR close, branch deletion, worktree deletion, "
        "Codex invocation, or agent start was performed.",
        "",
        "## Lifecycle Status",
        outcome.lifecycle_status,
        "",
    ]

    if outcome.blockers:
        lines.extend(("## Blockers",))
        lines.extend(f"- {blocker}" for blocker in outcome.blockers)
        lines.append("")

    if outcome.claimed_issue is not None:
        task_id = outcome.task_id or "missing-task-id"
        lines.extend(
            (
                "## Claimed Task",
                f"- Claimed issue number: #{outcome.claimed_issue.number}",
                f"- Task-ID: {task_id}",
                f"- Issue title: {outcome.claimed_issue.title}",
                "",
            )
        )
    else:
        lines.extend(("## Claimed Task", "- None.", ""))

    if outcome.matching_prs:
        matched = outcome.matching_prs[0]
        append_pr_details(lines, matched, heading="## Matching PR")
    elif outcome.pr_evaluations:
        lines.extend(("## Matching PR", "- None with a valid claimed-task footer.", ""))
    else:
        lines.extend(("## Matching PR", "- None.", ""))

    lines.extend(("## Footer Validation",))
    if outcome.pr_evaluations:
        for evaluation in outcome.pr_evaluations:
            result = "valid" if not evaluation.footer_errors else "invalid"
            lines.append(f"- PR #{evaluation.pull_request.number}: {result}")
            lines.append(f"  Task-ID footer: {evaluation.footer_task_id or 'missing'}")
            issue_text = (
                f"#{evaluation.footer_issue_number}"
                if evaluation.footer_issue_number is not None
                else "missing"
            )
            lines.append(f"  Task-Issue footer: {issue_text}")
            if evaluation.footer_errors:
                lines.extend(f"  Error: {error}" for error in evaluation.footer_errors)
    else:
        lines.append("- No candidate PR footer to validate.")

    lines.extend(
        (
            "",
            "## Human Action Needed",
            outcome.human_action_needed,
            "",
        )
    )
    return "\n".join(lines).rstrip() + "\n"


def build_review_readiness_outcome(state: QueueState) -> ReviewReadinessOutcome:
    claimed_issues = tuple(
        sorted(
            (issue for issue in state.in_progress_issues if status_label(issue) == "in-progress"),
            key=issue_sort_key,
        )
    )
    if not claimed_issues:
        return ReviewReadinessOutcome(
            readiness_status="blocked_no_claimed_task",
            claimed_issue=None,
            task_id=None,
            pr_evaluations=(),
            matching_prs=(),
            check_summary=None,
            blockers=("No status:in-progress issue exists.",),
            human_action_needed="Claim one ready task before checking PR review readiness.",
        )
    if len(claimed_issues) > 1:
        return ReviewReadinessOutcome(
            readiness_status="blocked_multiple_claimed_tasks",
            claimed_issue=None,
            task_id=None,
            pr_evaluations=(),
            matching_prs=(),
            check_summary=None,
            blockers=(
                "Multiple status:in-progress issues exist; review readiness requires exactly one claimed task.",
            ),
            human_action_needed="Resolve the queue so exactly one task is status:in-progress.",
        )

    claimed_issue = claimed_issues[0]
    task_id = parse_task_id(claimed_issue.body)
    if task_id is None:
        return ReviewReadinessOutcome(
            readiness_status="pr_footer_invalid",
            claimed_issue=claimed_issue,
            task_id=None,
            pr_evaluations=(),
            matching_prs=(),
            check_summary=None,
            blockers=(f"Claimed issue #{claimed_issue.number} has no valid Task-ID.",),
            human_action_needed="Fix the claimed issue metadata before checking PR review readiness.",
        )

    pr_pool = state.all_prs or state.open_prs
    evaluations = tuple(
        evaluate_pr_footer(pull_request, task_id=task_id, issue_number=claimed_issue.number)
        for pull_request in sorted(pr_pool, key=lambda pr: pr.number)
        if pr_is_candidate_for_claimed_task(
            pull_request,
            task_id=task_id,
            issue_number=claimed_issue.number,
        )
    )
    valid_matches = tuple(
        evaluation
        for evaluation in evaluations
        if evaluation.matches_claimed_task and not evaluation.footer_errors
    )
    invalid_candidates = tuple(evaluation for evaluation in evaluations if evaluation.footer_errors)

    if not evaluations:
        return ReviewReadinessOutcome(
            readiness_status="waiting_for_pr",
            claimed_issue=claimed_issue,
            task_id=task_id,
            pr_evaluations=(),
            matching_prs=(),
            check_summary=None,
            blockers=(),
            human_action_needed="Wait for the claimed task agent to open a PR with the required footer.",
        )
    if len(valid_matches) > 1:
        return ReviewReadinessOutcome(
            readiness_status="blocked_ambiguous_pr_match",
            claimed_issue=claimed_issue,
            task_id=task_id,
            pr_evaluations=evaluations,
            matching_prs=valid_matches,
            check_summary=None,
            blockers=("Multiple PRs match the claimed task footer.",),
            human_action_needed="Ask a human to resolve the duplicate matching PRs before review or merge.",
        )
    if not valid_matches:
        return ReviewReadinessOutcome(
            readiness_status="pr_footer_invalid",
            claimed_issue=claimed_issue,
            task_id=task_id,
            pr_evaluations=invalid_candidates,
            matching_prs=(),
            check_summary=None,
            blockers=("PR candidate exists, but its required task footer is invalid.",),
            human_action_needed="Fix the PR body footer so it ends with the claimed Task-ID and Task-Issue.",
        )

    match = valid_matches[0]
    pull_request = match.pull_request
    check_summary = summarize_status_checks(pull_request)
    readiness_status, blockers, action = determine_review_readiness_status(
        pull_request,
        check_summary,
    )
    return ReviewReadinessOutcome(
        readiness_status=readiness_status,
        claimed_issue=claimed_issue,
        task_id=task_id,
        pr_evaluations=evaluations,
        matching_prs=valid_matches,
        check_summary=check_summary,
        blockers=blockers,
        human_action_needed=action,
    )


def summarize_status_checks(pull_request: PullRequest) -> CheckSummary:
    if not pull_request.status_check_rollup:
        return CheckSummary(
            status="unknown",
            summary="statusCheckRollup unavailable or empty.",
        )

    pending: list[str] = []
    failed: list[str] = []
    passed: list[str] = []
    for item in pull_request.status_check_rollup:
        name = str(item.get("name") or item.get("workflowName") or "unnamed check")
        status = str(item.get("status") or "").upper()
        conclusion = str(item.get("conclusion") or "").upper()
        if status and status != "COMPLETED":
            pending.append(name)
        elif not conclusion:
            pending.append(name)
        elif conclusion in {"FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE"}:
            failed.append(name)
        else:
            passed.append(name)

    if failed:
        return CheckSummary(
            status="failed",
            summary="Failed checks: " + ", ".join(failed),
        )
    if pending:
        return CheckSummary(
            status="pending",
            summary="Pending checks: " + ", ".join(pending),
        )
    return CheckSummary(
        status="passed",
        summary=f"All reported checks passed ({len(passed)}).",
    )


def determine_review_readiness_status(
    pull_request: PullRequest,
    check_summary: CheckSummary,
) -> tuple[str, tuple[str, ...], str]:
    state = pull_request.state.upper()
    review_decision = pull_request.review_decision.upper()

    if state != "OPEN":
        return (
            "waiting_for_pr",
            (f"Matching PR is {state or 'not open'}, not OPEN.",),
            "Wait for or open an active task PR before review readiness can proceed.",
        )
    if pull_request.is_draft:
        return (
            "pr_draft_waiting",
            (),
            "Wait for the task PR to be marked ready for review.",
        )
    if check_summary.status == "pending":
        return (
            "checks_pending",
            (),
            "Wait for required checks to finish before review or merge decisions.",
        )
    if check_summary.status == "failed":
        return (
            "checks_failed",
            (),
            "Ask the task author to fix failing checks before human review or merge.",
        )
    if review_decision == "CHANGES_REQUESTED":
        return (
            "changes_requested",
            (),
            "Ask the task author to address requested changes.",
        )
    if review_decision == "REVIEW_REQUIRED":
        return (
            "review_required",
            (),
            "A human reviewer should review the PR.",
        )
    if review_decision == "APPROVED":
        if check_summary.status == "passed" and has_clean_merge_metadata(pull_request):
            return (
                "ready_for_human_merge",
                (),
                "Human may review final context and decide whether to merge.",
            )
        return (
            "ready_for_human_review",
            (),
            "Human should review mergeability details before deciding whether to merge.",
        )

    return (
        "ready_for_human_review",
        (),
        "Human reviewer should inspect the PR; review decision metadata is not approved yet.",
    )


def has_clean_merge_metadata(pull_request: PullRequest) -> bool:
    mergeable = pull_request.mergeable.upper()
    merge_state = pull_request.merge_state_status.upper()
    if mergeable and mergeable != "MERGEABLE":
        return False
    if merge_state and merge_state not in {"CLEAN", "HAS_HOOKS"}:
        return False
    return bool(mergeable or merge_state)


def build_review_readiness_report(outcome: ReviewReadinessOutcome) -> str:
    lines: list[str] = [
        "# PR Review Readiness Report",
        "",
        "Review readiness safety: read-only advisory mode; no GitHub mutation, PR approval, "
        "PR merge, issue or PR comment, issue or PR close, branch deletion, worktree deletion, "
        "Codex invocation, or agent start was performed.",
        "",
        "## Readiness Status",
        outcome.readiness_status,
        "",
    ]

    if outcome.blockers:
        lines.extend(("## Blockers",))
        lines.extend(f"- {blocker}" for blocker in outcome.blockers)
        lines.append("")

    if outcome.claimed_issue is not None:
        lines.extend(
            (
                "## Claimed Task",
                f"- Claimed issue number: #{outcome.claimed_issue.number}",
                f"- Task-ID: {outcome.task_id or 'missing-task-id'}",
                f"- Issue title: {outcome.claimed_issue.title}",
                "",
            )
        )
    else:
        lines.extend(("## Claimed Task", "- None.", ""))

    if outcome.matching_prs:
        append_review_pr_details(lines, outcome.matching_prs[0])
    elif outcome.pr_evaluations:
        lines.extend(("## Matching PR", "- None with a valid claimed-task footer.", ""))
    else:
        lines.extend(("## Matching PR", "- None.", ""))

    append_review_footer_validation(lines, outcome.pr_evaluations)
    lines.extend(
        (
            "",
            "## Human Action Needed",
            outcome.human_action_needed,
            "",
        )
    )
    return "\n".join(lines).rstrip() + "\n"


def append_review_pr_details(
    lines: list[str],
    evaluation: PullRequestFooterEvaluation,
) -> None:
    pull_request = evaluation.pull_request
    check_summary = summarize_status_checks(pull_request)
    lines.extend(
        (
            "## Matching PR",
            f"- Matching PR number: #{pull_request.number}",
            f"- PR title: {pull_request.title}",
            f"- PR head branch: {pull_request.head_ref_name}",
            f"- PR base branch: {pull_request.base_ref_name or 'unknown'}",
            f"- PR state: {pull_request.state or 'unknown'}",
            f"- PR draft: {'yes' if pull_request.is_draft else 'no'}",
            "",
            "## Check Summary",
            f"- Status: {check_summary.status}",
            f"- {check_summary.summary}",
            "",
            "## Review Decision Summary",
            f"- reviewDecision: {pull_request.review_decision or 'unavailable'}",
            "",
            "## Mergeability Summary",
            f"- mergeable: {pull_request.mergeable or 'unavailable'}",
            f"- mergeStateStatus: {pull_request.merge_state_status or 'unavailable'}",
            "",
        )
    )


def append_review_footer_validation(
    lines: list[str],
    evaluations: Sequence[PullRequestFooterEvaluation],
) -> None:
    lines.extend(("## Footer Validation",))
    if not evaluations:
        lines.append("- No candidate PR footer to validate.")
        return

    for evaluation in evaluations:
        result = "valid" if not evaluation.footer_errors else "invalid"
        lines.append(f"- PR #{evaluation.pull_request.number}: {result}")
        lines.append(f"  Task-ID footer: {evaluation.footer_task_id or 'missing'}")
        issue_text = (
            f"#{evaluation.footer_issue_number}"
            if evaluation.footer_issue_number is not None
            else "missing"
        )
        lines.append(f"  Task-Issue footer: {issue_text}")
        if evaluation.footer_errors:
            lines.extend(f"  Error: {error}" for error in evaluation.footer_errors)


def append_pr_details(
    lines: list[str],
    evaluation: PullRequestFooterEvaluation,
    heading: str,
) -> None:
    pull_request = evaluation.pull_request
    lines.extend(
        (
            heading,
            f"- Matching PR number: #{pull_request.number}",
            f"- PR title: {pull_request.title}",
            f"- PR head branch: {pull_request.head_ref_name}",
            f"- PR state: {pull_request.state or 'OPEN'}",
            f"- PR draft: {'yes' if pull_request.is_draft else 'no'}",
            "",
        )
    )


def require_issue(issue: Issue | None) -> Issue:
    if issue is None:
        raise ValueError("Missing issue")
    return issue


def claim_selected_issue(
    repository: str,
    package: HandoffPackage,
    runner: CommandRunner = subprocess_runner,
) -> ClaimResult:
    command = (
        "gh",
        "issue",
        "edit",
        str(package.selected_issue_number),
        "--repo",
        repository,
        "--remove-label",
        "status:ready",
        "--add-label",
        "status:in-progress",
    )
    try:
        runner(command)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else ""
        detail = stderr or str(exc)
        raise ClaimFailedError(
            f"Failed to claim issue #{package.selected_issue_number}: {detail}"
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        raise ClaimFailedError(
            f"Failed to claim issue #{package.selected_issue_number}: {exc}"
        ) from exc

    return ClaimResult(
        issue_number=package.selected_issue_number,
        removed_label="status:ready",
        added_label="status:in-progress",
        command=command,
    )


def git_state_blockers(runner: CommandRunner = subprocess_runner) -> tuple[str, ...]:
    status = runner(("git", "status", "--porcelain"))
    if status.strip():
        return ("Local git working tree is dirty; dispatch is blocked.",)
    return ()


def build_blocked_outcome(blockers: Sequence[str]) -> SelectionOutcome:
    return SelectionOutcome(
        package=None,
        blockers=tuple(blockers),
        ready_candidates=(),
        task_prs=(),
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Agent dispatch handoff reporter."
    )
    parser.add_argument("--repo", default=DEFAULT_REPOSITORY, help="GitHub repository.")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Read-only mode. This is the default and never mutates GitHub.",
    )
    mode_group.add_argument(
        "--claim",
        action="store_true",
        help=(
            "Explicit opt-in claim-and-prompt mode. After all safety checks pass, "
            "move exactly one selected issue from status:ready to status:in-progress."
        ),
    )
    mode_group.add_argument(
        "--handoff",
        action="store_true",
        help=(
            "Prepare local handoff instructions for one claimed status:in-progress issue. "
            "This mode does not invoke Codex."
        ),
    )
    mode_group.add_argument(
        "--lifecycle",
        action="store_true",
        help=(
            "Read-only PR lifecycle monitor for one claimed status:in-progress issue. "
            "Matches open PRs by Task-ID and Task-Issue footer."
        ),
    )
    mode_group.add_argument(
        "--review-status",
        action="store_true",
        help=(
            "Read-only review readiness and merge-candidate monitor for one claimed "
            "status:in-progress issue and its matching PR."
        ),
    )
    parser.add_argument(
        "--issue",
        type=int,
        help="Explicit issue number to verify with --handoff.",
    )
    parser.add_argument(
        "--invoke",
        action="store_true",
        help="Explicit live invocation request. Currently fails closed as unsupported.",
    )
    parser.add_argument(
        "--write-artifact",
        action="store_true",
        help="Write the generated prompt under the local artifact directory.",
    )
    parser.add_argument(
        "--artifact-dir",
        default=".agent-handoff",
        help="Local directory for generated handoff prompt artifacts.",
    )
    parser.add_argument(
        "--check-git-state",
        action="store_true",
        help="Block if the local git working tree has pending changes.",
    )
    parser.add_argument(
        "--issue-limit",
        type=int,
        default=500,
        help="Maximum issues or PRs to read from GitHub.",
    )
    if "--dry-run" in argv and "--claim" in argv:
        parser.error("--dry-run and --claim cannot be used together.")
    return parser.parse_args(argv)


def run_reporter(
    argv: Sequence[str] | None = None,
    runner: CommandRunner = subprocess_runner,
) -> tuple[int, str]:
    args = parse_args(list(argv or []))
    if args.dry_run and args.claim:
        return 2, "Error: --dry-run and --claim cannot be used together.\n"
    if args.invoke and not args.handoff:
        return 2, "Error: --invoke requires --handoff and is unsupported by default.\n"

    if args.check_git_state:
        blockers = git_state_blockers(runner)
        if blockers:
            return 2, build_report(build_blocked_outcome(blockers))

    state = load_queue_state(args.repo, runner=runner, issue_limit=args.issue_limit)
    if args.lifecycle:
        lifecycle_outcome = build_lifecycle_outcome(state)
        return (
            2 if lifecycle_outcome.blockers else 0,
            build_lifecycle_report(lifecycle_outcome),
        )

    if args.review_status:
        review_outcome = build_review_readiness_outcome(state)
        return (
            2 if review_outcome.blockers else 0,
            build_review_readiness_report(review_outcome),
        )

    if args.handoff:
        handoff_outcome = build_local_handoff_outcome(
            state,
            repository=args.repo,
            artifact_dir=Path(args.artifact_dir),
            issue_number=args.issue,
            invoke_requested=args.invoke,
        )
        return (0 if not handoff_outcome.blockers else 2), build_handoff_report(handoff_outcome)

    outcome = select_handoff_package(state, repository=args.repo)
    if outcome.package is not None and (args.write_artifact or args.claim):
        package = write_prompt_artifact(outcome.package, Path(args.artifact_dir))
        outcome = SelectionOutcome(
            package=package,
            blockers=outcome.blockers,
            ready_candidates=outcome.ready_candidates,
            task_prs=outcome.task_prs,
            claim_result=outcome.claim_result,
        )

    if outcome.package is not None and args.claim:
        try:
            claim_result = claim_selected_issue(args.repo, outcome.package, runner=runner)
        except ClaimFailedError as exc:
            failed_outcome = SelectionOutcome(
                package=None,
                blockers=(str(exc),),
                ready_candidates=outcome.ready_candidates,
                task_prs=outcome.task_prs,
            )
            return 2, build_report(failed_outcome)
        outcome = SelectionOutcome(
            package=outcome.package,
            blockers=outcome.blockers,
            ready_candidates=outcome.ready_candidates,
            task_prs=outcome.task_prs,
            claim_result=claim_result,
        )

    return (0 if not outcome.blockers else 2), build_report(outcome)


def main(argv: Sequence[str] | None = None) -> int:
    exit_code, report = run_reporter(list(argv or sys.argv[1:]))
    print(report)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
