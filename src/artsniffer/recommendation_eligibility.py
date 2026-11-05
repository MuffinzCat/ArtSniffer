"""Determine whether scored recommendation candidates qualify for a profile."""

from artsniffer.profile import RecommendationProfile
from artsniffer.recommendation import RecommendationCandidate


def is_recommendation_eligible(
    profile: RecommendationProfile,
    candidate: RecommendationCandidate,
) -> bool:
    """Return whether an enabled profile accepts this matching candidate's score."""
    return (
        profile.enabled
        and candidate.profile_id == profile.id
        and candidate.score >= profile.threshold
    )
