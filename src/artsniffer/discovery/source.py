"""Configured sources for discovering artwork posts."""

from dataclasses import dataclass


@dataclass
class DiscoverySource:
    """Configure a provider-neutral source of discovered posts."""

    # Stable identity for this configured source within ArtSniffer.
    id: str
    # Identifies the provider adapter used to discover posts.
    kind: str
    # Keeps source configuration available while discovery is paused.
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate the identifiers needed to configure a discovery source."""
        if not self.id.strip():
            raise ValueError("Discovery source ID must not be empty or whitespace.")
        if not self.kind.strip():
            raise ValueError("Discovery source kind must not be empty or whitespace.")
