# Contributing

Contributions are welcome for documentation, examples, parser mappings, source
discovery notes, database schema design, and implementation improvements.

CarbonOps-Parser is a public repository. Contributors may open issues, create
branches in their own fork, and submit pull requests for review. Only the
maintainer merges changes into the upstream repository.

Please keep changes small, reviewable, and aligned with the documented scope.
The project has a narrow production-ready verdict for the supported operator
path; contributions must not broaden that claim unless a task explicitly
changes the verdict.

## Good Contribution Areas

- Clarifying documentation.
- Improving source discovery notes.
- Proposing parser mapping details for GHG Protocol, DEFRA/DESNZ, or IPCC EFDB.
- Improving PostgreSQL schema documentation.
- Adding implementation work when a task explicitly calls for it.
- Improving issue and pull request quality.

## Before Opening A Pull Request

- Keep the change focused.
- Use one task, one branch, one commit, and one pull request when practical.
- Avoid adding dependencies unless the task explicitly requires them.
- Avoid committing local-only files such as `codex/`.
- Do not include confidential data, credentials, or private source files.
- Update documentation when behavior or scope changes.
- Run `python -m pytest` when Python package behavior or examples are affected.
- Run `git diff --check` before opening the pull request.
- List validation commands and results in the pull request.

## Branch And Pull Request Workflow

See [Branch And Pull Request Workflow](docs/branch-pr-workflow.md) for the
recommended issue, branch, validation, and review sequence.

In short:

1. Open or choose a scoped issue.
2. Create a topic branch or fork branch named for the task.
3. Keep the change focused on the issue scope.
4. Run the relevant validation.
5. Open a pull request using the repository template.
6. Wait for maintainer review and merge.

## Implementation Targets

Use the relevant target when opening an issue or pull request:

- Python
- .NET
- Docs
- Database
- Shared
