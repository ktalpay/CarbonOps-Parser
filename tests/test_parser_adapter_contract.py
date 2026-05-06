import builtins
import sqlite3
import urllib.request
from typing import get_type_hints

import pytest

from carbonfactor_parser.parsers import (
    ParserAdapter,
    ParserExecutionResult,
    ParserExecutionResultStatus,
    ParserInputContract,
    create_parser_execution_result,
    create_parser_input_contract,
)


class FakeMetadataOnlyParserAdapter:
    source_family = "defra_desnz"
    supported_content_types = ("text/csv",)
    supported_format_hints = ("csv",)

    def can_parse(self, parser_input: ParserInputContract) -> bool:
        if parser_input.source_family != self.source_family:
            return False
        if parser_input.content_type in self.supported_content_types:
            return True
        return parser_input.format_hint in self.supported_format_hints

    def parse(self, parser_input: ParserInputContract):  # noqa: ANN201
        raise NotImplementedError("Parser execution is outside this boundary.")


class FakeExecutionResultParserAdapter(FakeMetadataOnlyParserAdapter):
    def parse(self, parser_input: ParserInputContract) -> ParserExecutionResult:
        return create_parser_execution_result(
            status=ParserExecutionResultStatus.SUCCESS,
            parser_input=parser_input,
            parsed_record_count=1,
            parser_metadata={"adapter": "fake"},
        )


def test_parser_adapter_protocol_is_importable_from_public_api() -> None:
    assert ParserAdapter.__name__ == "ParserAdapter"


def test_parser_adapter_parse_boundary_returns_execution_result_type() -> None:
    type_hints = get_type_hints(ParserAdapter.parse)

    assert type_hints["return"] is ParserExecutionResult


def test_fake_in_memory_adapter_satisfies_protocol() -> None:
    adapter = FakeMetadataOnlyParserAdapter()

    assert isinstance(adapter, ParserAdapter)
    assert adapter.source_family == "defra_desnz"
    assert adapter.supported_content_types == ("text/csv",)
    assert adapter.supported_format_hints == ("csv",)


def test_can_parse_uses_parser_input_metadata_only() -> None:
    adapter = FakeMetadataOnlyParserAdapter()
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference="data/source-acquisition/defra_desnz/source.csv",
        content_type="text/csv",
    )

    assert adapter.can_parse(parser_input) is True


def test_can_parse_supports_format_hint_metadata() -> None:
    adapter = FakeMetadataOnlyParserAdapter()
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference="data/source-acquisition/defra_desnz/source.csv",
        format_hint="csv",
    )

    assert adapter.can_parse(parser_input) is True


def test_can_parse_rejects_incompatible_metadata() -> None:
    adapter = FakeMetadataOnlyParserAdapter()
    parser_input = create_parser_input_contract(
        source_family="ghg_protocol",
        source_id="ghg_protocol",
        acquisition_status="acquired",
        artifact_reference="data/source-acquisition/ghg_protocol/source.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        format_hint="xlsx",
    )

    assert adapter.can_parse(parser_input) is False


def test_can_parse_has_no_file_http_normalization_or_db_side_effects(
    monkeypatch,
    tmp_path,
) -> None:
    adapter = FakeMetadataOnlyParserAdapter()
    missing_artifact = tmp_path / "missing.csv"
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference=str(missing_artifact),
        content_type="text/csv",
    )

    def fail_side_effect(*args, **kwargs):
        raise AssertionError("can_parse must use metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    assert adapter.can_parse(parser_input) is True
    assert not missing_artifact.exists()


def test_parse_is_not_real_execution_in_fake_adapter() -> None:
    adapter = FakeMetadataOnlyParserAdapter()
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference="data/source-acquisition/defra_desnz/source.csv",
        content_type="text/csv",
    )

    with pytest.raises(NotImplementedError, match="outside this boundary"):
        adapter.parse(parser_input)


def test_fake_adapter_can_return_parser_execution_result() -> None:
    adapter = FakeExecutionResultParserAdapter()
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference="data/source-acquisition/defra_desnz/source.csv",
        content_type="text/csv",
    )

    result = adapter.parse(parser_input)

    assert isinstance(result, ParserExecutionResult)
    assert result.status == ParserExecutionResultStatus.SUCCESS
    assert result.parsed_record_count == 1
    assert result.parser_metadata == {"adapter": "fake"}
