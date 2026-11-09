# ArtSniffer Copilot Instructions

## Project context

ArtSniffer is a personal, self-hosted hobby project for personalised artwork discovery and
recommendation. It is intended to remain understandable to a reasonably capable beginner; optimise
for code Muffin can understand and increasingly modify with guidance. The project is under active,
incremental development in Python and aims to remain CPU-friendly.

The current repository provides core domain records and recommendation-scoring primitives; it does
not yet implement the complete service pipeline or persistence and delivery systems. Treat the
broader layers described here as architectural direction, not existing behaviour. Do not claim or
depend on unimplemented features.

## Source of truth and architecture

- Inspect relevant implementation and tests before editing. Verify field names, validation,
  interfaces, and behaviour from source; follow repository patterns rather than assumptions.
- Never invent existing behaviour. If a material architectural ambiguity affects the requested
  change, stop and report it rather than silently redesigning neighbouring systems.
- Keep domain models focused and provider-neutral unless a model is explicitly provider-specific.
  Keep reference ingestion, source discovery, analysis, recommendation/ranking, persistence, and
  delivery responsibilities modular.
- Keep delivery behaviour out of recommendation models and source-specific behaviour out of
  provider-neutral scoring logic. Preserve provenance for externally sourced data.
- Prefer straightforward Python, plain names, and direct control flow. Keep structure proportionate
  to behaviour; avoid speculative architecture, enterprise-style frameworks, and future-proofing
  without a concrete need.
- Avoid excessive files, packages, layers, wrappers, forwarding modules, and one-caller abstractions.
  Keep closely related code together when that reduces navigation, but do not turn a focused module
  into a miscellaneous collection. Functions, services, and modules are useful when they clarify
  real responsibilities; making them small or composable is not a goal in itself.
- Design expensive artwork analysis to be reusable per relevant artwork and model version, rather
  than repeatedly recomputing it across profiles. Do not imply that caching or persistence already
  exists.

## Scope and dependencies

- Implement only the requested behaviour and respect explicit file and scope limits. Avoid
  opportunistic refactors, unrelated formatting or cleanup, and combining distinct features.
- Report out-of-scope issues instead of silently fixing them.
- Prefer the standard library when sufficient. Do not install packages merely to complete a task.
  Add or change dependencies only when explicitly requested or clearly justified, and report the
  reason. Use the existing `uv` workflow.

## Python and style

- Support Python 3.12 or newer, as configured by `pyproject.toml` and `.python-version`. Use modern
  syntax compatible with that minimum.
- Use type annotations and dataclasses where appropriate and established. Write clear names,
  straightforward control flow, and concise module, class, and function docstrings.
- Validate domain invariants explicitly. Preserve stable, field-specific `ValueError` messages when
  they form part of a model or function's public contract.
- Follow Ruff's configured 100-character line length. Do not add another formatter, linter, type
  checker, or test framework.
- Write concise comments and docstrings that explain intent rather than restating syntax or names.
  Use natural British English and avoid formal, repetitive, bureaucratic, or generated-looking prose.

## Tests and validation

- Add focused tests for meaningful behaviour, relevant boundary conditions, safety, compatibility,
  and regressions. Test public behaviour and use real ArtSniffer domain objects where practical.
- Use `pytest.mark.parametrize` for genuinely repetitive cases when it improves clarity and
  `pytest.approx` for floating-point comparisons. Assert exact wording only when it is an
  intentional public contract.
- Do not duplicate validation tests owned by another model or function, or test behaviour the unit
  under test does not own. Include a regression test for bug fixes where practical.
- After code changes, run applicable checks using the repository's existing commands:
  `uv run ruff format --check .`, `uv run ruff check .`, `uv run pyright`, and `uv run pytest`.
  Also run `git diff --check`. Do not install substitute tools if expected development tools are
  unavailable.
- Before reporting completion, inspect `git status --short --untracked-files=all`, identify
  unexpected files or changes, and state which checks actually ran. Never claim an unrun check
  passed. For documentation-only changes, use scope-appropriate validation.

## Security and content boundaries

- Never commit credentials, tokens, API keys, passwords, private keys, session data, or other
  secrets. Use existing environment or configuration mechanisms rather than hardcoding secrets;
  never print secrets in logs, test output, commit messages, or generated documentation.
- Treat externally supplied content and metadata as untrusted. Request no broader external-service
  permissions than needed.
- Preserve source-provided content ratings and moderation metadata where available. General
  profiles must not silently permit higher-rated content. Mature/adult support must be explicit and
  opt-in, separate from general destinations, and subject to source/platform and destination
  eligibility. Always exclude prohibited sexual content, including content involving minors.
- Source adapters must respect supported APIs, moderation metadata, rate limits, and access rules.
  Do not scrape or work around policies to gain access to data.

## Performance and maintainability

- Favour CPU-friendly self-hosted designs. Consider repeated work, filesystem I/O, memory growth,
  database access, and algorithmic cost, including when comparing candidates across multiple
  profiles and references. Avoid repeated image analysis or model inference; reuse expensive
  derived analysis where the architecture permits and avoid loading unnecessary large datasets
  into memory.
- Measure before introducing complicated performance optimisations.
- Keep useful comments that explain intent, architecture, algorithms, policy boundaries, or
  non-obvious behaviour. Add comments when they materially help readers; avoid comments that merely
  restate syntax. Do not remove established intent or behaviour comments just to reduce comment
  count.

## Git behaviour

- Inspect Git status before and after work, respect the current branch, and do not switch branches
  unless explicitly requested.
- Do not commit, push, force-push, rebase, merge, create pull requests, or modify branch protection
  unless explicitly requested. Do not use destructive Git recovery commands without permission.
