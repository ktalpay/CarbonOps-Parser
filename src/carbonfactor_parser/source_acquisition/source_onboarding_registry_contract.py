"""Runtime-passive Phase 2 source onboarding registry contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


PHASE2_ONBOARDING_SOURCE_FAMILIES = (
    "ghg_protocol",
    "defra_desnz",
    "ipcc_efdb",
)

PHASE2_ONBOARDING_PARSER_KEYS_BY_SOURCE_FAMILY = {
    "ghg_protocol": "ghg_protocol_phase1_parser",
    "defra_desnz": "defra_desnz_phase1_parser",
    "ipcc_efdb": "ipcc_efdb_phase1_parser",
}


class SourceOnboardingDiscoveryStrategy(str, Enum):
    """Source discovery strategies that can be declared without execution."""

    DECLARED_REFERENCE = "declared_reference"
    SOURCE_SPECIFIC_DISCOVERY = "source_specific_discovery"


class SourceOnboardingUpdateCadence(str, Enum):
    """Declared source review cadence values for onboarding metadata."""

    UNKNOWN = "unknown"
    ANNUAL = "annual"
    PERIODIC = "periodic"


@dataclass(frozen=True)
class SourceOnboardingDocument:
    """Metadata contract for one document expected from a source family."""

    document_id: str
    display_name: str
    source_reference: str
    expected_format: str
    required: bool = True


@dataclass(frozen=True)
class SourceOnboardingParserCapability:
    """Parser capability metadata for an onboarded source family."""

    parser_key: str
    parser_source_format: str
    supports_parser_execution: bool
    capability_notes: str


@dataclass(frozen=True)
class SourceOnboardingValidationExpectations:
    """Declared validation expectations for future source onboarding."""

    required_document_fields: tuple[str, ...]
    checksum_required: bool
    schema_validation_required: bool
    validation_notes: str


@dataclass(frozen=True)
class SourceOnboardingRuntimeSafety:
    """Runtime safety metadata for source onboarding planning."""

    allows_network_calls: bool
    allows_file_reads: bool
    allows_database_writes: bool
    requires_credentials: bool
    safety_notes: str


@dataclass(frozen=True)
class SourceOnboardingRegistryEntry:
    """Complete onboarding metadata for one source family."""

    source_id: str
    source_family: str
    display_name: str
    documents: tuple[SourceOnboardingDocument, ...]
    discovery_strategy: SourceOnboardingDiscoveryStrategy
    parser_capability: SourceOnboardingParserCapability
    validation_expectations: SourceOnboardingValidationExpectations
    update_cadence: SourceOnboardingUpdateCadence
    runtime_safety: SourceOnboardingRuntimeSafety
    enabled: bool = True


@dataclass(frozen=True)
class SourceOnboardingRegistry:
    """Deterministic registry of source onboarding metadata."""

    entries: tuple[SourceOnboardingRegistryEntry, ...]


def create_phase2_source_onboarding_registry() -> SourceOnboardingRegistry:
    """Return Phase 2 onboarding metadata for existing Phase 1 source families."""

    entries = tuple(
        SourceOnboardingRegistryEntry(
            source_id=source_family,
            source_family=source_family,
            display_name=display_name,
            documents=(
                SourceOnboardingDocument(
                    document_id=f"{source_family}_declared_reference",
                    display_name=f"{display_name} declared reference",
                    source_reference=f"discovery://{source_family}/onboarding",
                    expected_format="discovery",
                    required=True,
                ),
            ),
            discovery_strategy=SourceOnboardingDiscoveryStrategy.DECLARED_REFERENCE,
            parser_capability=SourceOnboardingParserCapability(
                parser_key=(
                    PHASE2_ONBOARDING_PARSER_KEYS_BY_SOURCE_FAMILY[source_family]
                ),
                parser_source_format="discovery_reference",
                supports_parser_execution=False,
                capability_notes=(
                    "Registry metadata only; parser execution is outside this "
                    "onboarding contract."
                ),
            ),
            validation_expectations=SourceOnboardingValidationExpectations(
                required_document_fields=(
                    "document_id",
                    "display_name",
                    "source_reference",
                    "expected_format",
                ),
                checksum_required=False,
                schema_validation_required=False,
                validation_notes=(
                    "Declared discovery references are validated for contract "
                    "shape only."
                ),
            ),
            update_cadence=SourceOnboardingUpdateCadence.UNKNOWN,
            runtime_safety=SourceOnboardingRuntimeSafety(
                allows_network_calls=False,
                allows_file_reads=False,
                allows_database_writes=False,
                requires_credentials=False,
                safety_notes=(
                    "Default onboarding registry is runtime-passive and local-only."
                ),
            ),
            enabled=True,
        )
        for source_family, display_name in (
            ("ghg_protocol", "GHG Protocol"),
            ("defra_desnz", "DEFRA/DESNZ"),
            ("ipcc_efdb", "IPCC EFDB"),
        )
    )
    registry = SourceOnboardingRegistry(entries=entries)
    validate_source_onboarding_registry(registry)
    return registry


def validate_source_onboarding_registry(
    registry: SourceOnboardingRegistry,
) -> SourceOnboardingRegistry:
    """Validate onboarding registry shape and deterministic identifiers."""

    if not isinstance(registry, SourceOnboardingRegistry):
        raise TypeError("registry must be a SourceOnboardingRegistry.")

    seen_source_ids: set[str] = set()
    seen_source_families: set[str] = set()
    seen_document_ids: set[str] = set()

    for index, entry in enumerate(registry.entries):
        if not isinstance(entry, SourceOnboardingRegistryEntry):
            raise TypeError(
                f"entries[{index}] must be a SourceOnboardingRegistryEntry.",
            )

        _validate_required_string(entry.source_id, "source_id", entry.source_id)
        _validate_required_string(
            entry.source_family,
            "source_family",
            entry.source_id,
        )
        _validate_required_string(entry.display_name, "display_name", entry.source_id)
        if not entry.documents:
            raise ValueError(
                f"documents must include at least one document for source_id "
                f"'{entry.source_id}'."
            )
        if entry.source_id in seen_source_ids:
            raise ValueError(f"Duplicate source_id found: {entry.source_id}")
        if entry.source_family in seen_source_families:
            raise ValueError(
                f"Duplicate source_family found: {entry.source_family}",
            )
        seen_source_ids.add(entry.source_id)
        seen_source_families.add(entry.source_family)

        _validate_document_order(entry)
        for document in entry.documents:
            _validate_document(entry, document, seen_document_ids)
        if not isinstance(entry.discovery_strategy, SourceOnboardingDiscoveryStrategy):
            raise TypeError(
                f"discovery_strategy must be a SourceOnboardingDiscoveryStrategy "
                f"for source_id '{entry.source_id}'."
            )
        if not isinstance(entry.update_cadence, SourceOnboardingUpdateCadence):
            raise TypeError(
                f"update_cadence must be a SourceOnboardingUpdateCadence for "
                f"source_id '{entry.source_id}'."
            )
        _validate_bool(entry.enabled, "enabled", entry.source_id)
        _validate_parser_capability(entry)
        _validate_validation_expectations(entry)
        _validate_runtime_safety(entry)

    _validate_registry_order(registry.entries)
    return registry


def list_source_onboarding_entries(
    registry: SourceOnboardingRegistry | None = None,
) -> tuple[SourceOnboardingRegistryEntry, ...]:
    """List source onboarding entries without executing discovery or parsing."""

    active_registry = (
        create_phase2_source_onboarding_registry()
        if registry is None
        else validate_source_onboarding_registry(registry)
    )
    return active_registry.entries


def get_source_onboarding_entry(
    source_family: str,
    registry: SourceOnboardingRegistry | None = None,
) -> SourceOnboardingRegistryEntry | None:
    """Return one onboarding entry by source family, if declared."""

    for entry in list_source_onboarding_entries(registry):
        if entry.source_family == source_family:
            return entry
    return None


def _validate_document_order(entry: SourceOnboardingRegistryEntry) -> None:
    document_ids = tuple(document.document_id for document in entry.documents)
    if document_ids != tuple(sorted(document_ids)):
        raise ValueError(
            f"documents must be ordered by document_id for source_id "
            f"'{entry.source_id}'."
        )


def _validate_document(
    entry: SourceOnboardingRegistryEntry,
    document: SourceOnboardingDocument,
    seen_document_ids: set[str],
) -> None:
    if not isinstance(document, SourceOnboardingDocument):
        raise TypeError(
            f"documents for source_id '{entry.source_id}' must be "
            "SourceOnboardingDocument values."
        )

    _validate_required_string(document.document_id, "document_id", entry.source_id)
    _validate_required_string(
        document.display_name,
        "document.display_name",
        entry.source_id,
    )
    _validate_required_string(
        document.source_reference,
        "source_reference",
        entry.source_id,
    )
    _validate_required_string(
        document.expected_format,
        "expected_format",
        entry.source_id,
    )
    if document.document_id in seen_document_ids:
        raise ValueError(f"Duplicate document_id found: {document.document_id}")
    seen_document_ids.add(document.document_id)
    _validate_bool(document.required, "required", entry.source_id)


def _validate_parser_capability(entry: SourceOnboardingRegistryEntry) -> None:
    capability = entry.parser_capability
    if not isinstance(capability, SourceOnboardingParserCapability):
        raise TypeError(
            f"parser_capability must be a SourceOnboardingParserCapability for "
            f"source_id '{entry.source_id}'."
    )
    _validate_required_string(capability.parser_key, "parser_key", entry.source_id)
    _validate_required_string(
        capability.parser_source_format,
        "parser_source_format",
        entry.source_id,
    )
    _validate_required_string(
        capability.capability_notes,
        "capability_notes",
        entry.source_id,
    )
    _validate_bool(
        capability.supports_parser_execution,
        "supports_parser_execution",
        entry.source_id,
    )


def _validate_validation_expectations(entry: SourceOnboardingRegistryEntry) -> None:
    expectations = entry.validation_expectations
    if not isinstance(expectations, SourceOnboardingValidationExpectations):
        raise TypeError(
            "validation_expectations must be a "
            f"SourceOnboardingValidationExpectations for source_id '{entry.source_id}'."
        )
    if not expectations.required_document_fields:
        raise ValueError(
            f"required_document_fields must not be empty for source_id "
            f"'{entry.source_id}'."
        )
    for field_name in expectations.required_document_fields:
        _validate_required_string(
            field_name,
            "required_document_fields",
            entry.source_id,
        )
    _validate_required_string(
        expectations.validation_notes,
        "validation_notes",
        entry.source_id,
    )
    _validate_bool(expectations.checksum_required, "checksum_required", entry.source_id)
    _validate_bool(
        expectations.schema_validation_required,
        "schema_validation_required",
        entry.source_id,
    )


def _validate_runtime_safety(entry: SourceOnboardingRegistryEntry) -> None:
    safety = entry.runtime_safety
    if not isinstance(safety, SourceOnboardingRuntimeSafety):
        raise TypeError(
            f"runtime_safety must be a SourceOnboardingRuntimeSafety for source_id "
            f"'{entry.source_id}'."
        )
    _validate_required_string(safety.safety_notes, "safety_notes", entry.source_id)
    _validate_bool(safety.allows_network_calls, "allows_network_calls", entry.source_id)
    _validate_bool(safety.allows_file_reads, "allows_file_reads", entry.source_id)
    _validate_bool(
        safety.allows_database_writes,
        "allows_database_writes",
        entry.source_id,
    )
    _validate_bool(safety.requires_credentials, "requires_credentials", entry.source_id)


def _validate_registry_order(
    entries: tuple[SourceOnboardingRegistryEntry, ...],
) -> None:
    source_ids = tuple(entry.source_id for entry in entries)
    if source_ids != tuple(sorted(source_ids, key=_source_order_key)):
        raise ValueError(
            "entries must follow Phase 1 source order, then source_id order.",
        )


def _source_order_key(source_id: str) -> tuple[int, str]:
    try:
        return (PHASE2_ONBOARDING_SOURCE_FAMILIES.index(source_id), source_id)
    except ValueError:
        return (len(PHASE2_ONBOARDING_SOURCE_FAMILIES), source_id)


def _validate_required_string(value: str, field_name: str, source_id: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{field_name} must be a non-empty string for source_id '{source_id}'.",
        )


def _validate_bool(value: bool, field_name: str, source_id: str) -> None:
    if not isinstance(value, bool):
        raise TypeError(
            f"{field_name} must be a bool for source_id '{source_id}'.",
        )
