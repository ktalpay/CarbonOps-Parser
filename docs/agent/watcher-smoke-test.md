# Watcher Smoke Test

Task ID: OPS-007

This file is a docs-only smoke test artifact for the first Agent Task Watcher workflow.

The expected behavior is:

1. This PR is merged.
2. The watcher reads `Task-ID: OPS-007` and `Task-Issue: #<issue>` from the PR body.
3. The watcher resolves the target task issue from `Task-Issue`.
4. The watcher marks that issue as `status:merged`.
5. The watcher leaves a traceable issue comment.

This file does not define product behavior.
