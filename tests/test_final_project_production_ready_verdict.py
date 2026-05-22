from __future__ import annotations

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VERDICT_PATH = REPOSITORY_ROOT / "docs" / "final-project-production-ready-verdict.md"


def test_final_project_verdict_is_explicitly_not_production_ready() -> None:
    verdict = VERDICT_PATH.read_text(encoding="utf-8")
    normalized = " ".join(verdict.split())

    assert "Project-level production-ready: no." in verdict
    assert "Python runtime production path: yes" in verdict
    assert ".NET runtime production path: no" in normalized
    assert "production parity contract is therefore not satisfied" in normalized
    assert "Do not mark CarbonOps-Parser project-level production-ready." in verdict


def test_final_project_verdict_pins_dotnet_blocker_without_overclaiming() -> None:
    verdict = VERDICT_PATH.read_text(encoding="utf-8")
    normalized = " ".join(verdict.split())

    for marker in (
        "`run-once` command still fails closed",
        "`ingestion_status=not_implemented`",
        "opens no PostgreSQL connection",
        "inserts no records",
        "not an operator-supported production ingestion command",
    ):
        assert marker in normalized

    for forbidden_claim in (
        "Project-level production-ready: yes",
        ".NET runtime production path: yes",
    ):
        assert forbidden_claim not in verdict

    assert "exclude production carbon-accounting correctness" in normalized
    assert "legal or compliance correctness" in normalized


def test_final_project_verdict_lists_required_validation_evidence() -> None:
    verdict = VERDICT_PATH.read_text(encoding="utf-8")

    for marker in (
        "python -m pytest",
        "python scripts/release_validation_gate.py --check-only",
        "python scripts/production_rc_verification.py --output-format json",
        "git diff --check",
        "focused stable .NET production-safety contract tests",
        ".NET Docker PostgreSQL E2E/idempotency tests",
        "Python/.NET persisted PostgreSQL parity validation",
    ):
        assert marker in verdict
