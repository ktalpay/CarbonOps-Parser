from carbonfactor_parser.source_adapters import (
    AdapterDiscoveryResult,
    AdapterParseResult,
    NoOpSourceAdapter,
    SourceAdapter,
    SourceAdapterRegistry,
    SourceDocument,
    SourceFamily,
)


def make_document() -> SourceDocument:
    return SourceDocument(
        source_family=SourceFamily.DEFRA_DESNZ,
        source_name="Example local factor file",
        file_reference="data/raw/example/source.csv",
    )


def test_noop_source_adapter_satisfies_source_adapter_protocol() -> None:
    adapter = NoOpSourceAdapter()

    assert isinstance(adapter, SourceAdapter)


def test_default_source_family_is_stable() -> None:
    adapter = NoOpSourceAdapter()

    assert adapter.source_family is SourceFamily.GHG_PROTOCOL


def test_constructor_preserves_provided_source_family() -> None:
    adapter = NoOpSourceAdapter(source_family=SourceFamily.IPCC_EFDB)

    assert adapter.source_family is SourceFamily.IPCC_EFDB


def test_discover_returns_empty_discovery_result() -> None:
    adapter = NoOpSourceAdapter()

    result = adapter.discover()

    assert isinstance(result, AdapterDiscoveryResult)
    assert result.documents == ()
    assert result.warnings == ()


def test_parse_returns_empty_parse_result() -> None:
    adapter = NoOpSourceAdapter()

    result = adapter.parse(make_document())

    assert isinstance(result, AdapterParseResult)
    assert result.records == ()
    assert result.rejected_records == ()
    assert result.warnings == ()
    assert result.normalization_notes == ()


def test_parse_does_not_mutate_document() -> None:
    adapter = NoOpSourceAdapter()
    document = make_document()

    result = adapter.parse(document)

    assert result.records == ()
    assert document == make_document()


def test_noop_source_adapter_can_be_registered_and_retrieved() -> None:
    registry = SourceAdapterRegistry()
    adapter = NoOpSourceAdapter(source_family=SourceFamily.DEFRA_DESNZ)

    registry.register(adapter)

    assert registry.get(SourceFamily.DEFRA_DESNZ) is adapter
