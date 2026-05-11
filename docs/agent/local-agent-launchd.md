# Local Agent launchd Job

OPS-027 adds user-level macOS `launchd` installation for the local agent
supervisor. The job runs `scripts/local_agent_supervisor.py --config <path>
--once` on a fixed interval and does not merge PRs, approve PRs, close issues,
delete branches, or delete worktrees.

## Install

Prepare a local config first, usually from `.agent/local-agent.example.json`.
Keep credentials in your normal local tools (`gh`, Git, Codex), not in this
file.

```bash
cp .agent/local-agent.example.json .agent/local-agent.json
$EDITOR .agent/local-agent.json
```

Preview the generated plist and load command:

```bash
scripts/install_local_agent_launchd.sh \
  --config .agent/local-agent.json \
  --repo-root "$PWD" \
  --python-bin "$(command -v python3)" \
  --dry-run
```

Install and load the user-level job:

```bash
scripts/install_local_agent_launchd.sh \
  --config .agent/local-agent.json \
  --repo-root "$PWD" \
  --python-bin "$(command -v python3)"
```

The default label is `local.carbonops.agent.supervisor`. The default interval is
600 seconds. Override them with `--label` and `--interval-seconds`.

The plist is written to:

```text
~/Library/LaunchAgents/local.carbonops.agent.supervisor.plist
```

The installer does not require `sudo`.

## Verify

Check whether launchd knows about the job:

```bash
launchctl print "gui/$(id -u)/local.carbonops.agent.supervisor"
```

Inspect the plist:

```bash
plutil -p ~/Library/LaunchAgents/local.carbonops.agent.supervisor.plist
```

The job uses `RunAtLoad` and `StartInterval`, so it runs once after bootstrap and
then periodically.

## Logs

Supervisor runner logs are controlled by the supervisor config. launchd stdout
and stderr are written under the config `log_directory` when present, otherwise
under `<agents_root>/.logs` when `agents_root` is present. If neither can be
read, the installer uses this safe default:

```text
~/FutureOps/Agents/CarbonOps-Parser/.logs
```

Expected launchd log files:

```text
local-agent-supervisor.launchd.out.log
local-agent-supervisor.launchd.err.log
```

## Unload

Preview uninstall actions:

```bash
scripts/uninstall_local_agent_launchd.sh --dry-run
```

Unload the job and remove only its plist:

```bash
scripts/uninstall_local_agent_launchd.sh
```

The uninstall script does not remove logs, config files, repository files,
branches, or worktrees.

## Common Failures

- `Bootstrap failed`: the job may already be loaded. Run
  `scripts/uninstall_local_agent_launchd.sh`, then install again.
- `python executable not found or not executable`: pass an absolute Python path
  with `--python-bin "$(command -v python3)"`.
- `Config file not found`: pass the intended local config with `--config`.
- `launchd job starts but exits`: read the stderr log first, then the supervisor
  runner log directory from the local config.
- `gh` or Codex auth failures: fix local CLI authentication outside the plist;
  do not place production credentials in the config or plist.
