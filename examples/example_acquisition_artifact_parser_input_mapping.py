"""In-memory acquisition artifact to future parser input mapping example."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import PurePosixPath

from carbonfactor_parser.parsers import (
    ParserInputContract,
    create_parser_input_contract,
)
from carbonfactor_parser.source_acquisition import (
    ACQUISITION_STATUS_ACQUIRED,
    SourceAcquisitionManifestEntry,
    SourceAcquisitionResult,
    SourceAcquisitionRunResult,
    create_manifest_entry,
)


def build_acquisition_artifact_parser_input_mapping_example() -> dict[str, object]:
    """Map deterministic acquisition metadata into a future parser input shape.

    The example uses in-memory acquisition result metadata only. It does not
    read files, call HTTP transports, execute a parser, run normalization, or
    write to a database.
    """

    acquisition_result = SourceAcquisitionResult(
        source_family="defra_desnz",
        source_id="defra_desnz",
        status=ACQUISITION_STATUS_ACQUIRED,
        acquisition_url="memory:source-acquisition/defra-desnz",
        local_path="data/source-acquisition/defra_desnz/example-factors.csv",
        checksum_sha256="a" * 64,
        content_type="text/csv",
        content_length=256,
        message="Static in-memory acquisition artifact for parser input mapping.",
    )
    manifest_entry = create_manifest_entry(acquisition_result)
    run_result = SourceAcquisitionRunResult(
        results=(acquisition_result,),
        manifest_entries=(manifest_entry,),
        manifest_path=None,
        acquired_count=1,
        failed_count=0,
        skipped_count=0,
    )

    parser_input = map_acquisition_artifact_to_parser_input(
        acquisition_result=acquisition_result,
        manifest_entry=manifest_entry,
        run_result=run_result,
        run_label="static-example-run",
    )

    return {
        "parser_input": asdict(parser_input),
        "parser_output_produced": False,
        "normalization_output_produced": False,
    }


def map_acquisition_artifact_to_parser_input(
    *,
    acquisition_result: SourceAcquisitionResult,
    manifest_entry: SourceAcquisitionManifestEntry,
    run_result: SourceAcquisitionRunResult,
    run_label: str,
) -> ParserInputContract:
    """Build a parser input contract from acquisition metadata."""

    return create_parser_input_contract(
        source_family=acquisition_result.source_family,
        source_id=acquisition_result.source_id,
        acquisition_status=acquisition_result.status,
        checksum_sha256=acquisition_result.checksum_sha256,
        artifact_reference=acquisition_result.local_path,
        content_type=acquisition_result.content_type,
        format_hint=_format_hint_from_artifact(acquisition_result),
        acquisition_run_id=run_label,
        run_metadata={
            "run_label": run_label,
            "result_count": len(run_result.results),
            "manifest_entry_count": len(run_result.manifest_entries),
            "manifest_path": (
                str(run_result.manifest_path)
                if run_result.manifest_path is not None
                else None
            ),
            "acquired_count": run_result.acquired_count,
            "failed_count": run_result.failed_count,
            "skipped_count": run_result.skipped_count,
        },
        manifest_metadata={
            "source_family": manifest_entry.source_family,
            "source_id": manifest_entry.source_id,
            "local_path": manifest_entry.local_path,
            "checksum_sha256": manifest_entry.checksum_sha256,
            "content_type": manifest_entry.content_type,
            "content_length": manifest_entry.content_length,
            "status": manifest_entry.status,
            "message": manifest_entry.message,
        },
    )


def _format_hint_from_artifact(
    acquisition_result: SourceAcquisitionResult,
) -> str | None:
    if acquisition_result.content_type == "text/csv":
        return "csv"

    if acquisition_result.local_path is None:
        return None

    suffix = PurePosixPath(acquisition_result.local_path).suffix.lower()
    if not suffix:
        return None

    return suffix.removeprefix(".")
