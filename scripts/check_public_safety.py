#!/usr/bin/env python3
"""Local public wording and remote-reference safety check."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


SKIPPED_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "venv",
}

SKIPPED_FILES = {
    Path("scripts/check_public_safety.py"),
}


@dataclass(frozen=True)
class PatternRule:
    category: str
    name: str
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class Finding:
    path: Path
    line_number: int
    category: str
    pattern_name: str
    line: str


def phrase_pattern(*words: str) -> re.Pattern[str]:
    return re.compile(
        r"\b" + r"\s+".join(re.escape(word) for word in words) + r"\b",
        re.IGNORECASE,
    )


def word_pattern(word: str) -> re.Pattern[str]:
    return re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)


SENSITIVE_ASSIGNMENT_PATTERN = re.compile(
    r"\b(?:"
    + "|".join(("api[_-]?key", "sec" + "ret", "tok" + "en", "pass" + "word"))
    + r")\s*=",
    re.IGNORECASE,
)

README_BADGE_PREFIX = "https" + "://img.shields.io/"
APACHE_LICENSE_PREFIX = "http" + "://www.apache.org/licenses/"
SVG_NAMESPACE = "http" + "://www.w3.org/2000/svg"
EXAMPLE_CONFIG_PREFIX = "https" + "://example.org/"
TEST_PLACEHOLDER_PREFIX = "https" + "://example.invalid/"


PATTERN_RULES = (
    PatternRule(
        category="public claim risk",
        name="readiness claim",
        pattern=re.compile(r"\bproduction[- ]ready\b", re.IGNORECASE),
    ),
    PatternRule(
        category="public claim risk",
        name="public claim 1",
        pattern=phrase_pattern("compliance", "guaranteed"),
    ),
    PatternRule(
        category="public claim risk",
        name="public claim 2",
        pattern=phrase_pattern("legally", "compliant"),
    ),
    PatternRule(
        category="public claim risk",
        name="public claim 3",
        pattern=phrase_pattern("certified", "carbon", "accounting"),
    ),
    PatternRule(
        category="public claim risk",
        name="public claim 4",
        pattern=phrase_pattern("official", "validation"),
    ),
    PatternRule(
        category="public claim risk",
        name="public claim 5",
        pattern=phrase_pattern("correctness", "guaranteed"),
    ),
    PatternRule(
        category="restricted wording risk",
        name="restricted phrase 1",
        pattern=phrase_pattern("Global", "Talent", "Visa"),
    ),
    PatternRule(
        category="restricted wording risk",
        name="restricted phrase 2",
        pattern=phrase_pattern("Tech", "Nation", "endor" + "sement"),
    ),
    PatternRule(
        category="restricted wording risk",
        name="restricted word 1",
        pattern=word_pattern("immig" + "ration"),
    ),
    PatternRule(
        category="restricted wording risk",
        name="restricted phrase 3",
        pattern=phrase_pattern("endor" + "sement", "evidence"),
    ),
    PatternRule(
        category="sensitive text risk",
        name="sensitive assignment",
        pattern=SENSITIVE_ASSIGNMENT_PATTERN,
    ),
    PatternRule(
        category="sensitive text risk",
        name="sensitive identity phrase",
        pattern=phrase_pattern("service", "account"),
    ),
    PatternRule(
        category="remote reference risk",
        name="remote URL scheme",
        pattern=re.compile(r"\b(?:https?|ftp)://[^\s)>\"']+", re.IGNORECASE),
    ),
)


def scan_repository(root: Path) -> list[Finding]:
    root = root.resolve()
    findings: list[Finding] = []

    for path in iter_candidate_files(root):
        relative_path = path.relative_to(root)
        text = read_text_file(path)
        if text is None:
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            findings.extend(
                finding
                for finding in scan_line(relative_path, line_number, line)
                if not is_allowed_match(relative_path, line, finding.category)
            )

    return findings


def iter_candidate_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        relative_path = path.relative_to(root)
        if should_skip_path(relative_path):
            continue
        yield path


def should_skip_path(relative_path: Path) -> bool:
    if relative_path in SKIPPED_FILES:
        return True
    return bool(SKIPPED_DIRECTORIES.intersection(relative_path.parts))


def read_text_file(path: Path) -> str | None:
    try:
        content = path.read_bytes()
    except OSError:
        return None

    if b"\x00" in content:
        return None

    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return None


def scan_line(relative_path: Path, line_number: int, line: str) -> list[Finding]:
    findings: list[Finding] = []
    for rule in PATTERN_RULES:
        if rule.pattern.search(line):
            findings.append(
                Finding(
                    path=relative_path,
                    line_number=line_number,
                    category=rule.category,
                    pattern_name=rule.name,
                    line=line.strip(),
                )
            )
    return findings


def is_allowed_match(relative_path: Path, line: str, category: str) -> bool:
    path_text = relative_path.as_posix()

    if category == "sensitive text risk":
        if path_text in {
            "config/carbonops.config.example.yaml",
            "docs/configuration-model.md",
        }:
            return "Password=change-me" in line
        return False

    if category != "remote reference risk":
        return False

    if path_text == "README.md" and README_BADGE_PREFIX in line:
        return True
    if path_text == "LICENSE" and APACHE_LICENSE_PREFIX in line:
        return True
    if path_text == "docs/assets/carbonops-parser-banner.svg":
        return SVG_NAMESPACE in line
    if path_text in {
        "config/carbonops.config.example.yaml",
        "docs/configuration-model.md",
    }:
        return EXAMPLE_CONFIG_PREFIX in line
    if path_text.startswith("tests/") and TEST_PLACEHOLDER_PREFIX in line:
        return True

    return False


def format_findings(findings: Sequence[Finding]) -> str:
    return "\n".join(
        (
            f"{finding.path}:{finding.line_number}: "
            f"{finding.category} ({finding.pattern_name}): {finding.line}"
        )
        for finding in findings
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    root = Path(args[0]) if args else Path.cwd()
    findings = scan_repository(root)

    if findings:
        print(format_findings(findings))
        return 1

    print("Public safety check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
