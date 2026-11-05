"""Provider-neutral normalised content-rating records for discovered artwork.

A record is separate from ``DiscoveredArtwork``. Absence of a record means no normalised rating
record currently exists for the artwork; a record whose rating is ``ContentRating.UNKNOWN`` means
the rating-normalisation process produced no trustworthy known classification. Raw moderation
labels, semantic tags and prohibited-content safety decisions are separate concepts.
"""

from dataclasses import dataclass

from artsniffer.content.rating import ContentRating


@dataclass(frozen=True)
class DiscoveredArtworkContentRating:
    """Represent one normalised source content rating for one discovered artwork item."""

    # Identifies the DiscoveredArtwork whose content is classified.
    artwork_id: str
    # Identifies the DiscoverySource whose metadata or normalisation produced this rating.
    source_id: str
    # ArtSniffer's canonical normalised content rating.
    rating: ContentRating

    def __post_init__(self) -> None:
        """Validate the identifiers of a content-rating record."""
        if not self.artwork_id.strip():
            raise ValueError("Discovered artwork ID must not be empty or whitespace.")
        if not self.source_id.strip():
            raise ValueError("Content rating source ID must not be empty or whitespace.")


def unknown_discovered_artwork_content_rating(
    artwork_id: str,
    source_id: str,
) -> DiscoveredArtworkContentRating:
    """Return a new record explicitly classifying the artwork as ``ContentRating.UNKNOWN``."""
    return DiscoveredArtworkContentRating(
        artwork_id=artwork_id,
        source_id=source_id,
        rating=ContentRating.UNKNOWN,
    )
