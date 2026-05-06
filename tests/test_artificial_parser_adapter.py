import builtins
import sqlite3
import urllib.request

import pytest

from carbonfactor_parser.parsers import (
    ArtificialParserAdapter,
    ParserAdapter,
    ParserExecutionResult,
    ParserExecutionResultStatus,
    create_parser_adapter_registry,
    create_parser_input_contract,
    list_parser_adapters,
    run_parser_execution,
)


def _artificial_input(
    *,
    source_family: str = "artificial",
    content_type: str | None = "application/x-carbonops-artificial",
    format_hint: str | None = None,
):
    return create_parser_input_contract(
        source_family=source_family,
        source_id=source_family,
        acquisition_status="acquired",
        artifact_reference=f"memory://{source_family}/artifact",
        content_type=content_type,
        format_hint=format_hint,
    )


def test_artificial_parser_adapter_is_public_and_satisfies_protocol() -> None:
    adapter = ArtificialParserAdapter(parsed_record_count=2)

    assert isinstance(adapter, ParserAdapter)
    assert adapter.source_family == "artificial"
    assert adapter.supported_content_types == (
        "application/x-carbonops-artificial",
    )
    assert adapter.supported_format_hints == ("artificial",)
    assert adapter.parsed_record_count == 2


def test_artificial_parser_adapter_can_parse_matching_content_type() -> None:
    adapter = ArtificialParserAdapter()

    assert adapter.can_parse(_artificial_input()) is True


def test_artificial_parser_adapter_can_parse_matching_format_hint() -> None:
    adapter = ArtificialParserAdapter()

    assert adapter.can_parse(
        _artificial_input(content_type=None, format_hint="artificial"),
    ) is True


def test_artificial_parser_adapter_rejects_non_matching_input() -> None:
    adapter = ArtificialParserAdapter()

    assert adapter.can_parse(
        _artificial_input(
            source_family="defra_desnz",
            content_type="text/csv",
            format_hint="csv",
        ),
    ) is False


def test_artificial_parse_returns_success_execution_result() -> None:
    adapter = ArtificialParserAdapter(parsed_record_count=3)

    result = adapter.parse(_artificial_input())

    assert isinstance(result, ParserExecutionResult)
    assert result.status == ParserExecutionResultStatus.SUCCESS
    assert result.parsed_record_count == 3
    assert result.parser_metadata == {
        "adapter_kind": "artificial",
        "is_real_source_parser": False,
        "record_count_source": "adapter_configuration",
    }


def test_artificial_parsed_record_count_is_deterministic() -> None:
    adapter = ArtificialParserAdapter(parsed_record_count=5)
    parser_input = _artificial_input()

    first_result = adapter.parse(parser_input)
    second_result = adapter.parse(parser_input)

    assert first_result.parsed_record_count == 5
    assert second_result.parsed_record_count == 5


def test_artificial_adapter_can_be_registered() -> None:
    adapter = ArtificialParserAdapter()
    registry = create_parser_adapter_registry((adapter,))

    assert list_parser_adapters(registry) == (adapter,)


def test_run_parser_execution_returns_artificial_adapter_result() -> None:
    adapter = ArtificialParserAdapter(parsed_record_count=4)

    result = run_parser_execution(_artificial_input(), (adapter,))

    assert result.status == ParserExecutionResultStatus.SUCCESS
    assert result.parsed_record_count == 4
    assert result.parser_metadata["adapter_kind"] == "artificial"
    assert result.parser_metadata["is_real_source_parser"] is False


def test_artificial_parse_rejects_non_matching_input_with_unsupported_result() -> None:
    adapter = ArtificialParserAdapter()

    result = adapter.parse(
        _artificial_input(
            source_family="ghg_protocol",
            content_type="text/csv",
            format_hint="csv",
        ),
    )

    assert result.status == ParserExecutionResultStatus.UNSUPPORTED
    assert result.parsed_record_count == 0
    assert result.issues[0].code == "ARTIFICIAL_PARSER_INPUT_UNSUPPORTED"
    assert result.parser_metadata["is_real_source_parser"] is False


def test_artificial_parse_has_no_file_http_normalization_or_db_side_effects(
    monkeypatch,
    tmp_path,
) -> None:
    adapter = ArtificialParserAdapter(parsed_record_count=1)
    parser_input = create_parser_input_contract(
        source_family="artificial",
        source_id="artificial",
        acquisition_status="acquired",
        artifact_reference=str(tmp_path / "missing.artifact"),
        content_type="application/x-carbonops-artificial",
    )

    def fail_side_effect(*args, **kwargs):
        raise AssertionError(
            "ArtificialParserAdapter.parse must not touch external state",
        )

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    result = adapter.parse(parser_input)

    assert result.status == ParserExecutionResultStatus.SUCCESS
    assert not (tmp_path / "missing.artifact").exists()


def test_artificial_record_count_must_be_non_negative_integer() -> None:
    with pytest.raises(ValueError, match="non-negative integer"):
        ArtificialParserAdapter(parsed_record_count=-1)
