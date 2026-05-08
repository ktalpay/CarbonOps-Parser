from __future__ import annotations

import importlib
import sys

import pytest

from carbonfactor_parser.parsers.execution_boundary_contract import (
    ParserExecutionBoundaryDescriptor,
    ParserExecutionBoundaryResult,
    ParserExecutionBoundaryStatus,
    ParserExecutionRequest,
    create_phase1_parser_execution_boundary,
)
from carbonfactor_parser.parsers.run_contract import (
    ParserRunStatus,
    create_phase1_parser_run_contract,
)
from carbonfactor_parser.parsers.selection_registry_contract import (
    select_phase1_parsers,
)
from carbonfactor_parser.parsers.source_format_contract import ParserSourceFormat
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionPlanMode

EXPECTED_PHASE1_SOURCE_FAMILIES = (
    "ghg_protocol",
    "defra_desnz",
    "ipcc_efdb",
)

EXPECTED_PARSER_KEYS = (
    "ghg_protocol_phase1_parser",
    "defra_desnz_phase1_parser",
    "ipcc_efdb_phase1_parser",
)

FORBIDDEN_FRAGMENTS = (
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


def test_default_parser_execution_boundary_is_exact() -> None:
    result = create_phase1_parser_execution_boundary()

    assert result == ParserExecutionBoundaryResult(
        status=ParserExecutionBoundaryStatus.PLANNED,
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        descriptor=ParserExecutionBoundaryDescriptor(
            mode=SourceAcquisitionPlanMode.DRY_RUN,
            status=ParserExecutionBoundaryStatus.PLANNED,
            instantiates_parsers=False,
            executes_parsers=False,
            reads_files=False,
            performs_persistence=False,
        ),
        selected_source_families=EXPECTED_PHASE1_SOURCE_FAMILIES,
        requests=(
            ParserExecutionRequest(
                parser_run_id="dry_run_parser_run_001_ghg_protocol",
                source_family="ghg_protocol",
                source_document_id="dry_run_source_document_001_ghg_protocol",
                source_document_uri="discovery://ghg_protocol/adapter",
                source_checksum_sha256=None,
                parser_key="ghg_protocol_phase1_parser",
                parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
                parser_run_status=ParserRunStatus.NOT_STARTED,
                execution_status=ParserExecutionBoundaryStatus.PLANNED,
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
            ParserExecutionRequest(
                parser_run_id="dry_run_parser_run_002_defra_desnz",
                source_family="defra_desnz",
                source_document_id="dry_run_source_document_002_defra_desnz",
                source_document_uri="discovery://defra_desnz/adapter",
                source_checksum_sha256=None,
                parser_key="defra_desnz_phase1_parser",
                parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
                parser_run_status=ParserRunStatus.NOT_STARTED,
                execution_status=ParserExecutionBoundaryStatus.PLANNED,
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
            ParserExecutionRequest(
                parser_run_id="dry_run_parser_run_003_ipcc_efdb",
                source_family="ipcc_efdb",
                source_document_id="dry_run_source_document_003_ipcc_efdb",
                source_document_uri="discovery://ipcc_efdb/adapter",
                source_checksum_sha256=None,
                parser_key="ipcc_efdb_phase1_parser",
                parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
                parser_run_status=ParserRunStatus.NOT_STARTED,
                execution_status=ParserExecutionBoundaryStatus.PLANNED,
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
        ),
    )


def test_parser_execution_boundary_is_deterministic_and_ordered() -> None:
    first = create_phase1_parser_execution_boundary()
    second = create_phase1_parser_execution_boundary()

    assert first == second
    assert first.selected_source_families == EXPECTED_PHASE1_SOURCE_FAMILIES
    assert tuple(request.source_family for request in first.requests) == (
        EXPECTED_PHASE1_SOURCE_FAMILIES
    )
    assert tuple(request.parser_key for request in first.requests) == (
        EXPECTED_PARSER_KEYS
    )


def test_execution_request_count_matches_parser_selection_count() -> None:
    selection_result = select_phase1_parsers()
    result = create_phase1_parser_execution_boundary(selection_result=selection_result)

    assert len(result.requests) == len(selection_result.selections)
    assert tuple(request.source_document_id for request in result.requests) == tuple(
        selection.source_document_id for selection in selection_result.selections
    )


def test_parser_key_and_input_metadata_are_carried_through() -> None:
    selection_result = select_phase1_parsers()
    run_contract = create_phase1_parser_run_contract()
    result = create_phase1_parser_execution_boundary(
        selection_result=selection_result,
        run_contract=run_contract,
    )

    for selection, run_request, execution_request in zip(
        selection_result.selections,
        run_contract.requests,
        result.requests,
        strict=True,
    ):
        assert execution_request.parser_key == selection.parser_key
        assert execution_request.parser_source_format is selection.parser_source_format
        assert execution_request.source_document_id == selection.source_document_id
        assert execution_request.source_document_uri == selection.source_document_uri
        assert execution_request.parser_run_id == run_request.parser_run_id
        assert execution_request.parser_run_status is run_request.parser_status


def test_parser_execution_boundary_has_no_duplicate_requests() -> None:
    result = create_phase1_parser_execution_boundary()
    request_keys = tuple(
        (request.parser_run_id, request.source_document_id)
        for request in result.requests
    )

    assert len(request_keys) == len(set(request_keys))
    assert len({request.parser_key for request in result.requests}) == len(
        result.requests
    )


def test_parser_execution_boundary_uses_safe_passive_references_and_keys() -> None:
    result = create_phase1_parser_execution_boundary()

    for request in result.requests:
        assert request.source_document_uri.startswith("discovery://")
        assert not request.source_document_uri.startswith(("http://", "https://"))
        assert "localhost" not in request.source_document_uri
        assert "example" not in request.source_document_uri
        assert "://" not in request.parser_key
        assert request.execution_status is ParserExecutionBoundaryStatus.PLANNED
        assert request.parser_run_status is ParserRunStatus.NOT_STARTED
        assert not any(
            fragment in request.source_family or fragment in request.parser_key
            for fragment in FORBIDDEN_FRAGMENTS
        )


def test_parser_execution_boundary_descriptor_is_runtime_passive() -> None:
    descriptor = create_phase1_parser_execution_boundary().descriptor

    assert descriptor.mode is SourceAcquisitionPlanMode.DRY_RUN
    assert descriptor.status is ParserExecutionBoundaryStatus.PLANNED
    assert descriptor.instantiates_parsers is False
    assert descriptor.executes_parsers is False
    assert descriptor.reads_files is False
    assert descriptor.performs_persistence is False


def test_parser_execution_boundary_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = "carbonfactor_parser.parsers.execution_boundary_contract"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("parser execution boundary import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("parser execution boundary import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "create_phase1_parser_execution_boundary")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_modules_after - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )
