"""Define ArtSniffer's canonical provider-neutral content-rating vocabulary.

Providers will later normalise their own metadata into this vocabulary. Provider moderation
labels, semantic tags or traits, and content ratings remain separate concepts. Prohibited-content
safety decisions are not content ratings and belong to a separate unconditional safety gate.
"""

from enum import StrEnum


class ContentRating(StrEnum):
    """ArtSniffer-owned, provider-neutral content rating.

    ``UNKNOWN`` means no trustworthy normalised classification is available. It is neither
    ``GENERAL`` nor ``ADULT`` and sits outside the severity ordering. Severity is only exposed
    through ``content_rating_rank``; enum declaration order carries no meaning.
    """

    UNKNOWN = "unknown"
    GENERAL = "general"
    MATURE = "mature"
    ADULT = "adult"


_CONTENT_RATING_RANKS: dict[ContentRating, int] = {
    ContentRating.GENERAL: 0,
    ContentRating.MATURE: 1,
    ContentRating.ADULT: 2,
}


def is_known_content_rating(rating: ContentRating) -> bool:
    """Return whether the rating is an affirmative classification rather than ``UNKNOWN``."""
    return rating is not ContentRating.UNKNOWN


def content_rating_rank(rating: ContentRating) -> int:
    """Return the severity rank of a known rating; higher values are more restricted.

    Raises:
        ValueError: If the rating is ``UNKNOWN``, which has no severity rank.
    """
    if rating is ContentRating.UNKNOWN:
        raise ValueError("Unknown content rating has no severity rank.")
    return _CONTENT_RATING_RANKS[rating]
