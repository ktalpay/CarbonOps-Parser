#!/usr/bin/env python3
"""Production release-candidate dry-run verification.

The default path is local-only and non-destructive. It validates production-like
configuration metadata, schema-bootstrap readiness, service-host entrypoints,
orchestrator dry-run behavior, diagnostic redaction, and CI gate status without
loading environment values, opening network connections, or executing SQL.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import sys
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = REPOSITORY_ROOT / "src"
INTEGRATION_OPT_IN_ENV = "CARBONOPS_PRODUCTION_RC_RUN_INTEGRATION"
LIVE_OPT_IN_ENV = "CARBONOPS_PRODUCTION_RC_RUN_LIVE"

if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))


@dataclass(frozen=True)
class RCVerificationCheck:
    name: str
    status: str
    message: str
    next_step: str


@dataclass(frozen=True)
class RCVerificationReport:
    mode: str
    destructive_operations_enabled: bool
    live_source_calls_enabled: bool
    database_connections_enabled: bool
    checks: tuple[RCVerificationCheck, ...]

    @property
    def passed(self) -> bool:
        return all(check.status in {"passed", "skipped"} for check in self.checks)


def build_production_rc_verification_report(
    *,
    root: Path = REPOSITORY_ROOT,
    python_bin: str = sys.executable,
    mode: str = "dry-run",
    run_ci_gate: bool = False,
    env: dict[str, str] | None = None,
) -> RCVerificationReport:
    active_env = {} if env is None else dict(env)
    checks: list[RCVerificationCheck] = []

    checks.extend(_mode_guardrail_checks(mode, active_env))
    if checks and any(check.status == "failed" for check in checks):
        return RCVerificationReport(
            mode=mode,
            destructive_operations_enabled=False,
            live_source_calls_enabled=False,
            database_connections_enabled=False,
            checks=tuple(checks),
        )

    checks.append(_check_production_config_validation())
    checks.append(_check_schema_bootstrap_readiness())
    checks.append(_check_service_entrypoint())
    checks.append(_check_orchestrator_dry_run())
    checks.append(_check_diagnostics_redaction())
    checks.append(_check_ci_gate_status(root, python_bin, run_ci_gate, active_env))

    return RCVerificationReport(
        mode=mode,
        destructive_operations_enabled=False,
        live_source_calls_enabled=False,
        database_connections_enabled=False,
        checks=tuple(checks),
    )


def _mode_guardrail_checks(
    mode: str,
    env: dict[str, str],
) -> list[RCVerificationCheck]:
    if mode == "dry-run":
        return []
    if mode == "integration" and env.get(INTEGRATION_OPT_IN_ENV) == "1":
        return [
            RCVerificationCheck(
                name="integration mode guardrail",
                status="skipped",
                message=(
                    "Integration mode was explicitly requested; default RC "
                    "checks still avoid database connections unless delegated "
                    "CI integration variables are also supplied."
                ),
                next_step="Set release-gate integration variables only in an approved isolated runner.",
            )
        ]
    if mode == "live" and env.get(LIVE_OPT_IN_ENV) == "1":
        return [
            RCVerificationCheck(
                name="live mode guardrail",
                status="skipped",
                message=(
                    "Live mode was explicitly requested, but this verifier does "
                    "not call live source endpoints or deploy services."
                ),
                next_step="Use a separately approved live-run task before enabling source endpoints.",
            )
        ]
    return [
        RCVerificationCheck(
            name=f"{mode} mode guardrail",
            status="failed",
            message=(
                f"{mode} mode requires explicit opt-in and is separated from "
                "the default non-destructive dry-run path."
            ),
            next_step=(
                f"Use --mode dry-run, or set "
                f"{INTEGRATION_OPT_IN_ENV}=1/{LIVE_OPT_IN_ENV}=1 only in an "
                "approved runner for the matching mode."
            ),
        )
    ]


def _check_production_config_validation() -> RCVerificationCheck:
    from carbonfactor_parser.persistence.production_config_boundary import (
        validate_production_config_mapping,
    )

    result = validate_production_config_mapping(
        {
            "CARBONOPS_PARSER_ENV": "production",
            "CARBONOPS_PARSER_DATABASE_PROVIDER": "postgres",
            "CARBONOPS_PARSER_POSTGRES_HOST": "db.internal.example",
            "CARBONOPS_PARSER_POSTGRES_PORT": "5432",
            "CARBONOPS_PARSER_POSTGRES_DATABASE": "carbonops_parser",
            "CARBONOPS_PARSER_POSTGRES_USERNAME": "carbonops_runtime",
            "CARBONOPS_PARSER_POSTGRES_PASSWORD": "external-secret-present",
            "CARBONOPS_PARSER_POSTGRES_SCHEMA": "carbonops",
            "CARBONOPS_PARSER_RAW_ARCHIVE_PATH": "/var/lib/carbonops/raw",
            "CARBONOPS_PARSER_LOG_LEVEL": "info",
        }
    )
    if result.is_valid:
        return RCVerificationCheck(
            "production config validation",
            "passed",
            "Production-like split config keys validate without environment loading.",
            "Keep raw connection strings out of config and diagnostics.",
        )
    return RCVerificationCheck(
        "production config validation",
        "failed",
        _issue_summary(result.issues),
        "Fix the named production config keys before any service start attempt.",
    )


def _check_schema_bootstrap_readiness() -> RCVerificationCheck:
    from carbonfactor_parser.persistence.postgresql_schema_bootstrap import (
        build_postgresql_phase1_schema_bootstrap_report,
    )
    from carbonfactor_parser.persistence.postgresql_schema_catalog import (
        get_required_table_names,
    )

    report = build_postgresql_phase1_schema_bootstrap_report(
        present_table_names=get_required_table_names(),
        fail_on_missing=True,
    )
    if not report.missing_table_names:
        return RCVerificationCheck(
            "schema bootstrap readiness",
            "passed",
            "Required Phase 1 table names are present in the passive readiness report.",
            "Compare this report with the target schema before enabling any future runtime execution.",
        )
    return RCVerificationCheck(
        "schema bootstrap readiness",
        "failed",
        f"Missing table count: {len(report.missing_table_names)}.",
        "Review the PostgreSQL Phase 1 schema contract; do not run ad hoc destructive SQL.",
    )


def _check_service_entrypoint() -> RCVerificationCheck:
    from carbonfactor_parser.persistence.postgresql_options import (
        create_postgresql_persistence_options,
    )
    from carbonfactor_parser.persistence.postgresql_schema_bootstrap import (
        PostgreSQLSchemaBootstrapMode,
        build_postgresql_phase1_schema_bootstrap_report,
    )
    from carbonfactor_parser.persistence.postgresql_schema_catalog import (
        get_required_table_names,
    )
    from carbonfactor_parser.source_acquisition.phase1_ingestion_orchestrator import (
        Phase1IngestionOrchestratorRequest,
    )
    from carbonfactor_parser.source_acquisition.phase1_service_host import (
        Phase1ScheduledIngestionServiceHost,
        Phase1ScheduledRunStatus,
        Phase1ServiceHostConfig,
    )

    def checker(mode, fail_on_missing):
        return build_postgresql_phase1_schema_bootstrap_report(
            mode=mode,
            present_table_names=get_required_table_names(),
            fail_on_missing=fail_on_missing,
        )

    def runner(request: Phase1IngestionOrchestratorRequest):
        return _orchestrator_dry_run_result(request)

    host = Phase1ScheduledIngestionServiceHost(
        Phase1ServiceHostConfig(
            source_families=("ghg_protocol",),
            run_id_prefix="phase1-rc-dry-run",
            postgresql_options=create_postgresql_persistence_options(
                host="db.internal.example",
                port=5432,
                database="carbonops_parser",
                username="carbonops_runtime",
                password_set=True,
            ),
            schema_bootstrap_mode=PostgreSQLSchemaBootstrapMode.CHECK_ONLY,
            fail_on_missing_schema=True,
        ),
        schema_bootstrap_checker=checker,
        orchestrator_runner=runner,
    )
    startup = host.start()
    scheduled = host.trigger_scheduled_run()
    if startup.is_ready and scheduled.status is Phase1ScheduledRunStatus.STARTED:
        return RCVerificationCheck(
            "service entrypoint availability",
            "passed",
            "Service host starts after passive schema readiness and triggers one injected dry-run.",
            "Keep production wrappers behind the same startup and shutdown gates.",
        )
    return RCVerificationCheck(
        "service entrypoint availability",
        "failed",
        f"Startup={startup.status.value}; scheduled={scheduled.status.value}.",
        "Resolve service-host issue codes before any production start attempt.",
    )


def _check_orchestrator_dry_run() -> RCVerificationCheck:
    from carbonfactor_parser.source_acquisition.phase1_ingestion_orchestrator import (
        PHASE1_SOURCE_FAMILIES,
        Phase1IngestionOrchestratorRequest,
        Phase1IngestionRunStatus,
        run_phase1_ingestion_orchestrator,
    )

    result = run_phase1_ingestion_orchestrator(
        Phase1IngestionOrchestratorRequest(
            source_families=PHASE1_SOURCE_FAMILIES,
            run_id="phase1-rc-dry-run-000001",
            correlation_id="phase1-rc-dry-run",
        ),
        _dry_run_dependencies(),
    )
    if result.status is Phase1IngestionRunStatus.COMPLETED:
        return RCVerificationCheck(
            "orchestrator dry-run behavior",
            "passed",
            (
                "Injected fixture runtimes completed sequentially with "
                f"{result.summary.parsed_factor_row_count} parsed rows and no external calls."
            ),
            "Keep live source adapters disabled unless a later task explicitly scopes them.",
        )
    return RCVerificationCheck(
        "orchestrator dry-run behavior",
        "failed",
        _failure_summary(result.failures),
        "Inspect the named orchestrator stage before using the service host.",
    )


def _check_diagnostics_redaction() -> RCVerificationCheck:
    from carbonfactor_parser.persistence.postgresql_options import (
        create_postgresql_persistence_options,
    )
    from carbonfactor_parser.source_acquisition.phase1_observability import (
        REDACTED,
        redact_diagnostic_value,
        summarize_postgresql_options_for_diagnostics,
    )

    payload = summarize_postgresql_options_for_diagnostics(
        create_postgresql_persistence_options(
            host="secret-db.internal",
            port=5432,
            database="secret_database",
            username="secret_user",
            password_set=True,
        )
    )
    nested = redact_diagnostic_value(
        "payload",
        {"password": "raw-secret", "token": "raw-token", "safe": "visible"},
    )
    rendered = json.dumps({"payload": payload, "nested": nested}, sort_keys=True)
    leaked = [
        value
        for value in ("secret-db", "secret_database", "secret_user", "raw-secret", "raw-token")
        if value in rendered
    ]
    if payload["host"] == REDACTED and payload["database"] == REDACTED and not leaked:
        return RCVerificationCheck(
            "diagnostics redaction",
            "passed",
            "PostgreSQL options and sensitive diagnostic fields are redacted.",
            "Do not add raw configured values to failure output or logs.",
        )
    return RCVerificationCheck(
        "diagnostics redaction",
        "failed",
        "Sensitive diagnostic value appeared in rendered output.",
        "Redact the named diagnostic fields before retrying RC verification.",
    )


def _check_ci_gate_status(
    root: Path,
    python_bin: str,
    run_ci_gate: bool,
    env: dict[str, str],
) -> RCVerificationCheck:
    release_gate = _load_release_gate()
    captured_output = io.StringIO()
    with contextlib.redirect_stdout(captured_output), contextlib.redirect_stderr(
        captured_output,
    ):
        exit_code = release_gate.run_gate(
            root=root,
            python_bin=python_bin,
            run_commands=run_ci_gate,
            env=env,
        )
    if exit_code == 0:
        mode = "executed" if run_ci_gate else "static check-only"
        return RCVerificationCheck(
            "CI release gate status",
            "passed",
            f"Release validation gate {mode} completed successfully.",
            "Run python scripts/release_validation_gate.py before final review.",
        )
    return RCVerificationCheck(
        "CI release gate status",
        "failed",
        f"Release validation gate returned exit code {exit_code}.",
        "Run python scripts/release_validation_gate.py and fix the first failed command.",
    )


def _load_release_gate():
    path = SCRIPT_DIR / "release_validation_gate.py"
    spec = importlib.util.spec_from_file_location("release_validation_gate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load release_validation_gate.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _orchestrator_dry_run_result(request):
    from carbonfactor_parser.source_acquisition.phase1_ingestion_orchestrator import (
        Phase1IngestionOrchestratorResult,
        Phase1IngestionRunStatus,
        Phase1IngestionRunSummary,
    )

    return Phase1IngestionOrchestratorResult(
        status=Phase1IngestionRunStatus.COMPLETED,
        request=request,
        selected_source_families=request.source_families,
        family_results=(),
        summary=Phase1IngestionRunSummary(
            requested_family_count=len(request.source_families),
            completed_family_count=len(request.source_families),
            failed_family_count=0,
            source_candidate_count=0,
            source_artifact_count=0,
            parser_run_count=0,
            parsed_factor_row_count=0,
            persisted_source_run_count=0,
            persisted_source_document_count=0,
            persisted_parser_run_count=0,
            persisted_master_count=0,
            persisted_detail_count=0,
            failure_count=0,
        ),
    )


def _dry_run_dependencies():
    from carbonfactor_parser.source_acquisition.phase1_ingestion_orchestrator import (
        PHASE1_SOURCE_FAMILIES,
        Phase1IngestionOrchestratorDependencies,
    )

    return Phase1IngestionOrchestratorDependencies(
        source_runtimes={
            source_family: _DryRunSourceRuntime(source_family)
            for source_family in PHASE1_SOURCE_FAMILIES
        },
        source_run_repository=_DryRunSourceRunRepository(),
        source_document_repository=_DryRunSourceDocumentRepository(),
        parser_run_repository=_DryRunParserRunRepository(),
        parsed_factor_repository=_DryRunSourceFamilyRepository(),
    )


class _DryRunSourceRuntime:
    def __init__(self, source_family: str) -> None:
        self.source_family = source_family

    def discover(self, source_family, request):
        from carbonfactor_parser.source_acquisition.discovery_candidate_contract import (
            SourceDiscoveryCandidate,
            SourceDiscoveryCandidateResult,
        )

        return SourceDiscoveryCandidateResult(
            candidates=(
                SourceDiscoveryCandidate(
                    source_family=source_family,
                    source_key=source_family,
                    candidate_id=f"{source_family}-rc-candidate",
                    title=f"{source_family} RC fixture",
                    reference_uri=f"fixture://{source_family}/source.csv",
                    artifact_kind="csv",
                    reporting_year=2024,
                    content_type="text/csv",
                    extension=".csv",
                    version_label="rc-fixture",
                ),
            )
        )

    def download(self, source_family, discovery_result, request):
        from carbonfactor_parser.source_acquisition.download_artifact_contract import (
            create_source_download_artifact_from_candidate,
        )
        from carbonfactor_parser.source_acquisition.run_contract import (
            SourceAcquisitionRunResult,
            SourceAcquisitionRunStatus,
            SourceAcquisitionRunSummary,
        )

        artifact = create_source_download_artifact_from_candidate(
            discovery_result.candidates[0],
            artifact_id=f"{source_family}-rc-artifact",
            local_reference=f"fixture://{source_family}/downloaded.csv",
            content_type="text/csv",
            extension=".csv",
        )
        return SourceAcquisitionRunResult(
            source_family=source_family,
            source_key=source_family,
            status=SourceAcquisitionRunStatus.COMPLETED,
            candidates=discovery_result.candidates,
            artifacts=(artifact,),
            issues=(),
            summary=SourceAcquisitionRunSummary(
                candidate_count=1,
                artifact_count=1,
                issue_count=0,
                info_count=0,
                warning_count=0,
                error_count=0,
            ),
            run_id=request.run_id,
            version_label="rc-fixture",
        )

    def parse(self, source_family, acquisition_result, request):
        from carbonfactor_parser.parsers.input_artifact_contract import (
            create_phase1_parser_input_artifact,
        )
        from carbonfactor_parser.parsers.normalized_output_row_contract import (
            ParserNormalizedOutputRowStatus,
            create_parser_normalized_output_row,
        )
        from carbonfactor_parser.parsers.parser_run_contract import (
            ParserRunStatus,
            create_parser_run_request,
            create_parser_run_result,
        )

        artifact = create_phase1_parser_input_artifact(
            source_family=source_family,
            artifact_reference=acquisition_result.artifacts[0].local_reference,
            reporting_year=2024,
        )
        parser_request = create_parser_run_request(
            source_family=source_family,
            artifacts=(artifact,),
            run_id=f"{request.run_id}-{source_family}-parser",
            correlation_id=request.correlation_id,
        )
        row = create_parser_normalized_output_row(
            artifact=artifact,
            row_id=f"{source_family}-rc-row-001",
            status=ParserNormalizedOutputRowStatus.DECLARED,
            normalized_fields={
                "source_document_id": f"{source_family}-rc-artifact",
                "source_year": 2024,
                "source_version": "rc-fixture",
                "factor_id": f"{source_family}-rc-factor",
                "factor_value": Decimal("1.0"),
                "factor_unit": "kg CO2e",
            },
        )
        return create_parser_run_result(
            request=parser_request,
            status=ParserRunStatus.COMPLETED,
            rows=(row,),
        )


class _DryRunSourceRunRepository:
    @property
    def provider_name(self) -> str:
        return "rc_dry_run_source_runs"

    def persist_runs(self, runs):
        from carbonfactor_parser.source_acquisition.run_repository_contract import (
            create_source_acquisition_run_repository_persist_result,
        )

        return create_source_acquisition_run_repository_persist_result(
            provider_name=self.provider_name,
            runs=tuple(runs),
        )


class _DryRunSourceDocumentRepository:
    @property
    def provider_name(self) -> str:
        return "rc_dry_run_source_documents"

    def persist_source_documents(self, records):
        from carbonfactor_parser.persistence.source_document_repository import (
            create_source_document_repository_persist_result,
        )

        return create_source_document_repository_persist_result(
            provider_name=self.provider_name,
            records=tuple(records),
        )


class _DryRunParserRunRepository:
    @property
    def provider_name(self) -> str:
        return "rc_dry_run_parser_runs"

    def persist_runs(self, runs):
        from carbonfactor_parser.parsers.run_repository_contract import (
            create_parser_run_repository_persist_result,
        )

        return create_parser_run_repository_persist_result(
            provider_name=self.provider_name,
            runs=tuple(runs),
        )


class _DryRunSourceFamilyRepository:
    @property
    def provider_name(self) -> str:
        return "rc_dry_run_source_family"

    def persist_source_family_records(self, master_records, detail_records):
        from carbonfactor_parser.persistence.source_family_repository import (
            create_source_family_repository_persist_result,
        )

        return create_source_family_repository_persist_result(
            provider_name=self.provider_name,
            master_records=tuple(master_records),
            detail_records=tuple(detail_records),
        )


def _issue_summary(issues) -> str:
    return "; ".join(f"{issue.code} ({issue.field_name})" for issue in issues)


def _failure_summary(failures) -> str:
    if not failures:
        return "No failure detail was returned."
    return "; ".join(
        f"{failure.stage}:{failure.code} ({failure.field_name})"
        for failure in failures
    )


def render_report(report: RCVerificationReport, *, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(
            {
                **asdict(report),
                "passed": report.passed,
            },
            indent=2,
            sort_keys=True,
        )

    lines = [
        f"Production RC verification mode: {report.mode}",
        f"Passed: {str(report.passed).lower()}",
        "Safety: destructive_operations=false, live_source_calls="
        f"{str(report.live_source_calls_enabled).lower()}, "
        "database_connections="
        f"{str(report.database_connections_enabled).lower()}",
        "",
    ]
    for check in report.checks:
        lines.append(f"[{check.status}] {check.name}: {check.message}")
        lines.append(f"next: {check.next_step}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run safe Phase 1 production release-candidate dry-run verification.",
    )
    parser.add_argument("--root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--python-bin", default=sys.executable)
    parser.add_argument(
        "--mode",
        choices=("dry-run", "integration", "live"),
        default="dry-run",
        help="Verification mode. Dry-run is the non-destructive default.",
    )
    parser.add_argument(
        "--run-ci-gate",
        action="store_true",
        help="Execute the release validation gate commands instead of check-only status.",
    )
    parser.add_argument(
        "--output-format",
        choices=("text", "json"),
        default="text",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    import os

    report = build_production_rc_verification_report(
        root=args.root.resolve(),
        python_bin=args.python_bin,
        mode=args.mode,
        run_ci_gate=args.run_ci_gate,
        env=dict(os.environ),
    )
    print(render_report(report, output_format=args.output_format))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
