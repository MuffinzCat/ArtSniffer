---
name: Prepare ArtSniffer Pull Request
description: "Draft a concise pull-request title and summary from the current branch and verified evidence."
argument-hint: "Optionally identify the intended base branch or additional context."
agent: agent
---

Prepare, but do not create, a pull request for the current branch.

**Intended base or context (optional):** ${input:base:Provide a base branch or context if known}

Safely establish the relevant base where possible. Inspect the branch, changed files, commits where
relevant, actual diff, and validation evidence available in the current session or repository state.
Do not commit, push, or create a pull request.

Return:

- Suggested title
- Concise summary and meaningful implementation details
- Tests and validation supported by available evidence
- Known limitations or follow-ups

Do not claim checks ran without evidence, invent issue references, or narrate commits unnecessarily.
