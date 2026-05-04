"""Parser-to-normalization handoff model skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from carbonfactor_parser.parsers import ParserResult


@dataclass(frozen=True)
class ParserNormalizationHandoffEntry:
    """One parser record prepared for a future normalization boundary."""

    record_id: str
    parser_record: tuple[tuple[str, Any], ...]
    source_reference: str | None = None
    is_artificial: bool = True


@dataclass(frozen=True)
class ParserNormalizationHandoff:
    """Parser output metadata prepared for future normalization input."""

    parser_record_count: int
    issue_count: int
    entries: tuple[ParserNormalizationHandoffEntry, ...]
    source_reference: str | None = None
    is_artificial: bool = True


def build_parser_normalization_handoff(
    parser_result: ParserResult,
) -> ParserNormalizationHandoff:
    """Build a deterministic handoff model from an already-computed parser result."""

    entries = tuple(
        _entry_from_parser_record(
            parser_record,
            position=position,
            source_reference=parser_result.source_document.source_name,
        )
        for position, parser_record in enumerate(parser_result.records, start=1)
    )

    return ParserNormalizationHandoff(
        parser_record_count=len(parser_result.records),
        issue_count=len(parser_result.issues),
        entries=entries,
        source_reference=parser_result.source_document.source_name,
    )


def _entry_from_parser_record(
    parser_record: Mapping[str, Any],
    *,
    position: int,
    source_reference: str,
) -> ParserNormalizationHandoffEntry:
    record_items = _record_items(parser_record)

    return ParserNormalizationHandoffEntry(
        record_id=_record_id(record_items, position=position),
        parser_record=record_items,
        source_reference=source_reference,
    )


def _record_items(parser_record: Mapping[str, Any]) -> tuple[tuple[str, Any], ...]:
    return tuple(sorted(parser_record.items(), key=lambda item: item[0]))


def _record_id(
    record_items: tuple[tuple[str, Any], ...],
    *,
    position: int,
) -> str:
    for key, value in record_items:
        if key == "record_id" and isinstance(value, str) and value.strip():
            return value
    return f"parser-record-{position:03d}"
