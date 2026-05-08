from dataclasses import FrozenInstanceError
import importlib
import sys

import pytest

from carbonfactor_parser.contracts import SourceType
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor
from carbonfactor_parser.source_acquisition.registry import (
    create_default_source_acquisition_registry,
    validate_source_acquisition_registry,
)
from carbonfactor_parser.source_adapters import SourceFamily

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


def _fresh_import_registry_module():
    sys.modules.pop("carbonfactor_parser.source_acquisition.registry", None)
    return importlib.import_module("carbonfactor_parser.source_acquisition.registry")


def test_default_registry_contains_exactly_phase1_source_descriptors() -> None:
    registry = create_default_source_acquisition_registry()

    assert (
        tuple(descriptor.source_id for descriptor in registry)
        == EXPECTED_PHASE1_SOURCE_FAMILIES
    )
    assert (
        tuple(descriptor.source_family for descriptor in registry)
        == EXPECTED_PHASE1_SOURCE_FAMILIES
    )


def test_default_registry_matches_phase1_source_family_contracts() -> None:
    registry = create_default_source_acquisition_registry()

    assert tuple(descriptor.source_family for descriptor in registry) == tuple(
        item.value for item in SourceType
    )
    assert tuple(descriptor.source_family for descriptor in registry) == tuple(
        item.value for item in SourceFamily
    )


def test_default_registry_source_ids_are_unique() -> None:
    registry = create_default_source_acquisition_registry()

    assert len({descriptor.source_id for descriptor in registry}) == len(registry)


def test_default_registry_required_fields_are_non_empty() -> None:
    registry = create_default_source_acquisition_registry()

    for descriptor in registry:
        assert descriptor.source_id.strip()
        assert descriptor.source_family.strip()
        assert descriptor.homepage_url.strip()
        assert descriptor.acquisition_url.strip()


def test_default_registry_uses_offline_discovery_placeholders() -> None:
    registry = create_default_source_acquisition_registry()

    for descriptor in registry:
        assert descriptor.homepage_url.startswith("discovery://")
        assert descriptor.acquisition_url.startswith("discovery://")
        assert "://" in descriptor.homepage_url
        assert "://" in descriptor.acquisition_url


def test_default_registry_excludes_non_contract_source_family_fragments() -> None:
    registry = create_default_source_acquisition_registry()

    source_identifiers = tuple(
        value
        for descriptor in registry
        for value in (descriptor.source_id, descriptor.source_family)
    )

    for identifier in source_identifiers:
        assert not any(
            fragment in identifier
            for fragment in FORBIDDEN_SOURCE_FAMILY_FRAGMENTS
        )


def test_source_acquisition_descriptor_is_immutable() -> None:
    descriptor = create_default_source_acquisition_registry()[0]

    with pytest.raises(FrozenInstanceError):
        descriptor.source_id = "mutated"  # type: ignore[misc]


def test_duplicate_source_ids_raise_clear_exception() -> None:
    duplicate_registry = (
        SourceAcquisitionDescriptor(
            source_id="duplicate_source",
            source_family="family_one",
            display_name="One",
            homepage_url="discovery://test/one",
            acquisition_url="discovery://test/one/discovery",
            expected_format="discovery",
            description="placeholder",
            enabled=True,
        ),
        SourceAcquisitionDescriptor(
            source_id="duplicate_source",
            source_family="family_two",
            display_name="Two",
            homepage_url="discovery://test/two",
            acquisition_url="discovery://test/two/discovery",
            expected_format="discovery",
            description="placeholder",
            enabled=True,
        ),
    )

    with pytest.raises(ValueError, match="Duplicate source_id found: duplicate_source"):
        validate_source_acquisition_registry(duplicate_registry)


def test_registry_module_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("source acquisition registry import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("source acquisition registry import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = _fresh_import_registry_module()
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "create_default_source_acquisition_registry")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_modules_after - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )


def test_registry_exports_are_stable_and_deterministic() -> None:
    assert create_default_source_acquisition_registry() == (
        SourceAcquisitionDescriptor(
            source_id="ghg_protocol",
            source_family="ghg_protocol",
            display_name="GHG Protocol",
            homepage_url="discovery://ghg_protocol/homepage",
            acquisition_url="discovery://ghg_protocol/acquisition",
            expected_format="discovery",
            description=(
                "Discovery URL placeholder for future source-specific acquisition "
                "work; not a verified direct download endpoint."
            ),
            enabled=True,
        ),
        SourceAcquisitionDescriptor(
            source_id="defra_desnz",
            source_family="defra_desnz",
            display_name="DEFRA/DESNZ",
            homepage_url="discovery://defra_desnz/homepage",
            acquisition_url="discovery://defra_desnz/homepage",
            expected_format="discovery",
            description=(
                "Discovery URL placeholder for future source-specific acquisition "
                "work; not a verified direct download endpoint."
            ),
            enabled=True,
        ),
        SourceAcquisitionDescriptor(
            source_id="ipcc_efdb",
            source_family="ipcc_efdb",
            display_name="IPCC EFDB",
            homepage_url="discovery://ipcc_efdb/homepage",
            acquisition_url="discovery://ipcc_efdb/homepage",
            expected_format="discovery",
            description=(
                "Discovery URL placeholder for future source-specific acquisition "
                "work; not a verified direct download endpoint."
            ),
            enabled=True,
        ),
    )
