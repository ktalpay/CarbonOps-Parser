#!/usr/bin/env python3
"""Agent dispatch handoff reporter.

By default, the reporter inspects GitHub issue and PR state through read-only
`gh` CLI queries, selects one safe ready task, and prints a deterministic
handoff report. Explicit `--claim` mode may claim one selected issue by moving
`status:ready` to `status:in-progress`. The reporter never starts Codex,
approves PRs, merges PRs, closes issues, deletes branches, or deletes worktrees.
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
TASK_ISSUE_PATTERN = re.compile(r"^Task-Issue:\s*#?\d+\s*$", re.MULTILINE)

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
                    "number,title,headRefName,body",
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
        )
        for item in raw_items
        if isinstance(item, dict)
    ]


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
            "Return summary, branch, files changed, validation performed, read-only or "
            "claim-mode safety confirmation, remaining risks, PR URL if available, and "
            "a merge-ready or commit-ready verdict.",
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

    if args.check_git_state:
        blockers = git_state_blockers(runner)
        if blockers:
            return 2, build_report(build_blocked_outcome(blockers))

    state = load_queue_state(args.repo, runner=runner, issue_limit=args.issue_limit)
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
