"""Source acquisition client boundary models and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from carbonfactor_parser.source_acquisition.models import SourceAcquisitionDescriptor


@dataclass(frozen=True)
class SourceAcquisitionResult:
    """Result shape for one source acquisition attempt."""

    source_id: str
    source_family: str
    status: str
    acquisition_url: str
    content_type: str | None = None
    content_length: int | None = None
    checksum_sha256: str | None = None
    local_path: str | None = None
    message: str | None = None


class SourceAcquisitionClient(Protocol):
    """Protocol for source acquisition clients."""

    def acquire(self, descriptor: SourceAcquisitionDescriptor) -> SourceAcquisitionResult:
        """Acquire one source described by the descriptor."""


class NoopSourceAcquisitionClient:
    """Offline-safe no-op implementation for deferred acquisition."""

    def acquire(self, descriptor: SourceAcquisitionDescriptor) -> SourceAcquisitionResult:
        return SourceAcquisitionResult(
            source_id=descriptor.source_id,
            source_family=descriptor.source_family,
            status="not_implemented",
            acquisition_url=descriptor.acquisition_url,
            content_type=None,
            content_length=None,
            checksum_sha256=None,
            local_path=None,
            message=(
                "Real source acquisition is intentionally deferred; "
                "no network or file operations were performed."
            ),
        )


def acquire_all_sources(
    descriptors: tuple[SourceAcquisitionDescriptor, ...] | list[SourceAcquisitionDescriptor],
    client: SourceAcquisitionClient,
) -> tuple[SourceAcquisitionResult, ...]:
    """Acquire all sources in deterministic descriptor order."""

    return tuple(client.acquire(descriptor) for descriptor in descriptors)
