"""Command-line interface for source acquisition workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from carbonfactor_parser.source_acquisition.client import NoopSourceAcquisitionClient
from carbonfactor_parser.source_acquisition.registry import (
    create_default_source_acquisition_registry,
)
from carbonfactor_parser.source_acquisition.run import run_source_acquisition


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for source acquisition commands."""

    parser = argparse.ArgumentParser(
        prog="carbonfactor-parser-source-acquisition",
        description="Offline source acquisition CLI boundary.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser(
        "list",
        help="List default source descriptors.",
    )
    list_parser.add_argument(
        "--output-format",
        choices=("text", "json"),
        default="text",
        help="Output format for command results.",
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Run source acquisition with no-op client.",
    )
    run_parser.add_argument(
        "--manifest-path",
        type=Path,
        default=None,
        help="Optional local JSON manifest output path.",
    )
    run_parser.add_argument(
        "--output-format",
        choices=("text", "json"),
        default="text",
        help="Output format for command results.",
    )

    return parser


def _print_json_payload(payload: dict[str, object]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=False))


def _serialize_descriptor(descriptor: object) -> dict[str, object]:
    return {
        "source_id": descriptor.source_id,
        "source_family": descriptor.source_family,
        "display_name": descriptor.display_name,
        "expected_format": descriptor.expected_format,
        "enabled": descriptor.enabled,
    }


def _handle_list_command(output_format: str) -> int:
    descriptors = create_default_source_acquisition_registry()
    if output_format == "json":
        _print_json_payload(
            {
                "sources": [
                    _serialize_descriptor(descriptor)
                    for descriptor in descriptors
                ]
            }
        )
        return 0

    for descriptor in descriptors:
        print(
            " | ".join(
                (
                    descriptor.source_id,
                    descriptor.source_family,
                    descriptor.display_name,
                    descriptor.expected_format,
                    str(descriptor.enabled),
                )
            )
        )
    return 0


def _serialize_run_result(result: object) -> dict[str, object]:
    return {
        "source_id": result.source_id,
        "source_family": result.source_family,
        "status": result.status,
        "acquisition_url": result.acquisition_url,
        "local_path": result.local_path,
        "checksum_sha256": result.checksum_sha256,
        "message": result.message,
    }


def _handle_run_command(manifest_path: Path | None, output_format: str) -> int:
    descriptors = create_default_source_acquisition_registry()
    result = run_source_acquisition(
        descriptors=descriptors,
        client=NoopSourceAcquisitionClient(),
        manifest_path=manifest_path,
    )
    if output_format == "json":
        _print_json_payload(
            {
                "acquired_count": result.acquired_count,
                "failed_count": result.failed_count,
                "skipped_count": result.skipped_count,
                "manifest_path": str(result.manifest_path) if result.manifest_path is not None else None,
                "results": [_serialize_run_result(entry) for entry in result.results],
            }
        )
        return 0

    print(f"acquired_count={result.acquired_count}")
    print(f"failed_count={result.failed_count}")
    print(f"skipped_count={result.skipped_count}")
    if result.manifest_path is not None:
        print(f"manifest_path={result.manifest_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run source acquisition CLI command."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        return _handle_list_command(output_format=args.output_format)

    if args.command == "run":
        return _handle_run_command(
            manifest_path=args.manifest_path,
            output_format=args.output_format,
        )

    parser.print_usage()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
