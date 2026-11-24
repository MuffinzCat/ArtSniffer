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
    # Optional verified creator attribution.
    # None when the source does not provide trustworthy identity.
    creator_id: str | None
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
        if self.creator_id is not None and not self.creator_id.strip():
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
    # Exact content identity once the artwork bytes have been retrieved and hashed.
    # None means the artwork has been discovered but its exact content is not known yet.
    content_hash: str | None = None

    def __post_init__(self) -> None:
        """Validate the identifiers needed to track discovered artwork."""
        if not self.id.strip():
            raise ValueError("Discovered artwork ID must not be empty or whitespace.")
        if not self.post_id.strip():
            raise ValueError("Post ID must not be empty or whitespace.")
        if not self.source_item_id.strip():
            raise ValueError("Source item ID must not be empty or whitespace.")
        if self.content_hash is not None and not self.content_hash.strip():
            raise ValueError("Content hash must not be empty or whitespace.")


@dataclass(frozen=True)
class DiscoveredPostProvenance:
    """Preserve the provider's exact observed version of a discovered post."""

    post_id: str
    source_version_id: str

    def __post_init__(self) -> None:
        """Validate the identifiers for discovered post provenance."""
        if not self.post_id.strip():
            raise ValueError("Post ID must not be empty or whitespace.")
        if not self.source_version_id.strip():
            raise ValueError("Source version ID must not be empty or whitespace.")


@dataclass(frozen=True)
class DiscoveredArtworkSourceMetadata:
    """Preserve provider metadata for one discovered artwork item."""

    artwork_id: str
    source_media_id: str
    alt_text: str

    def __post_init__(self) -> None:
        """Validate the identifiers for discovered artwork source metadata."""
        if not self.artwork_id.strip():
            raise ValueError("Artwork ID must not be empty or whitespace.")
        if not self.source_media_id.strip():
            raise ValueError("Source media ID must not be empty or whitespace.")


@dataclass(frozen=True)
class DiscoveredSourceLabel:
    """Preserve provider moderation labels as source evidence, without safety interpretation."""

    src: str
    uri: str
    cid: str | None
    val: str
    ver: int | None
    neg: bool | None
    cts: str
    exp: str | None
    hydrated: bool

    def __post_init__(self) -> None:
        """Validate the required fields for provider-supplied label provenance."""
        if not self.src.strip():
            raise ValueError("Label source must not be empty or whitespace.")
        if not self.uri.strip():
            raise ValueError("Label URI must not be empty or whitespace.")
        if self.cid is not None and not self.cid.strip():
            raise ValueError("Label CID must not be empty or whitespace.")
        if not self.val.strip():
            raise ValueError("Label value must not be empty or whitespace.")
        if not self.cts.strip():
            raise ValueError("Label timestamp must not be empty or whitespace.")
        if self.exp is not None and not self.exp.strip():
            raise ValueError("Label expiry must not be empty or whitespace.")
