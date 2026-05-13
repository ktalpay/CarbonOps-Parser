from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "agent_task_watcher.py"
SPEC = importlib.util.spec_from_file_location("agent_task_watcher", SCRIPT_PATH)
assert SPEC is not None
watcher = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = watcher
SPEC.loader.exec_module(watcher)


Issue = watcher.Issue
PullRequest = watcher.PullRequest
WatcherError = watcher.WatcherError


class FakeClient:
    def __init__(self, *, issues: tuple[Issue, ...], pull_request: PullRequest) -> None:
        self.issues = {issue.number: issue for issue in issues}
        self.pull_request = pull_request
        self.comments: list[tuple[int, str]] = []
        self.find_calls: list[str] = []
        self.add_calls: list[tuple[int, str]] = []
        self.remove_calls: list[tuple[int, str]] = []
        self.edit_body_calls: list[tuple[int, str]] = []

    def view_pr(self, pr_number: int) -> PullRequest:
        assert pr_number == self.pull_request.number
        return self.pull_request

    def view_issue(self, issue_number: int) -> Issue:
        return self.issues[issue_number]

    def find_issue_for_task(self, task_id: str) -> int | None:
        self.find_calls.append(task_id)
        matches = [
            issue.number
            for issue in self.issues.values()
            if issue.title.startswith(f"[{task_id}]")
        ]
        return matches[0] if len(matches) == 1 else None

    def add_label(self, issue_number: int, label: str) -> None:
        self.add_calls.append((issue_number, label))
        issue = self.issues[issue_number]
        if label not in issue.labels:
            self.issues[issue_number] = Issue(
                number=issue.number,
                title=issue.title,
                body=issue.body,
                labels=issue.labels + (label,),
                state=issue.state,
            )

    def remove_label(self, issue_number: int, label: str) -> None:
        self.remove_calls.append((issue_number, label))
        issue = self.issues[issue_number]
        self.issues[issue_number] = Issue(
            number=issue.number,
            title=issue.title,
            body=issue.body,
            labels=tuple(existing for existing in issue.labels if existing != label),
            state=issue.state,
        )

    def edit_body(self, issue_number: int, body: str) -> None:
        self.edit_body_calls.append((issue_number, body))
        issue = self.issues[issue_number]
        self.issues[issue_number] = Issue(
            number=issue.number,
            title=issue.title,
            body=body,
            labels=issue.labels,
            state=issue.state,
        )

    def comment(self, issue_number: int, body: str) -> None:
        self.comments.append((issue_number, body))


def _issue(
    number: int,
    task_id: str,
    labels: tuple[str, ...],
    *,
    body: str | None = None,
) -> Issue:
    body = body if body is not None else f"Task ID: {task_id}\nDepends on: none\nUnblocks: none"
    return Issue(
        number=number,
        title=f"[{task_id}] Example task",
        body=body,
        labels=labels,
    )


def _pr(body: str, *, title: str = "[OPS-031] Example task") -> PullRequest:
    return PullRequest(number=505, title=title, body=body, merged=True)


def test_merged_transition_removes_other_status_labels_and_adds_merged() -> None:
    issue = _issue(
        505,
        "OPS-031",
        ("status:ready", "status:in-progress", "status:blocked", "lane:ops"),
    )
    client = FakeClient(issues=(issue,), pull_request=_pr("Task-ID: OPS-031\nTask-Issue: #505"))

    replacement = watcher.replace_status_label(client, issue, "status:merged")

    assert replacement.old_statuses == ("status:ready", "status:in-progress", "status:blocked")
    assert client.issues[505].labels == ("lane:ops", "status:merged")
    assert client.add_calls == [(505, "status:merged")]
    assert client.remove_calls == [
        (505, "status:ready"),
        (505, "status:in-progress"),
        (505, "status:blocked"),
    ]
    assert client.issues[505].body.startswith("Task ID: OPS-031\nStatus: merged\n")


def test_ready_transition_removes_blocked_in_progress_merged_and_adds_ready() -> None:
    issue = _issue(
        506,
        "OPS-032",
        ("status:blocked", "status:in-progress", "status:merged", "agent:ops"),
    )
    client = FakeClient(issues=(issue,), pull_request=_pr("Task-ID: OPS-031\nTask-Issue: #505"))

    replacement = watcher.replace_status_label(client, issue, "status:ready")

    assert replacement.old_statuses == ("status:blocked", "status:in-progress", "status:merged")
    assert client.issues[506].labels == ("agent:ops", "status:ready")
    assert client.issues[506].body.startswith("Task ID: OPS-032\nStatus: ready\n")


def test_blocked_transition_updates_body_status() -> None:
    issue = _issue(
        508,
        "OPS-034",
        ("status:ready", "lane:ops"),
        body="Task ID: OPS-034\nLane: ops\nStatus: ready\nDepends on: OPS-033\nUnblocks: none",
    )
    client = FakeClient(issues=(issue,), pull_request=_pr("Task-ID: OPS-034\nTask-Issue: #508"))

    watcher.replace_status_label(client, issue, "status:blocked")

    assert client.issues[508].labels == ("lane:ops", "status:blocked")
    assert client.issues[508].body.splitlines().count("Status: blocked") == 1
    assert "Status: ready" not in client.issues[508].body


def test_in_progress_transition_updates_existing_body_status() -> None:
    issue = _issue(
        507,
        "OPS-033",
        ("status:ready", "lane:ops"),
        body="Task ID: OPS-033\nLane: ops\nStatus: ready\nDepends on: none\nUnblocks: none",
    )
    client = FakeClient(issues=(issue,), pull_request=_pr("Task-ID: OPS-033\nTask-Issue: #507"))

    watcher.replace_status_label(client, issue, "status:in-progress")

    assert client.issues[507].labels == ("lane:ops", "status:in-progress")
    assert client.issues[507].body.splitlines().count("Status: in-progress") == 1
    assert "Status: ready" not in client.issues[507].body


def test_repeated_watcher_run_is_idempotent() -> None:
    source = _issue(
        505,
        "OPS-031",
        ("status:ready",),
        body="Task ID: OPS-031\nDepends on: OPS-030\nUnblocks: none",
    )
    dependency = _issue(504, "OPS-030", ("status:merged",))
    client = FakeClient(
        issues=(source, dependency),
        pull_request=_pr("Task-ID: OPS-031\nTask-Issue: #505"),
    )

    watcher.process_merged_pr(client, 505)
    first_labels = client.issues[505].labels
    first_body = client.issues[505].body
    watcher.process_merged_pr(client, 505)

    assert first_labels == ("status:merged",)
    assert client.issues[505].labels == first_labels
    assert client.issues[505].body == first_body
    assert client.issues[505].body.splitlines().count("Status: merged") == 1
    assert client.add_calls == [(505, "status:merged")]
    assert client.edit_body_calls == [(505, first_body)]


def test_pr_footer_task_issue_mapping_is_preferred_over_title_parsing() -> None:
    issue = _issue(700, "OPS-031", ("status:ready",))
    client = FakeClient(
        issues=(issue,),
        pull_request=_pr("Task-ID: OPS-031\nTask-Issue: #700", title="[OPS-999] Wrong title"),
    )

    result = watcher.process_merged_pr(client, 505)

    assert result is not None
    assert result.task_issue_number == 700
    assert client.find_calls == []
    assert client.issues[700].labels == ("status:merged",)


def test_task_issue_footer_uses_resolved_issue_task_id_when_pr_task_id_is_missing() -> None:
    issue = _issue(700, "OPS-031", ("status:ready",))
    client = FakeClient(
        issues=(issue,),
        pull_request=_pr("Task-Issue: #700", title="[OPS-999] Wrong title"),
    )

    result = watcher.process_merged_pr(client, 505)

    assert result is not None
    assert result.task_id == "OPS-031"
    assert result.task_issue_number == 700
    assert client.find_calls == []


def test_downstream_dependency_ready_update_uses_status_replacement() -> None:
    source = _issue(
        505,
        "OPS-031",
        ("status:in-progress",),
        body="Task ID: OPS-031\nDepends on: none\nUnblocks: OPS-032",
    )
    dependent = _issue(
        506,
        "OPS-032",
        ("status:blocked", "status:in-progress", "lane:ops"),
        body="Task ID: OPS-032\nDepends on: OPS-031\nUnblocks: none",
    )
    client = FakeClient(
        issues=(source, dependent),
        pull_request=_pr("Task-ID: OPS-031\nTask-Issue: #505"),
    )

    result = watcher.process_merged_pr(client, 505)

    assert result is not None
    assert client.issues[505].labels == ("status:merged",)
    assert client.issues[506].labels == ("lane:ops", "status:ready")
    assert "Status: merged" in client.issues[505].body
    assert "Status: ready" in client.issues[506].body
    assert (506, "status:ready") in client.add_calls
    assert (506, "status:blocked") in client.remove_calls
    assert (506, "status:in-progress") in client.remove_calls


def test_downstream_missing_depends_on_becomes_needs_attention() -> None:
    source = _issue(
        505,
        "OPS-031",
        ("status:ready",),
        body="Task ID: OPS-031\nDepends on: none\nUnblocks: OPS-032",
    )
    dependent = _issue(
        506,
        "OPS-032",
        ("status:blocked",),
        body="Task ID: OPS-032\nUnblocks: none",
    )
    client = FakeClient(
        issues=(source, dependent),
        pull_request=_pr("Task-ID: OPS-031\nTask-Issue: #505"),
    )

    result = watcher.process_merged_pr(client, 505)

    assert result is not None
    assert client.issues[506].labels == ("status:needs-attention",)
    assert "Status: needs-attention" in client.issues[506].body
    assert "`OPS-032` (#506) needs attention: missing `Depends on:` metadata." in result.skipped_downstream


def test_downstream_unresolved_dependency_becomes_needs_attention() -> None:
    source = _issue(
        505,
        "OPS-031",
        ("status:ready",),
        body="Task ID: OPS-031\nDepends on: none\nUnblocks: OPS-032",
    )
    dependent = _issue(
        506,
        "OPS-032",
        ("status:blocked",),
        body="Task ID: OPS-032\nDepends on: OPS-999\nUnblocks: none",
    )
    client = FakeClient(
        issues=(source, dependent),
        pull_request=_pr("Task-ID: OPS-031\nTask-Issue: #505"),
    )

    result = watcher.process_merged_pr(client, 505)

    assert result is not None
    assert client.issues[506].labels == ("status:needs-attention",)
    assert (
        "`OPS-032` (#506) needs attention: dependencies did not resolve to unique issues: `OPS-999`."
        in result.skipped_downstream
    )


def test_missing_task_mapping_produces_clear_diagnostic() -> None:
    client = FakeClient(
        issues=(),
        pull_request=_pr("Summary only", title="No task id here"),
    )

    with pytest.raises(WatcherError, match="no Task-Issue footer and no Task-ID/title task id"):
        watcher.process_merged_pr(client, 505)
