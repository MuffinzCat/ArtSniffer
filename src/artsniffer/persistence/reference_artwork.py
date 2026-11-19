"""Storage-neutral interface for persistent reference artwork state."""

from collections.abc import Sequence
from typing import Protocol

from artsniffer.references.artwork import ArtworkRecord


class ReferenceArtworkStore(Protocol):
    def get_for_source(self, source_id: str) -> Sequence[ArtworkRecord]:
        """Retrieve all artwork records for a given source ID."""
        ...

    def replace_for_source(self, source_id: str, artworks: Sequence[ArtworkRecord]) -> None:
        """Replace all artwork records for a given source ID with the provided sequence."""
        ...
