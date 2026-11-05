# ArtSniffer Copilot Instructions

## Project context

ArtSniffer is a self-hosted personalised artwork discovery and recommendation service, designed
around modular reference ingestion, source discovery, artwork analysis, recommendation and ranking,
persistence, and delivery layers. It aims to remain CPU-friendly and is under active, incremental
development in Python.

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
- Prefer small composable functions and services. Avoid abstractions for hypothetical needs and
  avoid redesigning existing models for unrelated features.
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
- Use British English in comments, documentation, and user-facing prose where natural.

## Tests and validation

- Add focused tests for new behaviour, including meaningful boundary conditions. Test public
  behaviour and use real ArtSniffer domain objects where practical.
- Use `pytest.mark.parametrize` for genuinely repetitive cases when it improves clarity,
  `pytest.approx` for floating-point comparisons, and exact message assertions for intentional
  validation behaviour.
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

- Favour CPU-friendly self-hosted designs. Avoid repeated image analysis or model inference, reuse
  expensive derived analysis where the architecture permits, and avoid loading unnecessary large
  datasets into memory.
- Consider algorithmic cost when comparing candidates across multiple profiles and references.
  Measure before introducing complex optimisations.
- Keep useful comments that explain intent, architecture, algorithms, policy boundaries, or
  non-obvious behaviour. Add comments when they materially help readers; avoid comments that merely
  restate syntax. Do not remove established intent or behaviour comments just to reduce comment
  count.

## Git behaviour

- Inspect Git status before and after work, respect the current branch, and do not switch branches
  unless explicitly requested.
- Do not commit, push, force-push, rebase, merge, create pull requests, or modify branch protection
  unless explicitly requested. Do not use destructive Git recovery commands without permission.
