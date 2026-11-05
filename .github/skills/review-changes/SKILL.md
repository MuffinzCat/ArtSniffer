---
name: review-changes
description: "Independently review ArtSniffer changes and report actionable findings without editing."
argument-hint: "Describe the review scope and, optionally, acceptance criteria or feature intent."
disable-model-invocation: true
---

# Review ArtSniffer Changes

Review the current working changes and diff within the supplied scope.

Use the supplied review scope and, optionally, acceptance criteria or feature intent. Consider
relevant surrounding code and tests. Follow ArtSniffer Reviewer’s review and reporting guidance.
This is a read-only review: do not edit files or apply fixes.

## Agent routing compatibility

The original prompt selected the **ArtSniffer Reviewer** agent. Skills cannot select an agent;
invoke this skill while that agent is active to retain its full review guidance.
