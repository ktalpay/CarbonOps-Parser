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
VALIDATION_MODES = ("minimal", "python", "dotnet", "ops", "full")


@dataclass(frozen=True)
class Issue:
    number: int
    title: str
    body: str
    labels: tuple[str, ...]
    state: str = "OPEN"


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


class CommandError(RunnerError):
    """Raised when a subprocess command fails."""

    def __init__(self, command: Sequence[str], returncode: int, message: str) -> None:
        self.command = tuple(command)
        self.returncode = returncode
        joined = " ".join(command)
        super().__init__(f"Command failed ({returncode}): {joined}\n{message}")


class ValidationError(RunnerError):
    """Raised when validation fails after task claim."""

    def __init__(self, command: Sequence[str], cause: RunnerError) -> None:
        self.command = tuple(command)
        super().__init__(str(cause))


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
        raise CommandError(command, completed.returncode, message)
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
    parser.add_argument("--issue-number", type=int, help="Select one exact open issue number.")
    parser.add_argument("--task-id", help="Select the open issue whose extracted task id matches this value.")
    parser.add_argument(
        "--validation-mode",
        choices=VALIDATION_MODES,
        default="minimal",
        help="Validation profile to run after Codex completes. Defaults to minimal.",
    )
    parser.add_argument(
        "--python-bin",
        default="python",
        help="Python executable used by Python validation commands.",
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
        state=str(raw_issue.get("state") or "OPEN"),
    )


def issue_list_command(repo: str, label: str | None = None) -> tuple[str, ...]:
    command = [
        "gh",
        "issue",
        "list",
        "--repo",
        repo,
        "--state",
        "open",
    ]
    if label is not None:
        command.extend(("--label", label))
    command.extend(("--json", "number,title,body,labels,state", "--limit", "200"))
    return tuple(command)


def list_issues(repo: str, label: str | None, runner: CommandRunner) -> tuple[Issue, ...]:
    output = runner(issue_list_command(repo, label), None, None)
    try:
        raw_issues = json.loads(output)
    except json.JSONDecodeError as exc:
        selector = f" for label {label!r}" if label is not None else ""
        raise RunnerError(f"gh issue list returned invalid JSON{selector}.") from exc
    if not isinstance(raw_issues, list):
        selector = f" for label {label!r}" if label is not None else ""
        raise RunnerError(f"gh issue list returned unexpected JSON{selector}.")
    return tuple(sorted((parse_issue(issue) for issue in raw_issues), key=lambda issue: issue.number))


def get_issue(repo: str, issue_number: int, runner: CommandRunner) -> Issue:
    output = runner(
        (
            "gh",
            "issue",
            "view",
            str(issue_number),
            "--repo",
            repo,
            "--json",
            "number,title,body,labels,state",
        ),
        None,
        None,
    )
    try:
        raw_issue = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RunnerError(f"gh issue view returned invalid JSON for issue #{issue_number}.") from exc
    if not isinstance(raw_issue, dict):
        raise RunnerError(f"gh issue view returned unexpected JSON for issue #{issue_number}.")
    issue = parse_issue(raw_issue)
    if issue.state.upper() != "OPEN":
        raise RunnerError(f"Selected issue #{issue.number} is not open.")
    return issue


def select_issue(args: argparse.Namespace, runner: CommandRunner) -> Issue:
    if args.issue_number is not None and args.task_id:
        raise RunnerError("Use only one explicit selector: --issue-number or --task-id.")

    if args.issue_number is not None:
        issue = get_issue(args.repo, args.issue_number, runner)
    elif args.task_id:
        requested_task_id = sanitize_task_id(args.task_id)
        matches = [
            issue
            for issue in list_issues(args.repo, None, runner)
            if extract_task_id(issue) == requested_task_id
        ]
        if not matches:
            raise RunnerError(f"No open issue found for task id {requested_task_id}.")
        if len(matches) > 1:
            issue_list = ", ".join(f"#{issue.number}" for issue in matches)
            raise RunnerError(f"Multiple open issues match task id {requested_task_id}: {issue_list}.")
        issue = matches[0]
    else:
        ready = list_issues(args.repo, READY_LABEL, runner)
        if not ready:
            raise RunnerError(f"No open issues labeled {READY_LABEL} were found.")
        issue = ready[0]

    if READY_LABEL not in issue.labels:
        raise RunnerError(
            f"Selected issue #{issue.number} ({extract_task_id(issue)}) is not labeled {READY_LABEL}; "
            "refusing to claim a non-ready task."
        )
    return issue


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


def validation_commands(plan: TaskPlan, mode: str, python_bin: str) -> tuple[tuple[str, ...], ...]:
    diff_check = ("git", "-C", str(plan.worktree_path), "diff", "--check")
    commands: list[tuple[str, ...]] = []

    if mode in ("python", "full"):
        commands.append((python_bin, "-m", "pytest"))
        if (plan.worktree_path / "scripts" / "check_public_safety.py").exists():
            commands.append((python_bin, "scripts/check_public_safety.py"))

    if mode in ("dotnet", "full"):
        sln_path = plan.worktree_path / "src" / "dotnet" / "CarbonOps.Parser.sln"
        if sln_path.exists():
            commands.append(("dotnet", "test", "src/dotnet/CarbonOps.Parser.sln", "--no-restore"))

    if mode in ("ops", "full"):
        test_path = plan.worktree_path / "tests" / "test_local_codex_task_runner.py"
        if test_path.exists():
            commands.append((python_bin, "-m", "pytest", "-q", "tests/test_local_codex_task_runner.py"))

    commands.append(diff_check)
    return tuple(commands)


def run_validation(plan: TaskPlan, mode: str, python_bin: str, runner: CommandRunner) -> None:
    for command in validation_commands(plan, mode, python_bin):
        print(f"Running validation: {' '.join(command)}")
        try:
            runner(command, None, plan.worktree_path if command[0] != "git" else None)
        except RunnerError as exc:
            raise ValidationError(command, exc) from exc


def print_validation_recovery(plan: TaskPlan, failed_command: Sequence[str]) -> None:
    print("Validation failed after issue claim; leaving issue status unchanged.", file=sys.stderr)
    print(f"Issue number: #{plan.issue.number}", file=sys.stderr)
    print(f"Task ID: {plan.task_id}", file=sys.stderr)
    print(f"Branch: {plan.branch}", file=sys.stderr)
    print(f"Worktree path: {plan.worktree_path}", file=sys.stderr)
    print(f"Failed command: {' '.join(failed_command)}", file=sys.stderr)
    print("Suggested manual commands:", file=sys.stderr)
    print(f"- cd {plan.worktree_path}", file=sys.stderr)
    print(f"- {' '.join(failed_command)}", file=sys.stderr)
    print("- fix validation failures", file=sys.stderr)
    print("- git diff --check", file=sys.stderr)


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


def create_pr(repo: str, plan: TaskPlan, validation_mode: str, runner: CommandRunner) -> str:
    validation_lines = [f"- validation-mode: {validation_mode}"]
    footer = f"Task-ID: {plan.task_id}\nTask-Issue: #{plan.issue.number}"
    pr_body = "\n".join(
        (
            f"Implements {plan.task_id}.",
            "",
            "Validation:",
            *validation_lines,
            "",
            footer,
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

    issue = select_issue(args, runner)
    plan = build_plan(issue, agents_root, args.base)
    prompt = generate_prompt(plan, args.repo)
    print_plan(plan, args.repo)

    if args.dry_run:
        print("Dry run: no labels, worktrees, files, Codex, validation, commits, pushes, or PRs were changed.")
        print("Planned commands:")
        print(f"- gh issue edit {plan.issue.number} --remove-label {READY_LABEL} --add-label {IN_PROGRESS_LABEL}")
        print(f"- git worktree add ... {plan.worktree_path} {plan.base}")
        print("- codex exec --sandbox workspace-write < prompt.md")
        for command in validation_commands(plan, args.validation_mode, args.python_bin):
            print(f"- {' '.join(command)}")
        print(f"- git push -u origin {plan.branch}")
        print(f"- gh pr create --base {plan.base} --head {plan.branch}")
        return 0

    claim_issue(args.repo, plan.issue, runner)
    prepare_worktree(source_root, plan, runner)
    write_prompt(plan, prompt)
    run_codex(plan, prompt, runner)
    try:
        run_validation(plan, args.validation_mode, args.python_bin, runner)
    except ValidationError as exc:
        print_validation_recovery(plan, exc.command)
        raise
    commit_hash = commit_changes(plan, runner)
    if commit_hash is None:
        raise RunnerError("Codex completed but produced no changes to commit; stopping before push and PR creation.")
    push_branch(plan, runner)
    pr_url = create_pr(args.repo, plan, args.validation_mode, runner)
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
