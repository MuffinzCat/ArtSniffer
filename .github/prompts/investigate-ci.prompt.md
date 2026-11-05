---
name: Investigate ArtSniffer CI
description: "Diagnose an ArtSniffer validation or CI failure from supplied output and repository evidence."
argument-hint: "Provide the failing check and any failure output or context."
agent: agent
---

Diagnose this ArtSniffer validation or CI failure without changing files:

**Failing check or output:** ${input:failure:Name the check and paste the failure output or context}

Identify the failing check, inspect relevant workflow configuration, source, and tests, then use
available evidence to determine the likely root cause. Distinguish task-caused, repository-caused,
and potentially transient or tooling failures where possible. Propose the smallest appropriate
correction and cite the evidence supporting the diagnosis.

Do not invent output or causes, edit files, commit, push, or run destructive or privileged
operations. Do not automatically rerun operations that could change state.
