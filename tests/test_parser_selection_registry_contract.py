from __future__ import annotations

import importlib
import sys

import pytest

from carbonfactor_parser.parsers.selection_registry_contract import (
    ParserIdentity,
    ParserSelection,
    ParserSelectionRegistry,
    ParserSelectionResult,
    ParserSelectionStatus,
    create_phase1_parser_selection_registry,
    select_phase1_parsers,
)
from carbonfactor_parser.parsers.source_format_contract import (
    ParserSourceFormat,
    create_phase1_parser_input_plan,
)
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

EXPECTED_REGISTRY = ParserSelectionRegistry(
    identities=(
        ParserIdentity(
            source_family="ghg_protocol",
            parser_key="ghg_protocol_phase1_parser",
            parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
            format_hint="discovery",
        ),
        ParserIdentity(
            source_family="defra_desnz",
            parser_key="defra_desnz_phase1_parser",
            parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
            format_hint="discovery",
        ),
        ParserIdentity(
            source_family="ipcc_efdb",
            parser_key="ipcc_efdb_phase1_parser",
            parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
            format_hint="discovery",
        ),
    ),
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


def test_default_parser_selection_registry_is_exact() -> None:
    assert create_phase1_parser_selection_registry() == EXPECTED_REGISTRY


def test_default_parser_selection_result_is_exact() -> None:
    result = select_phase1_parsers()

    assert result == ParserSelectionResult(
        status=ParserSelectionStatus.PLANNED,
        mode=SourceAcquisitionPlanMode.DRY_RUN,
        selected_source_families=EXPECTED_PHASE1_SOURCE_FAMILIES,
        registry=EXPECTED_REGISTRY,
        selections=(
            ParserSelection(
                source_family="ghg_protocol",
                source_document_id="dry_run_source_document_001_ghg_protocol",
                source_document_uri="discovery://ghg_protocol/adapter",
                parser_key="ghg_protocol_phase1_parser",
                parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
                status=ParserSelectionStatus.PLANNED,
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
            ParserSelection(
                source_family="defra_desnz",
                source_document_id="dry_run_source_document_002_defra_desnz",
                source_document_uri="discovery://defra_desnz/adapter",
                parser_key="defra_desnz_phase1_parser",
                parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
                status=ParserSelectionStatus.PLANNED,
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
            ParserSelection(
                source_family="ipcc_efdb",
                source_document_id="dry_run_source_document_003_ipcc_efdb",
                source_document_uri="discovery://ipcc_efdb/adapter",
                parser_key="ipcc_efdb_phase1_parser",
                parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
                status=ParserSelectionStatus.PLANNED,
                mode=SourceAcquisitionPlanMode.DRY_RUN,
            ),
        ),
    )


def test_parser_selection_registry_is_deterministic_and_ordered() -> None:
    first = create_phase1_parser_selection_registry()
    second = create_phase1_parser_selection_registry()

    assert first == second
    assert tuple(identity.source_family for identity in first.identities) == (
        EXPECTED_PHASE1_SOURCE_FAMILIES
    )
    assert tuple(identity.parser_key for identity in first.identities) == (
        EXPECTED_PARSER_KEYS
    )


def test_parser_key_mapping_is_explicit_and_stable() -> None:
    registry = create_phase1_parser_selection_registry()

    assert tuple(
        (identity.source_family, identity.parser_key)
        for identity in registry.identities
    ) == tuple(zip(EXPECTED_PHASE1_SOURCE_FAMILIES, EXPECTED_PARSER_KEYS, strict=True))
    assert all(
        identity.parser_source_format is ParserSourceFormat.DISCOVERY_REFERENCE
        for identity in registry.identities
    )
    assert {identity.format_hint for identity in registry.identities} == {"discovery"}


def test_parser_input_count_matches_parser_selection_count() -> None:
    parser_input_plan = create_phase1_parser_input_plan()
    result = select_phase1_parsers(parser_input_plan)

    assert len(result.selections) == len(parser_input_plan.documents)
    assert tuple(selection.source_document_id for selection in result.selections) == (
        tuple(document.source_document_id for document in parser_input_plan.documents)
    )


def test_parser_selection_result_has_no_duplicate_parser_keys() -> None:
    registry = create_phase1_parser_selection_registry()
    result = select_phase1_parsers()

    assert len({identity.parser_key for identity in registry.identities}) == len(
        registry.identities
    )
    assert tuple(selection.parser_key for selection in result.selections) == (
        EXPECTED_PARSER_KEYS
    )
    assert len({selection.source_document_id for selection in result.selections}) == (
        len(result.selections)
    )


def test_parser_selection_result_uses_safe_passive_references_and_keys() -> None:
    result = select_phase1_parsers()

    for selection in result.selections:
        assert selection.source_document_uri.startswith("discovery://")
        assert not selection.source_document_uri.startswith(("http://", "https://"))
        assert "localhost" not in selection.source_document_uri
        assert "example" not in selection.source_document_uri
        assert "://" not in selection.parser_key
        assert selection.status is ParserSelectionStatus.PLANNED
        assert not any(
            fragment in selection.source_family or fragment in selection.parser_key
            for fragment in FORBIDDEN_FRAGMENTS
        )


def test_parser_selection_registry_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = "carbonfactor_parser.parsers.selection_registry_contract"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("parser selection registry import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("parser selection registry import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "select_phase1_parsers")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_modules_after - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )
