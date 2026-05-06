# Local Public Safety Validation

`scripts/check_public_safety.py` is a lightweight local pre-review guard for public-facing repository text.

## Purpose

The script helps catch wording and references that should be reviewed before a task is opened for pull request review.

Run it from the repository root:

```bash
python scripts/check_public_safety.py
```

## What It Checks

The script scans text files for:

- Readiness, correctness, or certification-style public claims.
- Restricted personal-status wording.
- Sensitive assignment-like text.
- Remote URI schemes, with a small allowlist for existing known-safe repository examples.

Findings include file path, line number, category, and matched pattern name.

## What It Skips

The script skips generated or local environment folders such as `.git`, `.pytest_cache`, `__pycache__`, `.venv`, `venv`, `dist`, and `build`.

Binary-like files are skipped safely.

## Limits

This is a conservative local guard. It is not a compliance, legal, correctness, security, or release validator.

The script does not replace human review. Reviewers should still check scope, wording, documentation links, and validation evidence for each task.
