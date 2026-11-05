"""Tests for already-scored recommendation candidates."""

import pytest

from artsniffer.recommendation import RecommendationCandidate
from artsniffer.recommendation_score import RecommendationScoreComponent


def test_recommendation_candidate_preserves_identifiers_and_score() -> None:
    """A candidate should preserve its profile, artwork, and final score."""

    candidate = RecommendationCandidate(
        profile_id="cosy-foxes",
        artwork_id="artwork-001",
        score=0.72,
    )

    assert candidate.profile_id == "cosy-foxes"
    assert candidate.artwork_id == "artwork-001"
    assert candidate.score == 0.72


def test_recommendation_candidate_defaults_to_no_components() -> None:
    """Components should default to an empty tuple when no breakdown is supplied."""

    candidate = RecommendationCandidate(
        profile_id="cosy-foxes",
        artwork_id="artwork-001",
        score=0.72,
    )

    assert candidate.components == ()


def test_recommendation_candidate_preserves_component_order() -> None:
    """Explicit score components should be retained in their supplied order."""

    components = (
        RecommendationScoreComponent(name="semantic similarity", score=0.8),
        RecommendationScoreComponent(name="visual similarity", score=0.6),
    )
    candidate = RecommendationCandidate(
        profile_id="cosy-foxes",
        artwork_id="artwork-001",
        score=0.72,
        components=components,
    )

    assert candidate.components == components
    assert candidate.components[0].name == "semantic similarity"
    assert candidate.components[1].name == "visual similarity"


@pytest.mark.parametrize("score", [0.0, 0.42, 1.0])
def test_recommendation_candidate_accepts_finite_normalised_score(
    score: float,
) -> None:
    """Finite scores from zero to one inclusive should be accepted."""

    candidate = RecommendationCandidate(
        profile_id="cosy-foxes",
        artwork_id="artwork-001",
        score=score,
    )

    assert candidate.score == score


@pytest.mark.parametrize("invalid_profile_id", ["", " ", "   "])
def test_recommendation_candidate_rejects_empty_or_whitespace_profile_id(
    invalid_profile_id: str,
) -> None:
    """Profile IDs must contain at least one non-whitespace character."""

    with pytest.raises(ValueError) as error:
        RecommendationCandidate(
            profile_id=invalid_profile_id,
            artwork_id="artwork-001",
            score=0.72,
        )

    assert str(error.value) == "Profile ID must not be empty or whitespace."


@pytest.mark.parametrize("invalid_artwork_id", ["", " ", "   "])
def test_recommendation_candidate_rejects_empty_or_whitespace_artwork_id(
    invalid_artwork_id: str,
) -> None:
    """Artwork IDs must contain at least one non-whitespace character."""

    with pytest.raises(ValueError) as error:
        RecommendationCandidate(
            profile_id="cosy-foxes",
            artwork_id=invalid_artwork_id,
            score=0.72,
        )

    assert str(error.value) == "Artwork ID must not be empty or whitespace."


@pytest.mark.parametrize("score", [-0.01, -1.0])
def test_recommendation_candidate_rejects_score_below_zero(score: float) -> None:
    """Recommendation scores below zero must be rejected."""

    with pytest.raises(ValueError) as error:
        RecommendationCandidate(
            profile_id="cosy-foxes",
            artwork_id="artwork-001",
            score=score,
        )

    assert str(error.value) == "Recommendation score must be between 0.0 and 1.0."


@pytest.mark.parametrize("score", [1.01, 2.0])
def test_recommendation_candidate_rejects_score_above_one(score: float) -> None:
    """Recommendation scores above one must be rejected."""

    with pytest.raises(ValueError) as error:
        RecommendationCandidate(
            profile_id="cosy-foxes",
            artwork_id="artwork-001",
            score=score,
        )

    assert str(error.value) == "Recommendation score must be between 0.0 and 1.0."


@pytest.mark.parametrize(
    "score",
    [float("inf"), float("-inf"), float("nan")],
    ids=["positive-infinity", "negative-infinity", "nan"],
)
def test_recommendation_candidate_rejects_non_finite_score(score: float) -> None:
    """Recommendation scores must be finite before they can be ranked."""

    with pytest.raises(ValueError) as error:
        RecommendationCandidate(
            profile_id="cosy-foxes",
            artwork_id="artwork-001",
            score=score,
        )

    assert str(error.value) == "Recommendation score must be finite."
