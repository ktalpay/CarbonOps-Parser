"""Command-line interface for local CarbonOps parser boundaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from carbonfactor_parser.pipeline import (
    LocalFilePersistenceDryRunResult,
    LocalFilePersistenceDryRunStatus,
    run_local_file_normalized_persistence_dry_run,
)


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for local boundary commands."""

    parser = argparse.ArgumentParser(
        prog="carbonops-parser",
        description="Local CarbonOps parser boundary CLI.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    dry_run_parser = subparsers.add_parser(
        "local-dry-run",
        help="Run the local DEFRA/DESNZ fixture persistence dry-run.",
    )
    dry_run_parser.add_argument(
        "--local-path",
        type=Path,
        required=True,
        help="Explicit local UTF-8 DEFRA/DESNZ fixture file path.",
    )
    dry_run_parser.add_argument(
        "--source-family",
        required=True,
        help="Source family metadata, for example defra_desnz.",
    )
    dry_run_parser.add_argument(
        "--source-id",
        required=True,
        help="Source id metadata for the local fixture dry-run.",
    )
    dry_run_parser.add_argument(
        "--content-type",
        default=None,
        help="Optional content type hint, for example text/csv.",
    )
    dry_run_parser.add_argument(
        "--format-hint",
        default=None,
        help="Optional format hint, for example csv.",
    )
    dry_run_parser.add_argument(
        "--output-format",
        choices=("text", "json"),
        default="text",
        help="Output format for command results.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run local parser boundary CLI command."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "local-dry-run":
        if args.content_type is None and args.format_hint is None:
            parser.error(
                "local-dry-run requires --content-type or --format-hint.",
            )
        result = run_local_file_normalized_persistence_dry_run(
            local_path=args.local_path,
            source_family=args.source_family,
            source_id=args.source_id,
            content_type=args.content_type,
            format_hint=args.format_hint,
        )
        _emit_local_dry_run_result(result, output_format=args.output_format)
        return 0 if result.status == LocalFilePersistenceDryRunStatus.SUCCESS else 1

    parser.print_usage()
    return 2


def _emit_local_dry_run_result(
    result: LocalFilePersistenceDryRunResult,
    *,
    output_format: str,
) -> None:
    if output_format == "json":
        print(json.dumps(_serialize_local_dry_run_result(result), indent=2))
        return

    summary = _local_dry_run_summary(result)
    print(f"status={summary['status']}")
    print(f"parsed_record_count={summary['parsed_record_count']}")
    print(f"normalization_record_count={summary['normalization_record_count']}")
    print(f"persistence_input_record_count={summary['persistence_input_record_count']}")
    print(f"ddl_preview_present={summary['ddl_preview_present']}")
    print(f"issue_count={summary['issue_count']}")
    for issue in result.issues:
        print(
            " | ".join(
                (
                    issue.stage,
                    issue.severity,
                    issue.code,
                    issue.message,
                ),
            ),
        )


def _serialize_local_dry_run_result(
    result: LocalFilePersistenceDryRunResult,
) -> dict[str, object]:
    summary = _local_dry_run_summary(result)
    return {
        **summary,
        "source_family": result.source_family,
        "source_id": result.source_id,
        "local_path": result.local_path,
        "load_status": (
            result.load_result.status.value
            if result.load_result is not None
            else None
        ),
        "parser_status": (
            result.parser_result.status.value
            if result.parser_result is not None
            else None
        ),
        "handoff_status": (
            result.handoff_result.status.value
            if result.handoff_result is not None
            else None
        ),
        "normalization_input_status": (
            result.normalization_input_build_result.status.value
            if result.normalization_input_build_result is not None
            else None
        ),
        "normalization_mapping_status": (
            result.normalization_mapping_result.status.value
            if result.normalization_mapping_result is not None
            else None
        ),
        "persistence_input_status": (
            result.persistence_input_build_result.status.value
            if result.persistence_input_build_result is not None
            else None
        ),
        "ddl_preview": result.ddl_preview,
        "ddl_preview_metadata": result.ddl_preview_metadata,
        "issues": [
            {
                "stage": issue.stage,
                "severity": issue.severity,
                "code": issue.code,
                "message": issue.message,
            }
            for issue in result.issues
        ],
    }


def _local_dry_run_summary(
    result: LocalFilePersistenceDryRunResult,
) -> dict[str, object]:
    return {
        "status": result.status.value,
        "parsed_record_count": (
            result.parser_result.parsed_record_count
            if result.parser_result is not None
            else None
        ),
        "normalization_record_count": (
            len(result.normalization_mapping_result.normalization_result.records)
            if result.normalization_mapping_result is not None
            else None
        ),
        "persistence_input_record_count": (
            len(result.persistence_input.records)
            if result.persistence_input is not None
            else None
        ),
        "ddl_preview_present": result.ddl_preview is not None,
        "issue_count": len(result.issues),
    }


if __name__ == "__main__":
    raise SystemExit(main())
