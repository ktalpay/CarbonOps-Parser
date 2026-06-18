# RV-053 Service Host Production Readiness Review

## Summary

This review covers the Python and .NET Phase 1 service host contracts for
scheduled ingestion before observability, deployment packaging, and release
hardening. The reviewed surface is coherent enough for production hardening to
proceed: startup validation is fail-closed, schema-bootstrap readiness is
checked before scheduled source execution, only sequential scheduled execution
is accepted, overlapping trigger attempts are skipped, shutdown stops new work
while allowing active work to finish, and runner failures release the local
overlap guard.

No blocking contract mismatch was found that requires a code fix in this review
scope.

## Reviewed Scope

- Python `Phase1ScheduledIngestionServiceHost`, startup config validation,
  schema-bootstrap handoff, trigger lifecycle, shutdown handling, and dedicated
  tests.
- .NET `Phase1ScheduledIngestionServiceHost`, startup config validation,
  schema-bootstrap handoff, trigger lifecycle, shutdown handling, and dedicated
  tests.
- Phase 1 ingestion orchestrator readiness behavior used by the service host.
- PostgreSQL runtime config and schema-bootstrap boundary contracts used during
  service-host startup and orchestrator requests.
- Background job model and database startup documentation that define the
  deferred scheduler, lock, and startup expectations.

## Readiness Findings

Startup validation is explicit and fail-closed. Both language surfaces require
at least one Phase 1 source family, a non-empty run ID prefix, a positive
schedule interval, sequential execution, single parallelism, valid PostgreSQL
options, and an explicit `password_set`/`PasswordSet` credential availability
signal. Invalid configuration leaves the host blocked and prevents scheduled
orchestrator execution.

Bootstrap behavior is ordered before source execution. The host invokes a
schema-bootstrap checker only after local configuration validation succeeds.
When required Phase 1 tables are reported missing and `fail_on_missing_schema`
is enabled, startup returns blocked readiness and scheduled runs are not
accepted. The default bootstrap checker remains passive in the current
contracts: it describes table readiness and intent without opening a connection
or running SQL.

Scheduled execution is intentionally narrow. Both implementations accept only
sequential Phase 1 ingestion and build one orchestrator request per accepted
trigger with the selected source families, run ID, runtime config gate, and
startup schema-bootstrap report. The host does not introduce source-specific
ingestion, downloader behavior, parser behavior, database writes, production
credentials, or release packaging.

Overlapping-run prevention is coherent for a single service-host instance. A
local synchronization guard marks a run active before invoking the orchestrator.
Nested or concurrent trigger attempts observe the active run and return a
structured skipped-already-running result rather than starting another
orchestrator request. Runner exceptions still release the guard in `finally`
logic and return the host to ready unless shutdown was requested.

Shutdown semantics are explicit enough for hardening. A shutdown request sets a
host-level shutdown flag. If no run is active, the host stops immediately and
later trigger attempts are skipped. If a run is active, the host reports
shutdown-requested, rejects new trigger attempts, and transitions to stopped
after the active runner unwinds. The current contract does not interrupt active
work.

Operational failure modes are surfaced structurally. Startup failures produce
`blocked` startup results with issue codes and field names. Trigger-before-start,
trigger-while-running, and trigger-after-shutdown each return deterministic
skipped results with issue metadata. Orchestrator runner exceptions propagate to
the caller while still cleaning up host lifecycle state.

Python and .NET are aligned at the observable service-host level. Status enums,
startup result shape, scheduled run result shape, sequential-only validation,
bootstrap blocking, overlap prevention, shutdown transitions, run ID sequencing,
and runner-error cleanup are represented in both implementations. Naming differs
where each language follows local conventions, but no blocking behavioral drift
was found.

## Known Limitations

- The service host is a synchronous contract boundary, not a deployed
  production worker. It does not own OS service registration, container entry
  points, deployment packaging, health endpoints, or process supervision.
- The schedule interval is validated but not executed by an actual timer,
  cron loop, queue consumer, or hosted-service runtime in this scope.
- Overlap prevention is local to one host instance. There is no distributed
  lease, database-backed lock acquisition, stale-lock cleanup, lock renewal, or
  cross-process single-instance guarantee yet.
- Shutdown is graceful only at the host boundary. It does not pass cancellation
  tokens or cancellation signals into discovery, download, parser,
  normalization, or persistence runtime adapters.
- Bootstrap behavior is still passive by default. Real PostgreSQL connection
  checks, schema creation, migration execution, retries, and rollback behavior
  remain separate hardening scope.
- Operational observability remains deferred. The contracts expose structured
  results and issues, but they do not emit logs, metrics, traces, alerts,
  readiness probes, or run-history events.
- Retry, backoff, dead-letter handling, replay policy, and idempotent recovery
  after process failure are not implemented at the service-host layer.
- Production credential loading is intentionally outside this review. The host
  validates that credential availability was confirmed without storing or
  resolving secrets itself.
- Source correctness, parser correctness, normalization correctness, unit
  conversion correctness, compliance/legal interpretation, and carbon-accounting
  correctness are not assessed by this service-host review.

## Verdict

Merge-ready for RV-053 review scope.

The Phase 1 service host and scheduled execution behavior are coherent enough
for production hardening work to proceed, with the limitations above treated as
follow-on scope rather than blockers for this review.

Task-ID: RV-053
Task-Issue: #492
