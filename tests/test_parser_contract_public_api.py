from __future__ import annotations

import importlib
import sys

import pytest


EXPECTED_CONTRACT_API_SYMBOLS = (
    "DEFRA_DESNZ_PARSER_KEY",
    "DEFRA_DESNZ_SOURCE_FAMILY",
    "DefraDesnzParserAdapterDescriptor",
    "GHG_PROTOCOL_PARSER_KEY",
    "GHG_PROTOCOL_SOURCE_FAMILY",
    "GHGProtocolParserAdapterDescriptor",
    "IPCC_EFDB_PARSER_KEY",
    "IPCC_EFDB_SOURCE_FAMILY",
    "IpccEfdbParserAdapterDescriptor",
    "ParserAdapterReadinessCapability",
    "ParserAdapterReadinessReport",
    "ParserAdapterReadinessReportEntry",
    "ParserDryRunBoundaryResult",
    "ParserDryRunBoundaryStatus",
    "ParserDryRunBoundaryValidationIssue",
    "ParserDryRunBoundaryValidationResult",
    "ParserDryRunEligibility",
    "ParserDryRunSummary",
    "ParserInputArtifact",
    "ParserInputArtifactValidationIssue",
    "ParserInputArtifactValidationResult",
    "ParserNormalizedOutputBatch",
    "ParserNormalizedOutputRow",
    "ParserNormalizedOutputRowStatus",
    "ParserNormalizedOutputRowValidationIssue",
    "ParserNormalizedOutputRowValidationResult",
    "ParserRunContractValidationIssue",
    "ParserRunContractValidationResult",
    "ParserRunRequest",
    "ParserRunResult",
    "ParserRunStatus",
    "ParserRunSummary",
    "ParserValidationIssue",
    "ParserValidationIssueCollection",
    "ParserValidationIssueSeverity",
    "ParserValidationIssueValidationIssue",
    "ParserValidationIssueValidationResult",
    "Phase1ParserAdapterDescriptor",
    "Phase1ParserAdapterRegistry",
    "build_phase1_parser_adapter_readiness_report",
    "create_parser_normalized_output_batch",
    "create_parser_normalized_output_row",
    "create_parser_run_request",
    "create_parser_run_result",
    "create_parser_validation_issue",
    "create_parser_validation_issue_collection",
    "create_phase1_parser_adapter_registry",
    "create_phase1_parser_input_artifact",
    "describe_defra_desnz_parser_adapter",
    "describe_ghg_protocol_parser_adapter",
    "describe_ipcc_efdb_parser_adapter",
    "get_phase1_parser_adapter_by_parser_key",
    "get_phase1_parser_adapter_by_source_family",
    "list_phase1_parser_adapter_descriptors",
    "plan_parser_dry_run_boundary",
    "validate_parser_dry_run_boundary_result",
    "validate_parser_input_artifact",
    "validate_parser_normalized_output_batch",
    "validate_parser_normalized_output_row",
    "validate_parser_run_request",
    "validate_parser_run_result",
    "validate_parser_validation_issue",
    "validate_parser_validation_issue_collection",
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

BANNED_EXECUTABLE_PARSER_MODULES = (
    "carbonfactor_parser.parsers.defra_desnz_adapter",
    "carbonfactor_parser.parsers.defra_desnz_parser",
    "carbonfactor_parser.parsers.execution_runner",
    "carbonfactor_parser.parsers.file_content_loader",
)


def test_public_parser_contract_api_imports_expected_symbols() -> None:
    contract_api = importlib.import_module("carbonfactor_parser.parsers.contract_api")

    assert contract_api.__all__ == EXPECTED_CONTRACT_API_SYMBOLS
    for name in EXPECTED_CONTRACT_API_SYMBOLS:
        assert hasattr(contract_api, name)


def test_public_parser_contract_api_can_be_imported_from_parser_package() -> None:
    from carbonfactor_parser.parsers import contract_api

    assert contract_api.__all__ == EXPECTED_CONTRACT_API_SYMBOLS
    assert contract_api.GHG_PROTOCOL_SOURCE_FAMILY == "ghg_protocol"
    assert contract_api.DEFRA_DESNZ_SOURCE_FAMILY == "defra_desnz"
    assert contract_api.IPCC_EFDB_SOURCE_FAMILY == "ipcc_efdb"


def test_public_parser_contract_api_exports_work_together() -> None:
    from carbonfactor_parser.parsers import contract_api

    artifact = contract_api.create_phase1_parser_input_artifact(
        source_family="ghg_protocol",
        artifact_reference="artifact://phase1/ghg_protocol",
    )
    request = contract_api.create_parser_run_request(
        source_family="ghg_protocol",
        artifacts=(artifact,),
    )
    dry_run = contract_api.plan_parser_dry_run_boundary(request)

    assert dry_run.status is contract_api.ParserDryRunBoundaryStatus.PLANNED
    assert dry_run.parser_key == "ghg_protocol_phase1_parser"
    assert contract_api.validate_parser_dry_run_boundary_result(dry_run).is_valid


def test_parser_package_import_is_lazy_and_runtime_passive() -> None:
    _clear_parser_modules()

    imported_before = set(sys.modules)
    parsers = importlib.import_module("carbonfactor_parser.parsers")
    imported_after = set(sys.modules)

    assert parsers.__all__
    newly_imported = imported_after - imported_before
    assert not _has_banned_module(newly_imported)


def test_public_parser_contract_api_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    _clear_parser_modules()
    module_name = "carbonfactor_parser.parsers.contract_api"

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("parser contract public API import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("parser contract public API import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_before = set(sys.modules)
    contract_api = importlib.import_module(module_name)
    imported_after = set(sys.modules)

    assert contract_api.__all__ == EXPECTED_CONTRACT_API_SYMBOLS
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_after - imported_before
    assert not _has_banned_module(newly_imported)


def test_parser_contract_api_does_not_export_internal_module_names() -> None:
    from carbonfactor_parser.parsers import contract_api

    assert "adapter_registry_contract" not in contract_api.__all__
    assert "input_artifact_contract" not in contract_api.__all__
    assert "normalized_output_row_contract" not in contract_api.__all__
    assert "validation_issue_contract" not in contract_api.__all__
    assert "parser_run_contract" not in contract_api.__all__
    assert "dry_run_boundary_contract" not in contract_api.__all__
    assert all(not name.startswith("_") for name in contract_api.__all__)


def _clear_parser_modules() -> None:
    for module_name in tuple(sys.modules):
        if module_name == "carbonfactor_parser.parsers" or module_name.startswith(
            "carbonfactor_parser.parsers."
        ):
            sys.modules.pop(module_name, None)


def _has_banned_module(module_names: set[str]) -> bool:
    return any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in module_names
        for prefix in (*BANNED_RUNTIME_MODULE_PREFIXES, *BANNED_EXECUTABLE_PARSER_MODULES)
    )
