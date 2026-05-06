"""Parser execution result boundary contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from carbonfactor_parser.parsers.input_contract import ParserInputContract
from carbonfactor_parser.parsers.raw_record import ParsedRawRecordPayload


class ParserExecutionResultStatus(str, Enum):
    """Parser execution result status values."""

    SUCCESS = "success"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"
    NO_RECORDS = "no_records"


class ParserExecutionIssueSeverity(str, Enum):
    """Parser execution issue severity values."""

    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ParserExecutionIssue:
    """Structured parser execution issue metadata."""

    code: str
    message: str
    severity: ParserExecutionIssueSeverity
    location: str | None = None
    context: Mapping[str, object] | None = None


@dataclass(frozen=True)
class ParserExecutionResult:
    """Parser execution outcome boundary, separate from normalization."""

    status: ParserExecutionResultStatus
    source_family: str
    source_id: str
    parser_input: ParserInputContract
    parsed_record_count: int = 0
    issues: tuple[ParserExecutionIssue, ...] = ()
    parser_metadata: Mapping[str, object] | None = None
    raw_record_payload: ParsedRawRecordPayload | None = None


def create_parser_execution_result(
    *,
    status: ParserExecutionResultStatus,
    parser_input: ParserInputContract,
    parsed_record_count: int = 0,
    issues: tuple[ParserExecutionIssue, ...] | list[ParserExecutionIssue] = (),
    parser_metadata: Mapping[str, object] | None = None,
    raw_record_payload: ParsedRawRecordPayload | None = None,
) -> ParserExecutionResult:
    """Create a parser execution result without executing a parser."""

    return ParserExecutionResult(
        status=status,
        source_family=parser_input.source_family,
        source_id=parser_input.source_id,
        parser_input=parser_input,
        parsed_record_count=parsed_record_count,
        issues=tuple(issues),
        parser_metadata=dict(parser_metadata) if parser_metadata is not None else None,
        raw_record_payload=raw_record_payload,
    )
