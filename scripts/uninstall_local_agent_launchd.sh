#!/usr/bin/env bash
set -euo pipefail

DEFAULT_LABEL="local.carbonops.agent.supervisor"

usage() {
  cat <<'EOF'
Usage: scripts/uninstall_local_agent_launchd.sh [options]

Unload and remove the user-level launchd plist for the local agent supervisor.

Options:
  --label <launchd-label>   launchd label. Default: local.carbonops.agent.supervisor.
  --dry-run                 Print planned launchctl and rm commands without running them.
  -h, --help                Show this help.
EOF
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

label="$DEFAULT_LABEL"
dry_run=0

while [[ $# -gt 0 ]]; do
  case "$1" in
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

[[ -n "$label" ]] || die "--label must be non-empty"
[[ "$label" != */* ]] || die "--label must not contain /"

plist_path="${HOME}/Library/LaunchAgents/${label}.plist"
launchctl_target="gui/$(id -u)/${label}"

if [[ "$dry_run" -eq 1 ]]; then
  printf 'Would run: launchctl bootout %s\n' "$launchctl_target"
  printf 'Would remove plist: %s\n' "$plist_path"
  printf 'Would not remove logs, config files, repository files, branches, or worktrees.\n'
  exit 0
fi

if launchctl print "$launchctl_target" >/dev/null 2>&1; then
  launchctl bootout "$launchctl_target"
else
  printf 'launchd job is not loaded: %s\n' "$label"
fi

if [[ -f "$plist_path" ]]; then
  rm -f "$plist_path"
  printf 'Removed plist: %s\n' "$plist_path"
else
  printf 'Plist not found: %s\n' "$plist_path"
fi

printf 'Logs, config files, repository files, branches, and worktrees were left untouched.\n'
