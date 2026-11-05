"""Decide whether a normalised content rating satisfies a profile content policy.

This pure, provider-neutral decision runs before expensive analysis, recommendation scoring and
``RecommendationEligibilityDecision``. It is separate from the unconditional prohibited-content
safety gate (which conceptually runs first and cannot be configured or overridden here), global
adult-support enablement, source/provider normalisation, and destination eligibility.
"""

from dataclasses import dataclass
from enum import StrEnum

from artsniffer.content_rating import ContentRating, content_rating_rank, is_known_content_rating
from artsniffer.profile_content_policy import ProfileContentPolicy, ProfileContentPolicyMode


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


def _decision(reason: ContentPolicyReason) -> ContentPolicyDecision:
    return ContentPolicyDecision(allowed=reason is ContentPolicyReason.ALLOWED, reason=reason)


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
        return _decision(ContentPolicyReason.RATING_UNKNOWN)

    if policy.mode is ProfileContentPolicyMode.ADULT_ONLY:
        if rating is ContentRating.ADULT:
            return _decision(ContentPolicyReason.ALLOWED)
        return _decision(ContentPolicyReason.ADULT_REQUIRED)

    # The policy validates that MAX_RATING always carries a known max rating.
    assert policy.max_rating is not None
    if content_rating_rank(rating) > content_rating_rank(policy.max_rating):
        return _decision(ContentPolicyReason.RATING_ABOVE_MAXIMUM)
    return _decision(ContentPolicyReason.ALLOWED)


def is_content_allowed(policy: ProfileContentPolicy, rating: ContentRating) -> bool:
    """Return whether the rating satisfies the policy."""
    return evaluate_content_policy(policy, rating).allowed
