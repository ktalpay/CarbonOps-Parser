from __future__ import annotations

import importlib
import sys

import pytest

from carbonfactor_parser.source_acquisition.models import (
    SourceAcquisitionPlan,
    SourceAcquisitionPlanMode,
    SourceAcquisitionRequest,
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


def test_phase1_source_acquisition_request_defaults_to_all_families() -> None:
    request = create_phase1_source_acquisition_request()

    assert request == SourceAcquisitionRequest(
        selected_source_families=EXPECTED_PHASE1_SOURCE_FAMILIES,
        mode=SourceAcquisitionPlanMode.DRY_RUN,
    )


def test_phase1_source_acquisition_plan_defaults_to_all_families() -> None:
    plan = create_phase1_source_acquisition_plan()

    assert plan == SourceAcquisitionPlan(
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        selected_source_families=EXPECTED_PHASE1_SOURCE_FAMILIES,
        discovery_results=(
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
        ),
    )


def test_phase1_source_acquisition_plan_is_deterministic_and_ordered() -> None:
    first = create_phase1_source_acquisition_plan()
    second = create_phase1_source_acquisition_plan()

    assert first == second
    assert first.mode is SourceAcquisitionPlanMode.DRY_RUN
    assert first.selected_source_families == EXPECTED_PHASE1_SOURCE_FAMILIES
    assert tuple(
        result.documents[0].source_family
        for result in first.discovery_results
    ) == EXPECTED_PHASE1_SOURCE_FAMILIES


def test_phase1_source_acquisition_plan_filters_selected_families() -> None:
    request = create_phase1_source_acquisition_request(
        ("ipcc_efdb", "ghg_protocol"),
    )
    plan = create_phase1_source_acquisition_plan(request)

    assert plan.selected_source_families == ("ipcc_efdb", "ghg_protocol")
    assert tuple(
        result.documents[0].source_family
        for result in plan.discovery_results
    ) == ("ghg_protocol", "ipcc_efdb")


def test_phase1_source_acquisition_plan_rejects_unknown_or_duplicate_families() -> None:
    with pytest.raises(ValueError, match="Unknown source families"):
        create_phase1_source_acquisition_request(("unknown_family",))

    with pytest.raises(ValueError, match="must not contain duplicates"):
        create_phase1_source_acquisition_request(("ghg_protocol", "ghg_protocol"))

    with pytest.raises(ValueError, match="must not be empty"):
        create_phase1_source_acquisition_request(())


def test_phase1_source_acquisition_plan_uses_safe_passive_references() -> None:
    plan = create_phase1_source_acquisition_plan()
    documents = tuple(
        document
        for result in plan.discovery_results
        for document in result.documents
    )

    assert len(documents) == len(EXPECTED_PHASE1_SOURCE_FAMILIES)
    assert len({document.source_family for document in documents}) == len(documents)
    for document in documents:
        assert document.source_reference.startswith("discovery://")
        assert not document.source_reference.startswith(("http://", "https://"))
        assert "localhost" not in document.source_reference
        assert "example.com" not in document.source_reference
        assert "example.test" not in document.source_reference
        assert not any(
            fragment in document.source_family
            for fragment in FORBIDDEN_SOURCE_FAMILY_FRAGMENTS
        )


def test_source_acquisition_planning_module_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = "carbonfactor_parser.source_acquisition.planning"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("source acquisition planning import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("source acquisition planning import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "create_phase1_source_acquisition_plan")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_modules_after - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )
