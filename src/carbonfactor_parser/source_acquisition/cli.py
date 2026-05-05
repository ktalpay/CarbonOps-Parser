"""Command-line interface for source acquisition workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from carbonfactor_parser.source_acquisition.client import NoopSourceAcquisitionClient
from carbonfactor_parser.source_acquisition.http_client import HttpSourceAcquisitionClient
from carbonfactor_parser.source_acquisition.http_transport import (
    StandardLibraryHttpAcquisitionTransport,
)
from carbonfactor_parser.source_acquisition.descriptor_validation import (
    serialize_descriptor_validation_report,
    validate_source_descriptors,
)
from carbonfactor_parser.source_acquisition.registry import (
    create_default_source_acquisition_registry,
)
from carbonfactor_parser.source_acquisition.run import run_source_acquisition
from carbonfactor_parser.source_acquisition.targets import plan_source_acquisition_targets


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
    list_parser.add_argument(
        "--source-id",
        action="append",
        default=None,
        help="Filter to one or more source IDs from the default registry. Repeatable.",
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Run source acquisition with a selected client mode.",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan deterministic local target paths without acquisition or file writes.",
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
    run_parser.add_argument(
        "--source-id",
        action="append",
        default=None,
        help="Filter to one or more source IDs from the default registry. Repeatable.",
    )
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate default source descriptor metadata.",
    )
    validate_parser.add_argument(
        "--output-format",
        choices=("text", "json"),
        default="text",
        help="Output format for command results.",
    )
    validate_parser.add_argument(
        "--source-id",
        action="append",
        default=None,
        help="Filter to one or more source IDs from the default registry. Repeatable.",
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


def _build_run_client(
    *,
    client: str,
    base_directory: Path | None,
    persist_content: bool,
    timeout_seconds: float | None,
    parser: argparse.ArgumentParser,
) -> Any:
    if client == "noop":
        if persist_content:
            parser.error("--persist-content requires --client http.")
        if base_directory is not None:
            parser.error("--base-directory requires --client http.")
        if timeout_seconds is not None:
            parser.error("--timeout-seconds requires --client http.")
        return NoopSourceAcquisitionClient()

    if client != "http":
        parser.error(f"Unsupported client mode: {client}")

    if persist_content and base_directory is None:
        parser.error(
            "--base-directory is required when using --persist-content with --client http."
        )

    transport = StandardLibraryHttpAcquisitionTransport(timeout_seconds=timeout_seconds)
    return HttpSourceAcquisitionClient(
        transport=transport,
        timeout_seconds=timeout_seconds,
        base_directory=str(base_directory) if base_directory is not None else None,
        persist_content=persist_content,
    )


def _filter_descriptors_by_source_id(
    *,
    descriptors: tuple[object, ...],
    source_ids: list[str] | None,
    parser: argparse.ArgumentParser,
) -> tuple[object, ...]:
    if source_ids is None:
        return descriptors

    duplicate_source_ids = sorted(
        {
            source_id
            for source_id in source_ids
            if source_ids.count(source_id) > 1
        }
    )
    if duplicate_source_ids:
        parser.error(
            f"Duplicate --source-id values are not allowed: {', '.join(duplicate_source_ids)}"
        )

    requested_source_ids = set(source_ids)
    available_source_ids = {descriptor.source_id for descriptor in descriptors}
    unknown_source_ids = sorted(requested_source_ids - available_source_ids)
    if unknown_source_ids:
        parser.error(f"Unknown --source-id value(s): {', '.join(unknown_source_ids)}")

    return tuple(
        descriptor
        for descriptor in descriptors
        if descriptor.source_id in requested_source_ids
    )


def _handle_list_command(
    *,
    output_format: str,
    source_ids: list[str] | None,
    parser: argparse.ArgumentParser,
) -> int:
    descriptors = create_default_source_acquisition_registry()
    descriptors = _filter_descriptors_by_source_id(
        descriptors=descriptors,
        source_ids=source_ids,
        parser=parser,
    )

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


def _handle_run_command(
    *,
    manifest_path: Path | None,
    output_format: str,
    client: object,
    source_ids: list[str] | None,
    parser: argparse.ArgumentParser,
) -> int:
    descriptors = create_default_source_acquisition_registry()
    descriptors = _filter_descriptors_by_source_id(
        descriptors=descriptors,
        source_ids=source_ids,
        parser=parser,
    )
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


def _handle_dry_run_command(
    *,
    base_directory: Path,
    output_format: str,
    source_ids: list[str] | None,
    parser: argparse.ArgumentParser,
) -> int:
    descriptors = create_default_source_acquisition_registry()
    descriptors = _filter_descriptors_by_source_id(
        descriptors=descriptors,
        source_ids=source_ids,
        parser=parser,
    )
    targets = plan_source_acquisition_targets(
        descriptors=descriptors,
        base_directory=base_directory,
    )

    if output_format == "json":
        _emit_json(
            {
                "dry_run": True,
                "targets": [
                    {
                        "source_id": target.source_id,
                        "source_family": target.source_family,
                        "expected_format": target.expected_format,
                        "local_path": str(target.local_path),
                    }
                    for target in targets
                ],
            }
        )
        return 0

    for target in targets:
        print(f"source_id={target.source_id} local_path={target.local_path}")

    return 0


def _handle_validate_command(
    *,
    output_format: str,
    source_ids: list[str] | None,
    parser: argparse.ArgumentParser,
) -> int:
    descriptors = create_default_source_acquisition_registry()
    descriptors = _filter_descriptors_by_source_id(
        descriptors=descriptors,
        source_ids=source_ids,
        parser=parser,
    )
    report = validate_source_descriptors(descriptors)

    if output_format == "json":
        print(serialize_descriptor_validation_report(report))
    else:
        print(f"issue_count={report.issue_count}")
        print(f"warning_count={report.warning_count}")
        print(f"error_count={report.error_count}")
        for issue in report.issues:
            print(
                f"{issue.severity} | {issue.source_id} | {issue.field} | {issue.message}"
            )

    return 1 if report.error_count > 0 else 0


def main(argv: list[str] | None = None) -> int:
    """Run source acquisition CLI command."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        return _handle_list_command(
            output_format=args.output_format,
            source_ids=args.source_id,
            parser=parser,
        )

    if args.command == "run":
        if args.dry_run:
            if args.base_directory is None:
                parser.error("--dry-run requires --base-directory.")
            if args.manifest_path is not None:
                parser.error("--dry-run cannot be combined with --manifest-path.")
            if args.persist_content:
                parser.error("--dry-run cannot be combined with --persist-content.")
            if args.timeout_seconds is not None:
                parser.error("--dry-run cannot be combined with --timeout-seconds.")
            return _handle_dry_run_command(
                base_directory=args.base_directory,
                output_format=args.output_format,
                source_ids=args.source_id,
                parser=parser,
            )

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
            source_ids=args.source_id,
            parser=parser,
        )
    if args.command == "validate":
        return _handle_validate_command(
            output_format=args.output_format,
            source_ids=args.source_id,
            parser=parser,
        )

    parser.print_usage()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
