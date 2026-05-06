import builtins
import sqlite3
import urllib.request

from carbonfactor_parser.parsers import (
    NoopParserAdapter,
    ParserExecutionIssueSeverity,
    ParserExecutionResult,
    ParserExecutionResultStatus,
    create_parser_adapter_registry,
    create_parser_execution_result,
    create_parser_input_contract,
    run_parser_execution,
)


class RunnerFakeParserAdapter:
    def __init__(
        self,
        *,
        source_family: str,
        supported_content_types: tuple[str, ...] = (),
        supported_format_hints: tuple[str, ...] = (),
        result: ParserExecutionResult | None = None,
    ) -> None:
        self.source_family = source_family
        self.supported_content_types = supported_content_types
        self.supported_format_hints = supported_format_hints
        self.result = result
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
        if self.result is not None:
            return self.result
        return create_parser_execution_result(
            status=ParserExecutionResultStatus.SUCCESS,
            parser_input=parser_input,
            parsed_record_count=1,
        )


def _valid_parser_input():
    return create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference="data/source-acquisition/defra_desnz/source.csv",
        content_type="text/csv",
    )


def test_invalid_input_returns_failed_result_without_parse() -> None:
    adapter = RunnerFakeParserAdapter(
        source_family="defra_desnz",
        supported_content_types=("text/csv",),
    )
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference=" ",
        content_type="text/csv",
    )

    result = run_parser_execution(parser_input, (adapter,))

    assert result.status == ParserExecutionResultStatus.FAILED
    assert result.parsed_record_count == 0
    assert result.issues[0].code == "PARSER_INPUT_MISSING_ARTIFACT_REFERENCE"
    assert result.issues[0].severity == ParserExecutionIssueSeverity.ERROR
    assert result.parser_metadata == {"plan_status": "invalid_input"}
    assert adapter.can_parse_call_count == 0
    assert adapter.parse_call_count == 0


def test_no_matching_adapter_returns_unsupported_without_parse() -> None:
    adapter = RunnerFakeParserAdapter(
        source_family="ghg_protocol",
        supported_content_types=("text/csv",),
    )

    result = run_parser_execution(_valid_parser_input(), (adapter,))

    assert result.status == ParserExecutionResultStatus.UNSUPPORTED
    assert result.parsed_record_count == 0
    assert result.issues[0].code == "PARSER_EXECUTION_NO_ADAPTER"
    assert result.issues[0].severity == ParserExecutionIssueSeverity.WARNING
    assert result.parser_metadata == {"plan_status": "no_adapter"}
    assert adapter.parse_call_count == 0


def test_ready_plan_calls_fake_adapter_parse_once() -> None:
    adapter = RunnerFakeParserAdapter(
        source_family="defra_desnz",
        supported_content_types=("text/csv",),
    )

    result = run_parser_execution(_valid_parser_input(), (adapter,))

    assert result.status == ParserExecutionResultStatus.SUCCESS
    assert result.parsed_record_count == 1
    assert adapter.parse_call_count == 1


def test_ready_plan_returns_fake_adapter_execution_result() -> None:
    parser_input = _valid_parser_input()
    fake_result = create_parser_execution_result(
        status=ParserExecutionResultStatus.NO_RECORDS,
        parser_input=parser_input,
    )
    adapter = RunnerFakeParserAdapter(
        source_family="defra_desnz",
        supported_content_types=("text/csv",),
        result=fake_result,
    )

    result = run_parser_execution(parser_input, create_parser_adapter_registry((adapter,)))

    assert result is fake_result
    assert adapter.parse_call_count == 1


def test_noop_adapter_refuses_parse_and_runner_represents_failure() -> None:
    parser_input = create_parser_input_contract(
        source_family="noop",
        source_id="noop",
        acquisition_status="acquired",
        artifact_reference="memory://noop-artifact",
        content_type="application/x-carbonops-noop",
    )

    result = run_parser_execution(parser_input, (NoopParserAdapter(),))

    assert result.status == ParserExecutionResultStatus.FAILED
    assert result.parsed_record_count == 0
    assert result.issues[0].code == "PARSER_EXECUTION_ADAPTER_EXCEPTION"
    assert result.issues[0].context == {
        "exception_type": "NotImplementedError",
        "plan_status": "ready",
    }
    assert result.parser_metadata == {
        "adapter_source_family": "noop",
        "plan_status": "ready",
    }


def test_runner_has_no_file_http_normalization_or_db_side_effects(
    monkeypatch,
    tmp_path,
) -> None:
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference=str(tmp_path / "missing.csv"),
        content_type="text/csv",
    )
    adapter = RunnerFakeParserAdapter(
        source_family="defra_desnz",
        supported_content_types=("text/csv",),
    )

    def fail_side_effect(*args, **kwargs):
        raise AssertionError("runner boundary must not touch external state")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    result = run_parser_execution(parser_input, (adapter,))

    assert result.status == ParserExecutionResultStatus.SUCCESS
    assert not (tmp_path / "missing.csv").exists()
