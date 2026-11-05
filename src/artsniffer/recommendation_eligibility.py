"""Determine whether scored recommendation candidates qualify for a profile."""

from dataclasses import dataclass
from enum import StrEnum

from artsniffer.profiles.profile import RecommendationProfile
from artsniffer.recommendation import RecommendationCandidate


class RecommendationEligibilityReason(StrEnum):
    """Stable machine-readable reasons for a recommendation eligibility decision."""

    ELIGIBLE = "eligible"
    PROFILE_DISABLED = "profile_disabled"
    PROFILE_MISMATCH = "profile_mismatch"
    BELOW_THRESHOLD = "below_threshold"


@dataclass(frozen=True)
class RecommendationEligibilityDecision:
    """Represent whether a candidate qualifies and the rule determining the result."""

    eligible: bool
    reason: RecommendationEligibilityReason

    def __post_init__(self) -> None:
        """Reject eligibility flags that contradict the decision reason."""
        if self.eligible != (self.reason is RecommendationEligibilityReason.ELIGIBLE):
            raise ValueError("Eligibility flag must agree with the eligibility reason.")


def evaluate_recommendation_eligibility(
    profile: RecommendationProfile,
    candidate: RecommendationCandidate,
) -> RecommendationEligibilityDecision:
    """Return whether an enabled profile accepts a matching candidate's score and why."""
    if not profile.enabled:
        return RecommendationEligibilityDecision(
            eligible=False,
            reason=RecommendationEligibilityReason.PROFILE_DISABLED,
        )
    if candidate.profile_id != profile.id:
        return RecommendationEligibilityDecision(
            eligible=False,
            reason=RecommendationEligibilityReason.PROFILE_MISMATCH,
        )
    if candidate.score < profile.threshold:
        return RecommendationEligibilityDecision(
            eligible=False,
            reason=RecommendationEligibilityReason.BELOW_THRESHOLD,
        )
    return RecommendationEligibilityDecision(
        eligible=True,
        reason=RecommendationEligibilityReason.ELIGIBLE,
    )


def is_recommendation_eligible(
    profile: RecommendationProfile,
    candidate: RecommendationCandidate,
) -> bool:
    """Return whether an enabled profile accepts this matching candidate's score."""
    return evaluate_recommendation_eligibility(profile, candidate).eligible
