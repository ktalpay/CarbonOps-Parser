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
        "## PostgreSQL Readiness",
        "## Scheduling",
        "## Stop And Rerun",
        "## Troubleshooting",
        "## Production Validation Checklist",
    ):
        assert heading in runbook

    assert "Local fixture/dry-run" in runbook
    assert "Local PostgreSQL smoke" in runbook
    assert "Production PostgreSQL" in runbook


def test_runbook_documents_python_and_dotnet_entrypoint_alignment() -> None:
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")
    normalized = " ".join(runbook.split()).lower()

    assert "carbonops-parser" in runbook
    assert "carbonops-source-acquisition" in runbook
    assert "src/dotnet/CarbonOps.Parser.sln" in runbook
    assert "contracts/tests only; no deployed worker command" in normalized
    assert "CARBONOPS_POSTGRESQL_PASSWORD" in runbook
    assert "CARBONOPS_POSTGRESQL_DSN" in runbook
    assert "avoid in production because it is easier to leak" in runbook


def test_runbook_safe_commands_do_not_require_production_secrets() -> None:
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")
    normalized = " ".join(runbook.split())

    safe_command_markers = (
        "carbonops-source-acquisition validate",
        "carbonops-parser local-dry-run",
        "carbonops-parser validate-ingestion-config",
        "python -m pytest",
        "git diff --check",
    )

    for marker in safe_command_markers:
        assert marker in runbook

    assert "without opening PostgreSQL" in runbook
    assert "Do not put passwords, tokens, private DSNs, or real credentials" in normalized
    assert "postgresql_password_configured=True" in runbook


def test_runbook_documents_production_commands_and_required_config() -> None:
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")

    assert (
        "carbonops-parser run-ingestion \\\n"
        "  --config /etc/carbonops-parser/ingestion.production.json \\\n"
        "  --cycles 1"
    ) in runbook
    assert "CARBONOPS_POSTGRESQL_HOST" in runbook
    assert "CARBONOPS_POSTGRESQL_PORT" in runbook
    assert "CARBONOPS_POSTGRESQL_DATABASE" in runbook
    assert "CARBONOPS_POSTGRESQL_USERNAME" in runbook
    assert "CARBONOPS_POSTGRESQL_PASSWORD" in runbook
    assert "CARBONOPS_POSTGRESQL_APPLICATION_NAME" in runbook
    assert "CARBONOPS_POSTGRESQL_INITIAL_YEAR" in runbook
    assert "`archive_root`" in runbook
    assert "`enabled_source_families`" in runbook
    assert "`source_years.<family>.<year>.artifact_url`" in runbook


def test_runbook_documents_postgresql_readiness_queries_and_cron() -> None:
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")
    normalized = " ".join(runbook.split())

    for table_name in (
        "source_family_year_states",
        "ghg_emission_factor_masters",
        "ghg_emission_factor_details",
        "defra_emission_factor_masters",
        "defra_emission_factor_details",
        "ipcc_emission_factor_masters",
        "ipcc_emission_factor_details",
    ):
        assert table_name in runbook

    assert "CREATE TABLE IF NOT EXISTS" in normalized
    assert "CREATE INDEX IF NOT EXISTS" in normalized
    assert "SELECT source_family, max(ingested_year)" in runbook
    assert "Supported production scheduling is cron" in runbook
    assert "CARBONOPS_POSTGRESQL_PASSWORD_FILE" in runbook
