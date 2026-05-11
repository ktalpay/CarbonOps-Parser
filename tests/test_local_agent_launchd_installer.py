from __future__ import annotations

import json
import os
import plistlib
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "scripts" / "install_local_agent_launchd.sh"
UNINSTALLER = REPO_ROOT / "scripts" / "uninstall_local_agent_launchd.sh"


def run_script(script: Path, args: list[str], *, home: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    return subprocess.run(
        [str(script), *args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def plist_from_dry_run(stdout: str) -> dict[str, object]:
    start = stdout.index("<?xml")
    end = stdout.index("</plist>") + len("</plist>")
    return plistlib.loads(stdout[start:end].encode("utf-8"))


def write_config(tmp_path: Path, **overrides: object) -> Path:
    log_dir = tmp_path / "agent-logs"
    values: dict[str, object] = {
        "repo": "ktalpay/CarbonOps-Parser",
        "source_root": str(REPO_ROOT),
        "agents_root": str(tmp_path / "agents"),
        "log_directory": str(log_dir),
    }
    values.update(overrides)
    config = tmp_path / "local-agent.json"
    config.write_text(json.dumps(values), encoding="utf-8")
    return config


def test_install_dry_run_renders_default_launchd_plist(tmp_path: Path) -> None:
    config = write_config(tmp_path)

    result = run_script(
        INSTALLER,
        [
            "--config",
            str(config),
            "--repo-root",
            str(REPO_ROOT),
            "--python-bin",
            sys.executable,
            "--dry-run",
        ],
        home=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    plist = plist_from_dry_run(result.stdout)
    assert plist["Label"] == "local.carbonops.agent.supervisor"
    assert plist["StartInterval"] == 600
    assert plist["RunAtLoad"] is True
    assert plist["ProgramArguments"] == [
        sys.executable,
        str(REPO_ROOT / "scripts" / "local_agent_supervisor.py"),
        "--config",
        str(config),
        "--once",
    ]
    assert plist["StandardOutPath"] == str(tmp_path / "agent-logs" / "local-agent-supervisor.launchd.out.log")
    assert plist["StandardErrorPath"] == str(tmp_path / "agent-logs" / "local-agent-supervisor.launchd.err.log")
    assert plist["EnvironmentVariables"] == {
        "PATH": "/Users/oxygen/.npm-global/bin:/usr/local/bin:/usr/local/opt/python@3.12/libexec/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    }
    assert "Would run: launchctl bootstrap" in result.stdout
    assert not (tmp_path / "Library" / "LaunchAgents").exists()


def test_install_dry_run_renders_custom_label_python_and_interval(tmp_path: Path) -> None:
    config = write_config(tmp_path)

    result = run_script(
        INSTALLER,
        [
            "--config",
            str(config),
            "--repo-root",
            str(REPO_ROOT),
            "--python-bin",
            "/opt/custom/python",
            "--interval-seconds",
            "42",
            "--label",
            "local.test.agent",
            "--dry-run",
        ],
        home=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    plist = plist_from_dry_run(result.stdout)
    assert plist["Label"] == "local.test.agent"
    assert plist["StartInterval"] == 42
    assert plist["ProgramArguments"][0] == "/opt/custom/python"
    assert f"{tmp_path}/Library/LaunchAgents/local.test.agent.plist" in result.stdout


def test_install_dry_run_uses_safe_log_default_when_config_is_unreadable(tmp_path: Path) -> None:
    missing_config = tmp_path / "missing.json"

    result = run_script(
        INSTALLER,
        [
            "--config",
            str(missing_config),
            "--repo-root",
            str(REPO_ROOT),
            "--python-bin",
            sys.executable,
            "--dry-run",
        ],
        home=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    plist = plist_from_dry_run(result.stdout)
    assert plist["StandardOutPath"] == str(
        tmp_path / "FutureOps" / "Agents" / "CarbonOps-Parser" / ".logs" / "local-agent-supervisor.launchd.out.log"
    )


def test_uninstall_dry_run_plans_only_launchctl_and_plist_removal(tmp_path: Path) -> None:
    result = run_script(
        UNINSTALLER,
        ["--label", "local.test.agent", "--dry-run"],
        home=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    assert "Would run: launchctl bootout gui/" in result.stdout
    assert f"Would remove plist: {tmp_path}/Library/LaunchAgents/local.test.agent.plist" in result.stdout
    assert "Would not remove logs, config files, repository files, branches, or worktrees." in result.stdout
