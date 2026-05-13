# Configuration Model

CarbonOps-Parser uses a shared conceptual configuration model for both implementation paths. The repository-level example is [../config/carbonops.config.example.yaml](../config/carbonops.config.example.yaml).

The example documents the intended settings shape before runtime configuration loading is implemented. It is not a source URL registry, and its source URLs are safe placeholders until source discovery confirms exact check and download locations.

## Implementation Formats

Python and .NET may use different physical configuration formats:

- Python may use YAML.
- .NET may use `appsettings.json`.

Both implementations should follow the same conceptual model so users can choose either implementation path without learning a different configuration design.

## Top-Level Sections

The shared example contains:

- `app`: application identity, environment label, and log level.
- `database`: provider, split PostgreSQL connection fields, secret reference, and schema name.
- `storage`: raw source file archive path.
- `execution`: retry and single-instance lock settings.
- `sources`: source-specific check, download, schedule, and import settings.

## App Section

The `app` section identifies the service in logs and local configuration:

```yaml
app:
  name: CarbonOps-Parser
  environment: local
  logLevel: info
```

Expected fields:

- `name`: display name for the service.
- `environment`: local environment label, such as `local`, `dev`, or `test`.
- `logLevel`: intended logging verbosity.

## Database Section

Phase 1 implements PostgreSQL only.

The conceptual model reserves these provider names:

- `postgres`
- `mysql`
- `mssql`

If the configured provider is not `postgres` in Phase 1, startup should fail fast with this message:

```text
Unsupported database provider. Phase 1 supports postgres only.
```

Provider validation must happen before source checks, downloads, parsing, or imports. See [database-startup.md](database-startup.md).

### Database Field Reference

| Field | Required | Purpose | Phase 1 guidance |
| --- | --- | --- | --- |
| `provider` | Yes | Selects the database provider. | Use `postgres`. |
| `host` | Yes | PostgreSQL host name. | Use an environment-specific value outside committed production config. |
| `port` | Yes | PostgreSQL port. | Must be an integer from 1 to 65535. |
| `database` | Yes | PostgreSQL database name. | Use an environment-specific value outside committed production config. |
| `username` | Yes | PostgreSQL user name. | Use an environment-specific value outside committed production config. |
| `passwordEnvVar` | Yes | Names the environment variable or secret binding that supplies the PostgreSQL password. | Use `CARBONOPS_PARSER_POSTGRES_PASSWORD`; do not store the password here. |
| `schema` | Yes | Names the PostgreSQL schema for CarbonOps-Parser tables. | Use `carbonops`. |

Raw PostgreSQL connection strings are not accepted for production configuration because they commonly combine host, username, and password into one value that is easy to leak in diagnostics. Python and .NET both expect split non-secret fields plus `CARBONOPS_PARSER_POSTGRES_PASSWORD` as the secret boundary.

## Production Environment Boundary

Production startup validation is fail-closed. The runtime should validate these required keys before source checks, downloads, parsing, imports, or database execution:

- `CARBONOPS_PARSER_ENV`
- `CARBONOPS_PARSER_DATABASE_PROVIDER`
- `CARBONOPS_PARSER_POSTGRES_HOST`
- `CARBONOPS_PARSER_POSTGRES_PORT`
- `CARBONOPS_PARSER_POSTGRES_DATABASE`
- `CARBONOPS_PARSER_POSTGRES_USERNAME`
- `CARBONOPS_PARSER_POSTGRES_PASSWORD`
- `CARBONOPS_PARSER_POSTGRES_SCHEMA`
- `CARBONOPS_PARSER_RAW_ARCHIVE_PATH`
- `CARBONOPS_PARSER_LOG_LEVEL`

`CARBONOPS_PARSER_POSTGRES_PASSWORD` is the only required secret in this Phase 1 boundary. Validators may confirm that it is present, but validation results, logs, and diagnostics must not echo its value. Missing or invalid configuration messages should name the key and the expected shape only.

The Python and .NET contracts are intentionally aligned: both validate caller-provided mappings, both require PostgreSQL provider `postgres`, both reject raw connection-string config, and neither reads environment variables, config files, credentials, opens a PostgreSQL connection, or runs SQL during validation.

## Storage Section

The `storage` section defines where raw source files are archived:

```yaml
storage:
  rawArchivePath: "./data/raw"
```

Downloaded source files should be stored on disk, while PostgreSQL stores file metadata such as path, file name, content type, size, hash, downloaded timestamp, and source/version reference.

## Execution Section

The `execution` section describes retry and lock behavior at a configuration level:

```yaml
execution:
  maxRetryCount: 3
  retryDelaySeconds: 60
  singleInstanceLock: true
  lockTimeoutMinutes: 30
```

Expected fields:

- `maxRetryCount`: maximum retry attempts for a scheduled source check or import attempt.
- `retryDelaySeconds`: delay between retry attempts.
- `singleInstanceLock`: whether the implementation should use a lock to avoid overlapping work for the same source.
- `lockTimeoutMinutes`: lock expiration window for a scheduled job.

The lock concept is described in [background-job-model.md](background-job-model.md).

## Source Sections

The `sources` section contains independent configuration for:

- `ghgProtocol`
- `defraDesnz`
- `ipccEfdb`

Each source section should include:

- `enabled`
- `sourceCode`
- `checkUrl`
- `downloadUrl`
- `schedule`
- `import`

`checkUrl` and `downloadUrl` values in the example use placeholder URLs. Exact source locations should be confirmed through source discovery before implementation relies on them. See [source-support.md](source-support.md).

## Schedule Fields

Each source has an independent schedule. A schedule for one source should not force another source to run.

### Schedule Field Reference

| Field | Required | Purpose | Notes |
| --- | --- | --- | --- |
| `period` | Yes | Schedule period. | Use `day`, `week`, `month`, or `year`. |
| `interval` | Yes | Number of periods between checks. | `1` means every period. |
| `dayOfWeek` | Weekly schedules | Day for weekly checks. | Example: `monday`. |
| `dayOfMonth` | Monthly and yearly schedules | Day of month for checks. | Example: `1`. |
| `time` | Yes | Wall-clock time for the check. | Example: `"04:00"`. |
| `timezone` | Yes | Timezone for the schedule. | Use `UTC` unless a source needs another timezone. |

### Source Schedule Examples

The shared example uses:

- GHG Protocol: monthly at 04:00 UTC.
- DEFRA/DESNZ: yearly at 04:30 UTC.
- IPCC EFDB: monthly at 05:00 UTC.

## Import Behavior Fields

Each source has an `import` section:

```yaml
import:
  mode: check_latest_then_import
  duplicatePolicy: skip_if_same_hash
```

### Source Import Field Reference

| Field | Required | Purpose | Phase 1 guidance |
| --- | --- | --- | --- |
| `mode` | Yes | Describes check/import behavior. | Use `check_latest_then_import`. |
| `duplicatePolicy` | Yes | Describes duplicate import handling. | Use `skip_if_same_hash`. |

`skip_if_same_hash` means that if the same source version and raw file hash are already stored, the import should be skipped instead of duplicating records. This supports idempotent scheduled ingestion. See [background-job-model.md](background-job-model.md).

## Inline Example

The full example lives in [../config/carbonops.config.example.yaml](../config/carbonops.config.example.yaml). A shortened inline shape is shown below:

```yaml
app:
  name: CarbonOps-Parser
  environment: local
  logLevel: info

database:
  provider: postgres
  host: "${CARBONOPS_PARSER_POSTGRES_HOST}"
  port: 5432
  database: "${CARBONOPS_PARSER_POSTGRES_DATABASE}"
  username: "${CARBONOPS_PARSER_POSTGRES_USERNAME}"
  passwordEnvVar: CARBONOPS_PARSER_POSTGRES_PASSWORD
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
```
