from __future__ import annotations

import importlib
import sys

import pytest

from carbonfactor_parser.source_acquisition.models import (
    SourceDiscoveryDocument,
    SourceDiscoveryResult,
    SourceDiscoveryStatus,
)
from carbonfactor_parser.source_adapters.contracts import SourceFamily
from carbonfactor_parser.source_adapters.discovery import (
    SourceDiscoveryDryRunAdapter,
    create_phase1_source_discovery_dry_run_adapters,
    discover_phase1_sources_dry_run,
)

EXPECTED_PHASE1_SOURCE_FAMILIES = (
    "ghg_protocol",
    "defra_desnz",
    "ipcc_efdb",
)

FORBIDDEN_SOURCE_FAMILY_FRAGMENTS = (
    "temp",
    "test",
    "fake",
    "sample",
    "manual",
    "json_input",
)

BANNED_RUNTIME_MODULE_PREFIXES = (
    "requests",
    "psycopg",
    "sqlalchemy",
    "asyncpg",
    "dotenv",
    "boto3",
    "httpx",
    "urllib3",
)


def test_phase1_source_discovery_dry_run_adapters_are_exact_and_ordered() -> None:
    adapters = create_phase1_source_discovery_dry_run_adapters()

    assert adapters == (
        SourceDiscoveryDryRunAdapter(
            source_family=SourceFamily.GHG_PROTOCOL,
            source_name="GHG Protocol",
            source_reference="discovery://ghg_protocol/adapter",
        ),
        SourceDiscoveryDryRunAdapter(
            source_family=SourceFamily.DEFRA_DESNZ,
            source_name="DEFRA/DESNZ",
            source_reference="discovery://defra_desnz/adapter",
        ),
        SourceDiscoveryDryRunAdapter(
            source_family=SourceFamily.IPCC_EFDB,
            source_name="IPCC EFDB",
            source_reference="discovery://ipcc_efdb/adapter",
        ),
    )
    assert (
        tuple(adapter.source_family.value for adapter in adapters)
        == EXPECTED_PHASE1_SOURCE_FAMILIES
    )


def test_phase1_source_discovery_dry_run_results_are_deterministic() -> None:
    first = discover_phase1_sources_dry_run()
    second = discover_phase1_sources_dry_run()

    assert first == second
    assert first == (
        SourceDiscoveryResult(
            status=SourceDiscoveryStatus.DECLARED,
            documents=(
                SourceDiscoveryDocument(
                    source_family="ghg_protocol",
                    source_name="GHG Protocol",
                    source_reference="discovery://ghg_protocol/adapter",
                    reporting_year=None,
                    status=SourceDiscoveryStatus.DECLARED,
                ),
            ),
        ),
        SourceDiscoveryResult(
            status=SourceDiscoveryStatus.DECLARED,
            documents=(
                SourceDiscoveryDocument(
                    source_family="defra_desnz",
                    source_name="DEFRA/DESNZ",
                    source_reference="discovery://defra_desnz/adapter",
                    reporting_year=None,
                    status=SourceDiscoveryStatus.DECLARED,
                ),
            ),
        ),
        SourceDiscoveryResult(
            status=SourceDiscoveryStatus.DECLARED,
            documents=(
                SourceDiscoveryDocument(
                    source_family="ipcc_efdb",
                    source_name="IPCC EFDB",
                    source_reference="discovery://ipcc_efdb/adapter",
                    reporting_year=None,
                    status=SourceDiscoveryStatus.DECLARED,
                ),
            ),
        ),
    )


def test_phase1_source_discovery_dry_run_references_are_offline_safe() -> None:
    results = discover_phase1_sources_dry_run()

    documents = tuple(document for result in results for document in result.documents)
    assert (
        tuple(document.source_family for document in documents)
        == EXPECTED_PHASE1_SOURCE_FAMILIES
    )
    for document in documents:
        assert document.source_reference.startswith("discovery://")
        assert not document.source_reference.startswith(("http://", "https://"))
        assert "localhost" not in document.source_reference
        assert "example.com" not in document.source_reference
        assert "example.test" not in document.source_reference
        assert document.reporting_year is None


def test_phase1_source_discovery_dry_run_excludes_non_contract_families() -> None:
    results = discover_phase1_sources_dry_run()

    source_families = tuple(
        document.source_family
        for result in results
        for document in result.documents
    )

    assert source_families == EXPECTED_PHASE1_SOURCE_FAMILIES
    for source_family in source_families:
        assert not any(
            fragment in source_family
            for fragment in FORBIDDEN_SOURCE_FAMILY_FRAGMENTS
        )


def test_source_discovery_dry_run_adapter_module_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = "carbonfactor_parser.source_adapters.discovery"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("source discovery dry-run adapter import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError(
            "source discovery dry-run adapter import read environment"
        )

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "discover_phase1_sources_dry_run")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_modules_after - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )
