import builtins
import sqlite3
import urllib.request

import pytest

from carbonfactor_parser.parsers import (
    ParserAdapter,
    ParserAdapterRegistry,
    create_parser_adapter_registry,
    create_parser_input_contract,
    list_parser_adapters,
    register_parser_adapter,
    resolve_parser_adapters,
)


class RegistryFakeParserAdapter:
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
        self.parse_call_count = 0

    def can_parse(self, parser_input):  # noqa: ANN001, ANN201
        if parser_input.source_family != self.source_family:
            return False
        if parser_input.content_type in self.supported_content_types:
            return True
        return parser_input.format_hint in self.supported_format_hints

    def parse(self, parser_input):  # noqa: ANN001, ANN201
        self.parse_call_count += 1
        raise NotImplementedError("Registry tests must not execute parsers.")


def _parser_input(
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


def test_empty_parser_adapter_registry_has_no_adapters() -> None:
    registry = create_parser_adapter_registry()

    assert isinstance(registry, ParserAdapterRegistry)
    assert list_parser_adapters(registry) == ()
    assert resolve_parser_adapters(registry, _parser_input()) == ()


def test_parser_adapter_registration_appends_adapter() -> None:
    adapter = RegistryFakeParserAdapter(
        source_family="defra_desnz",
        supported_content_types=("text/csv",),
    )
    registry = register_parser_adapter(create_parser_adapter_registry(), adapter)

    assert isinstance(adapter, ParserAdapter)
    assert list_parser_adapters(registry) == (adapter,)


def test_parser_adapter_listing_is_deterministic() -> None:
    defra_adapter = RegistryFakeParserAdapter(source_family="defra_desnz")
    ghg_adapter = RegistryFakeParserAdapter(source_family="ghg_protocol")

    registry = create_parser_adapter_registry((defra_adapter, ghg_adapter))

    assert tuple(adapter.source_family for adapter in list_parser_adapters(registry)) == (
        "defra_desnz",
        "ghg_protocol",
    )


def test_matching_adapter_is_resolved_from_metadata() -> None:
    defra_adapter = RegistryFakeParserAdapter(
        source_family="defra_desnz",
        supported_content_types=("text/csv",),
    )
    ghg_adapter = RegistryFakeParserAdapter(
        source_family="ghg_protocol",
        supported_format_hints=("xlsx",),
    )
    registry = create_parser_adapter_registry((defra_adapter, ghg_adapter))

    matches = resolve_parser_adapters(registry, _parser_input())

    assert matches == (defra_adapter,)


def test_matching_adapter_can_be_resolved_by_format_hint() -> None:
    adapter = RegistryFakeParserAdapter(
        source_family="defra_desnz",
        supported_format_hints=("csv",),
    )
    registry = create_parser_adapter_registry((adapter,))

    matches = resolve_parser_adapters(
        registry,
        _parser_input(content_type=None, format_hint="csv"),
    )

    assert matches == (adapter,)


def test_non_matching_adapter_is_not_selected() -> None:
    adapter = RegistryFakeParserAdapter(
        source_family="ghg_protocol",
        supported_content_types=("text/csv",),
    )
    registry = create_parser_adapter_registry((adapter,))

    assert resolve_parser_adapters(registry, _parser_input()) == ()


def test_duplicate_parser_adapter_source_family_is_rejected() -> None:
    first = RegistryFakeParserAdapter(source_family="defra_desnz")
    second = RegistryFakeParserAdapter(source_family="defra_desnz")

    with pytest.raises(
        ValueError,
        match="Duplicate parser adapter source_family found: defra_desnz",
    ):
        create_parser_adapter_registry((first, second))


def test_registry_rejects_non_adapter_values() -> None:
    with pytest.raises(TypeError, match=r"adapters\[0\] must be a ParserAdapter"):
        create_parser_adapter_registry((object(),))  # type: ignore[arg-type]


def test_registry_rejects_blank_adapter_source_family() -> None:
    adapter = RegistryFakeParserAdapter(source_family=" ")

    with pytest.raises(
        ValueError,
        match=r"source_family must be a non-empty string for adapters\[0\]",
    ):
        create_parser_adapter_registry((adapter,))


def test_resolve_and_list_never_call_parse() -> None:
    adapter = RegistryFakeParserAdapter(
        source_family="defra_desnz",
        supported_content_types=("text/csv",),
    )
    registry = create_parser_adapter_registry((adapter,))

    assert list_parser_adapters(registry) == (adapter,)
    assert resolve_parser_adapters(registry, _parser_input()) == (adapter,)
    assert adapter.parse_call_count == 0


def test_registry_operations_have_no_file_http_normalization_or_db_side_effects(
    monkeypatch,
    tmp_path,
) -> None:
    adapter = RegistryFakeParserAdapter(
        source_family="defra_desnz",
        supported_content_types=("text/csv",),
    )
    registry = create_parser_adapter_registry((adapter,))
    parser_input = create_parser_input_contract(
        source_family="defra_desnz",
        source_id="defra_desnz",
        acquisition_status="acquired",
        artifact_reference=str(tmp_path / "missing.csv"),
        content_type="text/csv",
    )

    def fail_side_effect(*args, **kwargs):
        raise AssertionError("registry operations must use metadata only")

    monkeypatch.setattr(builtins, "open", fail_side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_side_effect)
    monkeypatch.setattr(sqlite3, "connect", fail_side_effect)

    assert list_parser_adapters(registry) == (adapter,)
    assert resolve_parser_adapters(registry, parser_input) == (adapter,)
    assert not (tmp_path / "missing.csv").exists()
