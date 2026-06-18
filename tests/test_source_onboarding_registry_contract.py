from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import importlib
import json
from pathlib import Path
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
from carbonfactor_parser.parsers.adapter_registry_contract import (
    create_phase1_parser_adapter_registry,
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
PARITY_EXPECTATIONS_PATH = (
    Path(__file__).parent
    / "fixtures/parity/source_onboarding_registry_expectations.json"
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


def test_phase2_source_onboarding_registry_matches_shared_parity_expectations() -> None:
    expectations = json.loads(PARITY_EXPECTATIONS_PATH.read_text())
    registry = create_phase2_source_onboarding_registry()

    assert _registry_to_wire_snapshot(registry) == {
        "phase2_source_families": expectations["phase2_source_families"],
        "entries": expectations["entries"],
    }
    assert expectations["accepted_asymmetries"] == [
        "Python validation raises TypeError or ValueError for invalid registries; "
        ".NET validation returns ContractValidationResult errors and lookup helpers "
        "throw ArgumentException when an invalid custom registry is supplied."
    ]


def test_phase2_source_onboarding_parser_keys_align_with_phase1_registry() -> None:
    onboarding_registry = create_phase2_source_onboarding_registry()
    parser_registry = create_phase1_parser_adapter_registry()
    parser_keys_by_source_family = {
        descriptor.source_family: descriptor.parser_key
        for descriptor in parser_registry.descriptors
    }

    assert parser_keys_by_source_family == PHASE2_ONBOARDING_PARSER_KEYS_BY_SOURCE_FAMILY
    for entry in onboarding_registry.entries:
        assert entry.parser_capability.parser_key == (
            parser_keys_by_source_family[entry.source_family]
        )


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
    mixed_source_ids = SourceOnboardingRegistry(
        entries=(
            _valid_entry("z_custom_source_id", source_family="ghg_protocol"),
            _valid_entry("a_custom_source_id", source_family="custom_source_family"),
        ),
    )
    mixed_source_ids_reordered = SourceOnboardingRegistry(
        entries=tuple(reversed(mixed_source_ids.entries)),
    )

    assert create_phase2_source_onboarding_registry() == registry
    assert list_source_onboarding_entries(registry) == registry.entries
    assert validate_source_onboarding_registry(mixed_source_ids) == mixed_source_ids
    with pytest.raises(ValueError, match="Phase 1 source order"):
        validate_source_onboarding_registry(reordered)
    with pytest.raises(ValueError, match="Phase 1 source order"):
        validate_source_onboarding_registry(mixed_source_ids_reordered)


def test_source_onboarding_registry_lookup_is_deterministic() -> None:
    registry = create_phase2_source_onboarding_registry()

    for source_family in EXPECTED_PHASE1_SOURCE_FAMILIES:
        entry = get_source_onboarding_entry(source_family, registry)

        assert entry is not None
        assert entry == get_source_onboarding_entry(source_family)
        assert entry.source_family == source_family

    assert get_source_onboarding_entry("unknown_source", registry) is None


def test_source_onboarding_registry_lookup_rejects_invalid_custom_registry() -> None:
    entry = _valid_entry("duplicate_registry_source")
    registry = SourceOnboardingRegistry(
        entries=(
            entry,
            replace(entry, source_family="duplicate_registry_source_two"),
        ),
    )

    with pytest.raises(ValueError, match="Duplicate source_id found"):
        get_source_onboarding_entry("duplicate_registry_source", registry)


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
    source_family: str | None = None,
    documents: tuple[SourceOnboardingDocument, ...] | None = None,
) -> SourceOnboardingRegistryEntry:
    return SourceOnboardingRegistryEntry(
        source_id=source_id,
        source_family=source_family or source_id,
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


def _registry_to_wire_snapshot(registry: SourceOnboardingRegistry) -> dict[str, object]:
    return {
        "phase2_source_families": list(PHASE2_ONBOARDING_SOURCE_FAMILIES),
        "entries": [
            {
                "source_id": entry.source_id,
                "source_family": entry.source_family,
                "display_name": entry.display_name,
                "documents": [
                    {
                        "document_id": document.document_id,
                        "display_name": document.display_name,
                        "source_reference": document.source_reference,
                        "expected_format": document.expected_format,
                        "required": document.required,
                    }
                    for document in entry.documents
                ],
                "discovery_strategy": entry.discovery_strategy.value,
                "parser_capability": {
                    "parser_key": entry.parser_capability.parser_key,
                    "parser_source_format": entry.parser_capability.parser_source_format,
                    "supports_parser_execution": (
                        entry.parser_capability.supports_parser_execution
                    ),
                    "capability_notes": entry.parser_capability.capability_notes,
                },
                "validation_expectations": {
                    "required_document_fields": list(
                        entry.validation_expectations.required_document_fields
                    ),
                    "checksum_required": (
                        entry.validation_expectations.checksum_required
                    ),
                    "schema_validation_required": (
                        entry.validation_expectations.schema_validation_required
                    ),
                    "validation_notes": (
                        entry.validation_expectations.validation_notes
                    ),
                },
                "update_cadence": entry.update_cadence.value,
                "runtime_safety": {
                    "allows_network_calls": entry.runtime_safety.allows_network_calls,
                    "allows_file_reads": entry.runtime_safety.allows_file_reads,
                    "allows_database_writes": (
                        entry.runtime_safety.allows_database_writes
                    ),
                    "requires_credentials": entry.runtime_safety.requires_credentials,
                    "safety_notes": entry.runtime_safety.safety_notes,
                },
                "enabled": entry.enabled,
            }
            for entry in registry.entries
        ],
    }


def _valid_document(document_id: str) -> SourceOnboardingDocument:
    return SourceOnboardingDocument(
        document_id=document_id,
        display_name="Declared document",
        source_reference=f"discovery://{document_id}",
        expected_format="discovery",
        required=True,
    )
