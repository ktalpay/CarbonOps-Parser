from __future__ import annotations

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RUNBOOK_PATH = REPOSITORY_ROOT / "docs" / "production-packaging-operator-runbook.md"


def test_production_packaging_operator_runbook_covers_operator_flow() -> None:
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")

    for heading in (
        "## Install",
        "## Configure",
        "## Validate",
        "## Run",
        "## Stop",
        "## Diagnose",
        "## Failure Recovery",
    ):
        assert heading in runbook

    assert "Dry-run" in runbook
    assert "Local fixture" in runbook
    assert "Isolated integration" in runbook
    assert "Production" in runbook
    assert "Task-ID: OPS-036\nTask-Issue: #498" in runbook


def test_runbook_documents_python_and_dotnet_entrypoint_alignment() -> None:
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")

    assert "carbonops-parser" in runbook
    assert "carbonops-source-acquisition" in runbook
    assert "src/dotnet/CarbonOps.Parser.sln" in runbook
    assert "no Worker Service executable is published yet" in runbook
    assert "CARBONOPS_PARSER_POSTGRES_PASSWORD" in runbook
    assert "Raw PostgreSQL connection strings are rejected" in runbook


def test_runbook_safe_commands_do_not_require_production_secrets() -> None:
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")

    safe_command_markers = (
        "carbonops-source-acquisition validate",
        "carbonops-source-acquisition run --dry-run",
        "carbonops-parser local-dry-run",
        "python -m pytest",
        "git diff --check",
        "dotnet test src/dotnet/CarbonOps.Parser.sln --configuration Release",
    )

    for marker in safe_command_markers:
        assert marker in runbook

    assert "The commands above must not require production configuration or credentials." in runbook
    assert "must not be" in runbook
    assert "printed, logged, copied into examples" in runbook
    assert "added to diagnostics" in runbook
