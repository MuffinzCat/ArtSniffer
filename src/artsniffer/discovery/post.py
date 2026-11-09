"""Provider-neutral records for discovered posts and their contained artwork."""

from dataclasses import dataclass


@dataclass
class DiscoveredPost:
    """Represent a discovered post while retaining its source and attribution metadata."""

    # Stable identity for this post within ArtSniffer.
    id: str
    # Identifies the configured discovery source that supplied the post.
    source_id: str
    # Stable identifier assigned to the post by its provider.
    source_post_id: str
    # Stable provider-specific identity for the post's creator or author.
    creator_id: str
    # Original provider-supplied URL used for attribution and navigation.
    url: str
    # Descriptive labels retained from the provider without reordering or deduplication.
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate the identifiers and attribution data for a discovered post."""
        if not self.id.strip():
            raise ValueError("Discovered post ID must not be empty or whitespace.")
        if not self.source_id.strip():
            raise ValueError("Source ID must not be empty or whitespace.")
        if not self.source_post_id.strip():
            raise ValueError("Source post ID must not be empty or whitespace.")
        if not self.creator_id.strip():
            raise ValueError("Creator ID must not be empty or whitespace.")
        if not self.url.strip():
            raise ValueError("URL must not be empty or whitespace.")
        if any(not tag.strip() for tag in self.tags):
            raise ValueError("Tag must not be empty or whitespace.")


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
