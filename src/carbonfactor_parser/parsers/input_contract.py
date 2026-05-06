"""Parser input contract for acquired artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ParserInputContract:
    """Source acquisition output prepared for future parser execution."""

    source_family: str
    source_id: str
    acquisition_status: str
    artifact_reference: str | None = None
    checksum_sha256: str | None = None
    content_type: str | None = None
    format_hint: str | None = None
    acquisition_run_id: str | None = None
    run_metadata: Mapping[str, object] | None = None
    manifest_metadata: Mapping[str, object] | None = None


def create_parser_input_contract(
    *,
    source_family: str,
    source_id: str,
    acquisition_status: str,
    artifact_reference: str | None = None,
    checksum_sha256: str | None = None,
    content_type: str | None = None,
    format_hint: str | None = None,
    acquisition_run_id: str | None = None,
    run_metadata: Mapping[str, object] | None = None,
    manifest_metadata: Mapping[str, object] | None = None,
) -> ParserInputContract:
    """Create a parser input contract without touching artifact contents."""

    return ParserInputContract(
        source_family=source_family,
        source_id=source_id,
        acquisition_status=acquisition_status,
        artifact_reference=artifact_reference,
        checksum_sha256=checksum_sha256,
        content_type=content_type,
        format_hint=format_hint,
        acquisition_run_id=acquisition_run_id,
        run_metadata=dict(run_metadata) if run_metadata is not None else None,
        manifest_metadata=(
            dict(manifest_metadata) if manifest_metadata is not None else None
        ),
    )
