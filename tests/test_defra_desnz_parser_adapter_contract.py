from __future__ import annotations

import importlib
import sys

import pytest

from carbonfactor_parser.parsers.defra_desnz_adapter_contract import (
    DEFRA_DESNZ_PARSER_KEY,
    DEFRA_DESNZ_SOURCE_FAMILY,
    DefraDesnzParserAdapterDescriptor,
    ParserAdapterCapability,
    ParserAdapterSkeletonReadiness,
    describe_defra_desnz_parser_adapter,
)
from carbonfactor_parser.parsers.selection_registry_contract import (
    PHASE1_PARSER_KEYS_BY_SOURCE_FAMILY,
    create_phase1_parser_selection_registry,
)
from carbonfactor_parser.parsers.source_format_contract import ParserSourceFormat
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionPlanMode

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


def test_defra_parser_adapter_descriptor_is_exact() -> None:
    descriptor = describe_defra_desnz_parser_adapter()

    assert descriptor == DefraDesnzParserAdapterDescriptor(
        source_family="defra_desnz",
        parser_key="defra_desnz_phase1_parser",
        readiness=ParserAdapterSkeletonReadiness.CONTRACT_ONLY,
        capability=ParserAdapterCapability(
            source_family="defra_desnz",
            parser_key="defra_desnz_phase1_parser",
            parser_source_format=ParserSourceFormat.DISCOVERY_REFERENCE,
            format_hint="discovery",
            supports_parser_execution=False,
            supports_file_reads=False,
            supports_content_inspection=False,
        ),
        mode=SourceAcquisitionPlanMode.DRY_RUN,
    )


def test_defra_parser_adapter_supports_only_defra_desnz() -> None:
    descriptor = describe_defra_desnz_parser_adapter()

    assert descriptor.source_family == DEFRA_DESNZ_SOURCE_FAMILY
    assert descriptor.capability.source_family == DEFRA_DESNZ_SOURCE_FAMILY
    assert descriptor.source_family == "defra_desnz"
    assert descriptor.source_family not in {"ghg_protocol", "ipcc_efdb"}


def test_defra_parser_key_matches_selection_registry() -> None:
    descriptor = describe_defra_desnz_parser_adapter()
    registry = create_phase1_parser_selection_registry()
    registry_identity = next(
        identity
        for identity in registry.identities
        if identity.source_family == DEFRA_DESNZ_SOURCE_FAMILY
    )

    assert DEFRA_DESNZ_PARSER_KEY == PHASE1_PARSER_KEYS_BY_SOURCE_FAMILY[
        DEFRA_DESNZ_SOURCE_FAMILY
    ]
    assert descriptor.parser_key == registry_identity.parser_key
    assert descriptor.capability.parser_key == registry_identity.parser_key


def test_defra_parser_adapter_descriptor_is_deterministic() -> None:
    first = describe_defra_desnz_parser_adapter()
    second = describe_defra_desnz_parser_adapter()

    assert first == second
    assert first.mode is SourceAcquisitionPlanMode.DRY_RUN
    assert first.capability.parser_source_format is (
        ParserSourceFormat.DISCOVERY_REFERENCE
    )
    assert first.capability.format_hint == "discovery"


def test_defra_parser_adapter_readiness_is_contract_only() -> None:
    descriptor = describe_defra_desnz_parser_adapter()

    assert descriptor.readiness is ParserAdapterSkeletonReadiness.CONTRACT_ONLY
    assert descriptor.capability.supports_parser_execution is False
    assert descriptor.capability.supports_file_reads is False
    assert descriptor.capability.supports_content_inspection is False


def test_defra_parser_adapter_descriptor_exposes_no_execution_methods() -> None:
    descriptor = describe_defra_desnz_parser_adapter()

    assert not hasattr(descriptor, "parse")
    assert not hasattr(descriptor, "can_parse")
    assert not hasattr(descriptor.capability, "parse")
    assert not hasattr(descriptor.capability, "can_parse")


def test_defra_parser_adapter_descriptor_uses_safe_passive_identifiers() -> None:
    descriptor = describe_defra_desnz_parser_adapter()

    assert "://" not in descriptor.parser_key
    assert "://" not in descriptor.source_family
    assert not descriptor.parser_key.startswith(("http://", "https://"))
    assert not descriptor.source_family.startswith(("http://", "https://"))
    assert "localhost" not in descriptor.parser_key
    assert "example" not in descriptor.parser_key
    assert not any(
        fragment in descriptor.source_family or fragment in descriptor.parser_key
        for fragment in FORBIDDEN_FRAGMENTS
    )


def test_defra_parser_adapter_contract_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = "carbonfactor_parser.parsers.defra_desnz_adapter_contract"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("DEFRA/DESNZ parser adapter contract import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError(
            "DEFRA/DESNZ parser adapter contract import read environment"
        )

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "describe_defra_desnz_parser_adapter")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_modules_after - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )
