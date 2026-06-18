"""Shared task issue status mutation helpers for local agent automation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


SUPPORTED_TASK_STATUS_LABELS = (
    "status:blocked",
    "status:ready",
    "status:in-progress",
    "status:merged",
    "status:needs-attention",
)


class TaskStatusClient(Protocol):
    def add_label(self, issue_number: int, label: str) -> None: ...

    def remove_label(self, issue_number: int, label: str) -> None: ...

    def edit_body(self, issue_number: int, body: str) -> None: ...


@dataclass(frozen=True)
class TaskStatusReplacement:
    issue_number: int
    old_statuses: tuple[str, ...]
    new_status: str
    old_body: str
    new_body: str


def status_labels(labels: Sequence[str]) -> tuple[str, ...]:
    return tuple(label for label in labels if label.startswith("status:"))


def bare_status(status_label: str) -> str:
    if status_label not in SUPPORTED_TASK_STATUS_LABELS:
        raise ValueError(f"Unsupported status label: {status_label}")
    return status_label.removeprefix("status:")


def sync_status_body(body: str, status_value: str) -> str:
    lines = body.splitlines()
    keep_trailing_newline = body.endswith("\n")
    replacement_line = f"Status: {status_value}"

    for index, line in enumerate(lines):
        if line.lstrip().lower().startswith("status:"):
            existing_indent = line[: len(line) - len(line.lstrip())]
            lines[index] = f"{existing_indent}{replacement_line}"
            updated = "\n".join(lines)
            return updated + ("\n" if keep_trailing_newline else "")

    insert_at = status_insert_index(lines)
    lines.insert(insert_at, replacement_line)
    updated = "\n".join(lines)
    return updated + ("\n" if keep_trailing_newline else "")


def status_insert_index(lines: Sequence[str]) -> int:
    if not lines:
        return 0

    task_id_index: int | None = None
    lane_index: int | None = None
    last_metadata_index: int | None = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            break
        if ":" not in stripped:
            break
        key = stripped.split(":", 1)[0].strip().lower()
        last_metadata_index = index
        if key in {"task id", "task-id"}:
            task_id_index = index
        elif key == "lane":
            lane_index = index

    if lane_index is not None:
        return lane_index + 1
    if task_id_index is not None:
        return task_id_index + 1
    if last_metadata_index is not None:
        return last_metadata_index + 1
    return 0


def replace_task_status(
    client: TaskStatusClient,
    *,
    issue_number: int,
    labels: Sequence[str],
    body: str,
    new_status: str,
) -> TaskStatusReplacement:
    status_value = bare_status(new_status)
    old_statuses = status_labels(labels)
    new_body = sync_status_body(body, status_value)

    replace_labels = getattr(client, "replace_status_labels", None)
    if callable(replace_labels):
        if old_statuses != (new_status,):
            replace_labels(issue_number, old_statuses, new_status)
    else:
        if new_status not in labels:
            client.add_label(issue_number, new_status)

        for label in old_statuses:
            if label != new_status:
                client.remove_label(issue_number, label)

    if new_body != body:
        client.edit_body(issue_number, new_body)

    return TaskStatusReplacement(
        issue_number=issue_number,
        old_statuses=old_statuses,
        new_status=new_status,
        old_body=body,
        new_body=new_body,
    )
