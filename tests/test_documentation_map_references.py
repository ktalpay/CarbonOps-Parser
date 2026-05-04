from __future__ import annotations

import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_MAP_FILES = (
    REPOSITORY_ROOT / "README.md",
    REPOSITORY_ROOT / "docs" / "index.md",
)

MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def test_documentation_map_markdown_references_exist() -> None:
    missing_references = [
        f"{source.relative_to(REPOSITORY_ROOT)} -> {target}"
        for source in DOCUMENTATION_MAP_FILES
        for target in _iter_missing_local_markdown_references(source)
    ]

    assert missing_references == []


def _iter_missing_local_markdown_references(source: Path) -> list[str]:
    missing_references: list[str] = []
    for reference in _iter_local_markdown_references(source):
        resolved_reference = (source.parent / reference).resolve()
        if not resolved_reference.is_file():
            missing_references.append(reference)
    return missing_references


def _iter_local_markdown_references(source: Path) -> list[str]:
    references: list[str] = []
    for raw_reference in MARKDOWN_LINK_PATTERN.findall(source.read_text(encoding="utf-8")):
        reference = _normalize_markdown_reference(raw_reference)
        if reference is not None:
            references.append(reference)
    return references


def _normalize_markdown_reference(raw_reference: str) -> str | None:
    reference = raw_reference.strip()
    if not reference or reference.startswith("#"):
        return None
    if "://" in reference:
        return None

    reference = reference.split("#", 1)[0].strip()
    if not reference.lower().endswith(".md"):
        return None

    return reference
