from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Sequence

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "local_codex_task_runner.py"
SPEC = importlib.util.spec_from_file_location("local_codex_task_runner", SCRIPT_PATH)
assert SPEC is not None
runner_module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = runner_module
SPEC.loader.exec_module(runner_module)


Issue = runner_module.Issue
RunnerError = runner_module.RunnerError


class FakeRunner:
    def __init__(
        self,
        *,
        ready: Sequence[Issue] = (),
        in_progress: Sequence[Issue] = (),
        branch_exists: bool = False,
        changes: bool = True,
    ) -> None:
        self.ready = tuple(ready)
        self.in_progress = tuple(in_progress)
        self.branch_exists = branch_exists
        self.changes = changes
        self.calls: list[tuple[tuple[str, ...], str | None, Path | None]] = []

    def __call__(
        self,
        command: Sequence[str],
        stdin: str | None = None,
        cwd: Path | None = None,
    ) -> str:
        command_tuple = tuple(command)
        self.calls.append((command_tuple, stdin, cwd))

        if command_tuple[:3] == ("gh", "issue", "list"):
            label = command_tuple[command_tuple.index("--label") + 1]
            issues = self.in_progress if label == "status:in-progress" else self.ready
            return json.dumps(
                [
                    {
                        "number": issue.number,
                        "title": issue.title,
                        "body": issue.body,
                        "labels": [{"name": label} for label in issue.labels],
                    }
                    for issue in issues
                ]
            )

        if "rev-parse" in command_tuple and "--verify" in command_tuple:
            if self.branch_exists:
                return "abc123\n"
            raise RunnerError("branch missing")

        if "branch" in command_tuple and "--show-current" in command_tuple:
            return "feature/ops-024-add-local-codex-one-shot-task-runner\n"

        if "status" in command_tuple and "--porcelain" in command_tuple:
            return "M scripts/local_codex_task_runner.py\n" if self.changes else ""

        if "rev-parse" in command_tuple and "HEAD" in command_tuple:
            return "deadbeef1234567890\n"

        if command_tuple[:3] == ("gh", "pr", "create"):
            return "https://github.com/ktalpay/CarbonOps-Parser/pull/445\n"

        return ""


def make_issue(
    number: int = 444,
    title: str = "[OPS-024] Add local Codex one-shot task runner",
    body: str = "Task body\n\nValidation: git diff --check",
    labels: tuple[str, ...] = ("status:ready",),
) -> Issue:
    return Issue(number=number, title=title, body=body, labels=labels)


def make_args(tmp_path: Path, **overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "repo": "ktalpay/CarbonOps-Parser",
        "source_root": tmp_path / "source",
        "agents_root": tmp_path / "agents",
        "base": "develop",
        "run_once": True,
        "dry_run": False,
        "override_in_progress": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def commands(fake: FakeRunner) -> list[tuple[str, ...]]:
    return [call[0] for call in fake.calls]


def test_refuses_when_issue_is_in_progress_without_override(tmp_path: Path) -> None:
    fake = FakeRunner(ready=(make_issue(),), in_progress=(make_issue(number=443),))

    with pytest.raises(RunnerError, match="Refusing to run"):
        runner_module.execute(make_args(tmp_path), fake)

    assert not any(command[:3] == ("gh", "issue", "edit") for command in commands(fake))


def test_override_allows_ready_issue_selection(tmp_path: Path) -> None:
    fake = FakeRunner(ready=(make_issue(),), in_progress=(make_issue(number=443),))

    result = runner_module.execute(make_args(tmp_path, override_in_progress=True), fake)

    assert result == 0
    assert (
        "gh",
        "issue",
        "edit",
        "444",
        "--repo",
        "ktalpay/CarbonOps-Parser",
        "--remove-label",
        "status:ready",
        "--add-label",
        "status:in-progress",
    ) in commands(fake)


def test_dry_run_does_not_mutate_or_write_files(tmp_path: Path) -> None:
    fake = FakeRunner(ready=(make_issue(),))

    result = runner_module.execute(make_args(tmp_path, dry_run=True), fake)

    assert result == 0
    assert not (tmp_path / "agents").exists()
    mutating_commands = [
        command
        for command in commands(fake)
        if command[:3] == ("gh", "issue", "edit")
        or command[:4] == ("git", "-C", str(tmp_path / "source"), "worktree")
        or command[:2] == ("codex", "exec")
    ]
    assert mutating_commands == []


def test_branch_worktree_and_prompt_naming_are_deterministic(tmp_path: Path) -> None:
    plan = runner_module.build_plan(make_issue(), tmp_path / "agents", "develop")

    assert plan.task_id == "OPS-024"
    assert plan.slug == "add-local-codex-one-shot-task-runner"
    assert plan.branch == "feature/ops-024-add-local-codex-one-shot-task-runner"
    assert plan.worktree_path == tmp_path / "agents" / "OPS-024"
    assert plan.prompt_path == tmp_path / "agents" / ".handoff" / "OPS-024" / "prompt.md"


def test_prompt_generation_uses_issue_body_and_safety_constraints(tmp_path: Path) -> None:
    issue = make_issue(body="Implement the exact issue body.")
    plan = runner_module.build_plan(issue, tmp_path / "agents", "develop")

    prompt = runner_module.generate_prompt(plan, "ktalpay/CarbonOps-Parser")

    assert "# Codex Task OPS-024" in prompt
    assert "Issue: #444" in prompt
    assert "Implement the exact issue body." in prompt
    assert "Do not merge pull requests." in prompt
    assert "Do not delete worktrees." in prompt


def test_command_planning_uses_expected_codex_validation_push_and_pr_commands(tmp_path: Path) -> None:
    fake = FakeRunner(ready=(make_issue(),), branch_exists=False)

    result = runner_module.execute(make_args(tmp_path), fake)

    assert result == 0
    command_list = commands(fake)
    assert any(command[:4] == ("git", "-C", str(tmp_path / "source"), "worktree") for command in command_list)
    assert ("codex", "exec", "--sandbox", "workspace-write") in command_list
    assert ("python", "-m", "pytest") in command_list
    assert any(command[-2:] == ("diff", "--check") for command in command_list)
    assert any(
        command[:4] == ("git", "-C", str(tmp_path / "agents" / "OPS-024"), "push")
        for command in command_list
    )
    assert any(command[:3] == ("gh", "pr", "create") for command in command_list)
    codex_call = next(
        call for call in fake.calls if call[0] == ("codex", "exec", "--sandbox", "workspace-write")
    )
    assert "Issue: #444" in (codex_call[1] or "")
