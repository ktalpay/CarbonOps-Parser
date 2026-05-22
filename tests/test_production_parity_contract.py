from __future__ import annotations

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPOSITORY_ROOT / "docs" / "production-parity-contract.md"


def test_production_parity_contract_defines_runtime_verdicts() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    normalized = " ".join(contract.split())

    assert "Project-level production-ready: no" in contract
    assert "Python runtime production path: yes" in contract
    assert ".NET runtime production path: no" in normalized
    assert "The .NET runtime is not production-ready yet" in normalized


def test_production_parity_contract_covers_required_behavior() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    for marker in (
        "same PostgreSQL schema/model",
        "GHG Protocol",
        "DEFRA/DESNZ",
        "IPCC EFDB",
        "The default initial year is `2024`",
        "latest_successful_imported_year + 1",
        "`no_available_source_year`",
        "Idempotency And Reruns",
        "Redaction And Secret Handling",
        "Operator Expectations",
        "Production Validation Expectations",
    ):
        assert marker in contract


def test_production_parity_contract_lists_dotnet_follow_up_sequence() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    for marker in (
        ".NET service/scheduled-worker entrypoint",
        ".NET production config loader and redaction",
        ".NET PostgreSQL schema bootstrap and year-state",
        ".NET source discovery/download/parsing orchestration",
        ".NET source-specific master/detail insert",
        ".NET idempotency and rerun behavior",
        ".NET Docker PostgreSQL E2E tests",
        "Python/.NET parity validation",
        "Final project production-ready verdict",
    ):
        assert marker in contract
