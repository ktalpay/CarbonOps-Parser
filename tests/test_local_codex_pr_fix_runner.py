from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Sequence

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "local_codex_pr_fix_runner.py"
SPEC = importlib.util.spec_from_file_location("local_codex_pr_fix_runner", SCRIPT_PATH)
assert SPEC is not None
runner_module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = runner_module
SPEC.loader.exec_module(runner_module)


PullRequest = runner_module.PullRequest
RunnerError = runner_module.RunnerError


class FakeRunner:
    def __init__(
        self,
        *,
        prs: Sequence[PullRequest] = (),
        changes: bool = True,
        fail_commands: Sequence[tuple[str, ...]] = (),
    ) -> None:
        self.prs = tuple(prs)
        self.changes = changes
        self.fail_commands = tuple(fail_commands)
        self.calls: list[tuple[tuple[str, ...], str | None, Path | None]] = []

    def __call__(self, command: Sequence[str], stdin: str | None = None, cwd: Path | None = None) -> str:
        command_tuple = tuple(command)
        self.calls.append((command_tuple, stdin, cwd))
        if command_tuple in self.fail_commands:
            raise RunnerError(f"forced failure: {' '.join(command_tuple)}")

        if command_tuple[:3] == ("gh", "pr", "list"):
            return json.dumps([self._raw_pr(pr) for pr in self.prs if pr.state.upper() == "OPEN"])

        if command_tuple[:3] == ("gh", "pr", "view"):
            number = int(command_tuple[3])
            matches = [pr for pr in self.prs if pr.number == number]
            if not matches:
                raise RunnerError(f"PR #{number} not found")
            return json.dumps(self._raw_pr(matches[0]))

        if "branch" in command_tuple and "--show-current" in command_tuple:
            return "feature/pr-fix\n"

        if "status" in command_tuple and "--porcelain" in command_tuple:
            return "M scripts/local_codex_pr_fix_runner.py\n" if self.changes else ""

        if "rev-parse" in command_tuple and "HEAD" in command_tuple:
            return "abc123def456\n"

        return ""

    @staticmethod
    def _raw_pr(pr: PullRequest) -> dict[str, object]:
        return {
            "number": pr.number,
            "title": pr.title,
            "body": pr.body,
            "labels": [{"name": label} for label in pr.labels],
            "state": pr.state,
            "merged": pr.merged,
            "headRefName": pr.head_branch,
            "baseRefName": pr.base_branch,
            "comments": [{"body": comment} for comment in pr.comments],
            "files": [{"path": path} for path in pr.files],
        }


def make_pr(
    number: int = 12,
    *,
    labels: tuple[str, ...] = ("pr:changes-requested",),
    comments: tuple[str, ...] = (),
    state: str = "OPEN",
    merged: bool = False,
    head_branch: str = "feature/pr-fix",
    base_branch: str = "develop",
    files: tuple[str, ...] = ("scripts/local_codex_pr_fix_runner.py",),
) -> PullRequest:
    return PullRequest(
        number=number,
        title="Fix parser automation",
        body="PR body with implementation context.",
        labels=labels,
        state=state,
        merged=merged,
        head_branch=head_branch,
        base_branch=base_branch,
        comments=comments,
        files=files,
    )


def make_args(tmp_path: Path, **overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "repo": "ktalpay/CarbonOps-Parser",
        "agents_root": tmp_path / "agents",
        "validation_mode": "minimal",
        "python_bin": "python",
        "pr_number": None,
        "dry_run": False,
        "once": True,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def commands(fake: FakeRunner) -> list[tuple[str, ...]]:
    return [call[0] for call in fake.calls]


def comments(fake: FakeRunner) -> list[str]:
    bodies: list[str] = []
    for command, _stdin, _cwd in fake.calls:
        if command[:3] == ("gh", "pr", "comment"):
            bodies.append(command[command.index("--body") + 1])
    return bodies


def test_explicit_pr_number_selection(tmp_path: Path) -> None:
    fake = FakeRunner(prs=(make_pr(12), make_pr(13)))

    result = runner_module.execute(make_args(tmp_path, pr_number=13), fake)

    assert result == 0
    assert any(command[:4] == ("gh", "pr", "view", "13") for command in commands(fake))
    assert ("git", "-C", str(tmp_path / "agents" / "PR-13"), "push", "origin", "feature/pr-fix") in commands(fake)


def test_detects_pr_by_changes_requested_label(tmp_path: Path) -> None:
    fake = FakeRunner(prs=(make_pr(21, labels=("docs",)), make_pr(22, labels=("pr:changes-requested",))))

    result = runner_module.execute(make_args(tmp_path), fake)

    assert result == 0
    assert ("git", "worktree", "add", str(tmp_path / "agents" / "PR-22"), "feature/pr-fix") in commands(fake)


def test_detects_pr_by_local_agent_fix_comment(tmp_path: Path) -> None:
    pr = make_pr(23, labels=(), comments=("Looks good.", "Please adjust tests. @local-agent fix"))
    fake = FakeRunner(prs=(pr,))

    result = runner_module.execute(make_args(tmp_path), fake)

    assert result == 0
    codex_call = next(call for call in fake.calls if call[0] == ("codex", "exec", "--sandbox", "workspace-write"))
    assert "Please adjust tests. @local-agent fix" in (codex_call[1] or "")


def test_dry_run_does_not_run_codex_commit_push_or_comment(tmp_path: Path) -> None:
    fake = FakeRunner(prs=(make_pr(24),))

    result = runner_module.execute(make_args(tmp_path, dry_run=True), fake)

    assert result == 0
    command_list = commands(fake)
    assert ("codex", "exec", "--sandbox", "workspace-write") not in command_list
    assert not any(command[:4] == ("git", "-C", str(tmp_path / "agents" / "PR-24"), "commit") for command in command_list)
    assert not any(command[:4] == ("git", "-C", str(tmp_path / "agents" / "PR-24"), "push") for command in command_list)
    assert not any(command[:3] == ("gh", "pr", "comment") for command in command_list)
    assert not (tmp_path / "agents").exists()


def test_closed_and_merged_prs_are_refused_for_explicit_selection(tmp_path: Path) -> None:
    closed = FakeRunner(prs=(make_pr(25, state="CLOSED"),))
    with pytest.raises(RunnerError, match="not open"):
        runner_module.execute(make_args(tmp_path, pr_number=25), closed)

    merged = FakeRunner(prs=(make_pr(26, merged=True),))
    with pytest.raises(RunnerError, match="merged"):
        runner_module.execute(make_args(tmp_path, pr_number=26), merged)

    assert not any(command[:2] == ("codex", "exec") for command in commands(closed))
    assert not any(command[:2] == ("codex", "exec") for command in commands(merged))


def test_closed_and_merged_prs_are_ignored_for_auto_selection(tmp_path: Path) -> None:
    fake = FakeRunner(
        prs=(
            make_pr(27, state="CLOSED"),
            make_pr(28, merged=True),
            make_pr(29, labels=("pr:changes-requested",)),
        )
    )

    result = runner_module.execute(make_args(tmp_path), fake)

    assert result == 0
    assert ("git", "worktree", "add", str(tmp_path / "agents" / "PR-29"), "feature/pr-fix") in commands(fake)


def test_minimal_validation_runs_only_git_diff_check(tmp_path: Path) -> None:
    fake = FakeRunner(prs=(make_pr(30),))

    result = runner_module.execute(make_args(tmp_path, validation_mode="minimal"), fake)

    assert result == 0
    validation_commands = [
        command
        for command in commands(fake)
        if command == ("python", "-m", "pytest")
        or command == ("python", "scripts/check_public_safety.py")
        or command[:2] == ("dotnet", "test")
        or command[-2:] == ("diff", "--check")
    ]
    assert validation_commands == [("git", "-C", str(tmp_path / "agents" / "PR-30"), "diff", "--check")]


def test_validation_failure_does_not_push_and_comments_recovery(tmp_path: Path) -> None:
    worktree = tmp_path / "agents" / "PR-31"
    failed_command = ("git", "-C", str(worktree), "diff", "--check")
    fake = FakeRunner(prs=(make_pr(31),), fail_commands=(failed_command,))

    with pytest.raises(runner_module.ValidationError):
        runner_module.execute(make_args(tmp_path), fake)

    assert not any(command[:4] == ("git", "-C", str(worktree), "push") for command in commands(fake))
    assert not any(command[:4] == ("git", "-C", str(worktree), "commit") for command in commands(fake))
    comment_body = comments(fake)[0]
    assert "validation failed" in comment_body
    assert "no push was performed" in comment_body
    assert f"failed-command: {' '.join(failed_command)}" in comment_body
    assert f"cd {worktree}" in comment_body


def test_successful_fix_pushes_same_branch_and_comments_commit_hash(tmp_path: Path) -> None:
    fake = FakeRunner(prs=(make_pr(32, head_branch="feature/same-pr-branch"),))

    result = runner_module.execute(make_args(tmp_path), fake)

    assert result == 0
    assert ("git", "-C", str(tmp_path / "agents" / "PR-32"), "push", "origin", "feature/same-pr-branch") in commands(fake)
    comment_body = comments(fake)[0]
    assert "abc123def456" in comment_body
    assert "validation-mode: minimal" in comment_body


def test_no_changes_comments_without_push(tmp_path: Path) -> None:
    fake = FakeRunner(prs=(make_pr(33),), changes=False)

    result = runner_module.execute(make_args(tmp_path), fake)

    assert result == 0
    assert not any(command[:4] == ("git", "-C", str(tmp_path / "agents" / "PR-33"), "push") for command in commands(fake))
    assert "no commit or push was needed" in comments(fake)[0]

def test_explicit_pr_number_without_fix_request_is_refused(tmp_path: Path) -> None:
    fake = FakeRunner(prs=(make_pr(34, labels=(), comments=()),))

    with pytest.raises(RunnerError, match="does not have label"):
        runner_module.execute(make_args(tmp_path, pr_number=34), fake)

    assert not any(
        command == ("codex", "exec", "--sandbox", "workspace-write")
        for command in commands(fake)
    )
    assert not any(
        command[:4] == ("git", "-C", str(tmp_path / "agents" / "PR-34"), "push")
        for command in commands(fake)
    )
    assert not any(
        command[:3] == ("gh", "pr", "comment")
        for command in commands(fake)
    )
