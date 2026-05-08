"""Runtime-passive Phase 1 parser adapter readiness report contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from carbonfactor_parser.parsers.adapter_registry_contract import (
    Phase1ParserAdapterRegistry,
    list_phase1_parser_adapter_descriptors,
)


@dataclass(frozen=True)
class ParserAdapterReadinessCapability:
    """Normalized capability metadata for one parser adapter descriptor."""

    source_family: str
    source_key: str
    parser_key: str
    parser_source_format: str
    format_hint: str
    supports_parser_execution: bool
    supports_file_reads: bool
    supports_content_inspection: bool


@dataclass(frozen=True)
class ParserAdapterReadinessReportEntry:
    """Readiness metadata for one registered Phase 1 parser adapter."""

    source_family: str
    source_key: str
    parser_key: str
    display_name: str | None
    name: str | None
    readiness: str
    execution_mode: str
    capability: ParserAdapterReadinessCapability


@dataclass(frozen=True)
class ParserAdapterReadinessReport:
    """Deterministic metadata-only report for registered Phase 1 adapters."""

    entries: tuple[ParserAdapterReadinessReportEntry, ...]

    @property
    def adapter_count(self) -> int:
        return len(self.entries)

    @property
    def source_keys(self) -> tuple[str, ...]:
        return tuple(entry.source_key for entry in self.entries)

    @property
    def parser_keys(self) -> tuple[str, ...]:
        return tuple(entry.parser_key for entry in self.entries)


def build_phase1_parser_adapter_readiness_report(
    registry: Phase1ParserAdapterRegistry | None = None,
) -> ParserAdapterReadinessReport:
    """Summarize registered Phase 1 parser adapters without execution."""

    entries = tuple(
        _entry_from_descriptor(descriptor)
        for descriptor in list_phase1_parser_adapter_descriptors(registry)
    )
    return ParserAdapterReadinessReport(entries=entries)


def _entry_from_descriptor(
    descriptor: Any,
) -> ParserAdapterReadinessReportEntry:
    capability = descriptor.capability
    source_key = descriptor.source_family

    return ParserAdapterReadinessReportEntry(
        source_family=descriptor.source_family,
        source_key=source_key,
        parser_key=descriptor.parser_key,
        display_name=_optional_text_metadata(descriptor, "display_name"),
        name=_optional_text_metadata(descriptor, "name"),
        readiness=_metadata_value(descriptor.readiness),
        execution_mode=_metadata_value(descriptor.mode),
        capability=ParserAdapterReadinessCapability(
            source_family=capability.source_family,
            source_key=capability.source_family,
            parser_key=capability.parser_key,
            parser_source_format=_metadata_value(capability.parser_source_format),
            format_hint=capability.format_hint,
            supports_parser_execution=capability.supports_parser_execution,
            supports_file_reads=capability.supports_file_reads,
            supports_content_inspection=capability.supports_content_inspection,
        ),
    )


def _optional_text_metadata(descriptor: Any, field_name: str) -> str | None:
    value = getattr(descriptor, field_name, None)
    return value if isinstance(value, str) else None


def _metadata_value(value: Any) -> str:
    enum_value = getattr(value, "value", value)
    return str(enum_value)
