from __future__ import annotations

import importlib
import sys

import pytest

from carbonfactor_parser.source_acquisition.dry_run_execution import (
    evaluate_source_acquisition_plan_dry_run,
)
from carbonfactor_parser.source_acquisition.models import (
    SourceAcquisitionDryRunExecutionResult,
    SourceAcquisitionDryRunFamilyResult,
    SourceAcquisitionDryRunResultStatus,
    SourceAcquisitionPlanMode,
    SourceDiscoveryDocument,
    SourceDiscoveryResult,
    SourceDiscoveryStatus,
)
from carbonfactor_parser.source_acquisition.planning import (
    create_phase1_source_acquisition_plan,
    create_phase1_source_acquisition_request,
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


def test_default_source_acquisition_dry_run_result_is_exact() -> None:
    result = evaluate_source_acquisition_plan_dry_run()

    assert result == SourceAcquisitionDryRunExecutionResult(
        status=SourceAcquisitionDryRunResultStatus.PLANNED,
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        selected_source_families=EXPECTED_PHASE1_SOURCE_FAMILIES,
        family_results=(
            SourceAcquisitionDryRunFamilyResult(
                source_family="ghg_protocol",
                status=SourceAcquisitionDryRunResultStatus.PLANNED,
                planned_document_count=1,
                discovery_result=SourceDiscoveryResult(
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
            ),
            SourceAcquisitionDryRunFamilyResult(
                source_family="defra_desnz",
                status=SourceAcquisitionDryRunResultStatus.PLANNED,
                planned_document_count=1,
                discovery_result=SourceDiscoveryResult(
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
            ),
            SourceAcquisitionDryRunFamilyResult(
                source_family="ipcc_efdb",
                status=SourceAcquisitionDryRunResultStatus.PLANNED,
                planned_document_count=1,
                discovery_result=SourceDiscoveryResult(
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
            ),
        ),
    )


def test_source_acquisition_dry_run_result_is_deterministic_and_ordered() -> None:
    first = evaluate_source_acquisition_plan_dry_run()
    second = evaluate_source_acquisition_plan_dry_run()

    assert first == second
    assert first.mode is SourceAcquisitionPlanMode.DRY_RUN
    assert first.status is SourceAcquisitionDryRunResultStatus.PLANNED
    assert (
        tuple(result.source_family for result in first.family_results)
        == EXPECTED_PHASE1_SOURCE_FAMILIES
    )
    assert first.warnings == ()
    assert all(result.warnings == () for result in first.family_results)


def test_source_acquisition_dry_run_result_matches_planned_families() -> None:
    request = create_phase1_source_acquisition_request(
        ("ipcc_efdb", "ghg_protocol"),
    )
    plan = create_phase1_source_acquisition_plan(request)
    result = evaluate_source_acquisition_plan_dry_run(plan)

    assert result.selected_source_families == ("ipcc_efdb", "ghg_protocol")
    assert len(result.family_results) == len(plan.discovery_results)
    assert len(result.family_results) == len(result.selected_source_families)
    assert tuple(
        family_result.source_family for family_result in result.family_results
    ) == (
        "ghg_protocol",
        "ipcc_efdb",
    )
    assert tuple(
        family_result.planned_document_count
        for family_result in result.family_results
    ) == (1, 1)


def test_source_acquisition_dry_run_result_has_no_duplicate_families() -> None:
    result = evaluate_source_acquisition_plan_dry_run()
    source_families = tuple(
        family_result.source_family
        for family_result in result.family_results
    )

    assert len(source_families) == len(set(source_families))


def test_source_acquisition_dry_run_result_uses_safe_passive_references() -> None:
    result = evaluate_source_acquisition_plan_dry_run()

    for family_result in result.family_results:
        assert not any(
            fragment in family_result.source_family
            for fragment in FORBIDDEN_SOURCE_FAMILY_FRAGMENTS
        )
        for document in family_result.discovery_result.documents:
            assert document.source_reference.startswith("discovery://")
            assert not document.source_reference.startswith(("http://", "https://"))
            assert "localhost" not in document.source_reference
            assert "example" not in document.source_reference


def test_source_acquisition_dry_run_execution_module_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = "carbonfactor_parser.source_acquisition.dry_run_execution"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("source acquisition dry-run import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("source acquisition dry-run import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "evaluate_source_acquisition_plan_dry_run")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_modules_after - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )
