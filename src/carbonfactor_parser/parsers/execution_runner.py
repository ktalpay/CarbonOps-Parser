"""Parser execution runner boundary."""

from __future__ import annotations

from typing import Iterable

from carbonfactor_parser.parsers.adapter import ParserAdapter
from carbonfactor_parser.parsers.adapter_registry import (
    ParserAdapterRegistry,
    create_parser_adapter_registry,
    resolve_parser_adapters,
)
from carbonfactor_parser.parsers.execution_plan import (
    ParserExecutionPlanStatus,
    plan_parser_execution,
)
from carbonfactor_parser.parsers.execution_result import (
    ParserExecutionIssue,
    ParserExecutionIssueSeverity,
    ParserExecutionResult,
    ParserExecutionResultStatus,
    create_parser_execution_result,
)
from carbonfactor_parser.parsers.input_contract import ParserInputContract


def run_parser_execution(
    parser_input: ParserInputContract,
    registry_or_adapters: ParserAdapterRegistry | Iterable[ParserAdapter],
) -> ParserExecutionResult:
    """Run the parser execution boundary when planning says execution is ready."""

    registry = _normalize_registry(registry_or_adapters)
    plan = plan_parser_execution(parser_input, registry)

    if plan.status == ParserExecutionPlanStatus.INVALID_INPUT:
        return create_parser_execution_result(
            status=ParserExecutionResultStatus.FAILED,
            parser_input=parser_input,
            issues=tuple(
                ParserExecutionIssue(
                    code=issue.code,
                    message=issue.message,
                    severity=ParserExecutionIssueSeverity.ERROR,
                    location=issue.field_name,
                    context={"plan_status": plan.status.value},
                )
                for issue in plan.validation_result.issues
            ),
            parser_metadata={"plan_status": plan.status.value},
        )

    if plan.status == ParserExecutionPlanStatus.NO_ADAPTER:
        return create_parser_execution_result(
            status=ParserExecutionResultStatus.UNSUPPORTED,
            parser_input=parser_input,
            issues=(
                ParserExecutionIssue(
                    code="PARSER_EXECUTION_NO_ADAPTER",
                    message=(
                        "No parser adapter matched the parser input metadata."
                    ),
                    severity=ParserExecutionIssueSeverity.WARNING,
                    location="parser_adapter_registry",
                    context={"plan_status": plan.status.value},
                ),
            ),
            parser_metadata={"plan_status": plan.status.value},
        )

    adapter = _select_ready_adapter(parser_input, registry)
    if adapter is None:
        return create_parser_execution_result(
            status=ParserExecutionResultStatus.UNSUPPORTED,
            parser_input=parser_input,
            issues=(
                ParserExecutionIssue(
                    code="PARSER_EXECUTION_SELECTED_ADAPTER_UNAVAILABLE",
                    message=(
                        "The ready parser execution plan did not resolve to an adapter."
                    ),
                    severity=ParserExecutionIssueSeverity.ERROR,
                    location="parser_adapter_registry",
                    context={"plan_status": plan.status.value},
                ),
            ),
            parser_metadata={"plan_status": plan.status.value},
        )

    try:
        return adapter.parse(parser_input)
    except Exception as exc:  # noqa: BLE001
        return create_parser_execution_result(
            status=ParserExecutionResultStatus.FAILED,
            parser_input=parser_input,
            issues=(
                ParserExecutionIssue(
                    code="PARSER_EXECUTION_ADAPTER_EXCEPTION",
                    message=str(exc) or exc.__class__.__name__,
                    severity=ParserExecutionIssueSeverity.ERROR,
                    location=adapter.source_family,
                    context={
                        "exception_type": exc.__class__.__name__,
                        "plan_status": plan.status.value,
                    },
                ),
            ),
            parser_metadata={
                "adapter_source_family": adapter.source_family,
                "plan_status": plan.status.value,
            },
        )


def _select_ready_adapter(
    parser_input: ParserInputContract,
    registry: ParserAdapterRegistry,
) -> ParserAdapter | None:
    matches = resolve_parser_adapters(registry, parser_input)
    if not matches:
        return None
    return matches[0]


def _normalize_registry(
    registry_or_adapters: ParserAdapterRegistry | Iterable[ParserAdapter],
) -> ParserAdapterRegistry:
    if isinstance(registry_or_adapters, ParserAdapterRegistry):
        return registry_or_adapters

    return create_parser_adapter_registry(registry_or_adapters)
