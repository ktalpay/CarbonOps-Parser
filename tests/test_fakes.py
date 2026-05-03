from carbonfactor_parser.source_adapters import (
    AdapterDiscoveryResult,
    AdapterParseResult,
    SourceAdapter,
    SourceFamily,
)
from fakes import FakeSourceAdapter, make_adapter_parse_result, make_source_document


def test_fake_source_adapter_discover_returns_configured_result() -> None:
    document = make_source_document(source_family=SourceFamily.IPCC_EFDB)
    discovery_result = AdapterDiscoveryResult(
        documents=[document],
        warnings=["sample warning"],
    )
    adapter = FakeSourceAdapter(
        source_family=SourceFamily.IPCC_EFDB,
        discovery_result=discovery_result,
    )

    assert adapter.discover() is discovery_result


def test_fake_source_adapter_parse_returns_configured_result() -> None:
    parse_result = make_adapter_parse_result(records=[{"row": 10}])
    adapter = FakeSourceAdapter(parse_result=parse_result)

    assert adapter.parse(make_source_document()) is parse_result


def test_fake_source_adapter_tracks_discover_and_parse_calls() -> None:
    document = make_source_document()
    adapter = FakeSourceAdapter()

    adapter.discover()
    adapter.discover()
    adapter.parse(document)

    assert adapter.discover_call_count == 2
    assert adapter.parsed_documents == (document,)


def test_fake_source_adapter_satisfies_source_adapter_protocol() -> None:
    adapter = FakeSourceAdapter(source_family=SourceFamily.GHG_PROTOCOL)

    assert isinstance(adapter, SourceAdapter)
    assert adapter.source_family is SourceFamily.GHG_PROTOCOL
    assert isinstance(adapter.discover(), AdapterDiscoveryResult)
    assert isinstance(adapter.parse(make_source_document()), AdapterParseResult)
