#!/usr/bin/env python3
"""Local Codex PR fix runner.

This script selects one open pull request that asks the local agent for fixes,
checks out the PR head branch in a deterministic worktree, runs Codex once from
a generated prompt, validates the result, and pushes a normal fix commit back to
the same PR branch. It intentionally has no merge, approval, close, branch
deletion, worktree deletion, force-push, or daemon behavior.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


CHANGES_REQUESTED_LABEL = "pr:changes-requested"
FIX_REQUEST_TOKEN = "@local-agent fix"
VALIDATION_MODES = ("minimal", "python", "dotnet", "ops", "full")

CommandRunner = Callable[[Sequence[str], str | None, Path | None], str]


@dataclass(frozen=True)
class PullRequest:
    number: int
    title: str
    body: str
    labels: tuple[str, ...]
    state: str
    merged: bool
    head_branch: str
    base_branch: str
    comments: tuple[str, ...] = ()
    files: tuple[str, ...] = ()


@dataclass(frozen=True)
class FixPlan:
    pr: PullRequest
    worktree_path: Path
    prompt_path: Path
    fix_comment: str | None


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
    """Raised when validation fails."""

    def __init__(self, command: Sequence[str], cause: RunnerError) -> None:
        self.command = tuple(command)
        super().__init__(str(cause))


def run_command(command: Sequence[str], stdin: str | None = None, cwd: Path | None = None) -> str:
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
    parser.add_argument("--agents-root", required=True, type=Path, help="Root directory for PR worktrees.")
    parser.add_argument(
        "--validation-mode",
        choices=VALIDATION_MODES,
        default="minimal",
        help="Validation profile to run after Codex completes. Defaults to minimal.",
    )
    parser.add_argument("--python-bin", default="python", help="Python executable for Python validation.")
    parser.add_argument("--pr-number", type=int, help="Select one exact open pull request number.")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without mutating state.")
    parser.add_argument("--once", action="store_true", help="Run exactly one PR fix.")
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


def comments_from_gh(raw_comments: object) -> tuple[str, ...]:
    if not isinstance(raw_comments, list):
        return ()
    comments: list[str] = []
    for comment in raw_comments:
        if isinstance(comment, dict):
            body = comment.get("body")
            if isinstance(body, str):
                comments.append(body)
        elif isinstance(comment, str):
            comments.append(comment)
    return tuple(comments)


def files_from_gh(raw_files: object) -> tuple[str, ...]:
    if not isinstance(raw_files, list):
        return ()
    files: list[str] = []
    for file_entry in raw_files:
        if isinstance(file_entry, dict):
            path = file_entry.get("path")
            if isinstance(path, str):
                files.append(path)
        elif isinstance(file_entry, str):
            files.append(file_entry)
    return tuple(files)


def parse_pr(raw_pr: dict[str, object]) -> PullRequest:
    return PullRequest(
        number=int(raw_pr["number"]),
        title=str(raw_pr.get("title") or ""),
        body=str(raw_pr.get("body") or ""),
        labels=labels_from_gh(raw_pr.get("labels")),
        state=str(raw_pr.get("state") or "OPEN"),
        merged=bool(raw_pr.get("merged") or raw_pr.get("mergedAt")),
        head_branch=str(raw_pr.get("headRefName") or ""),
        base_branch=str(raw_pr.get("baseRefName") or ""),
        comments=comments_from_gh(raw_pr.get("comments")),
        files=files_from_gh(raw_pr.get("files")),
    )


def pr_json_fields() -> str:
    return "number,title,body,labels,state,mergedAt,headRefName,baseRefName,comments,files"


def list_open_prs(repo: str, runner: CommandRunner) -> tuple[PullRequest, ...]:
    output = runner(
        ("gh", "pr", "list", "--repo", repo, "--state", "open", "--json", pr_json_fields(), "--limit", "100"),
        None,
        None,
    )
    try:
        raw_prs = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RunnerError("gh pr list returned invalid JSON.") from exc
    if not isinstance(raw_prs, list):
        raise RunnerError("gh pr list returned unexpected JSON.")
    return tuple(sorted((parse_pr(pr) for pr in raw_prs), key=lambda pr: pr.number))


def get_pr(repo: str, pr_number: int, runner: CommandRunner) -> PullRequest:
    output = runner(
        ("gh", "pr", "view", str(pr_number), "--repo", repo, "--json", pr_json_fields()),
        None,
        None,
    )
    try:
        raw_pr = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RunnerError(f"gh pr view returned invalid JSON for PR #{pr_number}.") from exc
    if not isinstance(raw_pr, dict):
        raise RunnerError(f"gh pr view returned unexpected JSON for PR #{pr_number}.")
    pr = parse_pr(raw_pr)
    ensure_open_unmerged(pr)
    return pr


def latest_fix_comment(pr: PullRequest) -> str | None:
    for comment in reversed(pr.comments):
        if FIX_REQUEST_TOKEN in comment.lower():
            return comment
    return None


def is_fix_requested(pr: PullRequest) -> bool:
    return CHANGES_REQUESTED_LABEL in pr.labels or latest_fix_comment(pr) is not None


def ensure_open_unmerged(pr: PullRequest) -> None:
    if pr.state.upper() != "OPEN":
        raise RunnerError(f"PR #{pr.number} is not open; refusing to apply local-agent fixes.")
    if pr.merged:
        raise RunnerError(f"PR #{pr.number} is merged; refusing to apply local-agent fixes.")
    if not pr.head_branch:
        raise RunnerError(f"PR #{pr.number} has no head branch.")
    if not pr.base_branch:
        raise RunnerError(f"PR #{pr.number} has no base branch.")


def select_pr(args: argparse.Namespace, runner: CommandRunner) -> PullRequest:
    if args.pr_number is not None:
        pr = get_pr(args.repo, args.pr_number, runner)
        if not is_fix_requested(pr):
            raise RunnerError(
                f"PR #{pr.number} does not have label {CHANGES_REQUESTED_LABEL!r} "
                f"or comment token {FIX_REQUEST_TOKEN!r}; refusing to apply local-agent fixes."
            )
        return pr

    candidates = []
    for pr in list_open_prs(args.repo, runner):
        if pr.state.upper() != "OPEN" or pr.merged:
            continue
        ensure_open_unmerged(pr)
        if is_fix_requested(pr):
            candidates.append(pr)
    if not candidates:
        raise RunnerError(
            f"No open PRs found with label {CHANGES_REQUESTED_LABEL!r} or comment token {FIX_REQUEST_TOKEN!r}."
        )
    return candidates[0]


def build_plan(pr: PullRequest, agents_root: Path) -> FixPlan:
    root = agents_root.expanduser()
    return FixPlan(
        pr=pr,
        worktree_path=root / f"PR-{pr.number}",
        prompt_path=root / ".handoff" / f"PR-{pr.number}" / "prompt.md",
        fix_comment=latest_fix_comment(pr),
    )


def generate_prompt(plan: FixPlan, repo: str) -> str:
    pr = plan.pr
    body = pr.body.strip() or "(No PR body provided.)"
    fix_comment = plan.fix_comment.strip() if plan.fix_comment else "(No fix request comment found.)"
    changed_files = "\n".join(f"- {path}" for path in pr.files) if pr.files else "- (Unavailable.)"
    return "\n".join(
        (
            f"# Codex PR Fix #{pr.number}",
            "",
            f"Repository: {repo}",
            f"Pull Request: #{pr.number}",
            f"Title: {pr.title}",
            f"Head branch: {pr.head_branch}",
            f"Base branch: {pr.base_branch}",
            "",
            "Apply only the requested fixes for this open pull request.",
            "",
            "Safety constraints:",
            "- Do not merge pull requests.",
            "- Do not approve pull requests.",
            "- Do not close pull requests.",
            "- Do not close issues.",
            "- Do not delete branches.",
            "- Do not delete worktrees.",
            "- Do not force push.",
            "- Do not modify unrelated PRs.",
            "- Do not apply fixes to merged/closed PRs.",
            "- Do not add production credentials.",
            "- Do not execute destructive database operations.",
            "",
            "PR body:",
            "",
            body,
            "",
            "Fix request comment:",
            "",
            fix_comment,
            "",
            "Changed files:",
            "",
            changed_files,
            "",
        )
    )


def print_plan(plan: FixPlan, repo: str) -> None:
    print(f"Selected PR: #{plan.pr.number} {plan.pr.title}")
    print(f"Head branch: {plan.pr.head_branch}")
    print(f"Base branch: {plan.pr.base_branch}")
    print(f"Worktree: {plan.worktree_path}")
    print(f"Prompt: {plan.prompt_path}")
    print(f"Repository: {repo}")


def current_branch(worktree_path: Path, runner: CommandRunner) -> str:
    return runner(("git", "-C", str(worktree_path), "branch", "--show-current"), None, None).strip()


def prepare_worktree(plan: FixPlan, runner: CommandRunner) -> None:
    pr = plan.pr
    runner(("git", "fetch", "origin", pr.base_branch), None, None)
    if plan.worktree_path.exists():
        runner(("git", "fetch", "origin", pr.head_branch), None, None)
        if current_branch(plan.worktree_path, runner) != pr.head_branch:
            runner(("git", "-C", str(plan.worktree_path), "switch", pr.head_branch), None, None)
        runner(("git", "-C", str(plan.worktree_path), "pull", "--ff-only", "origin", pr.head_branch), None, None)
        return

    plan.worktree_path.parent.mkdir(parents=True, exist_ok=True)
    runner(("git", "fetch", "origin", f"{pr.head_branch}:{pr.head_branch}"), None, None)
    runner(("git", "worktree", "add", str(plan.worktree_path), pr.head_branch), None, None)


def write_prompt(plan: FixPlan, prompt: str) -> None:
    plan.prompt_path.parent.mkdir(parents=True, exist_ok=True)
    plan.prompt_path.write_text(prompt, encoding="utf-8")


def run_codex(plan: FixPlan, prompt: str, runner: CommandRunner) -> None:
    print("Running: codex exec --sandbox workspace-write < prompt.md")
    runner(("codex", "exec", "--sandbox", "workspace-write"), prompt, plan.worktree_path)


def validation_commands(plan: FixPlan, mode: str, python_bin: str) -> tuple[tuple[str, ...], ...]:
    commands: list[tuple[str, ...]] = []
    if mode in ("python", "full"):
        commands.append((python_bin, "-m", "pytest"))
        if (plan.worktree_path / "scripts" / "check_public_safety.py").exists():
            commands.append((python_bin, "scripts/check_public_safety.py"))
    if mode in ("dotnet", "full"):
        if (plan.worktree_path / "src" / "dotnet" / "CarbonOps.Parser.sln").exists():
            commands.append(("dotnet", "test", "src/dotnet/CarbonOps.Parser.sln", "--no-restore"))
    if mode in ("ops", "full"):
        test_path = plan.worktree_path / "tests" / "test_local_codex_pr_fix_runner.py"
        if test_path.exists():
            commands.append((python_bin, "-m", "pytest", "-q", "tests/test_local_codex_pr_fix_runner.py"))
    commands.append(("git", "-C", str(plan.worktree_path), "diff", "--check"))
    return tuple(commands)


def run_validation(plan: FixPlan, mode: str, python_bin: str, runner: CommandRunner) -> None:
    for command in validation_commands(plan, mode, python_bin):
        print(f"Running validation: {' '.join(command)}")
        try:
            runner(command, None, plan.worktree_path if command[0] != "git" else None)
        except RunnerError as exc:
            raise ValidationError(command, exc) from exc


def has_changes(plan: FixPlan, runner: CommandRunner) -> bool:
    output = runner(("git", "-C", str(plan.worktree_path), "status", "--porcelain"), None, None)
    return bool(output.strip())


def commit_changes(plan: FixPlan, runner: CommandRunner) -> str | None:
    if not has_changes(plan, runner):
        return None
    runner(("git", "-C", str(plan.worktree_path), "add", "-A"), None, None)
    runner(("git", "-C", str(plan.worktree_path), "commit", "-m", f"Fix PR #{plan.pr.number} requested changes"), None, None)
    return runner(("git", "-C", str(plan.worktree_path), "rev-parse", "HEAD"), None, None).strip()


def push_branch(plan: FixPlan, runner: CommandRunner) -> None:
    runner(("git", "-C", str(plan.worktree_path), "push", "origin", plan.pr.head_branch), None, None)


def add_pr_comment(repo: str, pr_number: int, body: str, runner: CommandRunner) -> None:
    runner(("gh", "pr", "comment", str(pr_number), "--repo", repo, "--body", body), None, None)


def success_comment(commit_hash: str, validation_mode: str) -> str:
    return "\n".join(
        (
            "Local-agent fix completed.",
            "",
            f"- commit: {commit_hash}",
            f"- validation-mode: {validation_mode}",
            "- result: pushed to the PR head branch",
        )
    )


def no_changes_comment(validation_mode: str) -> str:
    return "\n".join(
        (
            "Local-agent fix completed with no changes.",
            "",
            f"- validation-mode: {validation_mode}",
            "- result: no commit or push was needed",
        )
    )


def validation_failure_comment(plan: FixPlan, validation_mode: str, failed_command: Sequence[str]) -> str:
    return "\n".join(
        (
            "Local-agent fix validation failed; no push was performed.",
            "",
            f"- validation-mode: {validation_mode}",
            f"- failed-command: {' '.join(failed_command)}",
            f"- worktree: {plan.worktree_path}",
            "",
            "Recovery:",
            f"- cd {plan.worktree_path}",
            f"- {' '.join(failed_command)}",
            "- fix validation failures",
            "- git diff --check",
        )
    )


def execute(args: argparse.Namespace, runner: CommandRunner = run_command) -> int:
    if not args.once:
        raise RunnerError("Refusing to run without --once; daemon/watch modes are not supported.")

    pr = select_pr(args, runner)
    plan = build_plan(pr, args.agents_root)
    prompt = generate_prompt(plan, args.repo)
    print_plan(plan, args.repo)

    if args.dry_run:
        print("Dry run: no worktrees, files, Codex, validation, commits, pushes, or comments were changed.")
        print("Planned commands:")
        print(f"- git fetch origin {pr.base_branch}")
        print(f"- git fetch origin {pr.head_branch}:{pr.head_branch}")
        print(f"- git worktree add {plan.worktree_path} {pr.head_branch}")
        print("- codex exec --sandbox workspace-write < prompt.md")
        for command in validation_commands(plan, args.validation_mode, args.python_bin):
            print(f"- {' '.join(command)}")
        print(f"- git push origin {pr.head_branch}")
        print(f"- gh pr comment {pr.number}")
        return 0

    prepare_worktree(plan, runner)
    write_prompt(plan, prompt)
    run_codex(plan, prompt, runner)
    try:
        run_validation(plan, args.validation_mode, args.python_bin, runner)
    except ValidationError as exc:
        add_pr_comment(args.repo, pr.number, validation_failure_comment(plan, args.validation_mode, exc.command), runner)
        raise

    commit_hash = commit_changes(plan, runner)
    if commit_hash is None:
        add_pr_comment(args.repo, pr.number, no_changes_comment(args.validation_mode), runner)
        print("No changes detected; skipping commit and push.")
        return 0

    push_branch(plan, runner)
    add_pr_comment(args.repo, pr.number, success_comment(commit_hash, args.validation_mode), runner)
    print(f"Committed and pushed: {commit_hash}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return execute(parse_args(argv))
    except RunnerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
