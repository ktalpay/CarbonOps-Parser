from __future__ import annotations

import importlib
import sys

import pytest

from carbonfactor_parser.parsers.source_format_contract import (
    ParserInputDocument,
    ParserInputPlan,
    ParserSourceFormat,
    ParserSourceFormatMapping,
    create_phase1_parser_input_plan,
    get_phase1_parser_source_format_mappings,
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

EXPECTED_FORMAT_MAPPINGS = (
    ParserSourceFormatMapping(
        source_family="ghg_protocol",
        parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
        format_hint="discovery",
    ),
    ParserSourceFormatMapping(
        source_family="defra_desnz",
        parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
        format_hint="discovery",
    ),
    ParserSourceFormatMapping(
        source_family="ipcc_efdb",
        parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
        format_hint="discovery",
    ),
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


def test_default_parser_input_plan_is_exact() -> None:
    plan = create_phase1_parser_input_plan()

    assert plan == ParserInputPlan(
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        selected_source_families=EXPECTED_PHASE1_SOURCE_FAMILIES,
        source_format_mappings=EXPECTED_FORMAT_MAPPINGS,
        documents=(
            ParserInputDocument(
                source_family="ghg_protocol",
                source_document_id="dry_run_source_document_001_ghg_protocol",
                source_document_uri="discovery://ghg_protocol/adapter",
                source_checksum_sha256=None,
                logical_document_name="GHG Protocol",
                target_logical_path="phase1/ghg_protocol/source",
                parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
                format_hint="discovery",
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
            ParserInputDocument(
                source_family="defra_desnz",
                source_document_id="dry_run_source_document_002_defra_desnz",
                source_document_uri="discovery://defra_desnz/adapter",
                source_checksum_sha256=None,
                logical_document_name="DEFRA/DESNZ",
                target_logical_path="phase1/defra_desnz/source",
                parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
                format_hint="discovery",
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
            ParserInputDocument(
                source_family="ipcc_efdb",
                source_document_id="dry_run_source_document_003_ipcc_efdb",
                source_document_uri="discovery://ipcc_efdb/adapter",
                source_checksum_sha256=None,
                logical_document_name="IPCC EFDB",
                target_logical_path="phase1/ipcc_efdb/source",
                parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
                format_hint="discovery",
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
        ),
    )


def test_parser_input_plan_is_deterministic_and_ordered() -> None:
    first = create_phase1_parser_input_plan()
    second = create_phase1_parser_input_plan()

    assert first == second
    assert first.mode is SourceAcquisitionPlanMode.DRY_RUN
    assert first.selected_source_families == EXPECTED_PHASE1_SOURCE_FAMILIES
    assert (
        tuple(document.source_family for document in first.documents)
        == EXPECTED_PHASE1_SOURCE_FAMILIES
    )


def test_parser_input_count_matches_source_document_records() -> None:
    mapping = create_source_document_persistence_mapping()
    plan = create_phase1_parser_input_plan(mapping)

    assert len(plan.documents) == len(mapping.records)
    assert tuple(document.source_document_id for document in plan.documents) == tuple(
        record.source_document_id for record in mapping.records
    )


def test_parser_input_plan_has_no_duplicate_inputs() -> None:
    plan = create_phase1_parser_input_plan()
    input_keys = tuple(
        (document.source_document_id, document.source_family)
        for document in plan.documents
    )

    assert len(input_keys) == len(set(input_keys))
    assert len({document.source_document_id for document in plan.documents}) == len(
        plan.documents
    )


def test_source_family_to_parser_format_mapping_is_explicit_and_deterministic() -> None:
    first = get_phase1_parser_source_format_mappings()
    second = get_phase1_parser_source_format_mappings()

    assert first == second
    assert first == EXPECTED_FORMAT_MAPPINGS
    assert tuple(item.source_family for item in first) == EXPECTED_PHASE1_SOURCE_FAMILIES
    assert all(
        item.parser_source_format is ParserSourceFormat.DISCOVERY_REFERENCE
        for item in first
    )
    assert {item.format_hint for item in first} == {"discovery"}


def test_parser_input_plan_uses_safe_passive_references() -> None:
    plan = create_phase1_parser_input_plan()

    for document in plan.documents:
        assert document.source_document_uri.startswith("discovery://")
        assert not document.source_document_uri.startswith(("http://", "https://"))
        assert "localhost" not in document.source_document_uri
        assert "example" not in document.source_document_uri
        assert "://" not in document.target_logical_path
        assert document.format_hint == "discovery"
        assert not any(
            fragment in document.source_family
            for fragment in FORBIDDEN_SOURCE_FAMILY_FRAGMENTS
        )


def test_parser_source_format_module_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = "carbonfactor_parser.parsers.source_format_contract"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("parser source format contract import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("parser source format contract import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "create_phase1_parser_input_plan")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_modules_after - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )
