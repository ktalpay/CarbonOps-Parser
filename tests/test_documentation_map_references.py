from __future__ import annotations

import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_MAP_FILES = (
    REPOSITORY_ROOT / "README.md",
    REPOSITORY_ROOT / "docs" / "index.md",
)
DOCUMENTATION_FILES = tuple(sorted((REPOSITORY_ROOT / "docs").glob("*.md")))

MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
RELATED_DOCUMENTS_HEADING_PATTERN = re.compile(
    r"^(#{2,6})\s+Related Documents\s*$",
    re.IGNORECASE,
)
MARKDOWN_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+")


def test_documentation_map_markdown_references_exist() -> None:
    missing_references = [
        f"{source.relative_to(REPOSITORY_ROOT)} -> {target}"
        for source in DOCUMENTATION_MAP_FILES
        for target in _iter_missing_local_markdown_references(source)
    ]

    assert missing_references == []


def test_related_documents_markdown_references_exist() -> None:
    missing_references = [
        f"{source.relative_to(REPOSITORY_ROOT)} -> {target}"
        for source in DOCUMENTATION_FILES
        for target in _iter_missing_related_documents_references(source)
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
    return _extract_local_markdown_references(source.read_text(encoding="utf-8"))


def _iter_missing_related_documents_references(source: Path) -> list[str]:
    missing_references: list[str] = []
    for section_text in _extract_related_documents_sections(source):
        for reference in _extract_local_markdown_references(section_text):
            resolved_reference = (source.parent / reference).resolve()
            if not resolved_reference.is_file():
                missing_references.append(reference)
    return missing_references


def _extract_related_documents_sections(source: Path) -> list[str]:
    sections: list[str] = []
    lines = source.read_text(encoding="utf-8").splitlines()
    line_index = 0

    while line_index < len(lines):
        heading_match = RELATED_DOCUMENTS_HEADING_PATTERN.match(lines[line_index])
        if heading_match is None:
            line_index += 1
            continue

        heading_level = len(heading_match.group(1))
        section_lines: list[str] = []
        line_index += 1

        while line_index < len(lines):
            next_heading_match = MARKDOWN_HEADING_PATTERN.match(lines[line_index])
            if (
                next_heading_match is not None
                and len(next_heading_match.group(1)) <= heading_level
            ):
                break

            section_lines.append(lines[line_index])
            line_index += 1

        sections.append("\n".join(section_lines))

    return sections


def _extract_local_markdown_references(text: str) -> list[str]:
    references: list[str] = []
    for raw_reference in MARKDOWN_LINK_PATTERN.findall(text):
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
