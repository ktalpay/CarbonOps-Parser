from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "release_validation_gate.py"

spec = importlib.util.spec_from_file_location("release_validation_gate", SCRIPT_PATH)
assert spec is not None
release_validation_gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = release_validation_gate
spec.loader.exec_module(release_validation_gate)


def test_default_release_gate_commands_are_local_only() -> None:
    commands = release_validation_gate.build_default_commands("python")
    rendered_commands = [" ".join(command.args) for command in commands]

    assert all(command.local_only for command in commands)
    python_test_commands = [
        command for command in commands if command.args[:3] == ("python", "-m", "pytest")
    ]
    assert len(python_test_commands) == 1
    assert python_test_commands[0].args != ("python", "-m", "pytest")
    assert all(
        target in python_test_commands[0].args
        for target in release_validation_gate.RELEASE_GATE_PYTHON_TEST_TARGETS
    )
    assert not any(
        "scripts/check_public_safety.py" in command for command in rendered_commands
    )
    assert any("carbonfactor_parser.source_acquisition.cli validate" in command for command in rendered_commands)
    assert any("carbonfactor_parser.source_acquisition.cli run --dry-run" in command for command in rendered_commands)
    assert any("carbonfactor_parser.cli local-dry-run" in command for command in rendered_commands)
    assert any("dotnet test src/dotnet/CarbonOps.Parser.sln --configuration Release" in command for command in rendered_commands)

    findings = release_validation_gate.validate_default_commands(commands)

    assert findings == []


def test_release_gate_static_checks_pass_for_repository() -> None:
    commands = release_validation_gate.build_default_commands("python")

    findings = release_validation_gate.static_gate_checks(commands)

    assert findings == []


def test_release_validation_workflow_installs_pytest_before_gate() -> None:
    workflow_text = (
        REPOSITORY_ROOT / ".github" / "workflows" / "release-validation.yml"
    ).read_text(encoding="utf-8")

    pytest_install_index = workflow_text.index("python -m pip install pytest")
    release_gate_index = workflow_text.index("python scripts/release_validation_gate.py")

    assert pytest_install_index < release_gate_index


def test_integration_validation_is_skipped_without_explicit_opt_in() -> None:
    findings = release_validation_gate.validate_integration_environment({})

    assert findings == []
    assert release_validation_gate.integration_enabled({}) is False


def test_integration_validation_requires_runner_controls() -> None:
    findings = release_validation_gate.validate_integration_environment(
        {"CARBONOPS_RELEASE_GATE_RUN_INTEGRATION": "1"}
    )

    assert [finding.name for finding in findings] == [
        "integration opt-in",
        "integration opt-in",
    ]
    assert "CARBONOPS_RUN_POSTGRESQL_INTEGRATION=1" in findings[0].message
    assert "CARBONOPS_POSTGRESQL_TEST_DSN" in findings[1].message


def test_sample_config_validation_rejects_raw_connection_strings(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "carbonops.config.example.yaml").write_text(
        "\n".join(
            (
                "database:",
                "  provider: postgres",
                '  host: "${CARBONOPS_PARSER_POSTGRES_HOST}"',
                "  port: 5432",
                '  database: "${CARBONOPS_PARSER_POSTGRES_DATABASE}"',
                '  username: "${CARBONOPS_PARSER_POSTGRES_USERNAME}"',
                "  passwordEnvVar: CARBONOPS_PARSER_POSTGRES_PASSWORD",
                "  connectionString: postgresql://user:secret@db/carbonops",
            )
        ),
        encoding="utf-8",
    )

    findings = release_validation_gate.validate_sample_config(tmp_path)

    assert any("postgres(?:ql)?://" in finding.message for finding in findings)


def test_release_gate_redacts_sensitive_output() -> None:
    output = release_validation_gate.sanitize_output(
        "password=super-secret token:abc postgresql://user:secret@localhost/db"
    )

    assert "super-secret" not in output
    assert "token:abc" not in output
    assert "user:secret@" not in output
    assert output.count("[REDACTED]") == 3
