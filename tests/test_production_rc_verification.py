from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "production_rc_verification.py"

spec = importlib.util.spec_from_file_location("production_rc_verification", SCRIPT_PATH)
assert spec is not None
production_rc_verification = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = production_rc_verification
spec.loader.exec_module(production_rc_verification)


def test_production_rc_default_path_passes_without_live_or_database_modes() -> None:
    report = production_rc_verification.build_production_rc_verification_report(
        root=REPOSITORY_ROOT,
        python_bin=sys.executable,
        env={},
    )

    assert report.passed
    assert report.mode == "dry-run"
    assert report.destructive_operations_enabled is False
    assert report.live_source_calls_enabled is False
    assert report.database_connections_enabled is False
    assert [check.name for check in report.checks] == [
        "production config validation",
        "schema bootstrap readiness",
        "service entrypoint availability",
        "orchestrator dry-run behavior",
        "diagnostics redaction",
        "CI release gate status",
    ]


def test_production_rc_blocks_integration_mode_without_explicit_opt_in() -> None:
    report = production_rc_verification.build_production_rc_verification_report(
        root=REPOSITORY_ROOT,
        python_bin=sys.executable,
        mode="integration",
        env={},
    )

    assert not report.passed
    assert report.checks[0].name == "integration mode guardrail"
    assert report.checks[0].status == "failed"
    assert "explicit opt-in" in report.checks[0].message


def test_production_rc_blocks_live_mode_without_explicit_opt_in() -> None:
    report = production_rc_verification.build_production_rc_verification_report(
        root=REPOSITORY_ROOT,
        python_bin=sys.executable,
        mode="live",
        env={},
    )

    assert not report.passed
    assert report.checks[0].name == "live mode guardrail"
    assert report.checks[0].status == "failed"
    assert "default non-destructive dry-run path" in report.checks[0].message


def test_production_rc_report_does_not_render_secret_values() -> None:
    report = production_rc_verification.build_production_rc_verification_report(
        root=REPOSITORY_ROOT,
        python_bin=sys.executable,
        env={},
    )
    rendered = production_rc_verification.render_report(
        report,
        output_format="json",
    )

    assert "external-secret-present" not in rendered
    assert "secret-db" not in rendered
    assert "secret_database" not in rendered
    assert "secret_user" not in rendered
    assert "raw-secret" not in rendered
    assert "raw-token" not in rendered


def test_production_rc_main_returns_nonzero_for_unapproved_live_mode(capsys) -> None:
    exit_code = production_rc_verification.main(["--mode", "live"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "[failed] live mode guardrail" in captured.out
