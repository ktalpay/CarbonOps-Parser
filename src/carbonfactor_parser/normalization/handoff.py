"""Parser-to-normalization handoff model skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from carbonfactor_parser.parsers import ParserResult
from carbonfactor_parser.parsers.execution_result import (
    ParserExecutionResult,
    ParserExecutionResultStatus,
)


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


class ParserExecutionNormalizationHandoffStatus(str, Enum):
    """Status for parser execution result to normalization handoff."""

    READY = "ready"
    NOT_READY = "not_ready"


@dataclass(frozen=True)
class ParserExecutionNormalizationHandoffIssue:
    """Issue explaining why a parser execution result is not ready."""

    code: str
    message: str
    parser_status: ParserExecutionResultStatus


@dataclass(frozen=True)
class ParserExecutionNormalizationHandoff:
    """Successful parser execution metadata prepared for future normalization."""

    source_family: str
    source_id: str
    parsed_record_count: int
    parser_status: ParserExecutionResultStatus
    parser_metadata: Mapping[str, object] | None = None
    parsed_records_payload_status: str = "deferred"


@dataclass(frozen=True)
class ParserExecutionNormalizationHandoffResult:
    """Structured result for parser execution to normalization handoff."""

    status: ParserExecutionNormalizationHandoffStatus
    parser_status: ParserExecutionResultStatus
    handoff: ParserExecutionNormalizationHandoff | None = None
    issues: tuple[ParserExecutionNormalizationHandoffIssue, ...] = ()


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


def build_parser_execution_normalization_handoff(
    parser_result: ParserExecutionResult,
) -> ParserExecutionNormalizationHandoffResult:
    """Build a normalization handoff from a successful parser execution result."""

    if parser_result.status != ParserExecutionResultStatus.SUCCESS:
        return ParserExecutionNormalizationHandoffResult(
            status=ParserExecutionNormalizationHandoffStatus.NOT_READY,
            parser_status=parser_result.status,
            issues=(
                ParserExecutionNormalizationHandoffIssue(
                    code="PARSER_EXECUTION_HANDOFF_NOT_READY",
                    message=(
                        "Parser execution result must be success before "
                        "normalization handoff is ready."
                    ),
                    parser_status=parser_result.status,
                ),
            ),
        )

    return ParserExecutionNormalizationHandoffResult(
        status=ParserExecutionNormalizationHandoffStatus.READY,
        parser_status=parser_result.status,
        handoff=ParserExecutionNormalizationHandoff(
            source_family=parser_result.source_family,
            source_id=parser_result.source_id,
            parsed_record_count=parser_result.parsed_record_count,
            parser_status=parser_result.status,
            parser_metadata=(
                dict(parser_result.parser_metadata)
                if parser_result.parser_metadata is not None
                else None
            ),
        ),
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
