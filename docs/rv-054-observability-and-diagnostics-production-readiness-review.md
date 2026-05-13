# RV-054 Observability And Diagnostics Production Readiness Review

## Summary

This review covers Phase 1 observability and operational diagnostics across
Python and .NET before final production hardening and release packaging. The
shared diagnostic payload contracts are mostly coherent: sensitive PostgreSQL
runtime values are redacted, orchestrator events carry run and correlation
identity, per-family diagnostics include source-family context, run status is
reported at family and orchestrator levels, and structured failure records carry
reason codes.

The review found no evidence of raw credential logging in the tested diagnostic
helpers. The previously blocking .NET service-host diagnostic gap and
Python/.NET orchestrator event-name drift have been resolved, so the PR is now
merge-ready for this review scope. This does not claim a complete production
observability stack; it confirms the contract-level diagnostics needed for the
next hardening increment.

## Reviewed Scope

- Python `phase1_observability` helpers for redaction, event serialization,
  PostgreSQL option summaries, orchestrator request summaries, per-family result
  summaries, and run-level result summaries.
- Python Phase 1 orchestrator operational log emission and tests.
- Python Phase 1 service-host startup and scheduled-run diagnostic emission and
  tests.
- .NET `Phase1OperationalDiagnostics` helpers for redaction, event
  serialization, PostgreSQL option summaries, orchestrator request summaries,
  per-family result summaries, and run-level result summaries.
- .NET Phase 1 orchestrator operational event sink and tests.
- .NET Phase 1 service-host operational event sink and lifecycle diagnostic
  tests.
- Shared `phase1_operational_diagnostics_expectations.json` parity fixture.
- Prior RV-052 and RV-053 findings for orchestrator and service-host readiness.

## Readiness Findings

Redaction is explicit and tested in both language surfaces. PostgreSQL host,
database, username, application name, DSN, connection string, URI, database URL,
password, token, secret, and credential-shaped fields are redacted before being
serialized into diagnostics. Connection URI user-info and assignment-style
secret fragments are also removed from diagnostic strings. The diagnostic
summaries expose `password_set` as a boolean capability signal without exposing
the password value.

Correlation is present for orchestrator diagnostics. Python and .NET emit
`correlation_id` and `run_id` in orchestrator start, per-family completion, and
run completion payloads using shared event names:
`phase1_ingestion_orchestrator_started`,
`phase1_source_family_completed`, and
`phase1_ingestion_orchestrator_completed`. This is enough to connect a selected
Phase 1 orchestrator run with its per-family diagnostic records when the
sink/logger is wired by a host.

Run-status reporting is structured. Python reports top-level statuses such as
`completed`, `completed_with_failures`, `failed`, and `not_executable`, plus
stage-specific family statuses such as `failed_parser` or
`failed_source_document_persistence`. .NET reports the same top-level run
statuses and coarser family statuses of `completed`, `failed`, and `skipped`.
The coarser .NET family status is acceptable only because failure `stage` and
`code` remain present in each structured failure record.

Source-family context is consistently included in diagnostic payloads. Request
diagnostics include selected source families; per-family diagnostics include
`source_family` and `source_key`; document summaries include source family,
source key, document ID, and safe checksum; failure summaries include source
family, source key, field name, stage, severity, and code.

Failure reason codes are present and deterministic enough for triage. Python
and .NET orchestrator failures carry structured codes rather than free-text-only
messages, and tested diagnostics preserve those codes while redacting sensitive
message fragments.

## Resolved Blocking Mismatches

- The .NET service host now accepts an optional operational event sink and emits
  structured lifecycle diagnostics for startup, startup result, scheduled-run
  start, scheduled-run completion, and skipped scheduled runs:
  `phase1_service_host_starting`, `phase1_service_host_started`,
  `phase1_service_host_scheduled_run_started`,
  `phase1_service_host_scheduled_run_completed`, and
  `phase1_service_host_scheduled_run_skipped`.
- Python and .NET orchestrator event names are now aligned on
  `phase1_ingestion_orchestrator_started` and
  `phase1_ingestion_orchestrator_completed`.
- The shared parity fixture now represents both orchestrator event-name parity
  and service-host lifecycle event-name parity, and .NET tests assert the
  service-host sink path and PostgreSQL-sensitive value redaction.

## Known Limitations

- Diagnostics are structured JSON/log-contract helpers, not a full
  observability stack. Metrics, traces, alert rules, dashboards, SLOs,
  retention policy, and centralized log ingestion are not implemented here.
- Python logs directly through the Phase 1 logger; .NET uses optional event
  sinks. Production log pipeline wiring remains separate from this contract
  work.
- Service-host diagnostics summarize lifecycle outcomes, but they do not add
  distributed scheduler identity, process identity, deployment version, host
  name, retry attempt, lock owner, or cancellation context.
- Distributed scheduler identity is not implemented.
- Distributed lock or lease behavior is not implemented.
- Runtime database execution was not performed. Redaction was validated through
  deterministic contract tests and local summaries only.
- Diagnostic checks do not prove live source availability, parser correctness,
  source correctness, carbon-accounting correctness, deployment packaging, or
  release packaging.
- Redaction is pattern-based. It protects the expected credential fields and
  common inline secret forms, but production logging policy should still avoid
  passing arbitrary raw exception payloads or connection strings into diagnostic
  messages.

## Verdict

Merge-ready for the RV-054 contract-level observability and diagnostics review
scope.

The Python and .NET diagnostic payload helpers are coherent enough to preserve
safe redaction, correlation identity, run status, source-family context, and
failure reason codes at the orchestrator and service-host levels. The earlier
blocking .NET service-host diagnostic gap, cross-language event-name drift, and
fixture coverage gap are fixed. The known limitations above remain out of scope
for this task and should be handled by later production hardening work.

Task-ID: RV-054
Task-Issue: #496
