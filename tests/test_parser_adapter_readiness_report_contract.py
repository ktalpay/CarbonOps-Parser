from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass
import importlib
import sys
import urllib.request

import pytest

from carbonfactor_parser.parsers.adapter_registry_contract import (
    Phase1ParserAdapterRegistry,
    create_phase1_parser_adapter_registry,
    list_phase1_parser_adapter_descriptors,
)
from carbonfactor_parser.parsers.parser_adapter_readiness_report_contract import (
    ParserAdapterReadinessCapability,
    ParserAdapterReadinessReport,
    ParserAdapterReadinessReportEntry,
    build_phase1_parser_adapter_readiness_report,
)

EXPECTED_SOURCE_KEYS = (
    "ghg_protocol",
    "defra_desnz",
    "ipcc_efdb",
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


def test_readiness_report_contains_exact_phase1_adapters() -> None:
    report = build_phase1_parser_adapter_readiness_report()

    assert isinstance(report, ParserAdapterReadinessReport)
    assert report.adapter_count == 3
    assert len(report.entries) == 3


def test_readiness_report_source_keys_are_exact_phase1_sources() -> None:
    report = build_phase1_parser_adapter_readiness_report()

    assert report.source_keys == EXPECTED_SOURCE_KEYS
    assert tuple(entry.source_family for entry in report.entries) == (
        EXPECTED_SOURCE_KEYS
    )


def test_readiness_report_parser_keys_align_with_registry_descriptors() -> None:
    registry = create_phase1_parser_adapter_registry()
    report = build_phase1_parser_adapter_readiness_report(registry)

    assert report.parser_keys == tuple(
        descriptor.parser_key for descriptor in registry.descriptors
    )
    assert tuple(
        (entry.source_key, entry.parser_key) for entry in report.entries
    ) == tuple(
        (descriptor.source_family, descriptor.parser_key)
        for descriptor in registry.descriptors
    )


def test_readiness_report_ordering_is_deterministic() -> None:
    first = build_phase1_parser_adapter_readiness_report()
    second = build_phase1_parser_adapter_readiness_report()

    assert first == second
    assert first.source_keys == EXPECTED_SOURCE_KEYS
    assert first.entries == tuple(
        build_phase1_parser_adapter_readiness_report().entries
    )


def test_readiness_report_uses_registry_descriptor_metadata() -> None:
    registry = create_phase1_parser_adapter_registry()
    report = build_phase1_parser_adapter_readiness_report(registry)

    for descriptor, entry in zip(registry.descriptors, report.entries, strict=True):
        assert entry.source_family == descriptor.source_family
        assert entry.source_key == descriptor.source_family
        assert entry.parser_key == descriptor.parser_key
        assert entry.display_name is None
        assert entry.name is None
        assert entry.readiness == descriptor.readiness.value
        assert entry.execution_mode == descriptor.mode.value
        assert entry.capability == ParserAdapterReadinessCapability(
            source_family=descriptor.capability.source_family,
            source_key=descriptor.capability.source_family,
            parser_key=descriptor.capability.parser_key,
            parser_source_format=descriptor.capability.parser_source_format.value,
            format_hint=descriptor.capability.format_hint,
            supports_parser_execution=(
                descriptor.capability.supports_parser_execution
            ),
            supports_file_reads=descriptor.capability.supports_file_reads,
            supports_content_inspection=(
                descriptor.capability.supports_content_inspection
            ),
        )


def test_readiness_report_respects_supplied_registry_without_inventing_adapters() -> None:
    registry = create_phase1_parser_adapter_registry()
    trimmed_registry = Phase1ParserAdapterRegistry(
        descriptors=registry.descriptors[:2],
    )

    report = build_phase1_parser_adapter_readiness_report(trimmed_registry)

    assert report.source_keys == EXPECTED_SOURCE_KEYS[:2]
    assert report.parser_keys == tuple(
        descriptor.parser_key for descriptor in trimmed_registry.descriptors
    )


def test_readiness_report_is_read_only() -> None:
    report = build_phase1_parser_adapter_readiness_report()

    with pytest.raises(FrozenInstanceError):
        report.entries = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.entries[0].parser_key = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.entries[0].capability.format_hint = "changed"  # type: ignore[misc]


def test_readiness_report_is_metadata_only_and_reflects_declared_capabilities() -> None:
    report = build_phase1_parser_adapter_readiness_report()

    assert tuple(entry.readiness for entry in report.entries) == (
        "contract_only",
        "contract_only",
        "content_parser_ready",
    )
    assert tuple(
        entry.capability.supports_parser_execution for entry in report.entries
    ) == (False, False, True)
    assert tuple(
        entry.capability.supports_content_inspection for entry in report.entries
    ) == (False, False, True)

    for entry in report.entries:
        assert entry.execution_mode == "dry_run"
        assert entry.capability.supports_file_reads is False
        assert not hasattr(entry, "parse")
        assert not hasattr(entry, "can_parse")
        assert not hasattr(entry.capability, "parse")
        assert not hasattr(entry.capability, "can_parse")


def test_readiness_report_operations_are_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import sqlite3

    def fail_side_effect(*args: object, **kwargs: object) -> object:
        raise AssertionError("readiness report contract must use metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)

    registry = create_phase1_parser_adapter_registry()
    report = build_phase1_parser_adapter_readiness_report(registry)

    assert report.source_keys == EXPECTED_SOURCE_KEYS
    assert report.entries == build_phase1_parser_adapter_readiness_report(
        registry
    ).entries
    assert list_phase1_parser_adapter_descriptors(registry) == registry.descriptors


def test_readiness_report_does_not_import_executable_parser_modules() -> None:
    imported_before = set(sys.modules)

    report = build_phase1_parser_adapter_readiness_report()

    imported_after = set(sys.modules)
    newly_imported = imported_after - imported_before
    assert report.adapter_count == 3
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_EXECUTABLE_PARSER_MODULES
    )


def test_readiness_report_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = (
        "carbonfactor_parser.parsers.parser_adapter_readiness_report_contract"
    )
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("readiness report contract import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("readiness report contract import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "build_phase1_parser_adapter_readiness_report")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_modules_after - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_EXECUTABLE_PARSER_MODULES
    )


def test_readiness_report_preserves_descriptor_display_metadata_if_exposed() -> None:
    registry = create_phase1_parser_adapter_registry()
    descriptor = registry.descriptors[0]

    @dataclass(frozen=True)
    class DescriptorWithDisplayMetadata:
        source_family: str
        parser_key: str
        readiness: object
        capability: object
        mode: object
        display_name: str
        name: str

    descriptor_with_display = DescriptorWithDisplayMetadata(
        source_family=descriptor.source_family,
        parser_key=descriptor.parser_key,
        readiness=descriptor.readiness,
        capability=descriptor.capability,
        mode=descriptor.mode,
        display_name="GHG Protocol",
        name="GHG Protocol Phase 1 parser adapter",
    )
    custom_registry = Phase1ParserAdapterRegistry(
        descriptors=(descriptor_with_display,),
    )

    report = build_phase1_parser_adapter_readiness_report(custom_registry)

    assert report.entries == (
        ParserAdapterReadinessReportEntry(
            source_family=descriptor.source_family,
            source_key=descriptor.source_family,
            parser_key=descriptor.parser_key,
            display_name="GHG Protocol",
            name="GHG Protocol Phase 1 parser adapter",
            readiness=descriptor.readiness.value,
            execution_mode=descriptor.mode.value,
            capability=report.entries[0].capability,
        ),
    )
