"""Command-line interface for source acquisition workflows."""

from __future__ import annotations

import argparse
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

    subparsers.add_parser(
        "list",
        help="List default source descriptors.",
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

    return parser


def _handle_list_command() -> int:
    descriptors = create_default_source_acquisition_registry()
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


def _handle_run_command(manifest_path: Path | None) -> int:
    descriptors = create_default_source_acquisition_registry()
    result = run_source_acquisition(
        descriptors=descriptors,
        client=NoopSourceAcquisitionClient(),
        manifest_path=manifest_path,
    )
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
        return _handle_list_command()

    if args.command == "run":
        return _handle_run_command(manifest_path=args.manifest_path)

    parser.print_usage()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
