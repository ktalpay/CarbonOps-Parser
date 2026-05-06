import builtins
import sqlite3
import urllib.request

import pytest

from carbonfactor_parser.parsers import (
    NoopParserAdapter,
    ParserAdapter,
    ParserExecutionPlanStatus,
    create_parser_adapter_registry,
    create_parser_input_contract,
    list_parser_adapters,
    plan_parser_execution,
)


def _noop_input(
    *,
    source_family: str = "noop",
    content_type: str | None = "application/x-carbonops-noop",
    format_hint: str | None = None,
):
    return create_parser_input_contract(
        source_family=source_family,
        source_id=source_family,
        acquisition_status="acquired",
        artifact_reference=f"data/source-acquisition/{source_family}/noop.artifact",
        content_type=content_type,
        format_hint=format_hint,
    )


def test_noop_parser_adapter_is_public_and_satisfies_protocol() -> None:
    adapter = NoopParserAdapter()

    assert isinstance(adapter, ParserAdapter)
    assert adapter.source_family == "noop"
    assert adapter.supported_content_types == ("application/x-carbonops-noop",)
    assert adapter.supported_format_hints == ("noop",)


def test_noop_parser_adapter_can_parse_matching_content_type() -> None:
    adapter = NoopParserAdapter()

    assert adapter.can_parse(_noop_input()) is True


def test_noop_parser_adapter_can_parse_matching_format_hint() -> None:
    adapter = NoopParserAdapter()

    assert adapter.can_parse(
        _noop_input(content_type=None, format_hint="noop"),
    ) is True


def test_noop_parser_adapter_rejects_non_matching_input() -> None:
    adapter = NoopParserAdapter()

    assert adapter.can_parse(
        _noop_input(
            source_family="defra_desnz",
            content_type="text/csv",
            format_hint="csv",
        ),
    ) is False


def test_noop_parser_adapter_can_be_registered() -> None:
    adapter = NoopParserAdapter()
    registry = create_parser_adapter_registry((adapter,))

    assert list_parser_adapters(registry) == (adapter,)


def test_parser_execution_planning_is_ready_with_noop_adapter() -> None:
    adapter = NoopParserAdapter()

    plan = plan_parser_execution(_noop_input(), (adapter,))

    assert plan.status == ParserExecutionPlanStatus.READY
    assert plan.selected_adapter_source_family == "noop"


def test_noop_parse_performs_no_side_effects_and_produces_no_output(
    monkeypatch,
    tmp_path,
) -> None:
    adapter = NoopParserAdapter()
    parser_input = create_parser_input_contract(
        source_family="noop",
        source_id="noop",
        acquisition_status="acquired",
        artifact_reference=str(tmp_path / "missing.noop"),
        content_type="application/x-carbonops-noop",
    )

    def fail_side_effect(*args, **kwargs):
        raise AssertionError("NoopParserAdapter.parse must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    with pytest.raises(NotImplementedError, match="does not perform parser execution"):
        adapter.parse(parser_input)

    assert not (tmp_path / "missing.noop").exists()
