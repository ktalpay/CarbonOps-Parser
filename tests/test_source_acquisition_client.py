from carbonfactor_parser import source_acquisition
from carbonfactor_parser.source_acquisition.client import (
    NoopSourceAcquisitionClient,
    SourceAcquisitionResult,
    acquire_all_sources,
)
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor
from carbonfactor_parser.source_acquisition.registry import (
    create_default_source_acquisition_registry,
)


def test_noop_client_returns_deterministic_result() -> None:
    descriptor = create_default_source_acquisition_registry()[0]
    client = NoopSourceAcquisitionClient()

    result = client.acquire(descriptor)

    assert result == SourceAcquisitionResult(
        source_id="ghg_protocol",
        source_family="ghg_protocol",
        status="not_implemented",
        acquisition_url="discovery://ghg_protocol/acquisition",
        content_type=None,
        content_length=None,
        checksum_sha256=None,
        local_path=None,
        message=(
            "Real source acquisition is intentionally deferred; "
            "no network or file operations were performed."
        ),
    )


def test_noop_result_references_descriptor_identity_fields() -> None:
    descriptor = SourceAcquisitionDescriptor(
        source_id="sample_source",
        source_family="sample_family",
        display_name="Sample Source",
        homepage_url="discovery://sample/homepage",
        acquisition_url="discovery://sample/acquisition",
        expected_format="discovery",
        description="placeholder",
        enabled=True,
    )

    result = NoopSourceAcquisitionClient().acquire(descriptor)

    assert result.source_id == descriptor.source_id
    assert result.source_family == descriptor.source_family
    assert result.acquisition_url == descriptor.acquisition_url


def test_noop_result_has_no_local_artifact_metadata() -> None:
    descriptor = create_default_source_acquisition_registry()[1]

    result = NoopSourceAcquisitionClient().acquire(descriptor)

    assert result.local_path is None
    assert result.checksum_sha256 is None
    assert result.content_length is None


def test_acquire_all_sources_returns_one_result_per_descriptor() -> None:
    descriptors = create_default_source_acquisition_registry()

    results = acquire_all_sources(descriptors, NoopSourceAcquisitionClient())

    assert len(results) == len(descriptors)


def test_acquire_all_sources_follows_registry_ordering() -> None:
    descriptors = create_default_source_acquisition_registry()

    results = acquire_all_sources(descriptors, NoopSourceAcquisitionClient())

    assert tuple(result.source_id for result in results) == tuple(
        descriptor.source_id for descriptor in descriptors
    )


def test_source_acquisition_client_public_api_exports_are_importable() -> None:
    assert source_acquisition.SourceAcquisitionDescriptor is SourceAcquisitionDescriptor
    assert (
        source_acquisition.create_default_source_acquisition_registry
        is create_default_source_acquisition_registry
    )
    assert source_acquisition.SourceAcquisitionResult is SourceAcquisitionResult
    assert source_acquisition.NoopSourceAcquisitionClient is NoopSourceAcquisitionClient
    assert source_acquisition.acquire_all_sources is acquire_all_sources
