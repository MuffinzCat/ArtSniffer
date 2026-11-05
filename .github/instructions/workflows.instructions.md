---
description: "Use when editing GitHub Actions workflows under .github/workflows/."
applyTo: ".github/workflows/**/*.{yml,yaml}"
---

# GitHub Actions workflow guidance

- Inspect related workflows and branch-protection assumptions before editing. Preserve the stable
  required `PR Gate` contract and do not casually rename required checks.
- Keep permissions to the minimum required by each workflow. Never expose, print, or hardcode
  secrets; do not add privileged triggers or secret access for convenience.
- Keep validation separate from automatic merging. Do not broaden automatic-merge eligibility
  without explicit requirements; retain the established owner and same-repository safety model
  unless the task explicitly changes it.
- Follow established action pinning or versioning practice. Avoid unrelated workflow rewrites.
- Treat pull-request content as untrusted. Before changing triggers, carefully assess the security
  differences between `pull_request`, `pull_request_target`, `push`, and other privileged contexts.
- Validate workflow syntax and applicable repository checks with existing tools where available.
  Report any requested change that would weaken repository protections.
