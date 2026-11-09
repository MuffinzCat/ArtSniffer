from dataclasses import dataclass


@dataclass
class ReferenceCollection:
    # Stable identity for this collection across configuration changes.
    id: str
    # Name shown to the user when selecting or managing collections.
    name: str
    # Identifies the configured source that supplies this collection.
    source_id: str
    # Controls whether this collection contributes reference artwork.
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate collection configuration immediately after initialisation.

        Invalid collections are rejected before entering the rest of the application.
        """
        if not self.id.strip():
            raise ValueError("Collection ID must not be empty or whitespace.")
        if not self.name.strip():
            raise ValueError("Collection name must not be empty or whitespace.")
        if not self.source_id.strip():
            raise ValueError("Collection source ID must not be empty or whitespace.")


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
