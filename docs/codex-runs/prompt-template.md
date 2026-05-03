# Codex Task Prompt Template

Use this template for future small repository tasks.

```text
You are working in the CarbonOps-Parser repository.

Task:
<Task ID>: <Task title>

Context:
<Relevant repository context>

Goal:
<Expected outcome>

Strict scope:
- <Boundary or non-goal>
- <Boundary or non-goal>

Expected implementation:
- <Expected files or changes>
- <Expected files or changes>

Tests to add:
- <Test expectation>
- <Test expectation>

Documentation:
- <Documentation expectation>

Validation:
Run:
- python -m pytest
- git diff --check
- <Other task-specific checks>

Commit:
Create exactly one commit.

Commit message:
<Task ID>: <commit message>

Output:
After implementation, report:
- Summary
- Files changed
- Tests/checks run and result
- Commit hash
- Remaining risks or intentionally deferred items
```
