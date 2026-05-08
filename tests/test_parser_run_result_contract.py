from __future__ import annotations

import importlib
import sys
from dataclasses import replace

import pytest

from carbonfactor_parser.parsers.run_contract import (
    DRY_RUN_TIMESTAMP_LABEL,
    PARSER_RUNS_TABLE_NAME,
    ParserResultSummary,
    ParserRunContractResult,
    ParserRunContractValidationIssue,
    ParserRunContractValidationResult,
    ParserRunRequest,
    ParserRunStatus,
    create_phase1_parser_run_contract,
    validate_parser_run_contract,
)
from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    get_postgresql_phase1_schema_catalog,
)
from carbonfactor_parser.persistence.source_document_mapping import (
    create_source_document_persistence_mapping,
)
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionPlanMode

EXPECTED_PHASE1_SOURCE_FAMILIES = (
    "ghg_protocol",
    "defra_desnz",
    "ipcc_efdb",
)

EXPECTED_PARSER_RUNS_COLUMNS = (
    "parser_run_id",
    "source_document_id",
    "parser_status",
    "error_details",
    "created_at",
    "updated_at",
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


def test_default_parser_run_contract_is_exact() -> None:
    result = create_phase1_parser_run_contract()

    assert result == ParserRunContractResult(
        status=ParserRunStatus.NOT_STARTED,
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        table_name=PARSER_RUNS_TABLE_NAME,
        column_names=EXPECTED_PARSER_RUNS_COLUMNS,
        selected_source_families=EXPECTED_PHASE1_SOURCE_FAMILIES,
        requests=(
            ParserRunRequest(
                parser_run_id="dry_run_parser_run_001_ghg_protocol",
                source_document_id="dry_run_source_document_001_ghg_protocol",
                source_family="ghg_protocol",
                source_document_uri="discovery://ghg_protocol/adapter",
                source_checksum_sha256=None,
                parser_status=ParserRunStatus.NOT_STARTED,
                error_details=(),
                created_at=DRY_RUN_TIMESTAMP_LABEL,
                updated_at=DRY_RUN_TIMESTAMP_LABEL,
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
            ParserRunRequest(
                parser_run_id="dry_run_parser_run_002_defra_desnz",
                source_document_id="dry_run_source_document_002_defra_desnz",
                source_family="defra_desnz",
                source_document_uri="discovery://defra_desnz/adapter",
                source_checksum_sha256=None,
                parser_status=ParserRunStatus.NOT_STARTED,
                error_details=(),
                created_at=DRY_RUN_TIMESTAMP_LABEL,
                updated_at=DRY_RUN_TIMESTAMP_LABEL,
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
            ParserRunRequest(
                parser_run_id="dry_run_parser_run_003_ipcc_efdb",
                source_document_id="dry_run_source_document_003_ipcc_efdb",
                source_family="ipcc_efdb",
                source_document_uri="discovery://ipcc_efdb/adapter",
                source_checksum_sha256=None,
                parser_status=ParserRunStatus.NOT_STARTED,
                error_details=(),
                created_at=DRY_RUN_TIMESTAMP_LABEL,
                updated_at=DRY_RUN_TIMESTAMP_LABEL,
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
        ),
        summary=ParserResultSummary(
            requested_source_document_count=3,
            parsed_record_count=0,
            issue_count=0,
            warning_count=0,
            error_count=0,
        ),
    )


def test_parser_run_contract_is_deterministic_and_ordered() -> None:
    first = create_phase1_parser_run_contract()
    second = create_phase1_parser_run_contract()

    assert first == second
    assert first.status is ParserRunStatus.NOT_STARTED
    assert first.mode is SourceAcquisitionPlanMode.DRY_RUN
    assert first.selected_source_families == EXPECTED_PHASE1_SOURCE_FAMILIES
    assert (
        tuple(request.source_family for request in first.requests)
        == EXPECTED_PHASE1_SOURCE_FAMILIES
    )


def test_parser_run_request_count_matches_source_document_records() -> None:
    mapping = create_source_document_persistence_mapping()
    result = create_phase1_parser_run_contract(mapping)

    assert len(result.requests) == len(mapping.records)
    assert tuple(request.source_document_id for request in result.requests) == tuple(
        record.source_document_id for record in mapping.records
    )


def test_parser_run_contract_aligns_with_parser_runs_schema_catalog() -> None:
    result = create_phase1_parser_run_contract()
    catalog = get_postgresql_phase1_schema_catalog()
    parser_runs_table = catalog.get_table(PARSER_RUNS_TABLE_NAME)

    assert result.table_name == parser_runs_table.name
    assert result.column_names == tuple(column.name for column in parser_runs_table.columns)
    for column_name in result.column_names:
        assert hasattr(result.requests[0], column_name)


def test_parser_run_contract_has_no_duplicate_requests() -> None:
    result = create_phase1_parser_run_contract()
    request_keys = tuple(
        (request.source_document_id, request.source_family)
        for request in result.requests
    )

    assert len(request_keys) == len(set(request_keys))
    assert len({request.parser_run_id for request in result.requests}) == len(
        result.requests
    )


def test_parser_run_contract_uses_safe_passive_references() -> None:
    result = create_phase1_parser_run_contract()

    for request in result.requests:
        assert request.source_document_uri.startswith("discovery://")
        assert not request.source_document_uri.startswith(("http://", "https://"))
        assert "localhost" not in request.source_document_uri
        assert "example" not in request.source_document_uri
        assert request.parser_run_id.startswith("dry_run_parser_run_")
        assert request.parser_status is ParserRunStatus.NOT_STARTED
        assert not any(
            fragment in request.source_family
            for fragment in FORBIDDEN_SOURCE_FAMILY_FRAGMENTS
        )


def test_parser_run_result_summary_counts_are_deterministic_and_non_negative() -> None:
    first = create_phase1_parser_run_contract()
    second = create_phase1_parser_run_contract()

    assert first.summary == second.summary
    assert first.summary.requested_source_document_count == len(first.requests)
    assert first.summary.parsed_record_count == 0
    assert first.summary.issue_count == 0
    assert first.summary.warning_count == 0
    assert first.summary.error_count == 0
    assert all(
        count >= 0
        for count in (
            first.summary.requested_source_document_count,
            first.summary.parsed_record_count,
            first.summary.issue_count,
            first.summary.warning_count,
            first.summary.error_count,
        )
    )


def test_parser_run_contract_validation_accepts_default_contract() -> None:
    result = validate_parser_run_contract(create_phase1_parser_run_contract())

    assert result == ParserRunContractValidationResult(issues=())
    assert result.is_valid


def test_parser_run_contract_validation_reports_issue_shape() -> None:
    issue = ParserRunContractValidationIssue(
        code="PARSER_RUN_CONTRACT_TEST",
        message="Parser run contract test issue.",
        field_name="requests[0].parser_run_id",
    )

    result = ParserRunContractValidationResult(issues=(issue,))

    assert not result.is_valid
    assert result.issues == (issue,)
    assert issue.severity == "error"


def test_parser_run_contract_validation_rejects_blank_request_metadata() -> None:
    contract = create_phase1_parser_run_contract()
    request = replace(
        contract.requests[0],
        parser_run_id=" ",
        source_document_id="",
        source_document_uri=" ",
    )
    invalid = replace(contract, requests=(request,) + contract.requests[1:])

    result = validate_parser_run_contract(invalid)

    assert _issue_codes(result)[:3] == (
        "PARSER_RUN_CONTRACT_MISSING_PARSER_RUN_ID",
        "PARSER_RUN_CONTRACT_MISSING_SOURCE_DOCUMENT_ID",
        "PARSER_RUN_CONTRACT_MISSING_SOURCE_DOCUMENT_URI",
    )
    assert not result.is_valid


def test_parser_run_contract_validation_rejects_unsupported_source_families() -> None:
    contract = create_phase1_parser_run_contract()
    request = replace(contract.requests[0], source_family="unknown_family")
    invalid = replace(
        contract,
        selected_source_families=("unknown_family",),
        requests=(request,),
        summary=replace(contract.summary, requested_source_document_count=1),
    )

    result = validate_parser_run_contract(invalid)

    assert _issue_codes(result) == (
        "PARSER_RUN_CONTRACT_UNSUPPORTED_SOURCE_FAMILY",
        "PARSER_RUN_CONTRACT_UNSUPPORTED_REQUEST_SOURCE_FAMILY",
    )


def test_parser_run_contract_validation_rejects_invalid_status_values() -> None:
    contract = create_phase1_parser_run_contract()
    request = replace(contract.requests[0], parser_status="pending")
    invalid = replace(
        contract,
        status="pending",
        requests=(request,) + contract.requests[1:],
    )

    result = validate_parser_run_contract(invalid)  # type: ignore[arg-type]

    assert _issue_codes(result) == (
        "PARSER_RUN_CONTRACT_INVALID_STATUS",
        "PARSER_RUN_CONTRACT_INVALID_REQUEST_STATUS",
    )


def test_parser_run_contract_validation_rejects_duplicate_request_ids() -> None:
    contract = create_phase1_parser_run_contract()
    duplicate = replace(
        contract.requests[1],
        parser_run_id=contract.requests[0].parser_run_id,
        source_document_id=contract.requests[0].source_document_id,
    )
    invalid = replace(contract, requests=(contract.requests[0], duplicate))

    result = validate_parser_run_contract(invalid)

    assert _issue_codes(result) == (
        "PARSER_RUN_CONTRACT_DUPLICATE_PARSER_RUN_ID",
        "PARSER_RUN_CONTRACT_DUPLICATE_SOURCE_DOCUMENT_ID",
        "PARSER_RUN_CONTRACT_SUMMARY_REQUEST_COUNT_MISMATCH",
    )


def test_parser_run_contract_validation_rejects_negative_summary_counts() -> None:
    contract = create_phase1_parser_run_contract()
    invalid = replace(
        contract,
        summary=replace(
            contract.summary,
            parsed_record_count=-1,
            issue_count=-1,
            warning_count=-1,
            error_count=-1,
        ),
    )

    result = validate_parser_run_contract(invalid)

    assert _issue_codes(result) == (
        "PARSER_RUN_CONTRACT_NEGATIVE_SUMMARY_COUNT",
        "PARSER_RUN_CONTRACT_NEGATIVE_SUMMARY_COUNT",
        "PARSER_RUN_CONTRACT_NEGATIVE_SUMMARY_COUNT",
        "PARSER_RUN_CONTRACT_NEGATIVE_SUMMARY_COUNT",
        "PARSER_RUN_CONTRACT_DRY_RUN_SUMMARY_NOT_ZERO",
    )


def test_parser_run_contract_validation_rejects_nonzero_dry_run_summary() -> None:
    contract = create_phase1_parser_run_contract()
    invalid = replace(
        contract,
        summary=ParserResultSummary(
            requested_source_document_count=len(contract.requests),
            parsed_record_count=2,
            issue_count=1,
            warning_count=1,
            error_count=1,
        ),
    )

    result = validate_parser_run_contract(invalid)

    assert _issue_codes(result) == (
        "PARSER_RUN_CONTRACT_SUMMARY_ISSUE_TOTAL_MISMATCH",
        "PARSER_RUN_CONTRACT_DRY_RUN_SUMMARY_NOT_ZERO",
    )


def test_parser_run_contract_module_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = "carbonfactor_parser.parsers.run_contract"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("parser run contract import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("parser run contract import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "create_phase1_parser_run_contract")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_modules_after - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )


def _issue_codes(
    result: ParserRunContractValidationResult,
) -> tuple[str, ...]:
    return tuple(issue.code for issue in result.issues)
