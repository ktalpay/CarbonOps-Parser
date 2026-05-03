# Codex-Assisted Runs

This folder documents a lightweight human-in-the-loop workflow for small Codex-assisted repository tasks.

## Purpose

The workflow keeps task execution, review, and merge decisions explicit. It is intended for small, reviewable changes where each task has a defined scope, validation plan, and commit message.

## Recommended Flow

1. Create or select a task from the queue.
2. Run the Codex developer task on a task branch.
3. Open a pull request with one commit.
4. Run CI or local checks listed by the task.
5. Run a reviewer pass using the reviewer checklist.
6. Human reviewer approves and merges, or requests changes.
7. Human selects the next task.

Auto-merge is intentionally out of scope.

Next-task selection remains human-approved unless a future workflow task changes this repository policy.

## Files

- [Task Queue](task-queue.md)
- [Reviewer Checklist](reviewer-checklist.md)
- [Prompt Template](prompt-template.md)
