"""Provider-neutral identity for artwork contained in discovered posts."""

from dataclasses import dataclass


@dataclass
class DiscoveredArtwork:
    """Identify an individual artwork item separately from its containing post."""

    # Stable identity for this artwork item within ArtSniffer.
    id: str
    # Identifies the post containing this artwork item.
    post_id: str
    # Stable identifier assigned to this individual media item by its provider.
    source_item_id: str
    # Content-derived identity used to compare artwork across provider locations.
    content_hash: str

    def __post_init__(self) -> None:
        """Validate the identifiers needed to track discovered artwork."""
        if not self.id.strip():
            raise ValueError("Discovered artwork ID must not be empty or whitespace.")
        if not self.post_id.strip():
            raise ValueError("Post ID must not be empty or whitespace.")
        if not self.source_item_id.strip():
            raise ValueError("Source item ID must not be empty or whitespace.")
        if not self.content_hash.strip():
            raise ValueError("Content hash must not be empty or whitespace.")
