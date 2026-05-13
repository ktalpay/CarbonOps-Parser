#!/usr/bin/env python3
"""Process merged task PRs and maintain deterministic task status labels."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Sequence

try:
    from scripts.agent_task_status import (
        SUPPORTED_TASK_STATUS_LABELS,
        TaskStatusReplacement,
        replace_task_status,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from agent_task_status import (  # type: ignore[no-redef]
        SUPPORTED_TASK_STATUS_LABELS,
        TaskStatusReplacement,
        replace_task_status,
    )

SUPPORTED_STATUS_LABELS = SUPPORTED_TASK_STATUS_LABELS

TASK_ID_PATTERN = re.compile(r"\b([A-Za-z]+-[0-9][0-9A-Za-z-]*)\b")
TASK_ID_FOOTER_PATTERN = re.compile(
    r"^[ \t]*Task-ID:[ \t]*([A-Za-z]+-[0-9][0-9A-Za-z-]*)[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)
TASK_ISSUE_FOOTER_PATTERN = re.compile(
    r"^[ \t]*Task-Issue:[ \t]*#?([0-9]+)[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)


CommandRunner = Callable[[Sequence[str]], str]


@dataclass(frozen=True)
class Issue:
    number: int
    title: str
    body: str
    labels: tuple[str, ...]
    state: str = "OPEN"


@dataclass(frozen=True)
class PullRequest:
    number: int
    title: str
    body: str
    merged: bool


StatusReplacement = TaskStatusReplacement


@dataclass(frozen=True)
class WatcherResult:
    task_id: str
    task_issue_number: int
    task_status: StatusReplacement
    updated_downstream: tuple[StatusReplacement, ...]
    skipped_downstream: tuple[str, ...]


class WatcherError(RuntimeError):
    """Raised for expected watcher failures with clear diagnostics."""


class CommandError(WatcherError):
    def __init__(self, command: Sequence[str], returncode: int, message: str) -> None:
        super().__init__(f"Command failed ({returncode}): {' '.join(command)}\n{message}")


def run_command(command: Sequence[str]) -> str:
    completed = subprocess.run(
        list(command),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise CommandError(command, completed.returncode, message)
    return completed.stdout


def labels_from_gh(raw_labels: object) -> tuple[str, ...]:
    if not isinstance(raw_labels, list):
        return ()
    labels: list[str] = []
    for raw_label in raw_labels:
        if isinstance(raw_label, dict) and isinstance(raw_label.get("name"), str):
            labels.append(raw_label["name"])
        elif isinstance(raw_label, str):
            labels.append(raw_label)
    return tuple(labels)


def parse_issue(raw_issue: dict[str, object]) -> Issue:
    return Issue(
        number=int(raw_issue["number"]),
        title=str(raw_issue.get("title") or ""),
        body=str(raw_issue.get("body") or ""),
        labels=labels_from_gh(raw_issue.get("labels")),
        state=str(raw_issue.get("state") or "OPEN"),
    )


def parse_pr(raw_pr: dict[str, object]) -> PullRequest:
    merged_at = str(raw_pr.get("mergedAt") or "")
    merged_value = raw_pr.get("merged")
    return PullRequest(
        number=int(raw_pr["number"]),
        title=str(raw_pr.get("title") or ""),
        body=str(raw_pr.get("body") or ""),
        merged=bool(merged_value) or bool(merged_at),
    )


class GitHubClient:
    def __init__(self, repo: str, runner: CommandRunner = run_command) -> None:
        self.repo = repo
        self.runner = runner

    def view_pr(self, pr_number: int) -> PullRequest:
        output = self.runner(
            (
                "gh",
                "pr",
                "view",
                str(pr_number),
                "--repo",
                self.repo,
                "--json",
                "number,title,body,mergedAt",
            )
        )
        try:
            raw_pr = json.loads(output)
        except json.JSONDecodeError as exc:
            raise WatcherError(f"gh pr view returned invalid JSON for PR #{pr_number}.") from exc
        if not isinstance(raw_pr, dict):
            raise WatcherError(f"gh pr view returned unexpected JSON for PR #{pr_number}.")
        return parse_pr(raw_pr)

    def view_issue(self, issue_number: int) -> Issue:
        output = self.runner(
            (
                "gh",
                "issue",
                "view",
                str(issue_number),
                "--repo",
                self.repo,
                "--json",
                "number,title,body,labels,state",
            )
        )
        try:
            raw_issue = json.loads(output)
        except json.JSONDecodeError as exc:
            raise WatcherError(f"gh issue view returned invalid JSON for issue #{issue_number}.") from exc
        if not isinstance(raw_issue, dict):
            raise WatcherError(f"gh issue view returned unexpected JSON for issue #{issue_number}.")
        return parse_issue(raw_issue)

    def find_issue_for_task(self, task_id: str) -> int | None:
        output = self.runner(
            (
                "gh",
                "issue",
                "list",
                "--repo",
                self.repo,
                "--state",
                "all",
                "--search",
                f"{task_id} in:title",
                "--json",
                "number,title",
                "--limit",
                "100",
            )
        )
        try:
            raw_issues = json.loads(output)
        except json.JSONDecodeError as exc:
            raise WatcherError(f"gh issue list returned invalid JSON while resolving {task_id}.") from exc
        if not isinstance(raw_issues, list):
            raise WatcherError(f"gh issue list returned unexpected JSON while resolving {task_id}.")
        prefix = f"[{task_id}]"
        matches = [
            int(issue["number"])
            for issue in raw_issues
            if isinstance(issue, dict) and str(issue.get("title") or "").startswith(prefix)
        ]
        if len(matches) == 1:
            return matches[0]
        return None

    def add_label(self, issue_number: int, label: str) -> None:
        self.runner(("gh", "issue", "edit", str(issue_number), "--repo", self.repo, "--add-label", label))

    def remove_label(self, issue_number: int, label: str) -> None:
        self.runner(("gh", "issue", "edit", str(issue_number), "--repo", self.repo, "--remove-label", label))

    def edit_body(self, issue_number: int, body: str) -> None:
        self.runner(("gh", "issue", "edit", str(issue_number), "--repo", self.repo, "--body", body))

    def comment(self, issue_number: int, body: str) -> None:
        self.runner(("gh", "issue", "comment", str(issue_number), "--repo", self.repo, "--body", body))


def parse_task_id(value: str) -> str | None:
    footer_matches = TASK_ID_FOOTER_PATTERN.findall(value)
    if footer_matches:
        return footer_matches[-1].upper()
    title_match = TASK_ID_PATTERN.search(value)
    if title_match:
        return title_match.group(1).upper()
    return None


def parse_task_issue_number(value: str) -> int | None:
    footer_matches = TASK_ISSUE_FOOTER_PATTERN.findall(value)
    if footer_matches:
        return int(footer_matches[-1])
    return None


def extract_field(field_name: str, body: str) -> str | None:
    needle = f"{field_name}:".lower()
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line.lower().startswith(needle):
            return line[len(needle) :].strip()
    return None


def parse_task_list(raw_value: str | None) -> tuple[str, ...]:
    if raw_value is None:
        return ()
    task_ids: list[str] = []
    for raw_part in raw_value.split(","):
        value = raw_part.strip()
        if not value or value.lower() in {"none", "n/a"} or value == "-":
            continue
        task_ids.append(value.upper())
    return tuple(task_ids)


def replace_status_label(client: GitHubClient, issue: Issue, new_status: str) -> StatusReplacement:
    try:
        return replace_task_status(
            client,
            issue_number=issue.number,
            labels=issue.labels,
            body=issue.body,
            new_status=new_status,
        )
    except ValueError as exc:
        raise WatcherError(str(exc)) from exc


def resolve_task_issue(client: GitHubClient, pull_request: PullRequest) -> tuple[str, Issue]:
    body_task_id = parse_task_id(pull_request.body)
    title_task_id = parse_task_id(pull_request.title)
    task_issue_number = parse_task_issue_number(pull_request.body)

    if task_issue_number is not None:
        issue = client.view_issue(task_issue_number)
        task_id = body_task_id or parse_task_id(issue.body) or parse_task_id(issue.title) or title_task_id
    else:
        task_id = body_task_id or title_task_id
        if task_id is None:
            raise WatcherError(
                f"PR #{pull_request.number} has no Task-Issue footer and no Task-ID/title task id; "
                "no task issue could be resolved."
            )
        task_issue_number = client.find_issue_for_task(task_id)
        if task_issue_number is None:
            raise WatcherError(
                f"PR #{pull_request.number} task {task_id} did not resolve to one unique issue."
            )
        issue = client.view_issue(task_issue_number)

    if task_id is None:
        raise WatcherError(
            f"PR #{pull_request.number} resolved issue #{issue.number}, but no Task-ID was found."
        )
    return task_id, issue


def evaluate_downstream(
    client: GitHubClient,
    source_issue: Issue,
    source_task_id: str,
    pr_number: int,
) -> tuple[tuple[StatusReplacement, ...], tuple[str, ...]]:
    updated: list[StatusReplacement] = []
    skipped: list[str] = []

    for dependent_task_id in parse_task_list(extract_field("Unblocks", source_issue.body)):
        dependent_issue_number = client.find_issue_for_task(dependent_task_id)
        if dependent_issue_number is None:
            skipped.append(
                f"`{dependent_task_id}` skipped: no unique issue title beginning "
                f"with `[{dependent_task_id}]` was found."
            )
            continue

        dependent_issue = client.view_issue(dependent_issue_number)
        depends_on = extract_field("Depends on", dependent_issue.body)
        if depends_on is None:
            replacement = replace_status_label(client, dependent_issue, "status:needs-attention")
            updated.append(replacement)
            skipped.append(
                f"`{dependent_task_id}` (#{dependent_issue_number}) needs attention: "
                "missing `Depends on:` metadata."
            )
            continue

        missing_dependencies: list[str] = []
        unresolved_dependencies: list[str] = []
        for dependency_task_id in parse_task_list(depends_on):
            dependency_issue_number = client.find_issue_for_task(dependency_task_id)
            if dependency_issue_number is None:
                unresolved_dependencies.append(dependency_task_id)
                continue
            dependency_issue = client.view_issue(dependency_issue_number)
            if "status:merged" not in dependency_issue.labels:
                missing_dependencies.append(dependency_task_id)

        if unresolved_dependencies:
            unresolved = ", ".join(f"`{task_id}`" for task_id in unresolved_dependencies)
            replacement = replace_status_label(client, dependent_issue, "status:needs-attention")
            updated.append(replacement)
            skipped.append(
                f"`{dependent_task_id}` (#{dependent_issue_number}) needs attention: "
                f"dependencies did not resolve to unique issues: {unresolved}."
            )
            continue

        if missing_dependencies:
            missing = ", ".join(f"`{task_id}`" for task_id in missing_dependencies)
            skipped.append(
                f"`{dependent_task_id}` (#{dependent_issue_number}) skipped: "
                f"dependencies not merged or unresolved: {missing}."
            )
            continue

        if "status:merged" in dependent_issue.labels:
            skipped.append(f"`{dependent_task_id}` (#{dependent_issue_number}) skipped: already `status:merged`.")
            continue

        replacement = replace_status_label(client, dependent_issue, "status:ready")
        updated.append(replacement)
        client.comment(
            dependent_issue_number,
            f"Agent Task Watcher changed status from {format_statuses(replacement.old_statuses)} "
            f"to `status:ready` because `{source_task_id}` merged in PR #{pr_number} "
            "and all declared dependencies are `status:merged`.",
        )

    return tuple(updated), tuple(skipped)


def format_statuses(statuses: Sequence[str]) -> str:
    if not statuses:
        return "`status:missing`"
    return ", ".join(f"`{status}`" for status in statuses)


def build_comment(result: WatcherResult, pr_number: int) -> str:
    lines = [
        "Agent Task Watcher updated task status.",
        "",
        f"Detected task: `{result.task_id}`",
        f"Merged PR: #{pr_number}",
        f"Task issue status: {format_statuses(result.task_status.old_statuses)} -> `{result.task_status.new_status}`",
        "",
        "Downstream task update summary:",
    ]
    if result.updated_downstream:
        lines.append("")
        lines.append("Updated:")
        for replacement in result.updated_downstream:
            lines.append(
                f"- #{replacement.issue_number}: "
                f"{format_statuses(replacement.old_statuses)} -> `{replacement.new_status}`"
            )
    if result.skipped_downstream:
        lines.append("")
        lines.append("Skipped:")
        for skipped in result.skipped_downstream:
            lines.append(f"- {skipped}")
    if not result.updated_downstream and not result.skipped_downstream:
        lines.append("")
        lines.append("No dependent tasks were declared in `Unblocks:`.")
    return "\n".join(lines)


def process_merged_pr(client: GitHubClient, pr_number: int) -> WatcherResult | None:
    pull_request = client.view_pr(pr_number)
    if not pull_request.merged:
        return None

    task_id, issue = resolve_task_issue(client, pull_request)
    task_status = replace_status_label(client, issue, "status:merged")
    refreshed_issue = client.view_issue(issue.number)
    updated_downstream, skipped_downstream = evaluate_downstream(
        client,
        refreshed_issue,
        task_id,
        pull_request.number,
    )
    result = WatcherResult(
        task_id=task_id,
        task_issue_number=issue.number,
        task_status=task_status,
        updated_downstream=updated_downstream,
        skipped_downstream=skipped_downstream,
    )
    client.comment(issue.number, build_comment(result, pull_request.number))
    return result


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr-number", required=True, type=int)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    client = GitHubClient(args.repo)
    try:
        result = process_merged_pr(client, args.pr_number)
    except WatcherError as exc:
        print(f"Agent Task Watcher error: {exc}", file=sys.stderr)
        return 1
    if result is None:
        print(f"PR #{args.pr_number} is not merged. No action taken.")
        return 0
    ready_count = sum(
        1 for replacement in result.updated_downstream if replacement.new_status == "status:ready"
    )
    print(
        f"Processed PR #{args.pr_number}: task {result.task_id} issue #{result.task_issue_number} "
        f"marked status:merged; {ready_count} ready downstream update(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
