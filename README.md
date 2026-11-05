# ArtSniffer

ArtSniffer is a self-hosted personalised artwork discovery and recommendation service.

The goal is to learn a user's visual preferences from curated reference collections, discover new artwork from supported sources, and recommend relevant posts through services such as Discord and Telegram.

## Status

ArtSniffer is currently in early development.

The initial project foundation is being built before work begins on reference-library integration, artwork analysis, recommendation profiles, source monitoring, and delivery services.

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

## Copyright and Usage

Copyright © 2026 Muffin. All rights reserved.

This repository is **source-available but not open source**.

No licence is granted to use, copy, modify, distribute, sublicense, or create derivative works from the source code in this repository except where permission is required by applicable law or provided by the applicable hosting platform's terms.

Viewing or forking this repository through GitHub does not grant a licence to use, modify, or redistribute the software outside the rights provided by GitHub's applicable terms.

If you would like permission to use any part of ArtSniffer, please contact the repository owner through GitHub.

See [`NOTICE.md`](NOTICE.md) for the full copyright and usage notice.