# PR Footer Metadata

## Purpose

Agent-created pull requests must end with explicit task metadata so the agent task watcher can update the correct GitHub issue after merge.

The metadata footer is separate from human-readable summary content and from GitHub's built-in issue-closing keywords.

## Required Footer

Every agent-created PR body must end with these two lines:

```text
Task-ID: <TASK_ID>
Task-Issue: #<ISSUE_NUMBER>
```

`Task-ID` identifies the logical task, such as `OPS-010`, `PY-004`, or `DN-004`.

`Task-Issue` identifies the GitHub issue that the watcher updates when the PR is merged.

## Watcher Behavior

The watcher reads the final matching `Task-ID:` and `Task-Issue:` lines from the PR body.

When multiple matching lines appear earlier in the PR body, the final matching footer lines are the watcher metadata. Earlier mentions may appear in summaries, examples, or discussion, but they do not replace the final footer.

No content should appear after the final footer. This keeps watcher metadata unambiguous and makes the PR body easy to verify before review.

## Closing Keywords

`Closes`, `Fixes`, and `Resolves` are GitHub issue-closing keywords. They are not watcher metadata.

Agent-created PRs may include closing keywords only when the task explicitly requires GitHub's issue-closing behavior. The watcher still relies on the final `Task-ID:` and `Task-Issue:` footer lines.

## Valid PR Body Ending

```text
Remaining risks:
- None known.

Task-ID: OPS-010
Task-Issue: #340
```
