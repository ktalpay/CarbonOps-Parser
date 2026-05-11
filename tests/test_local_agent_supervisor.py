from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Sequence

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "local_agent_supervisor.py"
SPEC = importlib.util.spec_from_file_location("local_agent_supervisor", SCRIPT_PATH)
assert SPEC is not None
supervisor = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = supervisor
SPEC.loader.exec_module(supervisor)


Issue = supervisor.Issue
PullRequest = supervisor.PullRequest
SupervisorError = supervisor.SupervisorError


class FakeRunner:
    def __init__(
        self,
        *,
        ready: Sequence[Issue] = (),
        in_progress: Sequence[Issue] = (),
        prs: Sequence[PullRequest] = (),
        dirty: bool = False,
        fail_ff: bool = False,
    ) -> None:
        self.ready = tuple(ready)
        self.in_progress = tuple(in_progress)
        self.prs = tuple(prs)
        self.dirty = dirty
        self.fail_ff = fail_ff
        self.calls: list[tuple[tuple[str, ...], str | None, Path | None]] = []

    def __call__(self, command: Sequence[str], stdin: str | None = None, cwd: Path | None = None) -> str:
        command_tuple = tuple(command)
        self.calls.append((command_tuple, stdin, cwd))

        if "status" in command_tuple and "--porcelain" in command_tuple:
            return "M README.md\n" if self.dirty else ""

        if "fetch" in command_tuple:
            if self.fail_ff:
                raise SupervisorError("fetch failed")
            return ""

        if "branch" in command_tuple and "--show-current" in command_tuple:
            return "develop\n"

        if "merge" in command_tuple and "--ff-only" in command_tuple:
            return ""

        if command_tuple[:3] == ("gh", "issue", "list"):
            label = command_tuple[command_tuple.index("--label") + 1]
            issues = self.in_progress if label == "status:in-progress" else self.ready
            return json.dumps(
                [
                    {
                        "number": issue.number,
                        "title": issue.title,
                        "labels": [{"name": label} for label in issue.labels],
                        "state": issue.state,
                    }
                    for issue in issues
                ]
            )

        if command_tuple[:3] == ("gh", "pr", "list"):
            return json.dumps(
                [
                    {
                        "number": pr.number,
                        "title": pr.title,
                        "labels": [{"name": label} for label in pr.labels],
                        "state": pr.state,
                        "merged": pr.merged,
                        "comments": [{"body": comment} for comment in pr.comments],
                    }
                    for pr in self.prs
                ]
            )

        return ""


def make_issue(number: int, title: str | None = None, label: str = "status:ready") -> Issue:
    return Issue(number=number, title=title or f"[OPS-{number}] Task {number}", labels=(label,))


def make_pr(
    number: int,
    title: str | None = None,
    labels: tuple[str, ...] = ("pr:changes-requested",),
    comments: tuple[str, ...] = (),
) -> PullRequest:
    return PullRequest(
        number=number,
        title=title or f"[OPS-{number}] PR {number}",
        labels=labels,
        comments=comments,
    )


def write_config(tmp_path: Path, **overrides: object) -> Path:
    source_root = tmp_path / "source"
    agents_root = tmp_path / "agents"
    source_root.mkdir()
    values: dict[str, object] = {
        "repo": "ktalpay/CarbonOps-Parser",
        "source_root": str(source_root),
        "agents_root": str(agents_root),
        "base_branch": "develop",
        "validation_mode": "minimal",
        "python_bin": "/opt/python",
        "runner_script_path": str(source_root / "scripts" / "local_codex_task_runner.py"),
        "log_directory": str(agents_root / ".logs"),
    }
    values.update(overrides)
    path = tmp_path / "local-agent.json"
    path.write_text(json.dumps(values), encoding="utf-8")
    return path


def make_args(config: Path, *, dry_run: bool = False, once: bool = True) -> argparse.Namespace:
    return argparse.Namespace(config=config, dry_run=dry_run, once=once)


def commands(fake: FakeRunner) -> list[tuple[str, ...]]:
    return [call[0] for call in fake.calls]


def expected_pr_list_command() -> tuple[str, ...]:
    return (
        "gh",
        "pr",
        "list",
        "--repo",
        "ktalpay/CarbonOps-Parser",
        "--state",
        "open",
        "--json",
        "number,title,labels,state,mergedAt,comments",
        "--limit",
        "100",
    )


def expected_in_progress_issue_list_command() -> tuple[str, ...]:
    return (
        "gh",
        "issue",
        "list",
        "--repo",
        "ktalpay/CarbonOps-Parser",
        "--state",
        "open",
        "--label",
        "status:in-progress",
        "--json",
        "number,title,labels,state",
        "--limit",
        "200",
    )


def test_config_loading_reads_expected_values(tmp_path: Path) -> None:
    config_path = write_config(tmp_path, base_branch="main", validation_mode="python")

    config = supervisor.load_config(config_path)

    assert config.repo == "ktalpay/CarbonOps-Parser"
    assert config.source_root == tmp_path / "source"
    assert config.agents_root == tmp_path / "agents"
    assert config.base == "main"
    assert config.validation_mode == "python"
    assert config.python_bin == "/opt/python"


def test_dry_run_does_not_invoke_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = write_config(tmp_path)
    fake = FakeRunner(ready=(make_issue(451),))
    invoked: list[tuple[str, ...]] = []
    monkeypatch.setattr(supervisor, "run_runner", lambda command, config: invoked.append(tuple(command)))

    result = supervisor.execute(make_args(config_path, dry_run=True), fake)

    assert result == 0
    assert invoked == []


def test_pr_fix_dispatch_runs_before_ready_issue_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = write_config(tmp_path)
    fake = FakeRunner(ready=(make_issue(451),), prs=(make_pr(12),))
    invoked: list[tuple[str, ...]] = []

    def fake_run_runner(command: Sequence[str], config: object) -> Path:
        invoked.append(tuple(command))
        return tmp_path / "runner.log"

    monkeypatch.setattr(supervisor, "run_runner", fake_run_runner)

    result = supervisor.execute(make_args(config_path), fake)

    assert result == 0
    assert len(invoked) == 1
    assert "--pr-number" in invoked[0]
    assert "--issue-number" not in invoked[0]
    assert not any(command[:3] == ("gh", "issue", "list") for command in commands(fake))


def test_pr_fix_dry_run_does_not_invoke_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = write_config(tmp_path)
    fake = FakeRunner(ready=(make_issue(451),), prs=(make_pr(12),))
    invoked: list[tuple[str, ...]] = []
    monkeypatch.setattr(supervisor, "run_runner", lambda command, config: invoked.append(tuple(command)))

    result = supervisor.execute(make_args(config_path, dry_run=True), fake)

    assert result == 0
    assert invoked == []
    assert not any(command[:3] == ("gh", "issue", "list") for command in commands(fake))


def test_supervisor_invokes_pr_fix_runner_with_expected_args(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = write_config(tmp_path, python_bin="/custom/python", validation_mode="ops")
    fake = FakeRunner(ready=(make_issue(451),), prs=(make_pr(12),))
    invoked: list[tuple[str, ...]] = []

    def fake_run_runner(command: Sequence[str], config: object) -> Path:
        invoked.append(tuple(command))
        return tmp_path / "runner.log"

    monkeypatch.setattr(supervisor, "run_runner", fake_run_runner)

    result = supervisor.execute(make_args(config_path), fake)

    assert result == 0
    command = invoked[0]
    assert command[:2] == (
        sys.executable,
        str(tmp_path / "source" / "scripts" / "local_codex_pr_fix_runner.py"),
    )
    assert ("--repo", "ktalpay/CarbonOps-Parser") == command[2:4]
    assert command[command.index("--agents-root") + 1] == str(tmp_path / "agents")
    assert "--once" in command
    assert command[command.index("--pr-number") + 1] == "12"
    assert command[command.index("--validation-mode") + 1] == "ops"
    assert command[command.index("--python-bin") + 1] == "/custom/python"


def test_no_pr_fix_continues_ready_issue_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = write_config(tmp_path)
    fake = FakeRunner(
        ready=(make_issue(451),),
        prs=(make_pr(12, labels=("docs",)),),
    )
    invoked: list[tuple[str, ...]] = []

    def fake_run_runner(command: Sequence[str], config: object) -> Path:
        invoked.append(tuple(command))
        return tmp_path / "runner.log"

    monkeypatch.setattr(supervisor, "run_runner", fake_run_runner)

    result = supervisor.execute(make_args(config_path), fake)

    assert result == 0
    assert len(invoked) == 1
    assert "--issue-number" in invoked[0]
    assert commands(fake).index(expected_pr_list_command()) < commands(fake).index(
        expected_in_progress_issue_list_command()
    )


def test_lock_prevents_concurrent_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    lock_path = tmp_path / "supervisor.lock"
    lock_path.write_text("pid=1\n", encoding="utf-8")
    config_path = write_config(tmp_path, lock_path=str(lock_path))
    fake = FakeRunner(ready=(make_issue(451),))
    monkeypatch.setattr(supervisor, "run_runner", lambda command, config: pytest.fail("runner should not run"))

    result = supervisor.execute(make_args(config_path), fake)

    assert result == 0
    assert commands(fake) == []
    assert "lock already held" in capsys.readouterr().out


def test_dirty_source_root_refuses_dispatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = write_config(tmp_path)
    fake = FakeRunner(ready=(make_issue(451),), dirty=True)
    monkeypatch.setattr(supervisor, "run_runner", lambda command, config: pytest.fail("runner should not run"))

    with pytest.raises(SupervisorError, match="uncommitted changes"):
        supervisor.execute(make_args(config_path), fake)

    assert not any(command[:3] == ("gh", "issue", "list") for command in commands(fake))


def test_in_progress_issue_guard_exits_without_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = write_config(tmp_path)
    fake = FakeRunner(
        ready=(make_issue(451),),
        in_progress=(make_issue(450, title="[OPS-025] Previous task", label="status:in-progress"),),
    )
    monkeypatch.setattr(supervisor, "run_runner", lambda command, config: pytest.fail("runner should not run"))

    result = supervisor.execute(make_args(config_path), fake)

    assert result == 0
    assert not any(command[-2:] == ("--label", "status:ready") for command in commands(fake))


def test_no_ready_queue_exits_without_dispatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = write_config(tmp_path)
    fake = FakeRunner()
    monkeypatch.setattr(supervisor, "run_runner", lambda command, config: pytest.fail("runner should not run"))

    result = supervisor.execute(make_args(config_path), fake)

    assert result == 0


def test_deterministic_ready_issue_selection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = write_config(tmp_path)
    fake = FakeRunner(ready=(make_issue(455), make_issue(451), make_issue(453)))
    invoked: list[tuple[str, ...]] = []

    def fake_run_runner(command: Sequence[str], config: object) -> Path:
        invoked.append(tuple(command))
        return tmp_path / "runner.log"

    monkeypatch.setattr(supervisor, "run_runner", fake_run_runner)

    result = supervisor.execute(make_args(config_path), fake)

    assert result == 0
    assert invoked
    command = invoked[0]
    assert command[command.index("--issue-number") + 1] == "451"


def test_supervisor_invokes_runner_with_expected_args(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = write_config(tmp_path, python_bin="/custom/python")
    fake = FakeRunner(ready=(make_issue(451),))
    invoked: list[tuple[str, ...]] = []

    def fake_run_runner(command: Sequence[str], config: object) -> Path:
        invoked.append(tuple(command))
        return tmp_path / "runner.log"

    monkeypatch.setattr(supervisor, "run_runner", fake_run_runner)

    result = supervisor.execute(make_args(config_path), fake)

    assert result == 0
    command = invoked[0]
    assert command[:2] == (
        sys.executable,
        str(tmp_path / "source" / "scripts" / "local_codex_task_runner.py"),
    )
    assert ("--repo", "ktalpay/CarbonOps-Parser") == command[2:4]
    assert "--run-once" in command
    assert command[command.index("--issue-number") + 1] == "451"
    assert command[command.index("--validation-mode") + 1] == "minimal"
    assert command[command.index("--python-bin") + 1] == "/custom/python"

def test_pr_fix_runner_failure_stops_cycle_without_issue_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = write_config(tmp_path)
    fake = FakeRunner(ready=(make_issue(451),), prs=(make_pr(12),))

    def fail_run_runner(command: Sequence[str], config: object) -> Path:
        assert "--pr-number" in command
        raise SupervisorError("fix runner failed")

    monkeypatch.setattr(supervisor, "run_runner", fail_run_runner)

    with pytest.raises(SupervisorError, match="fix runner failed"):
        supervisor.execute(make_args(config_path), fake)

    assert not any(
        command[:3] == ("gh", "issue", "list")
        for command in commands(fake)
    )
