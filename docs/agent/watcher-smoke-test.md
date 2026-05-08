# Watcher Smoke Test

Task ID: OPS-007

This file is a docs-only smoke test artifact for the first Agent Task Watcher workflow.

The expected behavior is:

1. This PR is merged.
2. The watcher reads `Task-ID: OPS-007` from the PR body.
3. The watcher reads `Closes #335` from the PR body.
4. The watcher marks issue #335 as `status:merged`.
5. The watcher leaves a traceable issue comment.

This file does not define product behavior.

Current Metadata Requirement

The watcher smoke-test standard now requires PR bodies to end with:

Task-ID: OPS-007
Task-Issue: #335

The watcher should use Task-Issue as the target issue and should use the final matching metadata footer.
