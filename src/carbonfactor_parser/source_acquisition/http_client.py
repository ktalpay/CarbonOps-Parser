"""HTTP acquisition client boundary with injected transport."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from carbonfactor_parser.source_acquisition.client import SourceAcquisitionResult
from carbonfactor_parser.source_acquisition.checksum import compute_sha256_hex
from carbonfactor_parser.source_acquisition.file_store import write_acquired_content
from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor
from carbonfactor_parser.source_acquisition.targets import plan_source_acquisition_target


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
        base_directory: Path | str | None = None,
        persist_content: bool = False,
    ) -> None:
        if persist_content and base_directory is None:
            raise ValueError(
                "base_directory must be provided when persist_content is True."
            )

        self._transport = transport
        self._timeout_seconds = timeout_seconds
        self._base_directory = base_directory
        self._persist_content = persist_content

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
            local_path = None
            message = (
                "HTTP content acquired in-memory with SHA-256 checksum metadata; "
                "file persistence is deferred."
            )

            if self._persist_content:
                target = plan_source_acquisition_target(
                    descriptor=descriptor,
                    base_directory=self._base_directory,
                )
                local_path = write_acquired_content(target, transport_response.content)
                message = (
                    "HTTP content acquired in-memory with SHA-256 checksum metadata "
                    "and persisted to planned local target path; existing files are "
                    "overwritten."
                )

            return SourceAcquisitionResult(
                source_id=descriptor.source_id,
                source_family=descriptor.source_family,
                status="acquired",
                acquisition_url=descriptor.acquisition_url,
                content_type=transport_response.content_type,
                content_length=transport_response.content_length,
                checksum_sha256=compute_sha256_hex(transport_response.content),
                local_path=local_path,
                message=message,
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
