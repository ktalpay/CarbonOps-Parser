#!/usr/bin/env python3
"""Phase 1 CI/release validation gate.

The default gate is intentionally local-only: it runs fixture, metadata, package,
and contract checks without live source endpoints or production databases.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_OPT_IN_ENV = "CARBONOPS_RELEASE_GATE_RUN_INTEGRATION"
POSTGRESQL_INTEGRATION_ENV = "CARBONOPS_RUN_POSTGRESQL_INTEGRATION"
POSTGRESQL_TEST_DSN_ENV = "CARBONOPS_POSTGRESQL_TEST_DSN"

SECRET_PATTERNS = (
    re.compile(r"(?i)(password\s*[=:]\s*)([^\s'\";]+)"),
    re.compile(r"(?i)(token\s*[=:]\s*)([^\s'\";]+)"),
    re.compile(r"(?i)(secret\s*[=:]\s*)([^\s'\";]+)"),
    re.compile(r"(?i)(postgres(?:ql)?://[^:\s]+:)([^@\s]+)(@)"),
)

FORBIDDEN_DEFAULT_COMMAND_FRAGMENTS = (
    "--client http",
    "--persist-content",
    "curl ",
    "wget ",
    "psycopg.connect",
    "DROP TABLE",
    "DELETE FROM",
    "TRUNCATE",
    "CREATE TABLE",
)

REQUIRED_PARITY_FIXTURES = (
    "defra_desnz_normalized_output_expectations.json",
    "ghg_protocol_normalized_output_expectations.json",
    "ipcc_efdb_normalized_output_expectations.json",
    "ipcc_source_download_execution_expectations.json",
    "parsed_factor_persistence_writer_expectations.json",
    "phase1_operational_diagnostics_expectations.json",
)

REQUIRED_RUNBOOK_MARKERS = (
    "python -m pytest",
    "git diff --check",
    "carbonops-source-acquisition validate",
    "carbonops-source-acquisition run --dry-run",
    "carbonops-parser local-dry-run",
    "dotnet test src/dotnet/CarbonOps.Parser.sln --configuration Release",
    "The commands above must not require production configuration or credentials.",
    "Raw PostgreSQL connection strings are rejected",
)

REQUIRED_CONFIG_MARKERS = (
    "provider: postgres",
    'host: "${CARBONOPS_PARSER_POSTGRES_HOST}"',
    'database: "${CARBONOPS_PARSER_POSTGRES_DATABASE}"',
    'username: "${CARBONOPS_PARSER_POSTGRES_USERNAME}"',
    "passwordEnvVar: CARBONOPS_PARSER_POSTGRES_PASSWORD",
)


@dataclass(frozen=True)
class GateCommand:
    name: str
    args: tuple[str, ...]
    local_only: bool = True


@dataclass(frozen=True)
class GateCheck:
    name: str
    message: str


class GateFailure(RuntimeError):
    """Raised when release validation cannot proceed safely."""


def sanitize_output(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]{match.group(3) if len(match.groups()) >= 3 else ''}", redacted)
    return redacted


def build_default_commands(python_bin: str) -> tuple[GateCommand, ...]:
    return (
        GateCommand("python tests", (python_bin, "-m", "pytest")),
        GateCommand(
            "source acquisition metadata validation",
            (
                python_bin,
                "-m",
                "carbonfactor_parser.source_acquisition.cli",
                "validate",
                "--output-format",
                "json",
            ),
        ),
        GateCommand(
            "source acquisition dry-run",
            (
                python_bin,
                "-m",
                "carbonfactor_parser.source_acquisition.cli",
                "run",
                "--dry-run",
                "--base-directory",
                "./data/source-acquisition",
                "--output-format",
                "json",
            ),
        ),
        GateCommand(
            "parser local fixture dry-run",
            (
                python_bin,
                "-m",
                "carbonfactor_parser.cli",
                "local-dry-run",
                "--local-path",
                "examples/fixtures/defra_desnz_minimal.csv",
                "--source-family",
                "defra_desnz",
                "--source-id",
                "defra-desnz-minimal-fixture",
                "--content-type",
                "text/csv",
                "--format-hint",
                "csv",
                "--output-format",
                "json",
                "--include-postgresql-preview",
            ),
        ),
        GateCommand(
            ".NET contract tests",
            (
                "dotnet",
                "test",
                "src/dotnet/CarbonOps.Parser.sln",
                "--configuration",
                "Release",
                "--no-restore",
            ),
        ),
        GateCommand("whitespace diff check", ("git", "diff", "--check")),
    )


def build_integration_commands(python_bin: str) -> tuple[GateCommand, ...]:
    return (
        GateCommand(
            "opt-in PostgreSQL integration smoke",
            (
                python_bin,
                "-m",
                "pytest",
                "-m",
                "postgresql_integration",
                "tests/test_postgresql_connection_smoke_boundary.py",
            ),
            local_only=False,
        ),
    )


def validate_default_commands(commands: Sequence[GateCommand]) -> list[GateCheck]:
    findings: list[GateCheck] = []
    for command in commands:
        rendered = " ".join(command.args)
        for fragment in FORBIDDEN_DEFAULT_COMMAND_FRAGMENTS:
            if fragment.lower() in rendered.lower():
                findings.append(
                    GateCheck(
                        name=command.name,
                        message=f"default command contains forbidden fragment: {fragment}",
                    )
                )
    return findings


def validate_sample_config(root: Path = REPOSITORY_ROOT) -> list[GateCheck]:
    path = root / "config" / "carbonops.config.example.yaml"
    text = path.read_text(encoding="utf-8")
    findings = [
        GateCheck("sample config", f"missing required marker: {marker}")
        for marker in REQUIRED_CONFIG_MARKERS
        if marker not in text
    ]
    forbidden_patterns = (
        r"postgres(?:ql)?://",
        r"(?i)\bpassword\s*[:=]\s*(?!CARBONOPS_PARSER_POSTGRES_PASSWORD\b|\$\{)",
        r"(?i)\btoken\s*[:=]",
        r"(?i)\bsecret\s*[:=]",
    )
    for pattern in forbidden_patterns:
        if re.search(pattern, text):
            findings.append(
                GateCheck("sample config", f"forbidden secret/config pattern: {pattern}")
            )
    return findings


def validate_parity_fixtures(root: Path = REPOSITORY_ROOT) -> list[GateCheck]:
    fixture_dir = root / "tests" / "fixtures" / "parity"
    findings: list[GateCheck] = []
    for fixture_name in REQUIRED_PARITY_FIXTURES:
        path = fixture_dir / fixture_name
        if not path.is_file():
            findings.append(
                GateCheck("parity fixtures", f"missing parity fixture: {path}")
            )
    return findings


def validate_packaging_runbook(root: Path = REPOSITORY_ROOT) -> list[GateCheck]:
    path = root / "docs" / "production-packaging-operator-runbook.md"
    text = path.read_text(encoding="utf-8")
    return [
        GateCheck("packaging runbook", f"missing runbook marker: {marker}")
        for marker in REQUIRED_RUNBOOK_MARKERS
        if marker not in text
    ]


def validate_workflow(root: Path = REPOSITORY_ROOT) -> list[GateCheck]:
    workflow_path = root / ".github" / "workflows" / "release-validation.yml"
    if not workflow_path.is_file():
        return [GateCheck("CI workflow", "missing .github/workflows/release-validation.yml")]

    text = workflow_path.read_text(encoding="utf-8")
    required_markers = (
        "python -m pip install --upgrade pip",
        'python -m pip install -e ".[postgresql]"',
        "python -m pip install pytest",
        "scripts/release_validation_gate.py",
        "dotnet test src/dotnet/CarbonOps.Parser.sln --configuration Release",
        "CARBONOPS_RELEASE_GATE_RUN_INTEGRATION",
    )
    return [
        GateCheck("CI workflow", f"missing workflow marker: {marker}")
        for marker in required_markers
        if marker not in text
    ]


def static_gate_checks(commands: Sequence[GateCommand]) -> list[GateCheck]:
    findings: list[GateCheck] = []
    findings.extend(validate_default_commands(commands))
    findings.extend(validate_sample_config())
    findings.extend(validate_parity_fixtures())
    findings.extend(validate_packaging_runbook())
    findings.extend(validate_workflow())
    return findings


def integration_enabled(env: Mapping[str, str]) -> bool:
    return env.get(INTEGRATION_OPT_IN_ENV) == "1"


def validate_integration_environment(env: Mapping[str, str]) -> list[GateCheck]:
    if not integration_enabled(env):
        return []

    findings: list[GateCheck] = []
    if env.get(POSTGRESQL_INTEGRATION_ENV) != "1":
        findings.append(
            GateCheck(
                "integration opt-in",
                f"{POSTGRESQL_INTEGRATION_ENV}=1 is required for integration mode",
            )
        )
    if not env.get(POSTGRESQL_TEST_DSN_ENV):
        findings.append(
            GateCheck(
                "integration opt-in",
                f"{POSTGRESQL_TEST_DSN_ENV} must be supplied externally for integration mode",
            )
        )
    return findings


def run_command(command: GateCommand, root: Path) -> int:
    print(f"[release-gate] running {command.name}: {' '.join(command.args)}")
    completed = subprocess.run(
        command.args,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = sanitize_output(completed.stdout)
    if output.strip():
        print(output.rstrip())
    if completed.returncode != 0:
        print(
            f"[release-gate] FAILED {command.name} with exit code {completed.returncode}",
            file=sys.stderr,
        )
    return completed.returncode


def run_gate(
    *,
    root: Path,
    python_bin: str,
    run_commands: bool,
    env: Mapping[str, str],
) -> int:
    commands = build_default_commands(python_bin)
    findings = static_gate_checks(commands)
    findings.extend(validate_integration_environment(env))

    include_integration = integration_enabled(env)
    if include_integration:
        commands = commands + build_integration_commands(python_bin)

    if findings:
        print("[release-gate] static validation failed:", file=sys.stderr)
        for finding in findings:
            print(
                f"- {finding.name}: {sanitize_output(finding.message)}",
                file=sys.stderr,
            )
        return 1

    print("[release-gate] static safety checks passed.")
    if not include_integration:
        print("[release-gate] integration checks skipped: explicit opt-in not set.")

    if not run_commands:
        print("[release-gate] command execution skipped by --check-only.")
        return 0

    for command in commands:
        return_code = run_command(command, root)
        if return_code != 0:
            return return_code

    print("[release-gate] release validation gate passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Phase 1 CI/release validation safety gate.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPOSITORY_ROOT,
        help="Repository root. Defaults to this script's repository.",
    )
    parser.add_argument(
        "--python-bin",
        default=sys.executable,
        help="Python executable used for Python checks.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Run static safety checks without executing validation commands.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        raise GateFailure(f"repository root does not exist: {root}")
    return run_gate(
        root=root,
        python_bin=args.python_bin,
        run_commands=not args.check_only,
        env=os.environ,
    )


if __name__ == "__main__":
    raise SystemExit(main())
