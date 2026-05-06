from __future__ import annotations

import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TASK_QUEUE_PATH = REPOSITORY_ROOT / "docs" / "codex-runs" / "task-queue.md"

TASK_IDENTIFIER_PATTERN = re.compile(r"^- (CO-[A-Z0-9-]+): .+$")
CURRENT_TASK_IDENTIFIER_PATTERN = re.compile(r"^CO-\d{3}[ABC]$")
COMPLETED_STATUS_PATTERN = re.compile(
    r"^- CO-[A-Z0-9-]+: (Added|Documented|Expanded) .+$"
)


def test_task_queue_file_exists() -> None:
    assert TASK_QUEUE_PATH.is_file()


def test_task_queue_task_identifiers_are_unique() -> None:
    task_identifiers = _extract_task_identifiers(TASK_QUEUE_PATH)

    assert task_identifiers
    assert len(task_identifiers) == len(set(task_identifiers))
    assert any(
        CURRENT_TASK_IDENTIFIER_PATTERN.fullmatch(identifier)
        for identifier in task_identifiers
    )


def test_recent_completed_tasks_are_present() -> None:
    task_identifiers = set(_extract_task_identifiers(TASK_QUEUE_PATH))

    assert {"CO-051A", "CO-051B", "CO-051C"}.issubset(task_identifiers)


def test_completed_task_lines_use_consistent_status_words() -> None:
    completed_lines = _extract_section_lines(TASK_QUEUE_PATH, "Completed")

    assert completed_lines
    assert all(
        COMPLETED_STATUS_PATTERN.fullmatch(line)
        for line in completed_lines
        if line.startswith("- CO-")
    )


def _extract_task_identifiers(path: Path) -> list[str]:
    task_identifiers: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = TASK_IDENTIFIER_PATTERN.fullmatch(line)
        if match is not None:
            task_identifiers.append(match.group(1))
    return task_identifiers


def _extract_section_lines(path: Path, section_name: str) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    section_heading = f"## {section_name}"
    section_lines: list[str] = []
    in_section = False

    for line in lines:
        if line == section_heading:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.strip():
            section_lines.append(line)

    return section_lines
