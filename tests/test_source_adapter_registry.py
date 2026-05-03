import pytest

from carbonfactor_parser.source_adapters import (
    SourceAdapterRegistry,
    SourceFamily,
)
from fakes import FakeSourceAdapter


def test_fake_adapter_can_be_registered_and_retrieved() -> None:
    registry = SourceAdapterRegistry()
    adapter = FakeSourceAdapter(source_family=SourceFamily.DEFRA_DESNZ)

    registry.register(adapter)

    assert registry.get(SourceFamily.DEFRA_DESNZ) is adapter


def test_duplicate_registration_for_source_family_is_rejected() -> None:
    registry = SourceAdapterRegistry()
    registry.register(FakeSourceAdapter(source_family=SourceFamily.GHG_PROTOCOL))

    with pytest.raises(
        ValueError,
        match="Source adapter already registered for ghg_protocol.",
    ):
        registry.register(FakeSourceAdapter(source_family=SourceFamily.GHG_PROTOCOL))


def test_missing_source_family_lookup_raises_key_error() -> None:
    registry = SourceAdapterRegistry()

    with pytest.raises(
        KeyError,
        match="No source adapter registered for ipcc_efdb.",
    ):
        registry.get(SourceFamily.IPCC_EFDB)


def test_contains_returns_expected_values() -> None:
    registry = SourceAdapterRegistry()
    registry.register(FakeSourceAdapter(source_family=SourceFamily.IPCC_EFDB))

    assert registry.contains(SourceFamily.IPCC_EFDB) is True
    assert registry.contains(SourceFamily.DEFRA_DESNZ) is False


def test_source_families_returns_registered_families_predictably() -> None:
    registry = SourceAdapterRegistry()
    registry.register(FakeSourceAdapter(source_family=SourceFamily.DEFRA_DESNZ))
    registry.register(FakeSourceAdapter(source_family=SourceFamily.GHG_PROTOCOL))

    assert registry.source_families() == (
        SourceFamily.DEFRA_DESNZ,
        SourceFamily.GHG_PROTOCOL,
    )


def test_registry_state_does_not_leak_across_instances() -> None:
    first = SourceAdapterRegistry()
    second = SourceAdapterRegistry()

    first.register(FakeSourceAdapter(source_family=SourceFamily.DEFRA_DESNZ))

    assert first.contains(SourceFamily.DEFRA_DESNZ) is True
    assert second.contains(SourceFamily.DEFRA_DESNZ) is False
    assert second.source_families() == ()
