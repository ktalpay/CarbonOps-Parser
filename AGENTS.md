# Agent Instructions

These instructions apply to Codex-assisted development, human developer work, and reviewer passes in this repository.

## Task Shape

- One task = one branch = one commit = one pull request.
- Keep tasks small, focused, and reviewable.
- Prefer documentation-first and testable increments.
- Treat scope creep as a review blocker.
- Treat missing validation as a review blocker.

## Scope Guards

- Do not add source-specific ingestion unless the task explicitly requests it.
- Do not add parser, database, scheduler, or downloader coupling unless the task explicitly requests it.
- Do not add production, compliance, legal, or carbon-accounting correctness claims.
- Do not use confidential company, customer, or private source data.
- Preserve the existing public API unless the task explicitly changes it.
- Keep examples deterministic and local-only unless the task explicitly says otherwise.

## Validation

- Run the checks requested by the task.
- At minimum, run the lightweight test command when Python package behavior or examples are affected:

```bash
python -m pytest
```

- Run `git diff --check` before committing.
- List validation results in the pull request and task handoff.
