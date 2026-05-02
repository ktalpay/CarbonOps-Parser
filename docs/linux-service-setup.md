# Linux Service Setup

CarbonOps-Parser is intended to run as a Linux background service in either the Python or .NET implementation path.

This document is conceptual for the documentation baseline. Implementation-specific service files should be added after the runtime entry points exist.

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

The exact command depends on the selected implementation. A future Python service might run a Python module, while a future .NET service might run a Worker Service binary.

```ini
[Unit]
Description=CarbonOps-Parser background ingestion service
After=network.target

[Service]
WorkingDirectory=/opt/carbonops-parser
Environment=CARBONOPS_PARSER_ENV=default
ExecStart=/opt/carbonops-parser/run-service
Restart=on-failure
User=carbonops
Group=carbonops

[Install]
WantedBy=multi-user.target
```

## Management Commands

Typical service management commands:

```bash
sudo systemctl daemon-reload
sudo systemctl enable carbonops-parser
sudo systemctl start carbonops-parser
sudo systemctl status carbonops-parser
sudo journalctl -u carbonops-parser -f
```

## Notes

Linux service documentation should explain how configuration is provided, where raw files are archived, and how logs are reviewed. Deployment hardening is outside the Phase 1 documentation baseline.
