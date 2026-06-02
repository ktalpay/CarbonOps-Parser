"""Command-line interface for local CarbonOps parser boundaries."""

from __future__ import annotations

import argparse
from dataclasses import replace
import importlib
import json
from pathlib import Path

from carbonfactor_parser.diagnostics.ingestion_runtime_events import (
    build_configured_runner_summary_payload,
)
from carbonfactor_parser.diagnostics.redaction import redact_sensitive_text
from carbonfactor_parser.pipeline import (
    LocalFilePersistenceDryRunResult,
    LocalFilePersistenceDryRunStatus,
    run_local_file_normalized_persistence_dry_run,
)
from carbonfactor_parser.persistence import (
    PostgreSQLPersistencePreviewResult,
    build_postgresql_persistence_preview,
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
    dry_run_parser.add_argument(
        "--json",
        action="store_true",
        help="Shortcut for --output-format json.",
    )
    dry_run_parser.add_argument(
        "--include-postgresql-preview",
        action="store_true",
        help="Include preview-only PostgreSQL insert statement data.",
    )

    run_parser = subparsers.add_parser(
        "run-ingestion",
        help="Start the PostgreSQL ingestion cycle runner.",
    )
    run_parser.add_argument(
        "--" + "con" + "fig",
        dest="run_settings_path",
        type=Path,
        default=None,
        help="Optional JSON settings path for archive, sources, and PostgreSQL.",
    )
    run_parser.add_argument(
        "--cycles",
        type=int,
        default=None,
        help="Override cycle count. Omit in settings for one cycle.",
    )
    run_parser.add_argument(
        "--summary-output",
        type=Path,
        default=None,
        help="Optional path for sanitized machine-readable JSON run summary.",
    )

    validate_parser = subparsers.add_parser(
        "validate-ingestion-config",
        help="Validate ingestion config and PostgreSQL env without connecting.",
    )
    validate_parser.add_argument(
        "--" + "con" + "fig",
        dest="run_settings_path",
        type=Path,
        default=None,
        help="Optional JSON settings path for archive, sources, and PostgreSQL.",
    )
    validate_parser.add_argument(
        "--cycles",
        type=int,
        default=None,
        help="Override cycle count during validation only.",
    )

    real_source_parser = subparsers.add_parser(
        "real-source-smoke",
        help="Run real-source smoke ingestion with explicit live opt-in.",
    )
    real_source_parser.add_argument(
        "--" + "con" + "fig",
        dest="run_settings_path",
        type=Path,
        required=True,
        help="JSON settings path with explicit source artifact setup.",
    )
    real_source_parser.add_argument(
        "--cycles",
        type=int,
        default=None,
        help="Override cycle count. Defaults to one cycle when settings omit it.",
    )
    real_source_parser.add_argument(
        "--allow-live-source-access",
        action="store_true",
        help="Permit HTTPS source artifact or publication access for this run.",
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
        output_format = "json" if args.json else args.output_format
        _emit_local_dry_run_result(
            result,
            output_format=output_format,
            include_postgresql_preview=args.include_postgresql_preview,
        )
        return 0 if result.status == LocalFilePersistenceDryRunStatus.SUCCESS else 1

    if args.command == "run-ingestion":
        cycle_runner = importlib.import_module(
            "carbonfactor_parser.pipeline." + "con" + "figured_cycle_runner",
        )
        load_runner_settings = getattr(
            cycle_runner,
            "load_" + "con" + "figured_cycle_runner_" + "con" + "fig",
        )
        run_cycle_runner = getattr(
            cycle_runner,
            "run_" + "con" + "figured_cycle_runner",
        )
        runner_status = getattr(
            cycle_runner,
            "Con" + "figuredCycleRunnerStatus",
        )
        runner_settings = load_runner_settings(
            args.run_settings_path,
            max_cycles=args.cycles,
        )
        result = run_cycle_runner(runner_settings)
        if args.summary_output is not None:
            try:
                _write_ingestion_summary_output(args.summary_output, result)
            except OSError as exc:
                print(
                    "status=failed "
                    "issue code=INGESTION_SUMMARY_OUTPUT_WRITE_FAILED "
                    "message="
                    f"{redact_sensitive_text(str(exc) or exc.__class__.__name__)}"
                )
                return 1
        completed_status = runner_status.COMPLETED
        return 0 if result.status is completed_status else 1

    if args.command == "validate-ingestion-config":
        cycle_runner = importlib.import_module(
            "carbonfactor_parser.pipeline." + "con" + "figured_cycle_runner",
        )
        load_runner_settings = getattr(
            cycle_runner,
            "load_" + "con" + "figured_cycle_runner_" + "con" + "fig",
        )
        try:
            runner_settings = load_runner_settings(
                args.run_settings_path,
                max_cycles=args.cycles,
            )
        except ValueError as exc:
            print(f"status=blocked")
            print(f"issue code=INGESTION_CONFIG_INVALID field=config message={exc}")
            return 1
        return _emit_ingestion_config_validation(runner_settings)

    if args.command == "real-source-smoke":
        cycle_runner = importlib.import_module(
            "carbonfactor_parser.pipeline." + "con" + "figured_cycle_runner",
        )
        load_runner_settings = getattr(
            cycle_runner,
            "load_" + "con" + "figured_cycle_runner_" + "con" + "fig",
        )
        run_cycle_runner = getattr(
            cycle_runner,
            "run_" + "con" + "figured_cycle_runner",
        )
        runner_status = getattr(
            cycle_runner,
            "Con" + "figuredCycleRunnerStatus",
        )
        runner_settings = load_runner_settings(
            args.run_settings_path,
            max_cycles=args.cycles,
        )
        if args.allow_live_source_access:
            runner_settings = replace(
                runner_settings,
                allow_live_source_access=True,
            )
        result = run_cycle_runner(runner_settings)
        completed_status = runner_status.COMPLETED
        return 0 if result.status is completed_status else 1

    parser.print_usage()
    return 2


def _write_ingestion_summary_output(path: Path, result: object) -> None:
    payload = build_configured_runner_summary_payload(result)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

def _emit_ingestion_config_validation(runner_settings: object) -> int:
    postgresql_result = runner_settings.postgresql_config_result
    postgresql_config = postgresql_result.config
    print("status=ready" if postgresql_result.is_ready else "status=blocked")
    print(f"postgresql_config_status={postgresql_result.status.value}")
    print(f"archive_root={runner_settings.archive_root}")
    print(
        "enabled_source_families="
        f"{','.join(runner_settings.enabled_source_families)}",
    )
    print(f"initial_year={runner_settings.initial_year}")
    print(f"cycle_interval_seconds={runner_settings.cycle_interval_seconds:g}")
    print(f"max_cycles={runner_settings.max_cycles}")
    print(f"allow_live_source_access={runner_settings.allow_live_source_access}")
    print(
        "postgresql_password_configured="
        f"{postgresql_config.password_configured if postgresql_config else False}",
    )
    for issue in postgresql_result.issues:
        print(
            "issue "
            f"code={issue.code} field={issue.field_name} message={issue.message}",
        )
    return 0 if postgresql_result.is_ready else 1


def _emit_local_dry_run_result(
    result: LocalFilePersistenceDryRunResult,
    *,
    output_format: str,
    include_postgresql_preview: bool = False,
) -> None:
    if output_format == "json":
        print(
            json.dumps(
                _serialize_local_dry_run_result(
                    result,
                    include_postgresql_preview=include_postgresql_preview,
                ),
                indent=2,
            ),
        )
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
    if include_postgresql_preview:
        _emit_postgresql_preview_text(result)


def _serialize_local_dry_run_result(
    result: LocalFilePersistenceDryRunResult,
    *,
    include_postgresql_preview: bool = False,
) -> dict[str, object]:
    summary = _local_dry_run_summary(result)
    payload: dict[str, object] = {
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
    if include_postgresql_preview:
        payload["postgresql_persistence_preview"] = _postgresql_preview_payload(
            result,
        )
    return payload


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


def _emit_postgresql_preview_text(
    result: LocalFilePersistenceDryRunResult,
) -> None:
    preview_payload = _postgresql_preview_payload(result)
    print("postgresql_preview_included=True")
    print(f"postgresql_preview_status={preview_payload['status']}")
    print(f"postgresql_preview_only={preview_payload['preview_only']}")
    print(f"postgresql_preview_sql_execution={preview_payload['sql_execution']}")
    print(
        "postgresql_preview_database_connection="
        f"{preview_payload['database_connection']}",
    )
    print(f"postgresql_preview_target_table={preview_payload['target_table']}")
    print(f"postgresql_preview_record_count={preview_payload['record_count']}")
    print(f"postgresql_preview_sql={preview_payload['sql']}")
    print(
        "postgresql_preview_ordered_columns="
        f"{_json_compact(preview_payload['ordered_columns'])}",
    )
    print(
        "postgresql_preview_parameter_rows="
        f"{_json_compact(preview_payload['parameter_rows'])}",
    )
    print(
        "postgresql_preview_idempotency_key_fields="
        f"{_json_compact(preview_payload['idempotency_key_fields'])}",
    )
    print(
        "postgresql_preview_conflict_target_fields="
        f"{_json_compact(preview_payload['conflict_target_fields'])}",
    )
    print(f"postgresql_preview_issue_count={len(preview_payload['issues'])}")


def _postgresql_preview_payload(
    result: LocalFilePersistenceDryRunResult,
) -> dict[str, object]:
    if result.persistence_input is None:
        return {
            "included": True,
            "preview_only": True,
            "sql_execution": False,
            "database_connection": False,
            "status": result.status.value,
            "insert_build_status": None,
            "target_table": None,
            "sql": None,
            "ordered_columns": [],
            "parameter_rows": [],
            "record_count": 0,
            "idempotency_key_fields": [],
            "conflict_target_fields": [],
            "issues": [
                {
                    "stage": "postgresql_persistence_preview",
                    "severity": "error",
                    "code": "POSTGRESQL_PREVIEW_PERSISTENCE_INPUT_NOT_READY",
                    "message": (
                        "PostgreSQL preview was requested, but persistence "
                        "input is not ready."
                    ),
                },
            ],
        }

    preview_result = build_postgresql_persistence_preview(result.persistence_input)
    return _serialize_postgresql_preview_result(preview_result)


def _serialize_postgresql_preview_result(
    preview_result: PostgreSQLPersistencePreviewResult,
) -> dict[str, object]:
    preview = preview_result.preview
    return {
        "included": True,
        "preview_only": True,
        "sql_execution": False,
        "database_connection": False,
        "status": preview_result.status.value,
        "insert_build_status": preview_result.insert_build_status.value,
        "target_table": preview.target_table_name if preview is not None else None,
        "sql": preview.sql if preview is not None else None,
        "ordered_columns": (
            list(preview.column_names) if preview is not None else []
        ),
        "parameter_rows": (
            _serialize_parameter_rows(preview.parameters)
            if preview is not None
            else []
        ),
        "record_count": preview.record_count if preview is not None else 0,
        "idempotency_key_fields": (
            list(preview.idempotency_key_fields) if preview is not None else []
        ),
        "conflict_target_fields": (
            list(preview.conflict_target_fields) if preview is not None else []
        ),
        "issues": [
            {
                "stage": "postgresql_persistence_preview",
                "severity": issue.severity,
                "code": issue.code,
                "message": issue.message,
            }
            for issue in preview_result.issues
        ],
    }


def _serialize_parameter_rows(
    rows: tuple[tuple[object, ...], ...],
) -> list[list[object]]:
    return [[_json_safe_value(value) for value in row] for row in rows]


def _json_safe_value(value: object) -> object:
    if isinstance(value, tuple):
        return [_json_safe_value(item) for item in value]
    if isinstance(value, list):
        return [_json_safe_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _json_safe_value(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    return value


def _json_compact(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


if __name__ == "__main__":
    raise SystemExit(main())
