# Contributing

Contributions are welcome for documentation, examples, parser mappings, source discovery notes, database schema design, and implementation improvements.

CarbonOps-Parser is project-level production-ready only in the narrow supported scope documented in the production-ready verdict. Keep changes small, reviewable, testable, and aligned with that scope. Do not broaden production, compliance, legal, source-owner, or carbon-accounting correctness claims.

## Open Issues

Use GitHub issues for reproducible bugs, scoped feature proposals,
documentation improvements, source-family questions, and production-readiness
scope questions. Choose the closest issue template and include:

- Implementation target: Python, .NET, Docs, Database, or Shared.
- Source family when relevant: GHG Protocol, DEFRA/DESNZ, or IPCC EFDB.
- Source version, file name, or fixture name when relevant.
- Concise reproduction steps for bugs.
- Expected result and actual result for bugs.
- Clear proposed scope and out-of-scope notes for features.

Do not include confidential company data, credentials, private source files,
private connection strings, or production infrastructure details in public
issues.

## Propose Features

Feature requests should describe the user need, the affected runtime or docs
area, and the smallest useful increment. Source-specific ingestion, parser,
database, scheduler, downloader, package publication, or production promotion
work must be explicitly requested and reviewed before implementation.

## Report Bugs

Bug reports should include commands, inputs, versions, source family, and
reproduction steps when available. For PostgreSQL reports, redact connection
details and share only non-sensitive configuration shape or error summaries.

## Improve Documentation

Documentation pull requests are welcome when they clarify usage, scope,
runbooks, examples, troubleshooting, source discovery notes, or contribution
workflow. Documentation changes must preserve the narrow production-ready scope
and must not add package publishing claims or broader correctness claims.

## Branches And Forks

External contributors should fork the repository and open pull requests into
`develop`. Maintainers may also create focused branches in the main repository.
Use short branch names with one of these prefixes:

- `fix/...`
- `feature/...`
- `docs/...`
- `chore/...`

One task should map to one branch, one commit, and one pull request whenever
practical.

## Good Contribution Areas

- Clarifying documentation.
- Improving source discovery notes.
- Proposing parser mapping details for GHG Protocol, DEFRA/DESNZ, or IPCC EFDB.
- Improving PostgreSQL schema documentation.
- Adding implementation work when a task explicitly calls for it.
- Improving issue and pull request quality.

## Pull Request Process

Open pull requests into `develop`. Use the pull request template and include
summary, scope, runtime impact, validation performed, PostgreSQL impact, docs
impact, secrets/artifacts checklist, production-ready claim checklist, and
maintainer-only merge acknowledgement.

Before opening a pull request:

- Keep the change focused.
- Avoid adding dependencies unless the task explicitly requires them.
- Avoid committing local-only files such as `codex/`.
- Do not include confidential data, credentials, private source files, or private connection strings.
- Do not commit generated artifacts, build outputs, caches, database dumps, downloaded source files, or local test output.
- Update documentation when behavior or scope changes.
- Respect the production-ready scope documented in the final verdict.
- Run `git diff --check`.
- Run the relevant tests for the affected area.

For Python package behavior or examples, run:

```bash
python -m pytest
```

Documentation-only changes should run any targeted documentation tests named by
the task. If a requested validation command cannot be run, state why in the PR.

## Merge Policy

Only maintainers merge pull requests. Contributors should not imply that they
can self-merge, close issues on behalf of maintainers, or approve production
scope changes. CODEOWNERS identifies the maintainer review boundary.

## Implementation Targets

Use the relevant target when opening an issue or pull request:

- Python
- .NET
- Docs
- Database
- Shared
