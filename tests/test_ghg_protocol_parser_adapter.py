from __future__ import annotations

import builtins
import sqlite3
import urllib.request

from carbonfactor_parser.parsers import (
    GHGProtocolParserAdapter,
    ParserAdapter,
    ParserExecutionResult,
    ParserExecutionResultStatus,
    create_parser_adapter_registry,
    create_parser_file_content_input,
    create_parser_input_contract,
    list_parser_adapters,
    plan_parser_execution,
    run_parser_execution,
)


def _ghg_input(
    *,
    source_family: str = "ghg_protocol",
    content_type: str | None = "text/csv",
    format_hint: str | None = None,
):
    return create_parser_input_contract(
        source_family=source_family,
        source_id=source_family,
        acquisition_status="acquired",
        artifact_reference=f"data/source-acquisition/{source_family}/source.csv",
        content_type=content_type,
        format_hint=format_hint,
    )


def test_ghg_protocol_parser_adapter_is_public_and_satisfies_protocol() -> None:
    adapter = GHGProtocolParserAdapter()

    assert isinstance(adapter, ParserAdapter)
    assert adapter.source_family == "ghg_protocol"
    assert adapter.supported_content_types == (
        "text/csv",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    assert adapter.supported_format_hints == ("csv", "xlsx")


def test_ghg_protocol_parser_adapter_can_parse_matching_metadata() -> None:
    adapter = GHGProtocolParserAdapter()

    assert adapter.can_parse(_ghg_input(content_type="text/csv")) is True
    assert adapter.can_parse(_ghg_input(content_type=None, format_hint="xlsx")) is True


def test_ghg_protocol_parser_adapter_rejects_non_matching_metadata() -> None:
    adapter = GHGProtocolParserAdapter()

    assert adapter.can_parse(_ghg_input(source_family="defra_desnz")) is False
    assert adapter.can_parse(
        _ghg_input(content_type="application/json", format_hint="json"),
    ) is False


def test_ghg_protocol_parse_returns_loaded_content_boundary_result() -> None:
    adapter = GHGProtocolParserAdapter()

    result = adapter.parse(_ghg_input())

    assert isinstance(result, ParserExecutionResult)
    assert result.status == ParserExecutionResultStatus.UNSUPPORTED
    assert result.issues[0].code == "GHG_PROTOCOL_PARSER_REQUIRES_LOADED_CONTENT"
    assert result.parser_metadata == {
        "adapter_kind": "source_specific_content_parser",
        "is_real_source_parser": True,
        "real_parsing_implemented": True,
        "requires_loaded_content": True,
    }


def test_ghg_protocol_adapter_can_be_registered_and_planned() -> None:
    adapter = GHGProtocolParserAdapter()
    registry = create_parser_adapter_registry((adapter,))

    assert list_parser_adapters(registry) == (adapter,)
    assert plan_parser_execution(
        _ghg_input(),
        (adapter,),
    ).selected_adapter_source_family == "ghg_protocol"


def test_run_parser_execution_returns_loaded_content_boundary_result() -> None:
    result = run_parser_execution(_ghg_input(), (GHGProtocolParserAdapter(),))

    assert result.status == ParserExecutionResultStatus.UNSUPPORTED
    assert result.issues[0].code == "GHG_PROTOCOL_PARSER_REQUIRES_LOADED_CONTENT"


def test_ghg_protocol_adapter_parse_content_uses_already_loaded_content() -> None:
    adapter = GHGProtocolParserAdapter()
    content_input = create_parser_file_content_input(
        source_family="ghg_protocol",
        source_id="ghg_protocol",
        content=(
            "record_type,source_year,source_version,factor_id,factor_name,"
            "factor_value,unit,category,subcategory,scope,gas,provenance_note\n"
            "emission_factor,2024,v1,GHG-001,Electricity,0.2,"
            "kg CO2e/kWh,Energy,Electricity,Scope 2,CO2e,row\n"
        ),
        content_type="text/csv",
        format_hint="csv",
    )

    result = adapter.parse_content(content_input)

    assert result.status == ParserExecutionResultStatus.SUCCESS
    assert result.parsed_record_count == 1
    assert result.parser_metadata["parser_kind"] == "ghg_protocol_normalized_content"


def test_ghg_protocol_parse_has_no_file_http_normalization_or_db_side_effects(
    monkeypatch,
    tmp_path,
) -> None:
    adapter = GHGProtocolParserAdapter()
    missing_artifact = tmp_path / "missing-ghg.csv"
    parser_input = create_parser_input_contract(
        source_family="ghg_protocol",
        source_id="ghg_protocol",
        acquisition_status="acquired",
        artifact_reference=str(missing_artifact),
        content_type="text/csv",
    )

    def fail_side_effect(*args, **kwargs):
        raise AssertionError("GHGProtocolParserAdapter.parse must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    result = adapter.parse(parser_input)

    assert result.status == ParserExecutionResultStatus.UNSUPPORTED
    assert not missing_artifact.exists()
