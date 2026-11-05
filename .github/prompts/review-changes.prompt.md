---
name: Review ArtSniffer Changes
description: "Independently review ArtSniffer changes and report actionable findings without editing."
argument-hint: "Describe the review scope and, optionally, acceptance criteria or feature intent."
agent: "ArtSniffer Reviewer"
---

Review the current working changes and diff within this scope:

**Review scope:** ${input:scope:Describe the changes or files to review}

**Acceptance criteria or feature intent (optional):** ${input:criteria:Provide context if useful}

Consider relevant surrounding code and tests. Follow ArtSniffer Reviewer’s review and reporting
guidance. This is a read-only review: do not edit files or apply fixes.
