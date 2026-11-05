---
name: artsniffer-domain-change
description: "Use when adding or modifying ArtSniffer domain models, relationships, invariants, validation, recommendation or scoring primitives, or other provider-neutral domain behaviour."
---

# ArtSniffer Domain Change

Use this workflow for focused changes to ArtSniffer's domain records and provider-neutral behaviour.
Follow the repository and applicable path-specific instructions; do not assume architectural
direction described there is already implemented.

## Procedure

1. Inspect the directly affected model or function.
2. Inspect its related tests.
3. Inspect adjacent domain objects and their relationships.
4. Establish which layer owns each invariant and validation rule.
5. Identify existing public behaviour and error contracts.
6. Make the smallest coherent domain change that meets the requested behaviour.
7. Add focused behavioural tests for the change and meaningful boundaries.
8. Check interactions with neighbouring domain objects.
9. Check for regressions and accidental architecture leakage.
10. Use the repository validation workflow before completion.

## Domain considerations

- Preserve stable identifiers and relationships. Avoid duplicating validation owned by another
  model or function.
- Keep provider-specific assumptions out of provider-neutral models and scoring; preserve source
  provenance where relevant. Keep delivery behaviour out of recommendation and domain models.
- Treat intentional `ValueError` messages established by tests as public contracts.
- Consider non-finite floating-point values when accepting scores, weights, embeddings, or other
  numeric data.
- Preserve conventional mathematical meaning in low-level utilities. Apply ArtSniffer-specific
  score normalisation at the appropriate higher layer.
- Prefer deterministic, non-mutating calculations where appropriate. Do not swallow lower-level
  errors without an explicit recovery policy.
- Avoid speculative abstractions for future features.
- If a material architectural decision is unresolved, stop and surface the ambiguity rather than
  silently redesigning surrounding models.
