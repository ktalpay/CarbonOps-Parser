# Configuration Model

CarbonOps-Parser uses a conceptual configuration model shared by the Python and .NET implementations. A shared example is available at [../config/carbonops.config.example.yaml](../config/carbonops.config.example.yaml).

Each implementation may use a language-appropriate physical format:

- Python may use YAML.
- .NET may use `appsettings.json`.

The core settings should remain conceptually aligned.

## Configuration Sections

The shared conceptual model includes:

- `app`: application identity, environment, and log level.
- `database`: provider, connection string, and schema name.
- `storage`: raw file archive path.
- `execution`: retry settings and single-instance lock settings.
- `sources`: source-specific check, download, schedule, and import settings.

## Database Provider

The configuration model recognizes these provider names:

- `postgres`
- `mysql`
- `mssql`

Phase 1 implements only `postgres`. If `mysql` or `mssql` is configured in Phase 1, the service should fail fast with a clear message:

```text
Unsupported database provider. Phase 1 supports postgres only.
```

## Shared Example

The repository-level example is:

- [config/carbonops.config.example.yaml](../config/carbonops.config.example.yaml)

The URLs in the example are safe placeholders for source discovery. Exact check and download URLs should be confirmed during source discovery before implementation work relies on them.

## Inline Example

```yaml
app:
  name: CarbonOps-Parser
  environment: local
  logLevel: info

database:
  provider: postgres
  connectionString: "Host=localhost;Port=5432;Database=carbonops_parser;Username=carbonops;Password=change-me"
  schema: carbonops

storage:
  rawArchivePath: "./data/raw"

execution:
  maxRetryCount: 3
  retryDelaySeconds: 60
  singleInstanceLock: true
  lockTimeoutMinutes: 30

sources:
  ghgProtocol:
    enabled: true
    sourceCode: GHG_PROTOCOL
    checkUrl: "https://example.org/sources/ghg-protocol/check"
    downloadUrl: "https://example.org/sources/ghg-protocol/download"
    schedule:
      period: month
      interval: 1
      dayOfMonth: 1
      time: "04:00"
      timezone: "UTC"
    import:
      mode: check_latest_then_import
      duplicatePolicy: skip_if_same_hash
  defraDesnz:
    enabled: true
    sourceCode: DEFRA_DESNZ
    checkUrl: "https://example.org/sources/defra-desnz/check"
    downloadUrl: "https://example.org/sources/defra-desnz/download"
    schedule:
      period: year
      interval: 1
      dayOfMonth: 1
      time: "04:30"
      timezone: "UTC"
    import:
      mode: check_latest_then_import
      duplicatePolicy: skip_if_same_hash
  ipccEfdb:
    enabled: true
    sourceCode: IPCC_EFDB
    checkUrl: "https://example.org/sources/ipcc-efdb/check"
    downloadUrl: "https://example.org/sources/ipcc-efdb/download"
    schedule:
      period: month
      interval: 1
      dayOfMonth: 1
      time: "05:00"
      timezone: "UTC"
    import:
      mode: check_latest_then_import
      duplicatePolicy: skip_if_same_hash
```

## Schedule Model

Each source has independent schedule settings. The schedule model should support:

- `day`
- `week`
- `month`
- `year`
- `time`
- `timezone`

Common schedule fields include:

- `period`: `day`, `week`, `month`, or `year`
- `interval`: numeric interval for the selected period
- `dayOfWeek`: used for weekly schedules
- `dayOfMonth`: used for monthly and yearly schedules
- `time`: local wall-clock time for the schedule
- `timezone`: IANA time zone or `UTC`

## Import Model

Each source import section should include:

- `mode`: the source check/import behavior. The Phase 1 example uses `check_latest_then_import`.
- `duplicatePolicy`: duplicate handling. The recommended Phase 1 policy is `skip_if_same_hash`.

## Source Configuration

Each Phase 1 source family should have an independent source configuration section:

- GHG Protocol
- DEFRA/DESNZ
- IPCC EFDB

Each source should be independently enabled, scheduled, checked for version/hash changes, parsed, validated, and persisted.
