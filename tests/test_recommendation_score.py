"""Tests for named recommendation score components."""

import pytest

from artsniffer.recommendation_score import RecommendationScoreComponent


def test_score_component_preserves_name_score_and_default_weight() -> None:
    """A valid component should preserve its name and score with normal weight."""

    component = RecommendationScoreComponent(
        name="visual similarity",
        score=0.65,
    )

    assert component.name == "visual similarity"
    assert component.score == 0.65
    assert component.weight == 1.0


@pytest.mark.parametrize("score", [0.0, 1.0])
def test_score_component_accepts_score_boundaries(score: float) -> None:
    """Normalised score boundary values should be accepted."""

    component = RecommendationScoreComponent(
        name="visual similarity",
        score=score,
    )

    assert component.score == score


def test_score_component_accepts_finite_score_between_boundaries() -> None:
    """Finite scores between zero and one should be accepted."""

    component = RecommendationScoreComponent(
        name="semantic similarity",
        score=0.42,
    )

    assert component.score == 0.42


@pytest.mark.parametrize("weight", [0.25, 2.5])
def test_score_component_preserves_finite_positive_weight(weight: float) -> None:
    """Finite positive weights smaller and larger than normal should be retained."""

    component = RecommendationScoreComponent(
        name="visual similarity",
        score=0.65,
        weight=weight,
    )

    assert component.weight == weight


@pytest.mark.parametrize("invalid_name", ["", " ", "   "])
def test_score_component_rejects_empty_or_whitespace_name(invalid_name: str) -> None:
    """Component names must contain at least one non-whitespace character."""

    with pytest.raises(ValueError) as error:
        RecommendationScoreComponent(name=invalid_name, score=0.65)

    assert str(error.value) == "Component name must not be empty or whitespace."


@pytest.mark.parametrize("score", [-0.01, -1.0])
def test_score_component_rejects_score_below_zero(score: float) -> None:
    """Component scores below zero must be rejected."""

    with pytest.raises(ValueError) as error:
        RecommendationScoreComponent(name="visual similarity", score=score)

    assert str(error.value) == "Component score must be between 0.0 and 1.0."


@pytest.mark.parametrize("score", [1.01, 2.0])
def test_score_component_rejects_score_above_one(score: float) -> None:
    """Component scores above one must be rejected."""

    with pytest.raises(ValueError) as error:
        RecommendationScoreComponent(name="visual similarity", score=score)

    assert str(error.value) == "Component score must be between 0.0 and 1.0."


@pytest.mark.parametrize(
    "score",
    [float("inf"), float("-inf"), float("nan")],
    ids=["positive-infinity", "negative-infinity", "nan"],
)
def test_score_component_rejects_non_finite_score(score: float) -> None:
    """Component scores must be finite before they can be normalised."""

    with pytest.raises(ValueError) as error:
        RecommendationScoreComponent(name="visual similarity", score=score)

    assert str(error.value) == "Component score must be finite."


def test_score_component_rejects_zero_weight() -> None:
    """A component weight must be greater than zero."""

    with pytest.raises(ValueError) as error:
        RecommendationScoreComponent(
            name="visual similarity",
            score=0.65,
            weight=0.0,
        )

    assert str(error.value) == "Component weight must be greater than 0.0."


@pytest.mark.parametrize("weight", [-0.01, -1.0])
def test_score_component_rejects_negative_weight(weight: float) -> None:
    """Negative component weights must be rejected."""

    with pytest.raises(ValueError) as error:
        RecommendationScoreComponent(
            name="visual similarity",
            score=0.65,
            weight=weight,
        )

    assert str(error.value) == "Component weight must be greater than 0.0."


@pytest.mark.parametrize(
    "weight",
    [float("inf"), float("-inf"), float("nan")],
    ids=["positive-infinity", "negative-infinity", "nan"],
)
def test_score_component_rejects_non_finite_weight(weight: float) -> None:
    """Component weights must be finite."""

    with pytest.raises(ValueError) as error:
        RecommendationScoreComponent(
            name="visual similarity",
            score=0.65,
            weight=weight,
        )

    assert str(error.value) == "Component weight must be finite."
