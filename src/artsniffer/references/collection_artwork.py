"""Weighted links between reference collections and artwork."""

from dataclasses import dataclass


@dataclass
class CollectionArtworkLink:
    """Record an artwork's membership and influence within a reference collection."""

    # Identifies the collection receiving this artwork.
    collection_id: str
    # Identifies the artwork belonging to the collection.
    artwork_id: str
    # Sets this artwork's influence in the collection; 1.0 is normal influence.
    weight: float = 1.0

    def __post_init__(self) -> None:
        """Validate collection membership and its influence weight."""
        if not self.collection_id.strip():
            raise ValueError("Collection ID must not be empty or whitespace.")
        if not self.artwork_id.strip():
            raise ValueError("Artwork ID must not be empty or whitespace.")
        if self.weight <= 0.0:
            raise ValueError("Weight must be greater than 0.0.")
