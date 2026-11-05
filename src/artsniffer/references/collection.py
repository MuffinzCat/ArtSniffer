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
