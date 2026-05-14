from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import importlib
import sys

import pytest

from carbonfactor_parser.source_acquisition.source_onboarding_registry_contract import (
    PHASE2_ONBOARDING_PARSER_KEYS_BY_SOURCE_FAMILY,
    PHASE2_ONBOARDING_SOURCE_FAMILIES,
    SourceOnboardingDiscoveryStrategy,
    SourceOnboardingDocument,
    SourceOnboardingParserCapability,
    SourceOnboardingRegistry,
    SourceOnboardingRegistryEntry,
    SourceOnboardingRuntimeSafety,
    SourceOnboardingUpdateCadence,
    SourceOnboardingValidationExpectations,
    create_phase2_source_onboarding_registry,
    get_source_onboarding_entry,
    list_source_onboarding_entries,
    validate_source_onboarding_registry,
)


EXPECTED_PHASE1_SOURCE_FAMILIES = (
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


def test_phase2_source_onboarding_registry_contains_phase1_source_families() -> None:
    registry = create_phase2_source_onboarding_registry()

    assert PHASE2_ONBOARDING_SOURCE_FAMILIES == EXPECTED_PHASE1_SOURCE_FAMILIES
    assert tuple(entry.source_id for entry in registry.entries) == (
        EXPECTED_PHASE1_SOURCE_FAMILIES
    )
    assert tuple(entry.source_family for entry in registry.entries) == (
        EXPECTED_PHASE1_SOURCE_FAMILIES
    )


def test_phase2_source_onboarding_registry_represents_future_metadata() -> None:
    registry = create_phase2_source_onboarding_registry()

    for entry in registry.entries:
        assert entry.discovery_strategy is (
            SourceOnboardingDiscoveryStrategy.DECLARED_REFERENCE
        )
        assert entry.update_cadence is SourceOnboardingUpdateCadence.UNKNOWN
        assert entry.parser_capability.parser_key == (
            PHASE2_ONBOARDING_PARSER_KEYS_BY_SOURCE_FAMILY[entry.source_family]
        )
        assert entry.parser_capability.parser_source_format == "discovery_reference"
        assert entry.validation_expectations.required_document_fields == (
            "document_id",
            "display_name",
            "source_reference",
            "expected_format",
        )
        assert entry.documents[0].source_reference.startswith("discovery://")


def test_phase2_source_onboarding_registry_is_runtime_safe_by_default() -> None:
    registry = create_phase2_source_onboarding_registry()

    for entry in registry.entries:
        assert entry.parser_capability.supports_parser_execution is False
        assert entry.validation_expectations.checksum_required is False
        assert entry.validation_expectations.schema_validation_required is False
        assert entry.runtime_safety.allows_network_calls is False
        assert entry.runtime_safety.allows_file_reads is False
        assert entry.runtime_safety.allows_database_writes is False
        assert entry.runtime_safety.requires_credentials is False


def test_source_onboarding_registry_valid_entry_passes_validation() -> None:
    registry = SourceOnboardingRegistry(entries=(_valid_entry("new_registry_source"),))

    assert validate_source_onboarding_registry(registry) == registry


def test_source_onboarding_registry_invalid_entry_type_raises() -> None:
    registry = SourceOnboardingRegistry(
        entries=("not an entry",),  # type: ignore[arg-type]
    )

    with pytest.raises(TypeError, match="SourceOnboardingRegistryEntry"):
        validate_source_onboarding_registry(registry)


def test_source_onboarding_registry_duplicate_source_ids_raise() -> None:
    entry = _valid_entry("duplicate_registry_source")
    registry = SourceOnboardingRegistry(
        entries=(
            entry,
            replace(entry, source_family="duplicate_registry_source_two"),
        ),
    )

    with pytest.raises(ValueError, match="Duplicate source_id found"):
        validate_source_onboarding_registry(registry)


def test_source_onboarding_registry_duplicate_source_families_raise() -> None:
    entry = _valid_entry("duplicate_registry_family")
    registry = SourceOnboardingRegistry(
        entries=(
            entry,
            replace(entry, source_id="duplicate_registry_family_two"),
        ),
    )

    with pytest.raises(ValueError, match="Duplicate source_family found"):
        validate_source_onboarding_registry(registry)


def test_source_onboarding_registry_duplicate_document_ids_raise() -> None:
    entry = _valid_entry(
        "new_registry_source",
        documents=(
            _valid_document("duplicate_document"),
            _valid_document("duplicate_document"),
        ),
    )
    registry = SourceOnboardingRegistry(entries=(entry,))

    with pytest.raises(ValueError, match="Duplicate document_id found"):
        validate_source_onboarding_registry(registry)


def test_source_onboarding_registry_missing_required_fields_raise() -> None:
    entry = replace(_valid_entry("new_registry_source"), source_family=" ")
    registry = SourceOnboardingRegistry(entries=(entry,))

    with pytest.raises(ValueError, match="source_family must be a non-empty string"):
        validate_source_onboarding_registry(registry)


def test_source_onboarding_registry_missing_documents_raise() -> None:
    entry = replace(_valid_entry("new_registry_source"), documents=())
    registry = SourceOnboardingRegistry(entries=(entry,))

    with pytest.raises(ValueError, match="documents must include at least one"):
        validate_source_onboarding_registry(registry)


def test_source_onboarding_registry_deterministic_ordering_is_enforced() -> None:
    registry = create_phase2_source_onboarding_registry()
    reordered = SourceOnboardingRegistry(
        entries=(registry.entries[1], registry.entries[0], registry.entries[2]),
    )

    assert create_phase2_source_onboarding_registry() == registry
    assert list_source_onboarding_entries(registry) == registry.entries
    with pytest.raises(ValueError, match="Phase 1 source order"):
        validate_source_onboarding_registry(reordered)


def test_source_onboarding_registry_lookup_is_deterministic() -> None:
    registry = create_phase2_source_onboarding_registry()

    for source_family in EXPECTED_PHASE1_SOURCE_FAMILIES:
        entry = get_source_onboarding_entry(source_family, registry)

        assert entry is not None
        assert entry == get_source_onboarding_entry(source_family)
        assert entry.source_family == source_family

    assert get_source_onboarding_entry("unknown_source", registry) is None


def test_source_onboarding_registry_records_are_immutable() -> None:
    registry = create_phase2_source_onboarding_registry()

    with pytest.raises(FrozenInstanceError):
        registry.entries = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        registry.entries[0].source_id = "mutated"  # type: ignore[misc]


def test_source_onboarding_registry_import_is_runtime_passive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import os

    module_name = (
        "carbonfactor_parser.source_acquisition.source_onboarding_registry_contract"
    )
    sys.modules.pop(module_name, None)

    open_calls: list[tuple[object, ...]] = []
    getenv_calls: list[tuple[object, ...]] = []

    def guard_open(*args: object, **kwargs: object) -> object:
        open_calls.append(args)
        raise AssertionError("source onboarding registry import read a file")

    def guard_getenv(*args: object, **kwargs: object) -> object:
        getenv_calls.append(args)
        raise AssertionError("source onboarding registry import read environment")

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(os, "getenv", guard_getenv)
    monkeypatch.setattr(os, "environ", {})

    imported_modules_before = set(sys.modules)
    module = importlib.import_module(module_name)
    imported_modules_after = set(sys.modules)

    assert hasattr(module, "create_phase2_source_onboarding_registry")
    assert open_calls == []
    assert getenv_calls == []

    newly_imported = imported_modules_after - imported_modules_before
    assert not any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for module_name in newly_imported
        for prefix in BANNED_RUNTIME_MODULE_PREFIXES
    )


def _valid_entry(
    source_id: str,
    *,
    documents: tuple[SourceOnboardingDocument, ...] | None = None,
) -> SourceOnboardingRegistryEntry:
    return SourceOnboardingRegistryEntry(
        source_id=source_id,
        source_family=source_id,
        display_name="New Registry Source",
        documents=documents or (_valid_document(f"{source_id}_document"),),
        discovery_strategy=SourceOnboardingDiscoveryStrategy.SOURCE_SPECIFIC_DISCOVERY,
        parser_capability=SourceOnboardingParserCapability(
            parser_key=f"{source_id}_parser",
            parser_source_format="discovery_reference",
            supports_parser_execution=False,
            capability_notes="metadata only",
        ),
        validation_expectations=SourceOnboardingValidationExpectations(
            required_document_fields=("document_id", "source_reference"),
            checksum_required=True,
            schema_validation_required=True,
            validation_notes="shape validation only",
        ),
        update_cadence=SourceOnboardingUpdateCadence.PERIODIC,
        runtime_safety=SourceOnboardingRuntimeSafety(
            allows_network_calls=False,
            allows_file_reads=False,
            allows_database_writes=False,
            requires_credentials=False,
            safety_notes="contract metadata only",
        ),
    )


def _valid_document(document_id: str) -> SourceOnboardingDocument:
    return SourceOnboardingDocument(
        document_id=document_id,
        display_name="Declared document",
        source_reference=f"discovery://{document_id}",
        expected_format="discovery",
        required=True,
    )
