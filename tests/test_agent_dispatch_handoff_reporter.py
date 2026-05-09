from pathlib import Path

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
