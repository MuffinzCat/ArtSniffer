"""Resolve the integrity and provenance of a discovered artwork content rating."""

from dataclasses import dataclass
from enum import StrEnum

from artsniffer.discovery.artwork import DiscoveredArtwork
from artsniffer.discovery.content_rating import DiscoveredArtworkContentRating
from artsniffer.discovery.post import DiscoveredPost


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


def _decision(
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
        return _decision(DiscoveredArtworkContentRatingResolutionReason.ARTWORK_MISMATCH)
    if artwork.post_id != post.id:
        return _decision(DiscoveredArtworkContentRatingResolutionReason.POST_MISMATCH)
    if rating.source_id != post.source_id:
        return _decision(DiscoveredArtworkContentRatingResolutionReason.SOURCE_MISMATCH)
    return _decision(DiscoveredArtworkContentRatingResolutionReason.RESOLVED)


def is_discovered_artwork_content_rating_resolved(
    rating: DiscoveredArtworkContentRating,
    artwork: DiscoveredArtwork,
    post: DiscoveredPost,
) -> bool:
    """Return whether the rating is associated with this artwork and its containing post."""
    return resolve_discovered_artwork_content_rating(rating, artwork, post).resolved
