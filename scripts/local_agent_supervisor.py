#!/usr/bin/env python3
"""Local agent supervisor for one-shot unattended task dispatch.

The supervisor first looks for one pull request that needs local-agent fixes.
If none exists, it scans GitHub issue labels, selects at most one ready issue,
and delegates execution to the appropriate local runner. It intentionally does
not run Codex directly and has no merge, approval, issue-closing, scheduler, or
watch behavior.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence


READY_LABEL = "status:ready"
IN_PROGRESS_LABEL = "status:in-progress"
PR_CHANGES_REQUESTED_LABEL = "pr:changes-requested"
PR_FIX_REQUEST_TOKEN = "@local-agent fix"
VALIDATION_MODES = ("minimal", "python", "dotnet", "ops", "full")


CommandRunner = Callable[[Sequence[str], str | None, Path | None], str]


class SupervisorError(RuntimeError):
    """Raised for expected supervisor failures with clear messages."""


class CommandError(SupervisorError):
    """Raised when a subprocess command fails."""

    def __init__(self, command: Sequence[str], returncode: int, message: str) -> None:
        joined = " ".join(command)
        super().__init__(f"Command failed ({returncode}): {joined}\n{message}")
        self.command = tuple(command)
        self.returncode = returncode


@dataclass(frozen=True)
class SupervisorConfig:
    repo: str
    source_root: Path
    agents_root: Path
    base: str = "develop"
    validation_mode: str = "minimal"
    python_bin: str | None = None
    runner_script_path: Path | None = None
    log_directory: Path | None = None
    lock_path: Path | None = None


@dataclass(frozen=True)
class Issue:
    number: int
    title: str
    labels: tuple[str, ...]
    state: str = "OPEN"


@dataclass(frozen=True)
class PullRequest:
    number: int
    title: str
    labels: tuple[str, ...]
    state: str = "OPEN"
    merged: bool = False
    comments: tuple[str, ...] = ()


class FileLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._fd: int | None = None
        self.acquired = False

    def __enter__(self) -> "FileLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._fd = os.open(
                str(self.path),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        except FileExistsError:
            return self
        os.write(self._fd, f"pid={os.getpid()}\n".encode("utf-8"))
        self.acquired = True
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        if self.acquired:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass


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
    parser.add_argument("--config", required=True, type=Path, help="Path to local supervisor JSON config.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the selected dispatch without invoking the runner.",
    )
    parser.add_argument("--once", action="store_true", help="Run one queue scan and dispatch at most one task.")
    return parser.parse_args(argv)


def _config_path(raw: object, key: str, config_dir: Path) -> Path | None:
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw.strip():
        raise SupervisorError(f"Config value {key!r} must be a non-empty string.")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = config_dir / path
    return path


def load_config(path: Path) -> SupervisorConfig:
    config_path = path.expanduser()
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SupervisorError(f"Config file not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise SupervisorError(f"Config file is not valid JSON: {config_path}") from exc
    if not isinstance(raw, dict):
        raise SupervisorError("Supervisor config must be a JSON object.")

    config_dir = config_path.parent
    repo = raw.get("repo")
    if not isinstance(repo, str) or not repo.strip():
        raise SupervisorError("Config value 'repo' is required.")

    source_root = _config_path(raw.get("source_root"), "source_root", config_dir)
    agents_root = _config_path(raw.get("agents_root"), "agents_root", config_dir)
    if source_root is None:
        raise SupervisorError("Config value 'source_root' is required.")
    if agents_root is None:
        raise SupervisorError("Config value 'agents_root' is required.")

    base = raw.get("base_branch", raw.get("base", "develop"))
    if not isinstance(base, str) or not base.strip():
        raise SupervisorError("Config value 'base_branch' must be a non-empty string.")

    validation_mode = raw.get("validation_mode", "minimal")
    if validation_mode not in VALIDATION_MODES:
        allowed = ", ".join(VALIDATION_MODES)
        raise SupervisorError(f"Config value 'validation_mode' must be one of: {allowed}.")

    python_bin = raw.get("python_bin")
    if python_bin is not None and (not isinstance(python_bin, str) or not python_bin.strip()):
        raise SupervisorError("Config value 'python_bin' must be a non-empty string when provided.")

    return SupervisorConfig(
        repo=repo.strip(),
        source_root=source_root,
        agents_root=agents_root,
        base=base.strip(),
        validation_mode=validation_mode,
        python_bin=python_bin,
        runner_script_path=_config_path(raw.get("runner_script_path"), "runner_script_path", config_dir),
        log_directory=_config_path(raw.get("log_directory"), "log_directory", config_dir),
        lock_path=_config_path(raw.get("lock_path"), "lock_path", config_dir),
    )


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
    comments: list[str] = []
    if not isinstance(raw_comments, list):
        return ()
    for comment in raw_comments:
        if isinstance(comment, dict) and isinstance(comment.get("body"), str):
            comments.append(comment["body"])
        elif isinstance(comment, str):
            comments.append(comment)
    return tuple(comments)


def parse_issue(raw_issue: dict[str, object]) -> Issue:
    return Issue(
        number=int(raw_issue["number"]),
        title=str(raw_issue.get("title") or ""),
        labels=labels_from_gh(raw_issue.get("labels")),
        state=str(raw_issue.get("state") or "OPEN"),
    )


def parse_pull_request(raw_pr: dict[str, object]) -> PullRequest:
    return PullRequest(
        number=int(raw_pr["number"]),
        title=str(raw_pr.get("title") or ""),
        labels=labels_from_gh(raw_pr.get("labels")),
        state=str(raw_pr.get("state") or "OPEN"),
        merged=bool(raw_pr.get("merged") or raw_pr.get("mergedAt")),
        comments=comments_from_gh(raw_pr.get("comments")),
    )


def issue_list_command(repo: str, label: str) -> tuple[str, ...]:
    return (
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
        "number,title,labels,state",
        "--limit",
        "200",
    )


def pr_list_command(repo: str) -> tuple[str, ...]:
    return (
        "gh",
        "pr",
        "list",
        "--repo",
        repo,
        "--state",
        "open",
        "--json",
        "number,title,labels,state,mergedAt,comments",
        "--limit",
        "100",
    )


def list_issues(repo: str, label: str, runner: CommandRunner) -> tuple[Issue, ...]:
    output = runner(issue_list_command(repo, label), None, None)
    try:
        raw_issues = json.loads(output)
    except json.JSONDecodeError as exc:
        raise SupervisorError(f"gh issue list returned invalid JSON for label {label!r}.") from exc
    if not isinstance(raw_issues, list):
        raise SupervisorError(f"gh issue list returned unexpected JSON for label {label!r}.")
    return tuple(sorted((parse_issue(issue) for issue in raw_issues), key=lambda issue: issue.number))


def list_pull_requests(repo: str, runner: CommandRunner) -> tuple[PullRequest, ...]:
    output = runner(pr_list_command(repo), None, None)
    try:
        raw_prs = json.loads(output)
    except json.JSONDecodeError as exc:
        raise SupervisorError("gh pr list returned invalid JSON.") from exc
    if not isinstance(raw_prs, list):
        raise SupervisorError("gh pr list returned unexpected JSON.")
    return tuple(sorted((parse_pull_request(pr) for pr in raw_prs), key=lambda pr: pr.number))


def pr_fix_requested(pr: PullRequest) -> bool:
    if PR_CHANGES_REQUESTED_LABEL in pr.labels:
        return True
    return any(PR_FIX_REQUEST_TOKEN in comment.lower() for comment in pr.comments)


def select_pr_for_fix(repo: str, runner: CommandRunner) -> PullRequest | None:
    for pr in list_pull_requests(repo, runner):
        if pr.state.upper() != "OPEN" or pr.merged:
            continue
        if pr_fix_requested(pr):
            return pr
    return None


def source_root_is_dirty(source_root: Path, runner: CommandRunner) -> bool:
    output = runner(("git", "-C", str(source_root), "status", "--porcelain"), None, None)
    return bool(output.strip())


def fast_forward_base_if_possible(source_root: Path, base: str, runner: CommandRunner) -> bool:
    try:
        runner(("git", "-C", str(source_root), "fetch", "origin", base), None, None)
        current = runner(("git", "-C", str(source_root), "branch", "--show-current"), None, None).strip()
        if current == base:
            runner(("git", "-C", str(source_root), "merge", "--ff-only", f"origin/{base}"), None, None)
        else:
            runner(("git", "-C", str(source_root), "fetch", "origin", f"{base}:{base}"), None, None)
    except SupervisorError as exc:
        print(f"Supervisor: could not fast-forward {base} from origin: {exc}")
        return False
    return True


def default_lock_path(config: SupervisorConfig) -> Path:
    if config.lock_path is not None:
        return config.lock_path.expanduser()
    try:
        return config.agents_root.expanduser() / ".local-agent-supervisor.lock"
    except RuntimeError:
        return Path(tempfile.gettempdir()) / "carbonops-local-agent-supervisor.lock"


def runner_script_path(config: SupervisorConfig) -> Path:
    if config.runner_script_path is not None:
        return config.runner_script_path.expanduser()
    return config.source_root.expanduser() / "scripts" / "local_codex_task_runner.py"


def pr_fix_runner_script_path(config: SupervisorConfig) -> Path:
    return config.source_root.expanduser() / "scripts" / "local_codex_pr_fix_runner.py"


def log_directory(config: SupervisorConfig) -> Path:
    if config.log_directory is not None:
        return config.log_directory.expanduser()
    return config.agents_root.expanduser() / ".logs"


def runner_command(config: SupervisorConfig, issue_number: int) -> tuple[str, ...]:
    command = [
        sys.executable,
        str(runner_script_path(config)),
        "--repo",
        config.repo,
        "--source-root",
        str(config.source_root.expanduser()),
        "--agents-root",
        str(config.agents_root.expanduser()),
        "--base",
        config.base,
        "--run-once",
        "--issue-number",
        str(issue_number),
        "--validation-mode",
        config.validation_mode,
    ]
    if config.python_bin:
        command.extend(("--python-bin", config.python_bin))
    return tuple(command)


def pr_fix_runner_command(config: SupervisorConfig, pr_number: int) -> tuple[str, ...]:
    command = [
        sys.executable,
        str(pr_fix_runner_script_path(config)),
        "--repo",
        config.repo,
        "--agents-root",
        str(config.agents_root.expanduser()),
        "--once",
        "--pr-number",
        str(pr_number),
        "--validation-mode",
        config.validation_mode,
    ]
    if config.python_bin:
        command.extend(("--python-bin", config.python_bin))
    return tuple(command)


def run_runner(command: Sequence[str], config: SupervisorConfig) -> Path:
    logs = log_directory(config)
    logs.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if "--issue-number" in command:
        target_kind = "issue"
        target_number = command[command.index("--issue-number") + 1]
        runner_name = "local_codex_task_runner.py"
    elif "--pr-number" in command:
        target_kind = "pr"
        target_number = command[command.index("--pr-number") + 1]
        runner_name = "local_codex_pr_fix_runner.py"
    else:
        target_kind = "runner"
        target_number = "unknown"
        runner_name = Path(command[1]).name if len(command) > 1 else "runner"
    log_path = logs / f"local-agent-supervisor-{target_kind}-{target_number}-{timestamp}.log"
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(f"$ {' '.join(command)}\n\n")
        completed = subprocess.run(
            list(command),
            cwd=str(config.source_root.expanduser()),
            text=True,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if completed.returncode != 0:
        raise SupervisorError(f"{runner_name} failed with exit code {completed.returncode}; log: {log_path}")
    return log_path


def execute(args: argparse.Namespace, runner: CommandRunner = run_command) -> int:
    if not args.once:
        raise SupervisorError("Refusing to run without --once; scheduler and watch modes are not supported.")

    config = load_config(args.config)
    lock_path = default_lock_path(config)
    with FileLock(lock_path) as lock:
        if not lock.acquired:
            print(f"Supervisor: lock already held at {lock_path}; exiting.")
            return 0

        print(f"Supervisor: scanning {config.repo}.")
        if source_root_is_dirty(config.source_root.expanduser(), runner):
            raise SupervisorError(f"Source root has uncommitted changes: {config.source_root.expanduser()}")

        fast_forward_base_if_possible(config.source_root.expanduser(), config.base, runner)

        pr = select_pr_for_fix(config.repo, runner)
        if pr is not None:
            print(f"Supervisor: selected PR #{pr.number} {pr.title}")
            command = pr_fix_runner_command(config, pr.number)
            if args.dry_run:
                print("Supervisor: dry run; runner was not invoked.")
                print(f"Supervisor: planned command: {' '.join(command)}")
                return 0

            log_path = run_runner(command, config)
            print(f"Supervisor: PR fix runner completed; log: {log_path}")
            return 0

        in_progress = list_issues(config.repo, IN_PROGRESS_LABEL, runner)
        if in_progress:
            issue_list = ", ".join(f"#{issue.number} {issue.title}" for issue in in_progress)
            print(f"Supervisor: found in-progress issue(s); no dispatch: {issue_list}")
            return 0

        ready = list_issues(config.repo, READY_LABEL, runner)
        if not ready:
            print("Supervisor: no ready issues found; no dispatch.")
            return 0

        selected = ready[0]
        print(f"Supervisor: selected issue #{selected.number} {selected.title}")
        command = runner_command(config, selected.number)
        if args.dry_run:
            print("Supervisor: dry run; runner was not invoked.")
            print(f"Supervisor: planned command: {' '.join(command)}")
            return 0

        log_path = run_runner(command, config)
        print(f"Supervisor: runner completed; log: {log_path}")
        return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return execute(parse_args(argv))
    except SupervisorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
