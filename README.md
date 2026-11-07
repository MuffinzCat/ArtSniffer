# ArtSniffer

ArtSniffer is a self-hosted personalised artwork discovery and recommendation service.

The goal is to learn a user's visual preferences from curated reference collections, discover new artwork from supported sources, and recommend relevant posts through services such as Discord and Telegram.

## Status

ArtSniffer is currently in early development.

The initial project foundation is being built before work begins on reference-library integration, artwork analysis, recommendation profiles, source monitoring, and delivery services.

## Current Domain Boundaries

The current domain primitives include subject-bound unconditional safety evaluation, profile
content-policy evaluation, service-level content permissions, analysis records and recommendation
scoring. They do not yet form an application pipeline.

`ServiceContentPermissions()` disables adult content by default. Its pure evaluator uses the
provider-neutral `ContentRating` vocabulary:

| Rating | Adult support disabled (default) | Adult support explicitly enabled |
|---|---|---|
| `UNKNOWN` | Rejected | Rejected |
| `GENERAL` | Permitted by the service | Permitted by the service |
| `MATURE` | Permitted by the service | Permitted by the service |
| `ADULT` | Rejected | Permitted by the service |

Service permissions are separate from profile preferences. A general profile still rejects MATURE
and ADULT, and a profile accepting ADULT does not enable service-wide adult support. Neither rating
policy can override unconditional safety or grant destination eligibility.

The intended processing order is:

```text
source metadata / labels -> unconditional safety -> service-level permissions
-> profile content policy -> expensive analysis -> recommendation scoring
-> recommendation eligibility -> destination eligibility -> delivery
```

Only an affirmative bound safety result exposes a `SafetyClearedSubject`. A future composed
pre-analysis boundary should require that clearance, preserve its artwork/content-version binding,
and stop on service rejection before evaluating profile policy. The standalone service and profile
evaluators are pure rating rules, not subject-bound authorisation to process content.

Gate composition and an analysis execution entry point are not implemented yet, so the intended
pipeline order is not yet enforced. Service permissions are only the first part of issue #36.
Full adult compliance, destination opt-in and platform-specific eligibility remain later work.

## Planned Recommendation Signals

Global whole-image embeddings are one complementary signal for visual, style and composition
similarity; they are not enough to capture component-level furry semantics such as characters,
interactions, species, clothing or pose. Furry-specific semantic analysis is another signal.
Authoritative source metadata (especially e621/e926 tags) remains distinct from generated concepts,
which retain model, version and confidence provenance. The intended architecture maps these inputs
to provider-neutral canonical traits and signals for separately explainable visual and semantic
scoring. Semantic analysis does not grant unconditional safety clearance. These semantic and
canonical-trait capabilities are planned, not yet implemented.

## Planned Features

ArtSniffer is planned to support:

- Multiple independent recommendation profiles.
- OneDrive-hosted reference artwork collections.
- Visual and semantic artwork similarity.
- Live discovery from supported artwork and social platforms.
- Discord and Telegram recommendation feeds.
- Profile-specific filtering, thresholds, and content controls.
- Recommendation feedback and preference learning.
- Artist affinity, discovery, novelty, and diversity controls.
- Duplicate and previously-seen artwork detection.
- Explainable recommendation scoring.
- Modular reference, source, recommendation, and delivery components.
- Optional content-rating modes with platform-appropriate safeguards.

The project is being designed as a self-hosted service with efficient CPU operation and minimal permanent storage of externally retrieved artwork.

## Development

ArtSniffer currently targets Python 3.12.

Development uses:

- `uv` for project and dependency management.
- Ruff for linting and formatting.
- Pyright for static type checking.
- pytest for automated testing.

## Local Benchmarks

Provider-neutral benchmark records live in `artsniffer.benchmark.models`, and timing runners live
in `artsniffer.benchmark.runner`. Production image analysers remain in `artsniffer.analysis`.

Keep local benchmark artwork in `benchmark-data/images/` with its original filenames, and keep
generated benchmark results within `benchmark-data/` too. Git ignores `benchmark-data/` directories
at any depth; artwork and results must never be committed. No `dataset.toml` format is defined yet.
Issue #62 tracks the broader multi-model furry-art benchmark.

The DINOv2 analyser uses `facebook/dinov2-small` and requires the optional `benchmark-dinov2`
dependency group. Run its tests with `uv run --group benchmark-dinov2 pytest` (or select that group
for the other development checks). Tests mock model loading and image access; they do not download
weights or read benchmark artwork. Constructing the real analyser may download uncached model files.

## Copyright and Usage

Copyright © 2026 Muffin. All rights reserved.

This repository is **source-available but not open source**.

No licence is granted to use, copy, modify, distribute, sublicense, or create derivative works from the source code in this repository except where permission is required by applicable law or provided by the applicable hosting platform's terms.

Viewing or forking this repository through GitHub does not grant a licence to use, modify, or redistribute the software outside the rights provided by GitHub's applicable terms.

If you would like permission to use any part of ArtSniffer, please contact the repository owner through GitHub.

See [`NOTICE.md`](NOTICE.md) for the full copyright and usage notice.