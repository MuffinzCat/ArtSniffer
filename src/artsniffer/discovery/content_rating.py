"""Provider-neutral normalised content-rating records for discovered artwork.

A record is separate from ``DiscoveredArtwork``. Absence of a record means no normalised rating
record currently exists for the artwork; a record whose rating is ``ContentRating.UNKNOWN`` means
the rating-normalisation process produced no trustworthy known classification. Raw moderation
labels, semantic tags and prohibited-content safety decisions are separate concepts.
"""

from dataclasses import dataclass
from enum import StrEnum

from artsniffer.content.rating import ContentRating
from artsniffer.discovery.post import DiscoveredArtwork, DiscoveredPost


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


class DiscoveredArtworkContentRatingResolutionReason(StrEnum):
    """Stable machine-readable reason for a content-rating relationship resolution."""

    RESOLVED = "resolved"
    ARTWORK_MISMATCH = "artwork_mismatch"
    POST_MISMATCH = "post_mismatch"
    SOURCE_MISMATCH = "source_mismatch"


@dataclass(frozen=True)
class DiscoveredArtworkContentRatingResolution:
    """Immutable relationship outcome; ``resolved`` holds exactly for the RESOLVED reason."""

    resolved: bool
    reason: DiscoveredArtworkContentRatingResolutionReason

    def __post_init__(self) -> None:
        """Reject a success flag that contradicts the resolution reason."""
        if self.resolved != (
            self.reason is DiscoveredArtworkContentRatingResolutionReason.RESOLVED
        ):
            raise ValueError("Resolution flag must agree with the resolution reason.")


def _rating_resolution(
    reason: DiscoveredArtworkContentRatingResolutionReason,
) -> DiscoveredArtworkContentRatingResolution:
    return DiscoveredArtworkContentRatingResolution(
        resolved=reason is DiscoveredArtworkContentRatingResolutionReason.RESOLVED,
        reason=reason,
    )


def resolve_discovered_artwork_content_rating(
    rating: DiscoveredArtworkContentRating,
    artwork: DiscoveredArtwork,
    post: DiscoveredPost,
) -> DiscoveredArtworkContentRatingResolution:
    """Resolve rating-to-artwork, artwork-to-post, and rating-to-source relationships in order."""
    if rating.artwork_id != artwork.id:
        return _rating_resolution(DiscoveredArtworkContentRatingResolutionReason.ARTWORK_MISMATCH)
    if artwork.post_id != post.id:
        return _rating_resolution(DiscoveredArtworkContentRatingResolutionReason.POST_MISMATCH)
    if rating.source_id != post.source_id:
        return _rating_resolution(DiscoveredArtworkContentRatingResolutionReason.SOURCE_MISMATCH)
    return _rating_resolution(DiscoveredArtworkContentRatingResolutionReason.RESOLVED)


def is_discovered_artwork_content_rating_resolved(
    rating: DiscoveredArtworkContentRating,
    artwork: DiscoveredArtwork,
    post: DiscoveredPost,
) -> bool:
    """Return whether the rating is associated with this artwork and its containing post."""
    return resolve_discovered_artwork_content_rating(rating, artwork, post).resolved
