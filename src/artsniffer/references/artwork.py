"""Provider-neutral artwork records."""

from dataclasses import dataclass


@dataclass
class ArtworkRecord:
    """Identify artwork independently of the provider location that supplied it."""

    # Stable identity used to refer to this artwork within ArtSniffer.
    id: str
    # Identifies the configured source that supplied the artwork.
    source_id: str
    # Stable identifier assigned to the item by its provider.
    source_item_id: str
    # Content-derived identity for recognising unchanged or duplicate artwork.
    content_hash: str

    def __post_init__(self) -> None:
        """Reject artwork records without the identifiers needed to track their content."""
        if not self.id.strip():
            raise ValueError("Artwork ID must not be empty or whitespace.")
        if not self.source_id.strip():
            raise ValueError("Source ID must not be empty or whitespace.")
        if not self.source_item_id.strip():
            raise ValueError("Source item ID must not be empty or whitespace.")
        if not self.content_hash.strip():
            raise ValueError("Content hash must not be empty or whitespace.")
