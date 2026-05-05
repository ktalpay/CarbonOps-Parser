"""Source acquisition configuration models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceAcquisitionDescriptor:
    """Immutable metadata describing a known source acquisition family."""

    source_id: str
    source_family: str
    display_name: str
    homepage_url: str
    acquisition_url: str
    expected_format: str
    description: str
    enabled: bool = True
