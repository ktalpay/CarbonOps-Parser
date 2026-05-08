from __future__ import annotations

import importlib
import sys

import pytest


EXPECTED_CONTRACT_API_SYMBOLS = (
    "AcquisitionToParserPlanIssue",
    "AcquisitionToParserPlanResult",
    "AcquisitionToParserPlanStatus",
    "AcquisitionToParserPlanSummary",
    "AcquisitionToParserPlanValidationResult",
    "Phase1OrchestrationPlan",
    "Phase1OrchestrationPlanIssue",
    "Phase1OrchestrationPlanStatus",
    "Phase1OrchestrationPlanSummary",
    "Phase1OrchestrationPlanValidationResult",
    "Phase1OrchestrationExecutorIssue",
    "Phase1OrchestrationExecutorReadiness",
    "Phase1OrchestrationExecutorRequest",
    "Phase1OrchestrationExecutorResult",
    "Phase1OrchestrationExecutorStatus",
    "Phase1OrchestrationExecutorSummary",
    "Phase1OrchestrationExecutorValidationResult",
    "SourceAcquisitionRunIssue",
    "SourceAcquisitionRunRequest",
    "SourceAcquisitionRunResult",
    "SourceAcquisitionRunStatus",
    "SourceAcquisitionRunSummary",
    "SourceAcquisitionRunValidationResult",
    "SourceDiscoveryCandidate",
    "SourceDiscoveryCandidateResult",
    "SourceDiscoveryCandidateValidationIssue",
    "SourceDiscoveryCandidateValidationResult",
    "SourceArtifactParserInputBridgeEntry",
    "SourceArtifactParserInputBridgeResult",
    "SourceArtifactParserInputBridgeValidationIssue",
    "SourceArtifactParserInputBridgeValidationResult",
    "SourceDownloadArtifact",
    "SourceDownloadArtifactResult",
    "SourceDownloadArtifactValidationIssue",
    "SourceDownloadArtifactValidationResult",
    "create_acquisition_to_parser_plan",
    "create_phase1_orchestration_plan",
    "create_phase1_orchestration_plans",
    "create_phase1_orchestration_executor_boundaries",
    "create_phase1_orchestration_executor_request",
    "create_phase1_acquisition_to_parser_plans",
    "create_phase1_source_artifact_parser_input_bridge",
    "create_phase1_source_acquisition_run_requests",
    "create_phase1_source_acquisition_run_results",
    "create_phase1_source_discovery_candidates",
    "create_phase1_source_download_artifacts",
    "create_source_artifact_parser_input_bridge_entry",
    "create_source_acquisition_run_request",
    "create_source_acquisition_run_result",
    "create_source_download_artifact_from_candidate",
    "validate_acquisition_to_parser_plan",
    "validate_acquisition_to_parser_plans",
    "validate_phase1_orchestration_plan",
    "validate_phase1_orchestration_plans",
    "plan_phase1_orchestration_executor_boundary",
    "validate_phase1_orchestration_executor_request",
    "validate_phase1_orchestration_executor_result",
    "validate_phase1_orchestration_executor_results",
    "validate_source_artifact_parser_input_bridge_entry",
    "validate_source_artifact_parser_input_bridge_result",
    "validate_source_acquisition_run_request",
    "validate_source_acquisition_run_result",
    "validate_source_discovery_candidate",
    "validate_source_discovery_candidate_result",
    "validate_source_download_artifact",
    "validate_source_download_artifact_result",
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

BANNED_SOURCE_ACQUISITION_RUNTIME_MODULES = (
    "carbonfactor_parser.source_acquisition.checksum",
    "carbonfactor_parser.source_acquisition.cli",
    "carbonfactor_parser.source_acquisition.client",
    "carbonfactor_parser.source_acquisition.file_store",
    "carbonfactor_parser.source_acquisition.http_client",
    "carbonfactor_parser.source_acquisition.http_transport",
    "carbonfactor_parser.source_acquisition.manifest",
    "carbonfactor_parser.source_acquisition.run",
)

BANNED_EXECUTABLE_PARSER_MODULES = (
    "carbonfactor_parser.parsers.defra_desnz_adapter",
    "carbonfactor_parser.parsers.defra_desnz_parser",
    "carbonfactor_parser.parsers.execution_runner",
    "carbonfactor_parser.parsers.file_content_loader",
)


def test_public_source_acquisition_contract_api_imports_expected_symbols() -> None:
    contract_api = importlib.import_module(
        "carbonfactor_parser.source_acquisition.contract_api",
    )

    assert contract_api.__all__ == EXPECTED_CONTRACT_API_SYMBOLS
    for name in EXPECTED_CONTRACT_API_SYMBOLS:
        assert hasattr(contract_api, name)


def test_public_source_acquisition_contract_api_can_be_imported_from_package() -> None:
    from carbonfactor_parser.source_acquisition import contract_api

    assert contract_api.__all__ == EXPECTED_CONTRACT_API_SYMBOLS
    assert tuple(
        request.source_key
        for request in contract_api.create_phase1_source_acquisition_run_requests()
    ) == ("ghg_protocol", "defra_desnz", "ipcc_efdb")


def test_public_source_acquisition_contract_api_exports_work_together() -> None:
    from carbonfactor_parser.source_acquisition import contract_api

    request = contract_api.create_source_acquisition_run_request(
        source_key="ghg_protocol",
    )
    result = contract_api.create_source_acquisition_run_result(
        request,
        status=contract_api.SourceAcquisitionRunStatus.COMPLETED,
    )
    bridge = contract_api.create_phase1_source_artifact_parser_input_bridge()
    plan = contract_api.create_phase1_acquisition_to_parser_plans()[0]
    orchestration = contract_api.create_phase1_orchestration_plans()[0]
    executor = contract_api.create_phase1_orchestration_executor_boundaries()[0]

    assert result.source_key == "ghg_protocol"
    assert result.status is contract_api.SourceAcquisitionRunStatus.COMPLETED
    assert contract_api.validate_source_acquisition_run_request(request).is_valid
    assert contract_api.validate_source_acquisition_run_result(result).is_valid
    assert bridge.entries[0].parser_input_artifact.source_key == "ghg_protocol"
    assert contract_api.validate_source_artifact_parser_input_bridge_result(
        bridge,
    ).is_valid
    assert plan.status is contract_api.AcquisitionToParserPlanStatus.PLANNED
    assert contract_api.validate_acquisition_to_parser_plan(plan).is_valid
    assert orchestration.status is contract_api.Phase1OrchestrationPlanStatus.PLANNED
    assert contract_api.validate_phase1_orchestration_plan(orchestration).is_valid
    assert (
        executor.status
        is contract_api.Phase1OrchestrationExecutorStatus.NOT_IMPLEMENTED
    )
    assert contract_api.validate_phase1_orchestration_executor_result(executor).is_valid


def test_source_acquisition_package_import_is_lazy_and_runtime_passive() -> None:
    cleared_modules = _clear_source_acquisition_modules()
    try:
        imported_before = set(sys.modules)
        source_acquisition = importlib.import_module(
            "carbonfactor_parser.source_acquisition",
        )
        imported_after = set(sys.modules)
    finally:
        _restore_modules(cleared_modules)

    assert source_acquisition.__all__
    newly_imported = imported_after - imported_before
    assert not _has_banned_module(newly_imported)


def test_public_source_acquisition_contract_api_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    cleared_modules = _clear_source_acquisition_modules()
    module_name = "carbonfactor_parser.source_acquisition.contract_api"

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("source acquisition contract public API import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError(
            "source acquisition contract public API import read environment",
        )

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    try:
        imported_before = set(sys.modules)
        contract_api = importlib.import_module(module_name)
        imported_after = set(sys.modules)
    finally:
        _restore_modules(cleared_modules)

    assert contract_api.__all__ == EXPECTED_CONTRACT_API_SYMBOLS
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_after - imported_before
    assert not _has_banned_module(newly_imported)


def test_source_acquisition_contract_api_does_not_export_internal_module_names() -> None:
    from carbonfactor_parser.source_acquisition import contract_api

    assert "discovery_candidate_contract" not in contract_api.__all__
    assert "download_artifact_contract" not in contract_api.__all__
    assert "run_contract" not in contract_api.__all__
    assert "source_artifact_parser_input_bridge_contract" not in contract_api.__all__
    assert "acquisition_to_parser_plan_contract" not in contract_api.__all__
    assert "phase1_orchestration_plan_contract" not in contract_api.__all__
    assert "phase1_orchestration_executor_boundary" not in contract_api.__all__
    assert all(not name.startswith("_") for name in contract_api.__all__)


def _clear_source_acquisition_modules() -> dict[str, object]:
    cleared_modules: dict[str, object] = {}
    for module_name in tuple(sys.modules):
        if module_name == "carbonfactor_parser" or module_name.startswith(
            "carbonfactor_parser.source_acquisition",
        ):
            module = sys.modules.pop(module_name, None)
            if module is not None:
                cleared_modules[module_name] = module
    return cleared_modules


def _restore_modules(cleared_modules: dict[str, object]) -> None:
    for module_name in tuple(sys.modules):
        if module_name == "carbonfactor_parser" or module_name.startswith(
            "carbonfactor_parser.source_acquisition",
        ):
            sys.modules.pop(module_name, None)
    sys.modules.update(cleared_modules)


def _has_banned_module(module_names: set[str]) -> bool:
    return any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in module_names
        for prefix in (
            *BANNED_RUNTIME_MODULE_PREFIXES,
            *BANNED_SOURCE_ACQUISITION_RUNTIME_MODULES,
            *BANNED_EXECUTABLE_PARSER_MODULES,
        )
    )
