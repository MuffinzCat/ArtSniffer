"""Define the provider-neutral profile-side content-rating policy.

The policy declares what a profile is willing to accept, independently of source or provider
metadata, recommendation scoring, destination eligibility, and the unconditional
prohibited-content safety gate. The safety gate is not configurable through this policy. This
module performs no filtering; deciding whether a candidate rating satisfies a policy belongs to a
later policy-decision function.
"""

from dataclasses import dataclass
from enum import StrEnum

from artsniffer.content.rating import ContentRating


class ProfileContentPolicyMode(StrEnum):
    """How a profile constrains content ratings.

    ``MAX_RATING`` declares the highest known rating a profile may accept: ``GENERAL`` permits only
    ``GENERAL``, ``MATURE`` permits ``GENERAL`` and ``MATURE``, and ``ADULT`` permits ``GENERAL``,
    ``MATURE`` and ``ADULT``.

    ``ADULT_ONLY`` represents an explicit policy requiring affirmative ``ADULT`` classification. It
    is distinct from ``MAX_RATING`` with ``ADULT`` and does not itself enable global adult support,
    which remains a later service-configuration concern.
    """

    MAX_RATING = "max_rating"
    ADULT_ONLY = "adult_only"


@dataclass(frozen=True)
class ProfileContentPolicy:
    """Immutable, validated profile content-rating policy.

    ``UNKNOWN`` is never a valid maximum rating. How unknown or unrated candidates are treated is
    decided by the later policy-decision function, not by this value object.
    """

    mode: ProfileContentPolicyMode
    max_rating: ContentRating | None = None

    def __post_init__(self) -> None:
        """Reject contradictory or incomplete mode and rating combinations."""
        if self.mode is ProfileContentPolicyMode.MAX_RATING:
            if self.max_rating is None:
                raise ValueError("Max-rating content policy requires a max rating.")
            if self.max_rating is ContentRating.UNKNOWN:
                raise ValueError("Max-rating content policy must not use an unknown max rating.")
        elif self.max_rating is not None:
            raise ValueError("Adult-only content policy must not define a max rating.")


def default_profile_content_policy() -> ProfileContentPolicy:
    """Return a new safe-default policy: accept known ``GENERAL``-rated content at most.

    This does not accept unknown or unrated content.
    """
    return ProfileContentPolicy(
        mode=ProfileContentPolicyMode.MAX_RATING,
        max_rating=ContentRating.GENERAL,
    )
