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
helpers. However, the production-readiness surface is not merge-ready yet
because the .NET service host does not expose or emit service-host diagnostics,
and Python/.NET orchestrator event names are not aligned. Those gaps make
cross-language operational dashboards, log queries, and runbooks harder to make
deterministic during production troubleshooting.

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

Correlation is present for orchestrator diagnostics. Python emits
`correlation_id` and `run_id` in orchestrator start, per-family completion, and
run completion payloads. .NET emits the same identifiers through the optional
orchestrator event sink. This is enough to connect a selected Phase 1
orchestrator run with its per-family diagnostic records when the sink/logger is
wired by a host.

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

## Blocking Mismatches

- The .NET service host does not currently accept an operational event sink and
  does not emit startup, bootstrap, scheduled-run, skipped-run, or
  orchestrator-result diagnostics. Python has service-host diagnostic events for
  these lifecycle states. This is a production troubleshooting gap for
  cross-language service deployments.
- Python and .NET orchestrator event names differ. Python emits
  `phase1_ingestion_orchestrator_started` and
  `phase1_ingestion_orchestrator_completed`, while .NET emits
  `phase1_orchestrator_started` and `phase1_orchestrator_completed`. The
  payload shape is mostly aligned, but event-name drift makes log queries and
  runbooks language-specific.
- The shared parity fixture covers diagnostic payload keys and the known .NET
  family-status coarseness, but it does not assert event-name parity or
  service-host diagnostic parity.

## Known Limitations

- Diagnostics are structured JSON/log-contract helpers, not a full
  observability stack. Metrics, traces, alert rules, dashboards, SLOs,
  retention policy, and centralized log ingestion are not implemented here.
- Python logs directly through the Phase 1 logger; .NET uses an optional
  orchestrator event sink. Production host wiring for .NET is not proven by the
  current service-host contract.
- Service-host diagnostics in Python summarize lifecycle outcomes, but they do
  not add distributed scheduler identity, process identity, deployment version,
  host name, retry attempt, lock owner, or cancellation context.
- Runtime database execution was not performed. Redaction was validated through
  deterministic contract tests and local summaries only.
- Diagnostic checks do not prove live source availability, parser correctness,
  source correctness, carbon-accounting correctness, or release packaging.
- Redaction is pattern-based. It protects the expected credential fields and
  common inline secret forms, but production logging policy should still avoid
  passing arbitrary raw exception payloads or connection strings into diagnostic
  messages.

## Verdict

Not merge-ready for production observability readiness.

The Python and .NET diagnostic payload helpers are coherent enough to preserve
safe redaction, correlation identity, run status, source-family context, and
failure reason codes at the orchestrator level. The remaining .NET service-host
diagnostic gap and cross-language event-name drift should be fixed or explicitly
accepted before this review can support final production hardening and release
packaging.

Task-ID: RV-054
Task-Issue: #496
