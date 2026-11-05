---
name: investigate-ci
description: "Diagnose an ArtSniffer validation or CI failure from supplied output and repository evidence."
argument-hint: "Provide the failing check and any failure output or context."
disable-model-invocation: true
---

# Investigate ArtSniffer CI

Diagnose the supplied ArtSniffer validation or CI failure without changing files.

Use the supplied failing check and output or context to identify the failure. Inspect relevant
workflow configuration, source, and tests, then use available evidence to determine the likely root
cause. Distinguish task-caused, repository-caused, and potentially transient or tooling failures
where possible. Propose the smallest appropriate correction and cite the evidence supporting the
diagnosis.

Do not invent output or causes, edit files, commit, push, or run destructive or privileged
operations. Do not automatically rerun operations that could change state.

## Agent routing compatibility

The original prompt selected the generic `agent` mode. Skills do not carry prompt agent-selection
metadata; run this skill in an agent chat.
