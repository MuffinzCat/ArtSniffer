---
description: "Use when writing or changing pytest tests in tests/."
applyTo: "tests/**/*.py"
---

# Test guidance

- Test public behaviour rather than private implementation details. Use real ArtSniffer dataclasses
  and domain objects where practical, with explicit inputs that make expected behaviour clear.
- Cover meaningful normal, boundary, and invalid cases. Use `pytest.approx` for floating-point
  comparisons and `pytest.mark.parametrize` for repetitive cases when it improves clarity.
- Assert exact `ValueError` messages when they intentionally form part of the public validation
  contract. Keep each model or function's tests focused on behaviour it owns; avoid repeating
  validation already comprehensively covered by a dependency.
- When a higher-level operation is expected to propagate a lower-level error, test that propagation
  where it matters.
- Verify non-mutation for pure or deterministic operations when relevant, and test ordering
  independence when the algorithm is expected to be order-independent.
- Add focused regression tests for bug fixes where practical. Avoid excessive mocking when plain
  domain objects make clearer tests, and do not weaken assertions merely to make a failing
  implementation pass.
