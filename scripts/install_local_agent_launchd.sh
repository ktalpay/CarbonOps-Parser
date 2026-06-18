#!/usr/bin/env bash
set -euo pipefail

DEFAULT_LABEL="local.carbonops.agent.supervisor"
DEFAULT_INTERVAL_SECONDS="600"
DEFAULT_SAFE_LOG_DIR="${HOME}/FutureOps/Agents/CarbonOps-Parser/.logs"
DEFAULT_LAUNCHD_PATH="/Users/oxygen/.npm-global/bin:/usr/local/bin:/usr/local/opt/python@3.12/libexec/bin:/usr/bin:/bin:/usr/sbin:/sbin"
PLIST_PYTHON="${PLIST_PYTHON:-/usr/bin/python3}"

usage() {
  cat <<'EOF'
Usage: scripts/install_local_agent_launchd.sh [options]

Install a user-level launchd job for scripts/local_agent_supervisor.py.

Options:
  --config <path>             Local agent supervisor JSON config path.
  --repo-root <path>          Repository root containing scripts/local_agent_supervisor.py.
  --python-bin <path>         Python executable used by launchd.
  --interval-seconds <secs>   launchd StartInterval. Default: 600.
  --label <launchd-label>     launchd label. Default: local.carbonops.agent.supervisor.
  --dry-run                   Print the planned plist and launchctl command without writing or loading.
  -h, --help                  Show this help.
EOF
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

absolute_path() {
  local raw="$1"
  if [[ "$raw" == /* ]]; then
    printf '%s\n' "$raw"
  elif [[ "$raw" == "~" ]]; then
    printf '%s\n' "$HOME"
  elif [[ "$raw" == "~/"* ]]; then
    printf '%s/%s\n' "$HOME" "${raw#~/}"
  else
    printf '%s/%s\n' "$(pwd)" "$raw"
  fi
}

repo_root="$(pwd)"
config_path=""
python_bin="python3"
interval_seconds="$DEFAULT_INTERVAL_SECONDS"
label="$DEFAULT_LABEL"
dry_run=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      [[ $# -ge 2 ]] || die "--config requires a path"
      config_path="$2"
      shift 2
      ;;
    --repo-root)
      [[ $# -ge 2 ]] || die "--repo-root requires a path"
      repo_root="$2"
      shift 2
      ;;
    --python-bin)
      [[ $# -ge 2 ]] || die "--python-bin requires a path"
      python_bin="$2"
      shift 2
      ;;
    --interval-seconds)
      [[ $# -ge 2 ]] || die "--interval-seconds requires a value"
      interval_seconds="$2"
      shift 2
      ;;
    --label)
      [[ $# -ge 2 ]] || die "--label requires a launchd label"
      label="$2"
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[[ "$interval_seconds" =~ ^[1-9][0-9]*$ ]] || die "--interval-seconds must be a positive integer"
[[ -n "$label" ]] || die "--label must be non-empty"
[[ "$label" != */* ]] || die "--label must not contain /"

repo_root="$(absolute_path "$repo_root")"
if [[ -z "$config_path" ]]; then
  config_path="${repo_root}/.agent/local-agent.json"
else
  config_path="$(absolute_path "$config_path")"
fi
if [[ "$python_bin" != */* ]]; then
  resolved_python_bin="$(command -v "$python_bin" || true)"
  [[ -n "$resolved_python_bin" ]] || die "python executable not found on PATH: $python_bin"
  python_bin="$resolved_python_bin"
else
  python_bin="$(absolute_path "$python_bin")"
fi

supervisor_path="${repo_root}/scripts/local_agent_supervisor.py"
plist_path="${HOME}/Library/LaunchAgents/${label}.plist"

if [[ "$dry_run" -eq 0 ]]; then
  [[ -f "$supervisor_path" ]] || die "supervisor script not found: $supervisor_path"
  [[ -f "$config_path" ]] || die "config file not found: $config_path"
  [[ -x "$python_bin" ]] || die "python executable not found or not executable: $python_bin"
fi

log_dir="$DEFAULT_SAFE_LOG_DIR"
if ! command -v "$PLIST_PYTHON" >/dev/null 2>&1; then
  PLIST_PYTHON="$(command -v python3 || true)"
fi
[[ -n "$PLIST_PYTHON" ]] || die "python3 is required to render the launchd plist"

if [[ -f "$config_path" ]]; then
  config_log_dir="$(
    "$PLIST_PYTHON" - "$config_path" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

config_path = Path(sys.argv[1]).expanduser()
try:
    raw = json.loads(config_path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(0)

if not isinstance(raw, dict):
    raise SystemExit(0)

value = raw.get("log_directory") or raw.get("agents_log_directory")
if value is None and isinstance(raw.get("agents_root"), str) and raw["agents_root"].strip():
    value = str(Path(raw["agents_root"]).expanduser() / ".logs")
if not isinstance(value, str) or not value.strip():
    raise SystemExit(0)

path = Path(value).expanduser()
if not path.is_absolute():
    path = config_path.parent / path
print(path)
PY
  )"
  if [[ -n "$config_log_dir" ]]; then
    log_dir="$config_log_dir"
  fi
fi

stdout_path="${log_dir}/local-agent-supervisor.launchd.out.log"
stderr_path="${log_dir}/local-agent-supervisor.launchd.err.log"

render_plist() {
  "$PLIST_PYTHON" - \
    "$label" \
    "$python_bin" \
    "$supervisor_path" \
    "$config_path" \
    "$interval_seconds" \
    "$stdout_path" \
    "$stderr_path" \
    "$DEFAULT_LAUNCHD_PATH" <<'PY'
from __future__ import annotations

import plistlib
import sys

label, python_bin, supervisor_path, config_path, interval, stdout_path, stderr_path, launchd_path = sys.argv[1:]
plist = {
    "Label": label,
    "EnvironmentVariables": {
        "PATH": launchd_path,
    },
    "ProgramArguments": [
        python_bin,
        supervisor_path,
        "--config",
        config_path,
        "--once",
    ],
    "RunAtLoad": True,
    "StartInterval": int(interval),
    "StandardOutPath": stdout_path,
    "StandardErrorPath": stderr_path,
    "WorkingDirectory": supervisor_path.rsplit("/scripts/local_agent_supervisor.py", 1)[0],
}
sys.stdout.buffer.write(plistlib.dumps(plist, sort_keys=True))
PY
}

if [[ "$dry_run" -eq 1 ]]; then
  printf 'Would write plist: %s\n' "$plist_path"
  printf 'Would create log directory: %s\n' "$log_dir"
  render_plist
  printf '\nWould run: launchctl bootstrap gui/%s %s\n' "$(id -u)" "$plist_path"
  exit 0
fi

mkdir -p "${HOME}/Library/LaunchAgents" "$log_dir"
render_plist > "$plist_path"
chmod 0644 "$plist_path"

launchctl bootstrap "gui/$(id -u)" "$plist_path"

printf 'Installed launchd job: %s\n' "$label"
printf 'Plist: %s\n' "$plist_path"
printf 'Logs: %s\n' "$log_dir"
