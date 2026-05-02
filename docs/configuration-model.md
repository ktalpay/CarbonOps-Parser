# Configuration Model

CarbonOps-Parser uses a conceptual configuration model shared by the Python and .NET implementations. Each implementation may use a language-appropriate physical format:

- Python may use YAML.
- .NET may use `appsettings.json`.

The core settings should remain conceptually aligned.

## Database Provider

The configuration model recognizes these provider names:

- `postgres`
- `mysql`
- `mssql`

Phase 1 implements only `postgres`. If `mysql` or `mssql` is configured in Phase 1, the service should fail fast with a clear message:

```text
Unsupported database provider. Phase 1 supports postgres only.
```

## Conceptual Example

```yaml
database:
  provider: postgres
  connectionString: "Host=localhost;Port=5432;Database=carbonops_parser;Username=carbonops;Password=change-me"

storage:
  rawArchivePath: "./data/raw"

sources:
  ghgProtocol:
    enabled: true
    schedule:
      period: month
      interval: 1
      dayOfMonth: 1
      time: "04:00"
      timezone: "UTC"
  defraDesnz:
    enabled: true
    schedule:
      period: month
      interval: 1
      dayOfMonth: 1
      time: "04:30"
      timezone: "UTC"
  ipccEfdb:
    enabled: true
    schedule:
      period: week
      interval: 1
      dayOfWeek: monday
      time: "05:00"
      timezone: "UTC"
```

## Schedule Model

Each source has independent schedule settings. The schedule model should support:

- `day`
- `week`
- `month`
- `time`
- `timezone`

Common schedule fields include:

- `period`: `day`, `week`, or `month`
- `interval`: numeric interval for the selected period
- `dayOfWeek`: used for weekly schedules
- `dayOfMonth`: used for monthly schedules
- `time`: local wall-clock time for the schedule
- `timezone`: IANA time zone or `UTC`

## Source Configuration

Each Phase 1 source family should have an independent source configuration section:

- GHG Protocol
- DEFRA/DESNZ
- IPCC EFDB

Each source should be independently enabled, scheduled, checked for version/hash changes, parsed, validated, and persisted.
