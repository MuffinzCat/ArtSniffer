"""Tests for recommendation candidate eligibility."""

from artsniffer.profile import RecommendationProfile
from artsniffer.recommendation import RecommendationCandidate
from artsniffer.recommendation_eligibility import is_recommendation_eligible


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
