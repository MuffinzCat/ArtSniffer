---
name: artsniffer-validation
description: "Use when validating ArtSniffer implementation changes, diagnosing validation failures, or preparing to report implementation completion."
---

# ArtSniffer Validation

Use the repository instructions for the authoritative check commands and scope. This skill provides
a reusable sequence for choosing checks, diagnosing failures, and reporting evidence.

## Procedure

1. Determine which repository checks apply to the change; consult the repository and applicable
   path-specific instructions.
2. Inspect `git status --short --untracked-files=all` before validation so existing changes are
   not mistaken for validation effects.
3. For normal Python changes, run the established non-mutating final checks: Ruff formatting in
   check-only mode, Ruff lint, Pyright, pytest, and `git diff --check`.
4. Inspect failures and their evidence; do not hide or silently dismiss them.
5. Fix failures caused by the current task only when the active agent or task has permission to
   edit. Do not opportunistically fix unrelated or pre-existing failures.
6. After a correction, rerun only the checks needed to verify it, then run the appropriate final
   validation.
7. Inspect final Git status and changed-file scope for unintended changes.
8. Report exactly which checks ran and whether each passed. Never claim an unexecuted check passed.

## Boundaries

- Read-only reviews and other read-only tasks must not mutate files during validation. Use only
  checks that do not intentionally write to the repository.
- Do not install substitute tools if repository tooling is unavailable; report the limitation.
- Validation success is not permission to commit or push.
