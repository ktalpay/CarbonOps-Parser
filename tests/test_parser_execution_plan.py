import builtins
import sqlite3
import urllib.request

from carbonfactor_parser.parsers import (
    ParserExecutionPlan,
    ParserExecutionPlanStatus,
    create_parser_adapter_registry,
    create_parser_input_contract,
    plan_parser_execution,
)


class PlanningFakeParserAdapter:
    def __init__(
        self,
        *,
        source_family: str,
        supported_content_types: tuple[str, ...] = (),
        supported_format_hints: tuple[str, ...] = (),
    ) -> None:
        self.source_family = source_family
        self.supported_content_types = supported_content_types
        self.supported_format_hints = supported_format_hints
        self.can_parse_call_count = 0
        self.parse_call_count = 0

    def can_parse(self, parser_input):  # noqa: ANN001, ANN201
        self.can_parse_call_count += 1
        if parser_input.source_family != self.source_family:
            return False
        if parser_input.content_type in self.supported_content_types:
            return True
        return parser_input.format_hint in self.supported_format_hints

    def parse(self, parser_input):  # noqa: ANN001, ANN201
        self.parse_call_count += 1
        raise AssertionError("planning must not execute parser adapters")


def _valid_parser_input():
    return create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference="data/source-acquisition/defra_desnz/source.csv",
        content_type="text/csv",
    )


def test_valid_input_with_matching_adapter_returns_ready_plan() -> None:
    adapter = PlanningFakeParserAdapter(
        source_family="defra_desnz",
        supported_content_types=("text/csv",),
    )
    registry = create_parser_adapter_registry((adapter,))

    plan = plan_parser_execution(_valid_parser_input(), registry)

    assert isinstance(plan, ParserExecutionPlan)
    assert plan.status == ParserExecutionPlanStatus.READY
    assert plan.selected_adapter_source_family == "defra_desnz"
    assert plan.issues == ()


def test_invalid_input_returns_invalid_input_plan_without_resolution() -> None:
    adapter = PlanningFakeParserAdapter(
        source_family="defra_desnz",
        supported_content_types=("text/csv",),
    )
    registry = create_parser_adapter_registry((adapter,))
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference=" ",
        content_type="text/csv",
    )

    plan = plan_parser_execution(parser_input, registry)

    assert plan.status == ParserExecutionPlanStatus.INVALID_INPUT
    assert plan.selected_adapter_source_family is None
    assert plan.issues == ("PARSER_INPUT_MISSING_ARTIFACT_REFERENCE",)
    assert adapter.can_parse_call_count == 0
    assert adapter.parse_call_count == 0


def test_valid_input_with_no_matching_adapter_returns_no_adapter_plan() -> None:
    adapter = PlanningFakeParserAdapter(
        source_family="ghg_protocol",
        supported_content_types=("text/csv",),
    )
    registry = create_parser_adapter_registry((adapter,))

    plan = plan_parser_execution(_valid_parser_input(), registry)

    assert plan.status == ParserExecutionPlanStatus.NO_ADAPTER
    assert plan.selected_adapter_source_family is None
    assert plan.issues == ("PARSER_EXECUTION_NO_ADAPTER",)


def test_planner_accepts_registered_adapters_iterable() -> None:
    adapter = PlanningFakeParserAdapter(
        source_family="defra_desnz",
        supported_content_types=("text/csv",),
    )

    plan = plan_parser_execution(_valid_parser_input(), (adapter,))

    assert plan.status == ParserExecutionPlanStatus.READY
    assert plan.selected_adapter_source_family == "defra_desnz"


def test_parse_is_never_called_during_planning() -> None:
    adapter = PlanningFakeParserAdapter(
        source_family="defra_desnz",
        supported_content_types=("text/csv",),
    )
    registry = create_parser_adapter_registry((adapter,))

    plan = plan_parser_execution(_valid_parser_input(), registry)

    assert plan.status == ParserExecutionPlanStatus.READY
    assert adapter.can_parse_call_count == 1
    assert adapter.parse_call_count == 0


def test_validation_result_is_included_in_plan() -> None:
    plan = plan_parser_execution(
        _valid_parser_input(),
        create_parser_adapter_registry(),
    )

    assert plan.validation_result.is_valid is True
    assert plan.validation_result.issues == ()
    assert plan.parser_input == _valid_parser_input()


def test_selected_adapter_source_family_is_represented_when_ready() -> None:
    adapter = PlanningFakeParserAdapter(
        source_family="defra_desnz",
        supported_content_types=("text/csv",),
    )

    plan = plan_parser_execution(_valid_parser_input(), (adapter,))

    assert plan.selected_adapter_source_family == adapter.source_family


def test_planning_has_no_file_http_normalization_or_db_side_effects(
    monkeypatch,
    tmp_path,
) -> None:
    adapter = PlanningFakeParserAdapter(
        source_family="defra_desnz",
        supported_content_types=("text/csv",),
    )
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference=str(tmp_path / "missing.csv"),
        content_type="text/csv",
    )

    def fail_side_effect(*args, **kwargs):
        raise AssertionError("planning must use metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    plan = plan_parser_execution(parser_input, (adapter,))

    assert plan.status == ParserExecutionPlanStatus.READY
    assert not (tmp_path / "missing.csv").exists()
