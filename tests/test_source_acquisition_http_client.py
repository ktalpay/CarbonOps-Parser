from pathlib import Path

from carbonfactor_parser import source_acquisition
from carbonfactor_parser.source_acquisition.client import NoopSourceAcquisitionClient
from carbonfactor_parser.source_acquisition.checksum import compute_sha256_hex
from carbonfactor_parser.source_acquisition.http_client import (
    HttpAcquisitionTransportResponse,
    HttpSourceAcquisitionClient,
)
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor


def _build_descriptor(acquisition_url: str = "discovery://example/source") -> SourceAcquisitionDescriptor:
    return SourceAcquisitionDescriptor(
        source_id="example_source",
        source_family="example_family",
        display_name="Example Source",
        homepage_url="discovery://example",
        acquisition_url=acquisition_url,
        expected_format="csv",
        description="Example descriptor",
        enabled=True,
    )


def test_http_client_success_response_returns_acquired_result() -> None:
    captured_urls: list[str] = []

    def fake_transport(acquisition_url: str) -> HttpAcquisitionTransportResponse:
        captured_urls.append(acquisition_url)
        return HttpAcquisitionTransportResponse(
            status_code=200,
            content=b"a,b\n1,2\n",
            content_type="text/csv",
            content_length=8,
            final_url="discovery://example/final.csv",
        )

    descriptor = _build_descriptor()
    client = HttpSourceAcquisitionClient(fake_transport)

    result = client.acquire(descriptor)

    assert result.status == "acquired"
    assert result.source_id == descriptor.source_id
    assert result.source_family == descriptor.source_family
    assert result.acquisition_url == descriptor.acquisition_url
    assert result.content_type == "text/csv"
    assert result.content_length == 8
    assert result.local_path is None
    assert result.checksum_sha256 == compute_sha256_hex(b"a,b\n1,2\n")
    assert captured_urls == [descriptor.acquisition_url]


def test_http_client_success_response_does_not_create_files_or_directories(tmp_path: Path) -> None:
    def fake_transport(_: str) -> HttpAcquisitionTransportResponse:
        return HttpAcquisitionTransportResponse(
            status_code=204,
            content=b"",
            content_type=None,
            content_length=0,
            final_url=None,
        )

    before_paths = tuple(tmp_path.iterdir())
    result = HttpSourceAcquisitionClient(fake_transport).acquire(_build_descriptor())
    after_paths = tuple(tmp_path.iterdir())

    assert result.status == "acquired"
    assert result.local_path is None
    assert result.checksum_sha256 == compute_sha256_hex(b"")
    assert before_paths == after_paths


def test_http_client_non_2xx_response_returns_failed_result() -> None:
    def fake_transport(_: str) -> HttpAcquisitionTransportResponse:
        return HttpAcquisitionTransportResponse(status_code=503, content=b"unavailable")

    result = HttpSourceAcquisitionClient(fake_transport).acquire(_build_descriptor())

    assert result.status == "failed"
    assert result.checksum_sha256 is None
    assert "503" in (result.message or "")


def test_http_client_transport_exception_returns_failed_result() -> None:
    def fake_transport(_: str) -> HttpAcquisitionTransportResponse:
        raise RuntimeError("offline failure")

    result = HttpSourceAcquisitionClient(fake_transport).acquire(_build_descriptor())

    assert result.status == "failed"
    assert result.checksum_sha256 is None
    assert "offline failure" in (result.message or "")


def test_http_source_acquisition_client_public_exports_are_importable() -> None:
    assert source_acquisition.HttpAcquisitionTransportResponse is HttpAcquisitionTransportResponse
    assert source_acquisition.HttpSourceAcquisitionClient is HttpSourceAcquisitionClient


def test_noop_source_acquisition_client_behavior_is_unchanged() -> None:
    descriptor = _build_descriptor(acquisition_url="discovery://example/acquisition")
    result = NoopSourceAcquisitionClient().acquire(descriptor)

    assert result.status == "not_implemented"
    assert result.local_path is None
    assert result.checksum_sha256 is None
