# PT-040 Parity Review: Runtime Config Gate

Task-ID: PT-040  
Task-Issue: #357

## Scope

Parity review for the PostgreSQL runtime configuration gate across the Python
and .NET contract surfaces.

Reviewed files:

- `src/carbonfactor_parser/persistence/postgresql_runtime_config_gate.py`
- `tests/test_postgresql_runtime_config_gate.py`
- `src/carbonfactor_parser/persistence/__init__.py`
- `src/dotnet/CarbonOps.Parser.Contracts/PostgreSQLRuntimeConfigGate.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/PostgreSQLRuntimeConfigGateDecision.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/PostgreSQLRuntimeConfigGateDescription.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/PostgreSQLRuntimeConfigGateIssue.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/PostgreSQLRuntimeConfigGateStatus.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/PostgreSQLRuntimeConfigGateEvaluator.cs`
- `src/dotnet/CarbonOps.Parser.Contracts/ContractWireNames.cs`
- `tests/dotnet/CarbonOps.Parser.Contracts.Tests/PostgreSQLRuntimeConfigGateContractTests.cs`

This review did not change runtime behavior, add configuration loading, add
credential loading, connect to PostgreSQL, execute SQL, or modify parser,
database, scheduler, downloader, or source-specific ingestion behavior.

## Parity Findings

No blocking parity mismatch was found.

### Behavior And Contracts

Python and .NET expose the same gate concepts:

- caller-provided `PostgreSQLRuntimeConfigGate` metadata
- structured `PostgreSQLRuntimeConfigGateDecision`
- side-effect-free `PostgreSQLRuntimeConfigGateDescription`
- structured `PostgreSQLRuntimeConfigGateIssue`
- pure evaluation/description helpers

Both implementations keep the gate passive. Evaluation and description do not
load environment variables, read config files, load credentials, open database
connections, create cursors, execute SQL, run migrations, or enable repository
runtime behavior.

### Naming And Wire Values

The shared status set is aligned:

| Concept | Python | .NET | Wire value |
| --- | --- | --- | --- |
| Disabled/default | `DISABLED` | `Disabled` | `disabled` |
| Requested but incomplete | `BLOCKED` | `Blocked` | `blocked` |
| Metadata complete but still not enabled | `NOT_ENABLED` | `NotEnabled` | `not_enabled` |

.NET includes explicit `ContractWireNames` mappings for these values. Python
uses string enum values matching the same wire names.

The required future component identifiers are aligned and ordered consistently:

1. `postgresql_implementation_safety_gate`
2. `postgresql_persistence_options_contract`
3. `explicit_runtime_configuration_opt_in`
4. `approved_secret_source`

### State Transitions

The state-transition semantics match:

- no caller request returns `disabled`
- caller request with incomplete future metadata returns `blocked`
- caller request with all future metadata marked complete returns `not_enabled`

All three states keep:

- `config_loading_enabled=False`
- `runtime_enabled=False`
- `loads_environment=False`
- `loads_config_files=False`
- `loads_credentials=False`

The description surface also keeps `opens_connection=False` and `runs_sql=False`
in both language paths.

### Error And Issue Semantics

Issue codes are aligned:

- `POSTGRESQL_RUNTIME_CONFIG_DISABLED_BY_DEFAULT`
- `POSTGRESQL_RUNTIME_CONFIG_BLOCKED`
- `POSTGRESQL_RUNTIME_CONFIG_NOT_ENABLED`

Requested states set `field_name`/`FieldName` to `requested`. Default-disabled
states leave the field unset/null. Both implementations use `warning` as the
default issue severity.

The review found no drift that would require code changes.

## Validation Performed

- Reviewed Python runtime config gate implementation and tests.
- Reviewed .NET runtime config gate contract records, evaluator, wire-name
  mappings, and tests.
- Compared status values, required component identifiers, passive runtime flags,
  transition outcomes, and issue codes/messages.

## Remaining Risks

- This is a parity review of current metadata-only gate behavior. It does not
  prove future runtime configuration loading behavior because that behavior is
  intentionally not implemented.
- Cross-language drift remains possible if a future task updates one gate
  surface without synchronized tests and documentation.
- The gate still relies on future safety-gated work before runtime
  configuration loading can be enabled.

## Verdict

Merge-ready for parity-review scope.

The Python and .NET runtime config gate surfaces are aligned for behavior,
contracts, naming, wire values, schema shape, state transitions, and issue
semantics. No code changes are required for PT-040.

Task-ID: PT-040  
Task-Issue: #357
