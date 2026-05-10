from __future__ import annotations

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_DOC_PATH = REPOSITORY_ROOT / "docs" / "postgresql-runtime-readiness-checkpoint.md"
DOCS_INDEX_PATH = REPOSITORY_ROOT / "docs" / "index.md"


def test_checkpoint_doc_exists_and_declares_blocked_status() -> None:
    text = CHECKPOINT_DOC_PATH.read_text(encoding="utf-8")

    assert "# PostgreSQL Runtime Readiness Checkpoint" in text
    assert "Task: DB-049" in text
    assert "Issue: #354" in text
    assert "Status: blocked" in text
    assert "**NO-GO**" in text


def test_checkpoint_doc_keeps_documentation_only_scope() -> None:
    text = CHECKPOINT_DOC_PATH.read_text(encoding="utf-8")
    normalized = " ".join(text.split())

    assert "documentation-only" in normalized
    assert "does **not**" in text
    assert "add, enable, or execute PostgreSQL runtime behavior" in text


def test_docs_index_links_checkpoint_doc() -> None:
    index_text = DOCS_INDEX_PATH.read_text(encoding="utf-8")

    assert "[PostgreSQL Runtime Readiness Checkpoint](postgresql-runtime-readiness-checkpoint.md)" in index_text
