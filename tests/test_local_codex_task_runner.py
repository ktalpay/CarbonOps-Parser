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
        open_issues: Sequence[Issue] = (),
        branch_exists: bool = False,
        changes: bool = True,
        fail_commands: Sequence[tuple[str, ...]] = (),
        pr_create_errors: Sequence[str] = (),
        existing_pr_url: str | None = None,
    ) -> None:
        self.ready = tuple(ready)
        self.in_progress = tuple(in_progress)
        self.open_issues = tuple(open_issues) or tuple(ready) + tuple(in_progress)
        self.branch_exists = branch_exists
        self.changes = changes
        self.fail_commands = tuple(fail_commands)
        self.pr_create_errors = list(pr_create_errors)
        self.existing_pr_url = existing_pr_url
        self.calls: list[tuple[tuple[str, ...], str | None, Path | None]] = []

    def __call__(
        self,
        command: Sequence[str],
        stdin: str | None = None,
        cwd: Path | None = None,
    ) -> str:
        command_tuple = tuple(command)
        self.calls.append((command_tuple, stdin, cwd))
        if command_tuple in self.fail_commands:
            raise RunnerError(f"forced failure: {' '.join(command_tuple)}")

        if command_tuple[:3] == ("gh", "issue", "list"):
            if "--label" in command_tuple:
                label = command_tuple[command_tuple.index("--label") + 1]
                issues = self.in_progress if label == "status:in-progress" else self.ready
            else:
                issues = self.open_issues
            return json.dumps(
                [
                    {
                        "number": issue.number,
                        "title": issue.title,
                        "body": issue.body,
                        "labels": [{"name": label} for label in issue.labels],
                        "state": issue.state,
                    }
                    for issue in issues
                ]
            )

        if command_tuple[:3] == ("gh", "issue", "view"):
            issue_number = int(command_tuple[3])
            matches = [issue for issue in self.open_issues if issue.number == issue_number]
            if not matches:
                raise RunnerError(f"issue #{issue_number} not found")
            issue = matches[0]
            return json.dumps(
                {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "labels": [{"name": label} for label in issue.labels],
                    "state": issue.state,
                }
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
            if self.pr_create_errors:
                raise RunnerError(self.pr_create_errors.pop(0))
            return "https://github.com/ktalpay/CarbonOps-Parser/pull/445\n"

        if command_tuple[:3] == ("gh", "pr", "list"):
            if self.existing_pr_url is None:
                return "[]"
            return json.dumps([{"url": self.existing_pr_url}])

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
        "issue_number": None,
        "task_id": None,
        "validation_mode": "minimal",
        "python_bin": "python",
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


def test_issue_number_selector_selects_exact_ready_issue(tmp_path: Path) -> None:
    issue_444 = make_issue(number=444, title="[OPS-024] Earlier task")
    issue_447 = make_issue(number=447, title="[OPS-025] Harden local runner")
    fake = FakeRunner(ready=(issue_444, issue_447), open_issues=(issue_444, issue_447))

    result = runner_module.execute(make_args(tmp_path, issue_number=447), fake)

    assert result == 0
    assert any(command[:4] == ("gh", "issue", "view", "447") for command in commands(fake))
    assert any(
        command[:4] == ("git", "-C", str(tmp_path / "agents" / "OPS-025"), "push")
        for command in commands(fake)
    )


def test_task_id_selector_selects_matching_open_ready_issue(tmp_path: Path) -> None:
    issue_444 = make_issue(number=444, title="[OPS-024] Earlier task")
    issue_447 = make_issue(number=447, title="[OPS-025] Harden local runner")
    fake = FakeRunner(ready=(issue_444, issue_447), open_issues=(issue_444, issue_447))

    result = runner_module.execute(make_args(tmp_path, task_id="ops-025"), fake)

    assert result == 0
    assert any(command[:3] == ("gh", "issue", "list") and "--label" not in command for command in commands(fake))
    assert any(
        command[:4] == ("git", "-C", str(tmp_path / "agents" / "OPS-025"), "push")
        for command in commands(fake)
    )


def test_selected_issue_must_be_ready(tmp_path: Path) -> None:
    issue = make_issue(number=447, title="[OPS-025] Harden local runner", labels=("priority:high",))
    fake = FakeRunner(open_issues=(issue,))

    with pytest.raises(RunnerError, match="not labeled status:ready"):
        runner_module.execute(make_args(tmp_path, issue_number=447), fake)

    assert not any(command[:3] == ("gh", "issue", "edit") for command in commands(fake))


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
    assert any(command[-2:] == ("diff", "--check") for command in command_list)
    assert ("python", "-m", "pytest") not in command_list
    assert any(
        command[:4] == ("git", "-C", str(tmp_path / "agents" / "OPS-024"), "push")
        for command in command_list
    )
    assert any(command[:3] == ("gh", "pr", "create") for command in command_list)
    codex_call = next(
        call for call in fake.calls if call[0] == ("codex", "exec", "--sandbox", "workspace-write")
    )
    assert "Issue: #444" in (codex_call[1] or "")


def test_validation_mode_minimal_runs_only_git_diff_check(tmp_path: Path) -> None:
    fake = FakeRunner(ready=(make_issue(),))

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
    assert validation_commands == [("git", "-C", str(tmp_path / "agents" / "OPS-024"), "diff", "--check")]


def test_python_bin_is_used_by_python_validation_mode(tmp_path: Path) -> None:
    fake = FakeRunner(ready=(make_issue(),))
    worktree = tmp_path / "agents" / "OPS-024"
    (worktree / "scripts").mkdir(parents=True)
    (worktree / "scripts" / "check_public_safety.py").write_text("print('ok')\n", encoding="utf-8")

    result = runner_module.execute(
        make_args(tmp_path, validation_mode="python", python_bin="/opt/custom/python"),
        fake,
    )

    assert result == 0
    assert ("/opt/custom/python", "-m", "pytest") in commands(fake)
    assert ("/opt/custom/python", "scripts/check_public_safety.py") in commands(fake)


def test_python_bin_is_used_by_ops_validation_mode(tmp_path: Path) -> None:
    fake = FakeRunner(ready=(make_issue(),))
    worktree = tmp_path / "agents" / "OPS-024"
    (worktree / "tests").mkdir(parents=True)
    (worktree / "tests" / "test_local_codex_task_runner.py").write_text("def test_ok(): pass\n", encoding="utf-8")

    result = runner_module.execute(
        make_args(tmp_path, validation_mode="ops", python_bin="/opt/custom/python"),
        fake,
    )

    assert result == 0
    assert (
        "/opt/custom/python",
        "-m",
        "pytest",
        "-q",
        "tests/test_local_codex_task_runner.py",
    ) in commands(fake)


def test_pr_body_footer_is_present_and_exact(tmp_path: Path) -> None:
    fake = FakeRunner(ready=(make_issue(number=447, title="[OPS-025] Harden local runner"),))

    result = runner_module.execute(make_args(tmp_path), fake)

    assert result == 0
    pr_call = next(call for call in fake.calls if call[0][:3] == ("gh", "pr", "create"))
    body = pr_call[0][pr_call[0].index("--body") + 1]
    assert body.endswith("Task-ID: OPS-025\nTask-Issue: #447")
    assert body.splitlines()[-2:] == ["Task-ID: OPS-025", "Task-Issue: #447"]


def test_pr_creation_retries_transient_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeRunner(ready=(make_issue(),), pr_create_errors=("GraphQL: HTTP 504 Gateway Timeout",))
    sleeps: list[float] = []
    monkeypatch.setattr(runner_module.time, "sleep", sleeps.append)

    result = runner_module.execute(make_args(tmp_path), fake)

    assert result == 0
    pr_create_calls = [command for command in commands(fake) if command[:3] == ("gh", "pr", "create")]
    assert len(pr_create_calls) == 2
    assert sleeps == [0.1]


def test_existing_pr_detection_after_pr_create_timeout(tmp_path: Path) -> None:
    existing_url = "https://github.com/ktalpay/CarbonOps-Parser/pull/487"
    fake = FakeRunner(
        ready=(make_issue(),),
        pr_create_errors=("GraphQL: HTTP 504 Gateway Timeout",),
        existing_pr_url=existing_url,
    )

    result = runner_module.execute(make_args(tmp_path), fake)

    assert result == 0
    pr_list_call = next(command for command in commands(fake) if command[:3] == ("gh", "pr", "list"))
    assert "--head" in pr_list_call
    assert pr_list_call[pr_list_call.index("--head") + 1] == "feature/ops-024-add-local-codex-one-shot-task-runner"
    assert len([command for command in commands(fake) if command[:3] == ("gh", "pr", "create")]) == 1


def test_recovery_report_after_repeated_pr_creation_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeRunner(
        ready=(make_issue(number=487, title="[OPS-030] Add PR creation retry"),),
        pr_create_errors=(
            "GraphQL: HTTP 504 Gateway Timeout",
            "temporary network failure",
            "API Gateway timeout",
        ),
    )
    monkeypatch.setattr(runner_module.time, "sleep", lambda seconds: None)

    with pytest.raises(runner_module.PrCreationError):
        runner_module.execute(make_args(tmp_path), fake)

    captured = capsys.readouterr()
    assert "PR creation failed after branch push" in captured.err
    assert "Task ID: OPS-030" in captured.err
    assert "Issue number: #487" in captured.err
    assert "Branch: feature/ops-030-add-pr-creation-retry" in captured.err
    assert "Commit hash: deadbeef1234567890" in captured.err
    assert "Base branch: develop" in captured.err
    assert "gh pr create" in captured.err
    assert "--head feature/ops-030-add-pr-creation-retry" in captured.err
    assert "GraphQL: HTTP 504 Gateway Timeout" in captured.err
    assert len([command for command in commands(fake) if command[:3] == ("gh", "pr", "create")]) == 3


def test_non_retryable_pr_creation_failure_remains_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeRunner(ready=(make_issue(),), pr_create_errors=("GraphQL: head ref must be a branch",))
    monkeypatch.setattr(runner_module.time, "sleep", lambda seconds: pytest.fail("should not sleep"))

    with pytest.raises(RunnerError, match="head ref must be a branch"):
        runner_module.execute(make_args(tmp_path), fake)

    assert len([command for command in commands(fake) if command[:3] == ("gh", "pr", "create")]) == 1
    assert len([command for command in commands(fake) if command[:3] == ("gh", "pr", "list")]) == 1


def test_validation_failure_does_not_commit_push_or_create_pr(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    issue = make_issue(number=447, title="[OPS-025] Harden local runner")
    worktree = tmp_path / "agents" / "OPS-025"
    failed_command = ("git", "-C", str(worktree), "diff", "--check")
    fake = FakeRunner(ready=(issue,), fail_commands=(failed_command,))

    with pytest.raises(runner_module.ValidationError):
        runner_module.execute(make_args(tmp_path), fake)

    command_list = commands(fake)
    assert not any(command[:4] == ("git", "-C", str(worktree), "commit") for command in command_list)
    assert not any(command[:4] == ("git", "-C", str(worktree), "push") for command in command_list)
    assert not any(command[:3] == ("gh", "pr", "create") for command in command_list)
    captured = capsys.readouterr()
    assert "Issue number: #447" in captured.err
    assert "Task ID: OPS-025" in captured.err
    assert f"Branch: feature/ops-025-harden-local-runner" in captured.err
    assert f"Worktree path: {worktree}" in captured.err
    assert f"Failed command: {' '.join(failed_command)}" in captured.err
