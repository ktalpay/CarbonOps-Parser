"""Command-line interface for source acquisition workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from carbonfactor_parser.source_acquisition.client import NoopSourceAcquisitionClient
from carbonfactor_parser.source_acquisition.http_client import HttpSourceAcquisitionClient
from carbonfactor_parser.source_acquisition.http_transport import (
    StandardLibraryHttpAcquisitionTransport,
)
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
        help="Run source acquisition with a selected client mode.",
    )
    run_parser.add_argument(
        "--client",
        choices=("noop", "http"),
        default="noop",
        help="Acquisition client mode. Default remains offline noop mode.",
    )
    run_parser.add_argument(
        "--manifest-path",
        type=Path,
        default=None,
        help="Optional local JSON manifest output path.",
    )
    run_parser.add_argument(
        "--base-directory",
        type=Path,
        default=None,
        help="Base directory used for persisted acquired content in HTTP mode.",
    )
    run_parser.add_argument(
        "--persist-content",
        action="store_true",
        help="Persist HTTP-acquired content to planned local target paths.",
    )
    run_parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=None,
        help="Optional HTTP timeout in seconds for HTTP mode transport.",
    )
    run_parser.add_argument(
        "--output-format",
        choices=("text", "json"),
        default="text",
        help="Output format for command results.",
    )

    return parser


def _emit_json(payload: dict[str, object]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=False))


def _serialize_descriptor(descriptor: object) -> dict[str, object]:
    return {
        "source_id": descriptor.source_id,
        "source_family": descriptor.source_family,
        "display_name": descriptor.display_name,
        "expected_format": descriptor.expected_format,
        "enabled": descriptor.enabled,
    }


def _serialize_result(result: object) -> dict[str, object]:
    return {
        "source_id": result.source_id,
        "source_family": result.source_family,
        "status": result.status,
        "acquisition_url": result.acquisition_url,
        "local_path": result.local_path,
        "checksum_sha256": result.checksum_sha256,
        "message": result.message,
    }


def _build_run_client(*, client: str, base_directory: Path | None, persist_content: bool, timeout_seconds: float | None, parser: argparse.ArgumentParser) -> object:
    if client == "noop":
        if persist_content:
            parser.error("--persist-content requires --client http.")
        if base_directory is not None:
            parser.error("--base-directory requires --client http.")
        if timeout_seconds is not None:
            parser.error("--timeout-seconds requires --client http.")
        return NoopSourceAcquisitionClient()

    if persist_content and base_directory is None:
        parser.error("--base-directory is required when using --persist-content with --client http.")

    transport = StandardLibraryHttpAcquisitionTransport(timeout_seconds=timeout_seconds)
    return HttpSourceAcquisitionClient(
        transport=transport,
        timeout_seconds=timeout_seconds,
        base_directory=str(base_directory) if base_directory is not None else None,
        persist_content=persist_content,
    )


def _handle_list_command(output_format: str) -> int:
    descriptors = create_default_source_acquisition_registry()

    if output_format == "json":
        _emit_json(
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


def _handle_run_command(*, manifest_path: Path | None, output_format: str, client: object) -> int:
    descriptors = create_default_source_acquisition_registry()
    result = run_source_acquisition(
        descriptors=descriptors,
        client=client,
        manifest_path=manifest_path,
    )

    if output_format == "json":
        _emit_json(
            {
                "acquired_count": result.acquired_count,
                "failed_count": result.failed_count,
                "skipped_count": result.skipped_count,
                "manifest_path": (
                    str(result.manifest_path)
                    if result.manifest_path is not None
                    else None
                ),
                "results": [
                    _serialize_result(entry)
                    for entry in result.results
                ],
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
        client = _build_run_client(
            client=args.client,
            base_directory=args.base_directory,
            persist_content=args.persist_content,
            timeout_seconds=args.timeout_seconds,
            parser=parser,
        )
        return _handle_run_command(
            manifest_path=args.manifest_path,
            output_format=args.output_format,
            client=client,
        )

    parser.print_usage()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
