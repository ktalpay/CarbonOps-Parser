"""HTTP acquisition client boundary with injected transport."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from carbonfactor_parser.source_acquisition.client import SourceAcquisitionResult
from carbonfactor_parser.source_acquisition.checksum import compute_sha256_hex
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor


@dataclass(frozen=True)
class HttpAcquisitionTransportResponse:
    """Immutable HTTP transport response payload for acquisition."""

    status_code: int
    content: bytes
    content_type: str | None = None
    content_length: int | None = None
    final_url: str | None = None


class HttpAcquisitionTransport(Protocol):
    """Protocol for transport callables used by HttpSourceAcquisitionClient."""

    def __call__(self, acquisition_url: str) -> HttpAcquisitionTransportResponse:
        """Execute one acquisition request for the given URL."""


class HttpSourceAcquisitionClient:
    """HTTP acquisition client using an injected transport callable."""

    def __init__(
        self,
        transport: HttpAcquisitionTransport,
        *,
        timeout_seconds: float | None = None,
    ) -> None:
        self._transport = transport
        self._timeout_seconds = timeout_seconds

    def acquire(self, descriptor: SourceAcquisitionDescriptor) -> SourceAcquisitionResult:
        try:
            transport_response = self._transport(descriptor.acquisition_url)
        except Exception as error:  # noqa: BLE001
            return SourceAcquisitionResult(
                source_id=descriptor.source_id,
                source_family=descriptor.source_family,
                status="failed",
                acquisition_url=descriptor.acquisition_url,
                message=f"HTTP acquisition failed due to transport error: {error}",
            )

        if 200 <= transport_response.status_code < 300:
            return SourceAcquisitionResult(
                source_id=descriptor.source_id,
                source_family=descriptor.source_family,
                status="acquired",
                acquisition_url=descriptor.acquisition_url,
                content_type=transport_response.content_type,
                content_length=transport_response.content_length,
                checksum_sha256=compute_sha256_hex(transport_response.content),
                local_path=None,
                message=(
                    "HTTP content acquired in-memory with SHA-256 checksum metadata; "
                    "file persistence is deferred."
                ),
            )

        return SourceAcquisitionResult(
            source_id=descriptor.source_id,
            source_family=descriptor.source_family,
            status="failed",
            acquisition_url=descriptor.acquisition_url,
            message=(
                "HTTP acquisition failed with status code "
                f"{transport_response.status_code}."
            ),
        )
