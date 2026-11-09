"""Define the provider-neutral profile-side content-rating policy.

The policy declares what a profile is willing to accept, independently of source or provider
metadata, recommendation scoring, destination eligibility, and the unconditional
prohibited-content safety gate. The safety gate is not configurable through this policy. This
module performs no filtering; deciding whether a candidate rating satisfies a policy belongs to a
later policy-decision function.
"""

from dataclasses import dataclass
from enum import StrEnum

from artsniffer.content.rating import (
    ContentRating,
    content_rating_rank,
    is_known_content_rating,
)


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


class ContentPolicyReason(StrEnum):
    """Stable machine-readable reason for a content-policy decision."""

    ALLOWED = "allowed"
    RATING_UNKNOWN = "rating_unknown"
    RATING_ABOVE_MAXIMUM = "rating_above_maximum"
    ADULT_REQUIRED = "adult_required"


@dataclass(frozen=True)
class ContentPolicyDecision:
    """Immutable content-policy outcome; ``allowed`` holds exactly when the reason is ALLOWED."""

    allowed: bool
    reason: ContentPolicyReason

    def __post_init__(self) -> None:
        """Reject a flag that contradicts the reason."""
        if self.allowed != (self.reason is ContentPolicyReason.ALLOWED):
            raise ValueError("Content policy allowed flag must agree with the decision reason.")


def _content_policy_decision(reason: ContentPolicyReason) -> ContentPolicyDecision:
    return ContentPolicyDecision(
        allowed=reason is ContentPolicyReason.ALLOWED,
        reason=reason,
    )


def evaluate_content_policy(
    policy: ProfileContentPolicy,
    rating: ContentRating,
) -> ContentPolicyDecision:
    """Evaluate one normalised rating against one profile content policy.

    ``UNKNOWN`` is always rejected first. ``MAX_RATING`` allows ratings up to and including the
    maximum, so a ``MAX_RATING`` policy of ``ADULT`` is not adult-only. ``ADULT_ONLY`` requires an
    affirmative ``ADULT`` rating.
    """
    if not is_known_content_rating(rating):
        return _content_policy_decision(ContentPolicyReason.RATING_UNKNOWN)

    if policy.mode is ProfileContentPolicyMode.ADULT_ONLY:
        if rating is ContentRating.ADULT:
            return _content_policy_decision(ContentPolicyReason.ALLOWED)
        return _content_policy_decision(ContentPolicyReason.ADULT_REQUIRED)

    # The policy validates that MAX_RATING always carries a known max rating.
    assert policy.max_rating is not None
    if content_rating_rank(rating) > content_rating_rank(policy.max_rating):
        return _content_policy_decision(ContentPolicyReason.RATING_ABOVE_MAXIMUM)
    return _content_policy_decision(ContentPolicyReason.ALLOWED)


def is_content_allowed(policy: ProfileContentPolicy, rating: ContentRating) -> bool:
    """Return whether the rating satisfies the policy."""
    return evaluate_content_policy(policy, rating).allowed
