from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib
import sys
import urllib.request

import pytest

from carbonfactor_parser.parsers.adapter_registry_contract import (
    Phase1ParserAdapterRegistry,
    create_phase1_parser_adapter_registry,
    get_phase1_parser_adapter_by_parser_key,
    get_phase1_parser_adapter_by_source_family,
    list_phase1_parser_adapter_descriptors,
)
from carbonfactor_parser.parsers.defra_desnz_adapter_contract import (
    describe_defra_desnz_parser_adapter,
)
from carbonfactor_parser.parsers.ghg_protocol_adapter_contract import (
    describe_ghg_protocol_parser_adapter,
)
from carbonfactor_parser.parsers.ipcc_efdb_adapter_contract import (
    describe_ipcc_efdb_parser_adapter,
)
from carbonfactor_parser.parsers.selection_registry_contract import (
    PHASE1_PARSER_KEYS_BY_SOURCE_FAMILY,
)
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionPlanMode

EXPECTED_SOURCE_FAMILIES = (
    "ghg_protocol",
    "defra_desnz",
    "ipcc_efdb",
)

EXPECTED_PARSER_KEYS = tuple(
    PHASE1_PARSER_KEYS_BY_SOURCE_FAMILY[source_family]
    for source_family in EXPECTED_SOURCE_FAMILIES
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


def test_phase1_parser_adapter_registry_contains_exact_descriptors() -> None:
    registry = create_phase1_parser_adapter_registry()

    assert registry == Phase1ParserAdapterRegistry(
        descriptors=(
            describe_ghg_protocol_parser_adapter(),
            describe_defra_desnz_parser_adapter(),
            describe_ipcc_efdb_parser_adapter(),
        ),
    )


def test_phase1_parser_adapter_registry_contains_exact_sources() -> None:
    registry = create_phase1_parser_adapter_registry()

    assert tuple(descriptor.source_family for descriptor in registry.descriptors) == (
        EXPECTED_SOURCE_FAMILIES
    )


def test_phase1_parser_adapter_registry_parser_keys_align_with_selection_contract() -> None:
    registry = create_phase1_parser_adapter_registry()

    assert tuple(descriptor.parser_key for descriptor in registry.descriptors) == (
        EXPECTED_PARSER_KEYS
    )
    assert tuple(
        (descriptor.source_family, descriptor.parser_key)
        for descriptor in registry.descriptors
    ) == tuple(zip(EXPECTED_SOURCE_FAMILIES, EXPECTED_PARSER_KEYS, strict=True))


def test_phase1_parser_adapter_registry_is_deterministic_and_read_only() -> None:
    first = create_phase1_parser_adapter_registry()
    second = create_phase1_parser_adapter_registry()

    assert first == second
    assert list_phase1_parser_adapter_descriptors(first) == first.descriptors
    assert list_phase1_parser_adapter_descriptors() == first.descriptors
    with pytest.raises(FrozenInstanceError):
        first.descriptors = ()  # type: ignore[misc]


def test_phase1_parser_adapter_lookup_by_source_family_is_deterministic() -> None:
    registry = create_phase1_parser_adapter_registry()

    for source_family in EXPECTED_SOURCE_FAMILIES:
        descriptor = get_phase1_parser_adapter_by_source_family(
            source_family,
            registry,
        )

        assert descriptor is not None
        assert descriptor == get_phase1_parser_adapter_by_source_family(source_family)
        assert descriptor.source_family == source_family


def test_phase1_parser_adapter_lookup_by_parser_key_is_deterministic() -> None:
    registry = create_phase1_parser_adapter_registry()

    for parser_key in EXPECTED_PARSER_KEYS:
        descriptor = get_phase1_parser_adapter_by_parser_key(parser_key, registry)

        assert descriptor is not None
        assert descriptor == get_phase1_parser_adapter_by_parser_key(parser_key)
        assert descriptor.parser_key == parser_key


def test_phase1_parser_adapter_lookup_unknown_values_returns_none() -> None:
    registry = create_phase1_parser_adapter_registry()

    assert get_phase1_parser_adapter_by_source_family("unknown", registry) is None
    assert get_phase1_parser_adapter_by_parser_key("unknown_parser", registry) is None


def test_phase1_parser_adapter_registry_reports_declared_capabilities() -> None:
    registry = create_phase1_parser_adapter_registry()

    for descriptor in registry.descriptors:
        assert descriptor.mode is SourceAcquisitionPlanMode.DRY_RUN
        assert descriptor.capability.supports_file_reads is False
        assert not hasattr(descriptor, "parse")
        assert not hasattr(descriptor, "can_parse")
        assert not hasattr(descriptor.capability, "parse")
        assert not hasattr(descriptor.capability, "can_parse")

    assert tuple(
        descriptor.capability.supports_parser_execution
        for descriptor in registry.descriptors
    ) == (False, False, True)
    assert tuple(
        descriptor.capability.supports_content_inspection
        for descriptor in registry.descriptors
    ) == (False, False, True)


def test_phase1_parser_adapter_registry_uses_safe_passive_identifiers() -> None:
    registry = create_phase1_parser_adapter_registry()

    assert len({descriptor.source_family for descriptor in registry.descriptors}) == (
        len(registry.descriptors)
    )
    assert len({descriptor.parser_key for descriptor in registry.descriptors}) == (
        len(registry.descriptors)
    )
    for descriptor in registry.descriptors:
        assert "://" not in descriptor.source_family
        assert "://" not in descriptor.parser_key
        assert not descriptor.source_family.startswith(("http://", "https://"))
        assert not descriptor.parser_key.startswith(("http://", "https://"))
        assert "localhost" not in descriptor.source_family
        assert "localhost" not in descriptor.parser_key
        assert "example" not in descriptor.source_family
        assert "example" not in descriptor.parser_key
        assert not any(
            fragment in descriptor.source_family or fragment in descriptor.parser_key
            for fragment in FORBIDDEN_FRAGMENTS
        )


def test_phase1_parser_adapter_registry_operations_are_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import sqlite3

    def fail_side_effect(*args: object, **kwargs: object) -> object:
        raise AssertionError("parser adapter registry contract must use metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)

    registry = create_phase1_parser_adapter_registry()

    assert list_phase1_parser_adapter_descriptors(registry) == registry.descriptors
    assert get_phase1_parser_adapter_by_source_family(
        "ghg_protocol",
        registry,
    ) == describe_ghg_protocol_parser_adapter()
    assert get_phase1_parser_adapter_by_parser_key(
        "ipcc_efdb_phase1_parser",
        registry,
    ) == describe_ipcc_efdb_parser_adapter()


def test_phase1_parser_adapter_registry_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = "carbonfactor_parser.parsers.adapter_registry_contract"
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("parser adapter registry contract import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError(
            "parser adapter registry contract import read environment"
        )

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "create_phase1_parser_adapter_registry")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_modules_after - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )
