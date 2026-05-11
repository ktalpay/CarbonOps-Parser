#!/usr/bin/env python3
"""Local Codex one-shot task runner.

This script claims one ready GitHub issue, prepares a deterministic local
worktree, runs Codex once from a generated prompt, validates the result, commits
changes, pushes the task branch, and opens a pull request. It intentionally has
no daemon, scheduler, merge, approval, issue-closing, branch-deletion, or
worktree-deletion behavior.
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


READY_LABEL = "status:ready"
IN_PROGRESS_LABEL = "status:in-progress"
TASK_ID_PATTERN = re.compile(r"\b([A-Za-z]+-\d+)\b")
BRACKETED_TASK_PATTERN = re.compile(r"\[([A-Za-z]+-\d+)\]")
SAFE_SEGMENT_PATTERN = re.compile(r"[^a-z0-9]+")


CommandRunner = Callable[[Sequence[str], str | None, Path | None], str]


@dataclass(frozen=True)
class Issue:
    number: int
    title: str
    body: str
    labels: tuple[str, ...]


@dataclass(frozen=True)
class TaskPlan:
    issue: Issue
    task_id: str
    slug: str
    branch: str
    worktree_path: Path
    prompt_path: Path
    base: str


class RunnerError(RuntimeError):
    """Raised for expected runner failures with clear user-facing messages."""


def run_command(
    command: Sequence[str],
    stdin: str | None = None,
    cwd: Path | None = None,
) -> str:
    """Run one command and return stdout, raising a clear error on failure."""

    completed = subprocess.run(
        list(command),
        cwd=str(cwd) if cwd else None,
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        joined = " ".join(command)
        raise RunnerError(f"Command failed ({completed.returncode}): {joined}\n{message}")
    return completed.stdout


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="GitHub repository, for example owner/name.")
    parser.add_argument("--source-root", required=True, type=Path, help="Path to the source repository.")
    parser.add_argument("--agents-root", required=True, type=Path, help="Root directory for task worktrees.")
    parser.add_argument("--base", default="develop", help="Base branch for the worktree and PR.")
    parser.add_argument("--run-once", action="store_true", help="Run exactly one ready task.")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without mutating state.")
    parser.add_argument(
        "--override-in-progress",
        action="store_true",
        help="Allow running when another open issue is status:in-progress.",
    )
    return parser.parse_args(argv)


def labels_from_gh(raw_labels: object) -> tuple[str, ...]:
    labels: list[str] = []
    if not isinstance(raw_labels, list):
        return ()
    for label in raw_labels:
        if isinstance(label, dict) and isinstance(label.get("name"), str):
            labels.append(label["name"])
        elif isinstance(label, str):
            labels.append(label)
    return tuple(labels)


def parse_issue(raw_issue: dict[str, object]) -> Issue:
    return Issue(
        number=int(raw_issue["number"]),
        title=str(raw_issue.get("title") or ""),
        body=str(raw_issue.get("body") or ""),
        labels=labels_from_gh(raw_issue.get("labels")),
    )


def list_issues(repo: str, label: str, runner: CommandRunner) -> tuple[Issue, ...]:
    output = runner(
        (
            "gh",
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--label",
            label,
            "--json",
            "number,title,body,labels",
            "--limit",
            "100",
        ),
        None,
        None,
    )
    try:
        raw_issues = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RunnerError(f"gh issue list returned invalid JSON for label {label!r}.") from exc
    if not isinstance(raw_issues, list):
        raise RunnerError(f"gh issue list returned unexpected JSON for label {label!r}.")
    return tuple(sorted((parse_issue(issue) for issue in raw_issues), key=lambda issue: issue.number))


def extract_task_id(issue: Issue) -> str:
    bracket_match = BRACKETED_TASK_PATTERN.search(issue.title)
    if bracket_match:
        return sanitize_task_id(bracket_match.group(1))
    body_match = TASK_ID_PATTERN.search(issue.body)
    if body_match:
        return sanitize_task_id(body_match.group(1))
    title_match = TASK_ID_PATTERN.search(issue.title)
    if title_match:
        return sanitize_task_id(title_match.group(1))
    return f"ISSUE-{issue.number}"


def sanitize_task_id(value: str) -> str:
    parts = re.findall(r"[A-Za-z0-9]+", value)
    if len(parts) >= 2:
        return f"{parts[0].upper()}-{parts[1]}"
    return SAFE_SEGMENT_PATTERN.sub("-", value.lower()).strip("-").upper()


def slugify(value: str, fallback: str = "task") -> str:
    without_task_id = BRACKETED_TASK_PATTERN.sub("", value)
    slug = SAFE_SEGMENT_PATTERN.sub("-", without_task_id.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return (slug or fallback)[:64].strip("-") or fallback


def build_plan(issue: Issue, agents_root: Path, base: str) -> TaskPlan:
    task_id = extract_task_id(issue)
    task_segment = task_id.lower()
    slug = slugify(issue.title)
    branch = f"feature/{task_segment}-{slug}"
    worktree_path = agents_root.expanduser() / task_id
    prompt_path = agents_root.expanduser() / ".handoff" / task_id / "prompt.md"
    return TaskPlan(
        issue=issue,
        task_id=task_id,
        slug=slug,
        branch=branch,
        worktree_path=worktree_path,
        prompt_path=prompt_path,
        base=base,
    )


def generate_prompt(plan: TaskPlan, repo: str) -> str:
    body = plan.issue.body.strip() or "(No issue body provided.)"
    return "\n".join(
        (
            f"# Codex Task {plan.task_id}",
            "",
            f"Repository: {repo}",
            f"Issue: #{plan.issue.number}",
            f"Title: {plan.issue.title}",
            f"Branch: {plan.branch}",
            "",
            "Implement only the task described in this issue.",
            "",
            "Safety constraints:",
            "- Do not merge pull requests.",
            "- Do not approve pull requests.",
            "- Do not close issues.",
            "- Do not delete branches.",
            "- Do not delete worktrees.",
            "- Do not claim unrelated product tasks.",
            "",
            "Issue body:",
            "",
            body,
            "",
        )
    )


def print_plan(plan: TaskPlan, repo: str) -> None:
    print(f"Selected issue: #{plan.issue.number} {plan.issue.title}")
    print(f"Task ID: {plan.task_id}")
    print(f"Branch: {plan.branch}")
    print(f"Worktree: {plan.worktree_path}")
    print(f"Prompt: {plan.prompt_path}")
    print(f"Base: {plan.base}")
    print(f"Repository: {repo}")


def claim_issue(repo: str, issue: Issue, runner: CommandRunner) -> None:
    runner(
        (
            "gh",
            "issue",
            "edit",
            str(issue.number),
            "--repo",
            repo,
            "--remove-label",
            READY_LABEL,
            "--add-label",
            IN_PROGRESS_LABEL,
        ),
        None,
        None,
    )


def local_branch_exists(source_root: Path, branch: str, runner: CommandRunner) -> bool:
    try:
        runner(("git", "-C", str(source_root), "rev-parse", "--verify", f"refs/heads/{branch}"), None, None)
    except RunnerError:
        return False
    return True


def current_branch(worktree_path: Path, runner: CommandRunner) -> str:
    return runner(("git", "-C", str(worktree_path), "branch", "--show-current"), None, None).strip()


def prepare_worktree(source_root: Path, plan: TaskPlan, runner: CommandRunner) -> None:
    if plan.worktree_path.exists():
        if current_branch(plan.worktree_path, runner) != plan.branch:
            runner(("git", "-C", str(plan.worktree_path), "switch", plan.branch), None, None)
        return

    plan.worktree_path.parent.mkdir(parents=True, exist_ok=True)
    if local_branch_exists(source_root, plan.branch, runner):
        runner(("git", "-C", str(source_root), "worktree", "add", str(plan.worktree_path), plan.branch), None, None)
        return
    runner(
        ("git", "-C", str(source_root), "worktree", "add", "-b", plan.branch, str(plan.worktree_path), plan.base),
        None,
        None,
    )


def write_prompt(plan: TaskPlan, prompt: str) -> None:
    plan.prompt_path.parent.mkdir(parents=True, exist_ok=True)
    plan.prompt_path.write_text(prompt, encoding="utf-8")


def run_codex(plan: TaskPlan, prompt: str, runner: CommandRunner) -> None:
    print("Running: codex exec --sandbox workspace-write < prompt.md")
    runner(("codex", "exec", "--sandbox", "workspace-write"), prompt, plan.worktree_path)


def run_validation(plan: TaskPlan, runner: CommandRunner) -> None:
    print("Running validation: python -m pytest")
    runner(("python", "-m", "pytest"), None, plan.worktree_path)
    print("Running validation: git diff --check")
    runner(("git", "-C", str(plan.worktree_path), "diff", "--check"), None, None)


def has_changes(plan: TaskPlan, runner: CommandRunner) -> bool:
    output = runner(("git", "-C", str(plan.worktree_path), "status", "--porcelain"), None, None)
    return bool(output.strip())


def commit_changes(plan: TaskPlan, runner: CommandRunner) -> str | None:
    if not has_changes(plan, runner):
        print("No changes detected; skipping commit.")
        return None
    runner(("git", "-C", str(plan.worktree_path), "add", "-A"), None, None)
    runner(
        (
            "git",
            "-C",
            str(plan.worktree_path),
            "commit",
            "-m",
            f"[{plan.task_id}] {plan.issue.title}",
        ),
        None,
        None,
    )
    return runner(("git", "-C", str(plan.worktree_path), "rev-parse", "HEAD"), None, None).strip()


def push_branch(plan: TaskPlan, runner: CommandRunner) -> None:
    runner(("git", "-C", str(plan.worktree_path), "push", "-u", "origin", plan.branch), None, None)


def create_pr(repo: str, plan: TaskPlan, runner: CommandRunner) -> str:
    pr_body = "\n".join(
        (
            f"Implements {plan.task_id}.",
            "",
            "Validation:",
            "- python -m pytest",
            "- git diff --check",
            "",
            f"Task-Issue: #{plan.issue.number}",
        )
    )
    output = runner(
        (
            "gh",
            "pr",
            "create",
            "--repo",
            repo,
            "--base",
            plan.base,
            "--head",
            plan.branch,
            "--title",
            f"[{plan.task_id}] {plan.issue.title}",
            "--body",
            pr_body,
        ),
        None,
        plan.worktree_path,
    )
    return output.strip()


def execute(args: argparse.Namespace, runner: CommandRunner = run_command) -> int:
    if not args.run_once:
        raise RunnerError("Refusing to run without --run-once; daemon/watch modes are not supported.")

    source_root = args.source_root.expanduser()
    agents_root = args.agents_root.expanduser()

    in_progress = list_issues(args.repo, IN_PROGRESS_LABEL, runner)
    if in_progress and not args.override_in_progress:
        issue_list = ", ".join(f"#{issue.number} {issue.title}" for issue in in_progress)
        raise RunnerError(
            f"Refusing to run because open issue(s) are labeled {IN_PROGRESS_LABEL}: {issue_list}. "
            "Use --override-in-progress to run anyway."
        )

    ready = list_issues(args.repo, READY_LABEL, runner)
    if not ready:
        raise RunnerError(f"No open issues labeled {READY_LABEL} were found.")

    plan = build_plan(ready[0], agents_root, args.base)
    prompt = generate_prompt(plan, args.repo)
    print_plan(plan, args.repo)

    if args.dry_run:
        print("Dry run: no labels, worktrees, files, Codex, validation, commits, pushes, or PRs were changed.")
        print("Planned commands:")
        print(f"- gh issue edit {plan.issue.number} --remove-label {READY_LABEL} --add-label {IN_PROGRESS_LABEL}")
        print(f"- git worktree add ... {plan.worktree_path} {plan.base}")
        print("- codex exec --sandbox workspace-write < prompt.md")
        print("- python -m pytest")
        print("- git diff --check")
        print(f"- git push -u origin {plan.branch}")
        print(f"- gh pr create --base {plan.base} --head {plan.branch}")
        return 0

    claim_issue(args.repo, plan.issue, runner)
    prepare_worktree(source_root, plan, runner)
    write_prompt(plan, prompt)
    run_codex(plan, prompt, runner)
    run_validation(plan, runner)
    commit_hash = commit_changes(plan, runner)
    if commit_hash is None:
        raise RunnerError("Codex completed but produced no changes to commit; stopping before push and PR creation.")
    push_branch(plan, runner)
    pr_url = create_pr(args.repo, plan, runner)
    print(f"Committed: {commit_hash}")
    print(f"Pull request: {pr_url}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        return execute(args)
    except RunnerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
