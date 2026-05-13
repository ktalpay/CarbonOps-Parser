# Linux Service Setup

CarbonOps-Parser is intended to run as a Linux background service in either the
Python or .NET implementation path.

This document is a non-installing template for operator planning. It does not
install a service, enable a service, start a service, create a user, read
configuration, load credentials, connect to PostgreSQL, run SQL, or download
sources. Implementation-specific service files should be added only after the
runtime entry point is explicitly published for the selected implementation.

## Service Responsibilities

A Linux service setup should define:

- Working directory
- Environment variables
- Database configuration source
- Raw archive path
- Service user
- Restart policy
- Logging destination
- Basic service management commands

## Conceptual systemd Unit

The exact command depends on the selected implementation. A future Python
service may run an approved Python host module. A future .NET service may run an
approved Worker Service binary. Until that executable exists, keep `ExecStart`
as an operator-owned placeholder.

```ini
[Unit]
Description=CarbonOps-Parser background ingestion service
After=network.target

[Service]
WorkingDirectory=/opt/carbonops-parser
EnvironmentFile=/etc/carbonops-parser/runtime.env
ExecStart=/opt/carbonops-parser/<approved-runtime-entrypoint>
Restart=on-failure
User=carbonops
Group=carbonops
KillSignal=SIGTERM
TimeoutStopSec=300

[Install]
WantedBy=multi-user.target
```

The environment file path above is illustrative. It must be created and managed
outside the repository and must not be committed with environment-specific
values.

## Management Commands

Typical service management commands after a reviewed unit is installed:

```bash
sudo systemctl daemon-reload
sudo systemctl start carbonops-parser
sudo systemctl status carbonops-parser
sudo journalctl -u carbonops-parser -f
sudo systemctl stop carbonops-parser
```

## Notes

Linux service documentation must explain how configuration is provided, where
raw files are archived, how logs are reviewed, and how graceful stop is handled.
Do not add automatic enablement, destructive cleanup, branch or worktree
cleanup, schema deletion, or ad hoc database mutation to service management
steps.

For the full install, configure, validate, run, stop, diagnose, and rollback
flow, see [Production Packaging And Operator Runbook](production-packaging-operator-runbook.md).
