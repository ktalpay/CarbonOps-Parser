import json
from pathlib import Path

import pytest

from scripts.agent_dispatch_handoff_reporter import (
    Issue,
    PullRequest,
    QueueState,
    build_handoff_package,
    build_report,
    expected_branch_name,
    load_queue_state,
    parse_task_id,
    parse_task_list,
    run_reporter,
    select_handoff_package,
    select_prompt_template,
    write_prompt_artifact,
)


def _issue(
    number: int,
    task_id: str,
    lane: str,
    status: str,
    title: str | None = None,
    depends_on: str = "",
    agent: str | None = None,
    body_extra: str = "",
) -> Issue:
    title = title or f"[{task_id}] Example task"
    agent = agent or f"agent:{lane}"
    body = "\n".join(
        (
            f"Task ID: {task_id}",
            f"Lane: {lane}",
            f"Status: {status}",
            f"Agent: {agent.removeprefix('agent:')}-agent",
            f"Depends on: {depends_on}",
            "Unblocks:",
            "",
            "Scope:",
            "Implement a focused local-only task.",
            "",
            "Non-goals:",
            "- Do not delete branches.",
            "- Do not delete worktrees.",
            "",
            "Allowed files:",
            "- scripts/example.py",
            body_extra,
        )
    )
    return Issue(
        number=number,
        title=title,
        body=body,
        labels=(f"status:{status}", f"lane:{lane}", agent),
        state="OPEN",
    )


def _state(
    ready_issues=(),
    in_progress_issues=(),
    all_issues=(),
    open_prs=(),
) -> QueueState:
    return QueueState(
        ready_issues=tuple(ready_issues),
        in_progress_issues=tuple(in_progress_issues),
        all_issues=tuple(all_issues),
        open_prs=tuple(open_prs),
    )


def _issue_payload(issue: Issue) -> dict:
    return {
        "number": issue.number,
        "title": issue.title,
        "body": issue.body,
        "labels": [{"name": label} for label in issue.labels],
        "state": issue.state,
    }


def _pr_payload(pull_request: PullRequest) -> dict:
    return {
        "number": pull_request.number,
        "title": pull_request.title,
        "headRefName": pull_request.head_ref_name,
        "body": pull_request.body,
    }


def _queue_runner(
    *,
    ready_issues=(),
    in_progress_issues=(),
    all_issues=(),
    open_prs=(),
    calls: list[tuple[str, ...]] | None = None,
):
    command_calls = calls if calls is not None else []

    def runner(command):
        command_tuple = tuple(command)
        command_calls.append(command_tuple)
        if command_tuple[1:3] == ("issue", "list") and "status:ready" in command_tuple:
            return json.dumps([_issue_payload(issue) for issue in ready_issues])
        if command_tuple[1:3] == ("issue", "list") and "status:in-progress" in command_tuple:
            return json.dumps([_issue_payload(issue) for issue in in_progress_issues])
        if command_tuple[1:3] == ("issue", "list"):
            return json.dumps([_issue_payload(issue) for issue in all_issues])
        if command_tuple[1:3] == ("pr", "list"):
            return json.dumps([_pr_payload(pr) for pr in open_prs])
        if command_tuple[1:3] == ("issue", "edit"):
            return ""
        raise AssertionError(command)

    return runner


def _assert_no_forbidden_commands(calls: list[tuple[str, ...]]) -> None:
    forbidden_words = {
        "merge",
        "review",
        "close",
        "delete",
        "worktree",
        "codex",
    }
    for call in calls:
        joined = " ".join(call).lower()
        assert not any(word in joined for word in forbidden_words), call


def test_parse_task_id_and_dependency_list() -> None:
    body = "Task ID: OPS-015\nDepends on: OPS-014, PY-002\n"

    assert parse_task_id(body) == "OPS-015"
    assert parse_task_list(body, "Depends on") == ("OPS-014", "PY-002")


def test_selects_highest_priority_lane_then_lowest_issue_number() -> None:
    ops_ready = _issue(405, "OPS-015", "ops", "ready", depends_on="OPS-014")
    ops_ready_higher = _issue(410, "OPS-016", "ops", "ready", depends_on="OPS-014")
    python_ready = _issue(399, "PY-010", "python", "ready", depends_on="OPS-014")
    dependency = _issue(344, "OPS-014", "ops", "merged")

    outcome = select_handoff_package(
        _state(
            ready_issues=(python_ready, ops_ready_higher, ops_ready),
            all_issues=(python_ready, ops_ready_higher, ops_ready, dependency),
        ),
        repository="example/repo",
    )

    assert outcome.blockers == ()
    assert outcome.package is not None
    assert outcome.package.selected_issue_number == 405
    assert outcome.package.selected_prompt_template == "ops workflow/automation"
    assert "Repository: example/repo" in outcome.package.generated_prompt


def test_blocks_when_open_task_pr_exists() -> None:
    ready = _issue(405, "OPS-015", "ops", "ready")
    task_pr = PullRequest(
        number=404,
        title="OPS-014: Agent dispatch handoff model",
        head_ref_name="feature/ops-014-agent-dispatch-handoff",
        body="Task-ID: OPS-014\nTask-Issue: #344",
    )

    outcome = select_handoff_package(_state(ready_issues=(ready,), all_issues=(ready,), open_prs=(task_pr,)))

    assert outcome.package is None
    assert "Open task PR blocks dispatch" in outcome.blockers[0]


def test_blocks_when_in_progress_issue_exists() -> None:
    ready = _issue(405, "OPS-015", "ops", "ready")
    active = _issue(406, "OPS-016", "ops", "in-progress")

    outcome = select_handoff_package(
        _state(ready_issues=(ready,), in_progress_issues=(active,), all_issues=(ready, active))
    )

    assert outcome.package is None
    assert "status:in-progress issue blocks dispatch" in outcome.blockers[0]


def test_blocks_when_dependency_issue_is_missing() -> None:
    ready = _issue(405, "OPS-015", "ops", "ready", depends_on="OPS-014")

    outcome = select_handoff_package(_state(ready_issues=(ready,), all_issues=(ready,)))

    assert outcome.package is None
    assert outcome.blockers == ("Dependency issue not found for OPS-014.",)


def test_blocks_when_dependency_is_not_merged() -> None:
    ready = _issue(405, "OPS-015", "ops", "ready", depends_on="OPS-014")
    dependency = _issue(344, "OPS-014", "ops", "in-review")

    outcome = select_handoff_package(_state(ready_issues=(ready,), all_issues=(ready, dependency)))

    assert outcome.package is None
    assert outcome.blockers == ("Dependency OPS-014 is status:in-review, not status:merged.",)


def test_prompt_template_categories_cover_expected_lanes() -> None:
    assert select_prompt_template(_issue(1, "OPS-001", "ops", "ready")) == "ops workflow/automation"
    assert (
        select_prompt_template(_issue(2, "PY-001", "python", "ready"))
        == "python source discovery boundary"
    )
    assert (
        select_prompt_template(
            _issue(3, "PY-002", "python", "ready", title="[PY-002] Download execution")
        )
        == "python source download execution"
    )
    assert (
        select_prompt_template(_issue(4, "DN-001", "dotnet", "ready"))
        == "dotnet source discovery boundary"
    )
    assert (
        select_prompt_template(
            _issue(5, "DN-002", "dotnet", "ready", title="[DN-002] Repository contract")
        )
        == "dotnet repository contract"
    )
    assert select_prompt_template(_issue(6, "PT-001", "parity", "ready")) == "parity review"


def test_handoff_package_contains_required_prompt_and_footer() -> None:
    ready = _issue(
        405,
        "OPS-015",
        "ops",
        "ready",
        title="[OPS-015] Read-only agent dispatch handoff reporter",
        depends_on="OPS-014",
    )
    dependency = _issue(344, "OPS-014", "ops", "merged")
    task_index = {"OPS-014": dependency, "OPS-015": ready}

    package = build_handoff_package(ready, task_index)

    assert package.required_pr_footer == "Task-ID: OPS-015\nTask-Issue: #405"
    assert package.expected_branch_name_pattern == (
        "feature/ops-015-read-only-agent-dispatch-handoff-reporter"
    )
    assert "Repository: ktalpay/CarbonOps-Parser" in package.generated_prompt
    assert "Base branch: develop" in package.generated_prompt
    assert "Issue: #405" in package.generated_prompt
    assert "## PR Fallback Report Requirement" in package.generated_prompt
    assert "Do not delete worktrees." in package.generated_prompt


def test_report_embeds_prompt_when_artifact_is_not_written() -> None:
    ready = _issue(405, "OPS-015", "ops", "ready")
    outcome = select_handoff_package(_state(ready_issues=(ready,), all_issues=(ready,)))

    report = build_report(outcome)

    assert "## Generated Prompt" in report
    assert "Task-ID: OPS-015" in report
    assert "Read-only safety" in report


def test_write_prompt_artifact_uses_safe_generated_path(tmp_path: Path) -> None:
    ready = _issue(405, "OPS-015", "ops", "ready")
    package = build_handoff_package(ready, {"OPS-015": ready})

    updated = write_prompt_artifact(package, tmp_path / ".agent-handoff")

    assert updated.artifact_path == tmp_path / ".agent-handoff" / "OPS-015-405-prompt.md"
    assert updated.artifact_path.read_text(encoding="utf-8").startswith("# Codex Handoff Prompt")


def test_load_queue_state_uses_read_only_gh_commands() -> None:
    calls: list[tuple[str, ...]] = []

    def runner(command):
        calls.append(tuple(command))
        if command[1:3] == ("issue", "list") and "status:ready" in command:
            return '[{"number":405,"title":"[OPS-015] Ready","body":"Task ID: OPS-015","labels":[{"name":"status:ready"}],"state":"OPEN"}]'
        if command[1:3] == ("issue", "list") and "status:in-progress" in command:
            return "[]"
        if command[1:3] == ("issue", "list"):
            return "[]"
        if command[1:3] == ("pr", "list"):
            return "[]"
        raise AssertionError(command)

    state = load_queue_state("ktalpay/CarbonOps-Parser", runner=runner)

    assert state.ready_issues[0].number == 405
    assert all("edit" not in call and "merge" not in call and "review" not in call for call in calls)


def test_expected_branch_name_is_deterministic() -> None:
    assert expected_branch_name("OPS-015", "[OPS-015] Read-only agent dispatch handoff reporter") == (
        "feature/ops-015-read-only-agent-dispatch-handoff-reporter"
    )


def test_dry_run_performs_no_mutation_commands(tmp_path: Path) -> None:
    ready = _issue(407, "OPS-016", "ops", "ready", depends_on="OPS-015")
    dependency = _issue(405, "OPS-015", "ops", "merged")
    calls: list[tuple[str, ...]] = []

    exit_code, report = run_reporter(
        ["--repo", "example/repo", "--dry-run", "--artifact-dir", str(tmp_path)],
        runner=_queue_runner(
            ready_issues=(ready,),
            all_issues=(ready, dependency),
            calls=calls,
        ),
    )

    assert exit_code == 0
    assert "Read-only safety" in report
    assert not any(call[1:3] == ("issue", "edit") for call in calls)
    assert not list(tmp_path.iterdir())
    _assert_no_forbidden_commands(calls)


def test_dry_run_and_claim_conflict_fails_before_mutation(tmp_path: Path, capsys) -> None:
    ready = _issue(407, "OPS-016", "ops", "ready", depends_on="OPS-015")
    dependency = _issue(405, "OPS-015", "ops", "merged")
    calls: list[tuple[str, ...]] = []

    with pytest.raises(SystemExit) as exc_info:
        run_reporter(
            [
                "--repo",
                "example/repo",
                "--dry-run",
                "--claim",
                "--artifact-dir",
                str(tmp_path),
            ],
            runner=_queue_runner(
                ready_issues=(ready,),
                all_issues=(ready, dependency),
                calls=calls,
            ),
        )

    assert exc_info.value.code == 2
    assert "--dry-run and --claim cannot be used together." in capsys.readouterr().err
    assert calls == []


def test_claim_mode_emits_expected_issue_edit_command(tmp_path: Path) -> None:
    ready = _issue(
        407,
        "OPS-016",
        "ops",
        "ready",
        title="[OPS-016] Agent dispatch claim-and-prompt mode",
        depends_on="OPS-015",
    )
    dependency = _issue(405, "OPS-015", "ops", "merged")
    calls: list[tuple[str, ...]] = []

    exit_code, report = run_reporter(
        ["--repo", "example/repo", "--claim", "--artifact-dir", str(tmp_path / ".agent-handoff")],
        runner=_queue_runner(
            ready_issues=(ready,),
            all_issues=(ready, dependency),
            calls=calls,
        ),
    )

    assert exit_code == 0
    assert (
        "gh",
        "issue",
        "edit",
        "407",
        "--repo",
        "example/repo",
        "--remove-label",
        "status:ready",
        "--add-label",
        "status:in-progress",
    ) in calls
    assert "## Label Mutation Performed" in report
    assert "- Removed label: `status:ready`" in report
    assert "- Added label: `status:in-progress`" in report
    assert "Prompt artifact:" in report
    assert (tmp_path / ".agent-handoff" / "OPS-016-407-prompt.md").exists()
    _assert_no_forbidden_commands(calls)


def test_claim_mode_refuses_when_open_pr_exists(tmp_path: Path) -> None:
    ready = _issue(407, "OPS-016", "ops", "ready", depends_on="OPS-015")
    dependency = _issue(405, "OPS-015", "ops", "merged")
    task_pr = PullRequest(
        number=406,
        title="OPS-015: Read-only agent dispatch handoff reporter",
        head_ref_name="feature/ops-015-dispatch-handoff-reporter",
        body="Task-ID: OPS-015\nTask-Issue: #405",
    )
    calls: list[tuple[str, ...]] = []

    exit_code, report = run_reporter(
        ["--repo", "example/repo", "--claim", "--artifact-dir", str(tmp_path)],
        runner=_queue_runner(
            ready_issues=(ready,),
            all_issues=(ready, dependency),
            open_prs=(task_pr,),
            calls=calls,
        ),
    )

    assert exit_code == 2
    assert "Open task PR blocks dispatch" in report
    assert not any(call[1:3] == ("issue", "edit") for call in calls)


def test_claim_mode_refuses_when_in_progress_exists(tmp_path: Path) -> None:
    ready = _issue(407, "OPS-016", "ops", "ready", depends_on="OPS-015")
    dependency = _issue(405, "OPS-015", "ops", "merged")
    active = _issue(408, "OPS-017", "ops", "in-progress")
    calls: list[tuple[str, ...]] = []

    exit_code, report = run_reporter(
        ["--repo", "example/repo", "--claim", "--artifact-dir", str(tmp_path)],
        runner=_queue_runner(
            ready_issues=(ready,),
            in_progress_issues=(active,),
            all_issues=(ready, dependency, active),
            calls=calls,
        ),
    )

    assert exit_code == 2
    assert "status:in-progress issue blocks dispatch" in report
    assert not any(call[1:3] == ("issue", "edit") for call in calls)


def test_claim_mode_refuses_when_dependency_missing_or_not_merged(tmp_path: Path) -> None:
    missing_dependency_ready = _issue(407, "OPS-016", "ops", "ready", depends_on="OPS-015")
    calls_missing: list[tuple[str, ...]] = []

    missing_exit_code, missing_report = run_reporter(
        ["--repo", "example/repo", "--claim", "--artifact-dir", str(tmp_path / "missing")],
        runner=_queue_runner(
            ready_issues=(missing_dependency_ready,),
            all_issues=(missing_dependency_ready,),
            calls=calls_missing,
        ),
    )

    assert missing_exit_code == 2
    assert "Dependency issue not found for OPS-015." in missing_report
    assert not any(call[1:3] == ("issue", "edit") for call in calls_missing)

    not_merged_ready = _issue(407, "OPS-016", "ops", "ready", depends_on="OPS-015")
    not_merged_dependency = _issue(405, "OPS-015", "ops", "in-review")
    calls_not_merged: list[tuple[str, ...]] = []

    not_merged_exit_code, not_merged_report = run_reporter(
        ["--repo", "example/repo", "--claim", "--artifact-dir", str(tmp_path / "not-merged")],
        runner=_queue_runner(
            ready_issues=(not_merged_ready,),
            all_issues=(not_merged_ready, not_merged_dependency),
            calls=calls_not_merged,
        ),
    )

    assert not_merged_exit_code == 2
    assert "Dependency OPS-015 is status:in-review, not status:merged." in not_merged_report
    assert not any(call[1:3] == ("issue", "edit") for call in calls_not_merged)


def test_claim_mode_claims_exactly_one_issue_by_lane_priority_and_number(tmp_path: Path) -> None:
    ops_ready = _issue(407, "OPS-016", "ops", "ready", depends_on="OPS-015")
    later_ops_ready = _issue(409, "OPS-018", "ops", "ready", depends_on="OPS-015")
    python_ready = _issue(300, "PY-020", "python", "ready", depends_on="OPS-015")
    dependency = _issue(405, "OPS-015", "ops", "merged")
    calls: list[tuple[str, ...]] = []

    exit_code, report = run_reporter(
        ["--repo", "example/repo", "--claim", "--artifact-dir", str(tmp_path)],
        runner=_queue_runner(
            ready_issues=(python_ready, later_ops_ready, ops_ready),
            all_issues=(python_ready, later_ops_ready, ops_ready, dependency),
            calls=calls,
        ),
    )

    issue_edit_calls = [call for call in calls if call[1:3] == ("issue", "edit")]
    assert exit_code == 0
    assert len(issue_edit_calls) == 1
    assert issue_edit_calls[0][3] == "407"
    assert "Selected issue number: #407" in report


def test_claim_mode_generated_prompt_includes_required_footer(tmp_path: Path) -> None:
    ready = _issue(407, "OPS-016", "ops", "ready", depends_on="OPS-015")
    dependency = _issue(405, "OPS-015", "ops", "merged")

    exit_code, report = run_reporter(
        ["--repo", "example/repo", "--claim", "--artifact-dir", str(tmp_path)],
        runner=_queue_runner(ready_issues=(ready,), all_issues=(ready, dependency)),
    )

    prompt_path = tmp_path / "OPS-016-407-prompt.md"
    prompt = prompt_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert "Task-ID: OPS-016" in report
    assert "Task-Issue: #407" in report
    assert "Task-ID: OPS-016" in prompt
    assert "Task-Issue: #407" in prompt


def test_handoff_mode_reports_prompt_artifact_for_one_in_progress_issue(tmp_path: Path) -> None:
    claimed = _issue(
        409,
        "OPS-017",
        "ops",
        "in-progress",
        title="[OPS-017] Local Codex handoff invocation adapter",
        depends_on="OPS-016",
    )
    dependency = _issue(407, "OPS-016", "ops", "merged")
    calls: list[tuple[str, ...]] = []

    exit_code, report = run_reporter(
        ["--repo", "example/repo", "--handoff", "--artifact-dir", str(tmp_path)],
        runner=_queue_runner(
            in_progress_issues=(claimed,),
            all_issues=(claimed, dependency),
            calls=calls,
        ),
    )

    prompt_path = tmp_path / "OPS-017-409-prompt.md"
    assert exit_code == 0
    assert prompt_path.exists()
    assert "## Handoff Status\nready-for-manual-handoff" in report
    assert "Selected issue number: #409" in report
    assert "Task-ID: OPS-017" in report
    assert "Prompt artifact path:" in report
    assert "local Codex invocation unsupported; use generated prompt artifact manually." in report
    assert "Start the local Codex session" in report
    assert not any(call[1:3] == ("issue", "edit") for call in calls)
    _assert_no_forbidden_commands(calls)


def test_handoff_mode_refuses_without_in_progress_issue(tmp_path: Path) -> None:
    calls: list[tuple[str, ...]] = []

    exit_code, report = run_reporter(
        ["--repo", "example/repo", "--handoff", "--artifact-dir", str(tmp_path)],
        runner=_queue_runner(calls=calls),
    )

    assert exit_code == 2
    assert "No status:in-progress issue is available for handoff." in report
    assert not list(tmp_path.iterdir())
    assert not any(call[1:3] == ("issue", "edit") for call in calls)


def test_handoff_mode_refuses_multiple_in_progress_without_explicit_issue(tmp_path: Path) -> None:
    first = _issue(409, "OPS-017", "ops", "in-progress", depends_on="OPS-016")
    second = _issue(410, "OPS-018", "ops", "in-progress", depends_on="OPS-016")
    dependency = _issue(407, "OPS-016", "ops", "merged")
    calls: list[tuple[str, ...]] = []

    exit_code, report = run_reporter(
        ["--repo", "example/repo", "--handoff", "--artifact-dir", str(tmp_path)],
        runner=_queue_runner(
            in_progress_issues=(second, first),
            all_issues=(first, second, dependency),
            calls=calls,
        ),
    )

    assert exit_code == 2
    assert "Multiple status:in-progress issues exist" in report
    assert "#409 OPS-017" in report
    assert "#410 OPS-018" in report
    assert not list(tmp_path.iterdir())
    assert not any(call[1:3] == ("issue", "edit") for call in calls)


def test_handoff_mode_refuses_explicit_issue_when_multiple_in_progress_exist(tmp_path: Path) -> None:
    first = _issue(409, "OPS-017", "ops", "in-progress", depends_on="OPS-016")
    second = _issue(410, "OPS-018", "ops", "in-progress", depends_on="OPS-016")
    dependency = _issue(407, "OPS-016", "ops", "merged")
    calls: list[tuple[str, ...]] = []

    exit_code, report = run_reporter(
        ["--repo", "example/repo", "--handoff", "--issue", "410", "--artifact-dir", str(tmp_path)],
        runner=_queue_runner(
            in_progress_issues=(first, second),
            all_issues=(first, second, dependency),
            calls=calls,
        ),
    )

    assert exit_code == 2
    assert "Multiple status:in-progress issues exist" in report
    assert not (tmp_path / "OPS-018-410-prompt.md").exists()
    assert not any(call[1:3] == ("issue", "edit") for call in calls)


def test_handoff_mode_accepts_explicit_issue_when_single_claimed_issue_matches(tmp_path: Path) -> None:
    claimed = _issue(409, "OPS-017", "ops", "in-progress", depends_on="OPS-016")
    dependency = _issue(407, "OPS-016", "ops", "merged")
    calls: list[tuple[str, ...]] = []

    exit_code, report = run_reporter(
        ["--repo", "example/repo", "--handoff", "--issue", "409", "--artifact-dir", str(tmp_path)],
        runner=_queue_runner(
            in_progress_issues=(claimed,),
            all_issues=(claimed, dependency),
            calls=calls,
        ),
    )

    assert exit_code == 0
    assert "Selected issue number: #409" in report
    assert (tmp_path / "OPS-017-409-prompt.md").exists()
    assert not any(call[1:3] == ("issue", "edit") for call in calls)
    _assert_no_forbidden_commands(calls)


def test_handoff_mode_refuses_explicit_issue_when_single_claimed_issue_differs(tmp_path: Path) -> None:
    claimed = _issue(409, "OPS-017", "ops", "in-progress", depends_on="OPS-016")
    dependency = _issue(407, "OPS-016", "ops", "merged")
    calls: list[tuple[str, ...]] = []

    exit_code, report = run_reporter(
        ["--repo", "example/repo", "--handoff", "--issue", "410", "--artifact-dir", str(tmp_path)],
        runner=_queue_runner(
            in_progress_issues=(claimed,),
            all_issues=(claimed, dependency),
            calls=calls,
        ),
    )

    assert exit_code == 2
    assert "Explicit issue #410 does not match the single claimed status:in-progress issue #409." in report
    assert not list(tmp_path.iterdir())
    assert not any(call[1:3] == ("issue", "edit") for call in calls)


def test_handoff_invoke_fails_closed_as_unsupported(tmp_path: Path) -> None:
    claimed = _issue(409, "OPS-017", "ops", "in-progress", depends_on="OPS-016")
    dependency = _issue(407, "OPS-016", "ops", "merged")
    calls: list[tuple[str, ...]] = []

    exit_code, report = run_reporter(
        ["--repo", "example/repo", "--handoff", "--invoke", "--artifact-dir", str(tmp_path)],
        runner=_queue_runner(
            in_progress_issues=(claimed,),
            all_issues=(claimed, dependency),
            calls=calls,
        ),
    )

    assert exit_code == 2
    assert "local Codex invocation unsupported; use generated prompt artifact manually." in report
    assert (tmp_path / "OPS-017-409-prompt.md").exists()
    assert not any(call[1:3] == ("issue", "edit") for call in calls)
    _assert_no_forbidden_commands(calls)


def test_invoke_without_handoff_fails_before_commands() -> None:
    calls: list[tuple[str, ...]] = []

    exit_code, report = run_reporter(
        ["--repo", "example/repo", "--invoke"],
        runner=_queue_runner(calls=calls),
    )

    assert exit_code == 2
    assert "--invoke requires --handoff" in report
    assert calls == []
