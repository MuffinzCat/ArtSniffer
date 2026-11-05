"""Tests for recommendation candidate eligibility."""

import pytest

from artsniffer.profiles.profile import RecommendationProfile
from artsniffer.recommendations.candidate import RecommendationCandidate
from artsniffer.recommendations.eligibility import (
    RecommendationEligibilityDecision,
    RecommendationEligibilityReason,
    evaluate_recommendation_eligibility,
    is_recommendation_eligible,
)


@pytest.mark.parametrize(
    ("eligible", "reason"),
    [
        (True, RecommendationEligibilityReason.ELIGIBLE),
        (False, RecommendationEligibilityReason.PROFILE_DISABLED),
        (False, RecommendationEligibilityReason.PROFILE_MISMATCH),
        (False, RecommendationEligibilityReason.BELOW_THRESHOLD),
    ],
)
def test_eligibility_decision_accepts_consistent_flag_and_reason(
    eligible: bool,
    reason: RecommendationEligibilityReason,
) -> None:
    """Every valid eligibility reason can be represented consistently."""

    decision = RecommendationEligibilityDecision(eligible=eligible, reason=reason)

    assert decision.eligible is eligible
    assert decision.reason is reason


@pytest.mark.parametrize(
    ("eligible", "reason"),
    [
        (False, RecommendationEligibilityReason.ELIGIBLE),
        (True, RecommendationEligibilityReason.PROFILE_DISABLED),
        (True, RecommendationEligibilityReason.PROFILE_MISMATCH),
        (True, RecommendationEligibilityReason.BELOW_THRESHOLD),
    ],
)
def test_eligibility_decision_rejects_contradictory_flag_and_reason(
    eligible: bool,
    reason: RecommendationEligibilityReason,
) -> None:
    """Contradictory eligibility and reason values are rejected."""

    with pytest.raises(ValueError) as error:
        RecommendationEligibilityDecision(eligible=eligible, reason=reason)

    assert str(error.value) == "Eligibility flag must agree with the eligibility reason."


@pytest.mark.parametrize(
    ("enabled", "profile_id", "threshold", "candidate_profile_id", "score", "eligible", "reason"),
    [
        (True, "cosy-foxes", 0.75, "cosy-foxes", 0.75, True, "eligible"),
        (False, "cosy-foxes", 0.75, "cosy-foxes", 0.9, False, "profile_disabled"),
        (False, "cosy-foxes", 0.75, "quiet-birds", 0.9, False, "profile_disabled"),
        (True, "cosy-foxes", 0.75, "quiet-birds", 0.9, False, "profile_mismatch"),
        (True, "cosy-foxes", 0.75, "cosy-foxes", 0.74, False, "below_threshold"),
        (True, "cosy-foxes", 0.0, "cosy-foxes", 0.0, True, "eligible"),
        (True, "cosy-foxes", 1.0, "cosy-foxes", 1.0, True, "eligible"),
    ],
)
def test_eligibility_decision_reports_stable_reason(
    enabled: bool,
    profile_id: str,
    threshold: float,
    candidate_profile_id: str,
    score: float,
    eligible: bool,
    reason: str,
) -> None:
    """Eligibility decisions report the existing rule that determined the result."""
    profile = RecommendationProfile(
        id=profile_id,
        name="Cosy Foxes",
        enabled=enabled,
        threshold=threshold,
    )
    candidate = RecommendationCandidate(
        profile_id=candidate_profile_id,
        artwork_id="artwork-001",
        score=score,
    )

    decision = evaluate_recommendation_eligibility(profile, candidate)

    assert decision == RecommendationEligibilityDecision(
        eligible=eligible,
        reason=RecommendationEligibilityReason(reason),
    )
    assert decision.reason.value == reason


def test_eligible_candidate_above_profile_threshold() -> None:
    """An enabled matching profile accepts a score above its threshold."""

    profile = RecommendationProfile(
        id="cosy-foxes",
        name="Cosy Foxes",
        threshold=0.75,
    )
    candidate = RecommendationCandidate(
        profile_id="cosy-foxes",
        artwork_id="artwork-001",
        score=0.76,
    )

    assert is_recommendation_eligible(profile, candidate) is True


def test_eligible_candidate_at_profile_threshold() -> None:
    """A score exactly at the profile threshold is eligible."""

    profile = RecommendationProfile(
        id="cosy-foxes",
        name="Cosy Foxes",
        threshold=0.75,
    )
    candidate = RecommendationCandidate(
        profile_id="cosy-foxes",
        artwork_id="artwork-001",
        score=0.75,
    )

    assert is_recommendation_eligible(profile, candidate) is True


def test_candidate_below_profile_threshold_is_not_eligible() -> None:
    """A matching candidate below the profile threshold is not eligible."""

    profile = RecommendationProfile(
        id="cosy-foxes",
        name="Cosy Foxes",
        threshold=0.75,
    )
    candidate = RecommendationCandidate(
        profile_id="cosy-foxes",
        artwork_id="artwork-001",
        score=0.74,
    )

    assert is_recommendation_eligible(profile, candidate) is False


def test_disabled_profile_does_not_accept_eligible_candidate() -> None:
    """A disabled profile never accepts a candidate, even when its score qualifies."""

    profile = RecommendationProfile(
        id="cosy-foxes",
        name="Cosy Foxes",
        enabled=False,
        threshold=0.75,
    )
    candidate = RecommendationCandidate(
        profile_id="cosy-foxes",
        artwork_id="artwork-001",
        score=0.9,
    )

    assert is_recommendation_eligible(profile, candidate) is False


def test_candidate_for_another_profile_is_not_eligible() -> None:
    """A candidate evaluated for another profile is not eligible here."""

    profile = RecommendationProfile(
        id="cosy-foxes",
        name="Cosy Foxes",
        threshold=0.5,
    )
    candidate = RecommendationCandidate(
        profile_id="quiet-birds",
        artwork_id="artwork-001",
        score=0.9,
    )

    assert is_recommendation_eligible(profile, candidate) is False


def test_zero_score_meets_zero_threshold() -> None:
    """A score of zero qualifies when the profile threshold is zero."""

    profile = RecommendationProfile(
        id="cosy-foxes",
        name="Cosy Foxes",
        threshold=0.0,
    )
    candidate = RecommendationCandidate(
        profile_id="cosy-foxes",
        artwork_id="artwork-001",
        score=0.0,
    )

    assert is_recommendation_eligible(profile, candidate) is True


def test_maximum_score_meets_maximum_threshold() -> None:
    """A score of one qualifies when the profile threshold is one."""

    profile = RecommendationProfile(
        id="cosy-foxes",
        name="Cosy Foxes",
        threshold=1.0,
    )
    candidate = RecommendationCandidate(
        profile_id="cosy-foxes",
        artwork_id="artwork-001",
        score=1.0,
    )

    assert is_recommendation_eligible(profile, candidate) is True


def test_eligibility_check_does_not_mutate_profile_or_candidate() -> None:
    """Checking eligibility leaves the profile and candidate unchanged."""

    profile = RecommendationProfile(
        id="cosy-foxes",
        name="Cosy Foxes",
        enabled=True,
        threshold=0.75,
    )
    candidate = RecommendationCandidate(
        profile_id="cosy-foxes",
        artwork_id="artwork-001",
        score=0.8,
    )
    profile_values = (profile.id, profile.name, profile.enabled, profile.threshold)
    candidate_values = (
        candidate.profile_id,
        candidate.artwork_id,
        candidate.score,
        candidate.components,
    )

    assert is_recommendation_eligible(profile, candidate) is True

    assert (profile.id, profile.name, profile.enabled, profile.threshold) == profile_values
    assert (
        candidate.profile_id,
        candidate.artwork_id,
        candidate.score,
        candidate.components,
    ) == candidate_values
