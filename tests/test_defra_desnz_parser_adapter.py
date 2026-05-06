import builtins
import sqlite3
import urllib.request

from carbonfactor_parser.parsers import (
    DefraDesnzParserAdapter,
    ParserAdapter,
    ParserExecutionPlanStatus,
    ParserExecutionResult,
    ParserExecutionResultStatus,
    create_parser_adapter_registry,
    create_parser_input_contract,
    list_parser_adapters,
    plan_parser_execution,
    run_parser_execution,
)


def _defra_desnz_input(
    *,
    source_family: str = "defra_desnz",
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


def test_defra_desnz_parser_adapter_is_public_and_satisfies_protocol() -> None:
    adapter = DefraDesnzParserAdapter()

    assert isinstance(adapter, ParserAdapter)
    assert adapter.source_family == "defra_desnz"
    assert adapter.supported_content_types == (
        "text/csv",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    assert adapter.supported_format_hints == ("csv", "xlsx")


def test_defra_desnz_parser_adapter_can_parse_matching_content_type() -> None:
    adapter = DefraDesnzParserAdapter()

    assert adapter.can_parse(_defra_desnz_input(content_type="text/csv")) is True


def test_defra_desnz_parser_adapter_can_parse_matching_format_hint() -> None:
    adapter = DefraDesnzParserAdapter()

    assert adapter.can_parse(
        _defra_desnz_input(content_type=None, format_hint="xlsx"),
    ) is True


def test_defra_desnz_parser_adapter_rejects_non_matching_source_family() -> None:
    adapter = DefraDesnzParserAdapter()

    assert adapter.can_parse(
        _defra_desnz_input(source_family="ghg_protocol", content_type="text/csv"),
    ) is False


def test_defra_desnz_parser_adapter_rejects_unsupported_format_metadata() -> None:
    adapter = DefraDesnzParserAdapter()

    assert adapter.can_parse(
        _defra_desnz_input(
            content_type="application/json",
            format_hint="json",
        ),
    ) is False


def test_defra_desnz_parse_returns_skeleton_unsupported_result() -> None:
    adapter = DefraDesnzParserAdapter()

    result = adapter.parse(_defra_desnz_input())

    assert isinstance(result, ParserExecutionResult)
    assert result.status == ParserExecutionResultStatus.UNSUPPORTED
    assert result.parsed_record_count == 0
    assert result.issues[0].code == "DEFRA_DESNZ_PARSER_NOT_IMPLEMENTED"
    assert result.parser_metadata == {
        "adapter_kind": "source_specific_skeleton",
        "is_real_source_parser": False,
        "real_parsing_implemented": False,
    }


def test_defra_desnz_adapter_can_be_registered() -> None:
    adapter = DefraDesnzParserAdapter()
    registry = create_parser_adapter_registry((adapter,))

    assert list_parser_adapters(registry) == (adapter,)


def test_parser_execution_planning_is_ready_for_matching_defra_desnz_input() -> None:
    adapter = DefraDesnzParserAdapter()

    plan = plan_parser_execution(_defra_desnz_input(), (adapter,))

    assert plan.status == ParserExecutionPlanStatus.READY
    assert plan.selected_adapter_source_family == "defra_desnz"


def test_run_parser_execution_returns_defra_desnz_skeleton_result() -> None:
    adapter = DefraDesnzParserAdapter()

    result = run_parser_execution(_defra_desnz_input(), (adapter,))

    assert result.status == ParserExecutionResultStatus.UNSUPPORTED
    assert result.issues[0].code == "DEFRA_DESNZ_PARSER_NOT_IMPLEMENTED"
    assert result.parser_metadata["real_parsing_implemented"] is False


def test_defra_desnz_parse_has_no_file_http_normalization_or_db_side_effects(
    monkeypatch,
    tmp_path,
) -> None:
    adapter = DefraDesnzParserAdapter()
    missing_artifact = tmp_path / "missing-defra-desnz.csv"
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference=str(missing_artifact),
        content_type="text/csv",
    )

    def fail_side_effect(*args, **kwargs):
        raise AssertionError(
            "DefraDesnzParserAdapter.parse must not touch external state",
        )

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    result = adapter.parse(parser_input)

    assert result.status == ParserExecutionResultStatus.UNSUPPORTED
    assert not missing_artifact.exists()
