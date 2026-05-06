"""Parser execution planning boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from carbonfactor_parser.parsers.adapter import ParserAdapter
from carbonfactor_parser.parsers.adapter_registry import (
    ParserAdapterRegistry,
    create_parser_adapter_registry,
    resolve_parser_adapters,
)
from carbonfactor_parser.parsers.input_contract import (
    ParserInputContract,
    ParserInputValidationResult,
    validate_parser_input_contract,
)


class ParserExecutionPlanStatus(str, Enum):
    """Parser execution planning status values."""

    READY = "ready"
    INVALID_INPUT = "invalid_input"
    NO_ADAPTER = "no_adapter"


@dataclass(frozen=True)
class ParserExecutionPlan:
    """Metadata-only plan for future parser execution."""

    parser_input: ParserInputContract
    validation_result: ParserInputValidationResult
    status: ParserExecutionPlanStatus
    selected_adapter_source_family: str | None = None
    issues: tuple[str, ...] = ()


def plan_parser_execution(
    parser_input: ParserInputContract,
    registry_or_adapters: ParserAdapterRegistry | Iterable[ParserAdapter],
) -> ParserExecutionPlan:
    """Plan future parser execution without calling parse()."""

    validation_result = validate_parser_input_contract(parser_input)
    if not validation_result.is_valid:
        return ParserExecutionPlan(
            parser_input=parser_input,
            validation_result=validation_result,
            status=ParserExecutionPlanStatus.INVALID_INPUT,
            issues=tuple(issue.code for issue in validation_result.issues),
        )

    registry = _normalize_registry(registry_or_adapters)
    matches = resolve_parser_adapters(registry, parser_input)

    if not matches:
        return ParserExecutionPlan(
            parser_input=parser_input,
            validation_result=validation_result,
            status=ParserExecutionPlanStatus.NO_ADAPTER,
            issues=("PARSER_EXECUTION_NO_ADAPTER",),
        )

    selected_adapter = matches[0]
    return ParserExecutionPlan(
        parser_input=parser_input,
        validation_result=validation_result,
        status=ParserExecutionPlanStatus.READY,
        selected_adapter_source_family=selected_adapter.source_family,
    )


def _normalize_registry(
    registry_or_adapters: ParserAdapterRegistry | Iterable[ParserAdapter],
) -> ParserAdapterRegistry:
    if isinstance(registry_or_adapters, ParserAdapterRegistry):
        return registry_or_adapters

    return create_parser_adapter_registry(registry_or_adapters)
