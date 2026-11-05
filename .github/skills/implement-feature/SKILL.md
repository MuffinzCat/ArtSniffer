---
name: implement-feature
description: "Implement a bounded ArtSniffer feature with focused tests and repository validation."
argument-hint: "Describe the feature, acceptance criteria, and any file-scope limits."
disable-model-invocation: true
---

# Implement ArtSniffer Feature

Implement the ArtSniffer feature described in the invocation.

Use the supplied details as the task boundary:

- **Task:** Describe the requested feature.
- **Acceptance criteria:** List observable requirements.
- **Permitted file scope:** Optional file or directory limits.

Inspect the affected architecture, related tests, and applicable instructions first. Implement only
the described feature, test its behaviour, run applicable repository validation, review scope, and
report changes and checks actually run. Do not commit or push.

## Agent routing compatibility

The original prompt selected the **ArtSniffer Developer** agent. Skills cannot select an agent;
invoke this skill while that agent is active when its role-specific workflow is required.
