# Linux Service Setup

This document is legacy planning material for a possible future Linux service.
It is not the supported production scheduling mode for PROD-001. Supported
production scheduling is cron or manual one-cycle execution of the packaged
Python command documented in the production operator runbook.

This document is a non-installing template for operator planning. It does not
install a service, enable a service, start a service, create a user, read
configuration, load credentials, connect to PostgreSQL, run SQL, or download
sources. It must not be used to imply daemon, system service, or installer
support for production operation. It also does not imply that the .NET runtime
has a production service path. Implementation-specific service files should be
added only after a future task explicitly scopes and reviews service support for
the selected implementation.

## Service Responsibilities

A future Linux service setup would need to define:

- Working directory
- Environment variables
- Database configuration source
- Raw archive path
- Service user
- Restart policy
- Logging destination
- Basic service management commands

## Conceptual systemd Unit

The example below is conceptual and not a supported production unit. The exact
command would depend on a future reviewed service implementation. Until that
implementation exists, keep `ExecStart` as an operator-owned placeholder and use
cron or manual one-cycle execution for supported production scheduling.

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

Typical service management commands after a future reviewed unit is installed:

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

For the supported production install, configure, validate, run, stop, diagnose,
and rollback flow, see
[Production Packaging And Operator Runbook](production-packaging-operator-runbook.md).
For project-level Python/.NET parity requirements, see
[Production Parity Contract](production-parity-contract.md).
