---
description: "Use when implementing or changing Python source in src/."
applyTo: "src/**/*.py"
---

# Python implementation guidance

- Inspect related models, functions, and tests before changing behaviour. Keep each model or
  function responsible for its own validation; do not duplicate another unit's checks unnecessarily.
- Keep provider-neutral domain and scoring code free of source-specific assumptions. Preserve stable
  identifiers and the relationships between domain objects.
- Keep data models focused on representation and invariants, not unrelated service behaviour. Use
  existing dataclasses and domain objects rather than adding wrappers without a concrete need.
- Prefer small pure functions for deterministic calculations where appropriate. Avoid unnecessary
  mutation and favour predictable results.
- When handling floating-point values, embeddings, scores, or weights, explicitly consider
  non-finite values and relevant numeric boundaries.
- Preserve conventional mathematical meanings in low-level utilities; apply application-specific
  normalisation in the appropriate higher-level scoring layer.
- Do not silently swallow lower-level errors unless the calling layer has an explicit recovery
  policy.
- Comments should explain intent, constraints, architecture, algorithms, or non-obvious behaviour;
  avoid comments that merely restate syntax.
