import pytest

from carbonfactor_parser.source_adapters import (
    AdapterDiscoveryResult,
    AdapterParseResult,
    SourceAdapterRegistry,
    SourceDocument,
    SourceFamily,
)


class FakeAdapter:
    def __init__(self, source_family: SourceFamily) -> None:
        self._source_family = source_family

    @property
    def source_family(self) -> SourceFamily:
        return self._source_family

    def discover(self) -> AdapterDiscoveryResult:
        return AdapterDiscoveryResult()

    def parse(self, document: SourceDocument) -> AdapterParseResult:
        return AdapterParseResult(records=[{"source_name": document.source_name}])


def test_fake_adapter_can_be_registered_and_retrieved() -> None:
    registry = SourceAdapterRegistry()
    adapter = FakeAdapter(SourceFamily.DEFRA_DESNZ)

    registry.register(adapter)

    assert registry.get(SourceFamily.DEFRA_DESNZ) is adapter


def test_duplicate_registration_for_source_family_is_rejected() -> None:
    registry = SourceAdapterRegistry()
    registry.register(FakeAdapter(SourceFamily.GHG_PROTOCOL))

    with pytest.raises(
        ValueError,
        match="Source adapter already registered for ghg_protocol.",
    ):
        registry.register(FakeAdapter(SourceFamily.GHG_PROTOCOL))


def test_missing_source_family_lookup_raises_key_error() -> None:
    registry = SourceAdapterRegistry()

    with pytest.raises(
        KeyError,
        match="No source adapter registered for ipcc_efdb.",
    ):
        registry.get(SourceFamily.IPCC_EFDB)


def test_contains_returns_expected_values() -> None:
    registry = SourceAdapterRegistry()
    registry.register(FakeAdapter(SourceFamily.IPCC_EFDB))

    assert registry.contains(SourceFamily.IPCC_EFDB) is True
    assert registry.contains(SourceFamily.DEFRA_DESNZ) is False


def test_source_families_returns_registered_families_predictably() -> None:
    registry = SourceAdapterRegistry()
    registry.register(FakeAdapter(SourceFamily.DEFRA_DESNZ))
    registry.register(FakeAdapter(SourceFamily.GHG_PROTOCOL))

    assert registry.source_families() == (
        SourceFamily.DEFRA_DESNZ,
        SourceFamily.GHG_PROTOCOL,
    )


def test_registry_state_does_not_leak_across_instances() -> None:
    first = SourceAdapterRegistry()
    second = SourceAdapterRegistry()

    first.register(FakeAdapter(SourceFamily.DEFRA_DESNZ))

    assert first.contains(SourceFamily.DEFRA_DESNZ) is True
    assert second.contains(SourceFamily.DEFRA_DESNZ) is False
    assert second.source_families() == ()
