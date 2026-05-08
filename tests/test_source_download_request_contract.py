from __future__ import annotations

import importlib
import sys

import pytest

from carbonfactor_parser.source_acquisition.download_planning import (
    create_source_download_batch_plan,
)
from carbonfactor_parser.source_acquisition.dry_run_execution import (
    evaluate_source_acquisition_plan_dry_run,
)
from carbonfactor_parser.source_acquisition.models import (
    SourceAcquisitionPlanMode,
    SourceDownloadBatchPlan,
    SourceDownloadRequest,
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


def test_default_source_download_batch_plan_is_exact() -> None:
    plan = create_source_download_batch_plan()

    assert plan == SourceDownloadBatchPlan(
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        selected_source_families=EXPECTED_PHASE1_SOURCE_FAMILIES,
        requests=(
            SourceDownloadRequest(
                source_family="ghg_protocol",
                source_name="GHG Protocol",
                source_reference="discovery://ghg_protocol/adapter",
                target_logical_path="phase1/ghg_protocol/source",
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
            SourceDownloadRequest(
                source_family="defra_desnz",
                source_name="DEFRA/DESNZ",
                source_reference="discovery://defra_desnz/adapter",
                target_logical_path="phase1/defra_desnz/source",
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
            SourceDownloadRequest(
                source_family="ipcc_efdb",
                source_name="IPCC EFDB",
                source_reference="discovery://ipcc_efdb/adapter",
                target_logical_path="phase1/ipcc_efdb/source",
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
        ),
    )


def test_source_download_batch_plan_is_deterministic_and_ordered() -> None:
    first = create_source_download_batch_plan()
    second = create_source_download_batch_plan()

    assert first == second
    assert first.mode is SourceAcquisitionPlanMode.DRY_RUN
    assert first.selected_source_families == EXPECTED_PHASE1_SOURCE_FAMILIES
    assert (
        tuple(request.source_family for request in first.requests)
        == EXPECTED_PHASE1_SOURCE_FAMILIES
    )


def test_source_download_request_count_matches_planned_discovery_documents() -> None:
    dry_run_result = evaluate_source_acquisition_plan_dry_run()
    plan = create_source_download_batch_plan(dry_run_result)

    planned_document_count = sum(
        family_result.planned_document_count
        for family_result in dry_run_result.family_results
    )
    discovery_document_count = sum(
        len(family_result.discovery_result.documents)
        for family_result in dry_run_result.family_results
    )

    assert len(plan.requests) == planned_document_count
    assert len(plan.requests) == discovery_document_count


def test_source_download_batch_plan_can_derive_selected_families() -> None:
    request = create_phase1_source_acquisition_request(
        ("ipcc_efdb", "ghg_protocol"),
    )
    acquisition_plan = create_phase1_source_acquisition_plan(request)
    dry_run_result = evaluate_source_acquisition_plan_dry_run(acquisition_plan)
    download_plan = create_source_download_batch_plan(dry_run_result)

    assert download_plan.selected_source_families == ("ipcc_efdb", "ghg_protocol")
    assert tuple(request.source_family for request in download_plan.requests) == (
        "ghg_protocol",
        "ipcc_efdb",
    )


def test_source_download_batch_plan_has_no_duplicate_request_entries() -> None:
    plan = create_source_download_batch_plan()
    request_keys = tuple(
        (
            request.source_family,
            request.source_reference,
            request.target_logical_path,
        )
        for request in plan.requests
    )

    assert len(request_keys) == len(set(request_keys))
    assert len({request.source_family for request in plan.requests}) == len(
        EXPECTED_PHASE1_SOURCE_FAMILIES
    )


def test_source_download_batch_plan_uses_safe_passive_references() -> None:
    plan = create_source_download_batch_plan()

    for request in plan.requests:
        assert request.source_reference.startswith("discovery://")
        assert not request.source_reference.startswith(("http://", "https://"))
        assert "localhost" not in request.source_reference
        assert "example" not in request.source_reference
        assert "://" not in request.target_logical_path
        assert not any(
            fragment in request.source_family
            for fragment in FORBIDDEN_SOURCE_FAMILY_FRAGMENTS
        )


def test_source_download_planning_module_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = "carbonfactor_parser.source_acquisition.download_planning"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("source download planning import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("source download planning import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "create_source_download_batch_plan")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_modules_after - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )
