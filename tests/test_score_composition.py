"""Tests for recommendation score composition."""

import sys

import pytest

from artsniffer.recommendation_score import RecommendationScoreComponent
from artsniffer.score_composition import compose_recommendation_score


def component(score: float, weight: float = 1.0, name: str = "c") -> RecommendationScoreComponent:
    """Build a score component for composition tests."""
    return RecommendationScoreComponent(name=name, score=score, weight=weight)


def test_single_component_returns_its_score() -> None:
    """One component should yield its own score."""
    assert compose_recommendation_score([component(0.37, weight=4.0)]) == pytest.approx(0.37)


def test_equal_weights_produce_arithmetic_mean() -> None:
    """Equal weights should give the plain mean."""
    result = compose_recommendation_score([component(0.2), component(0.6)])

    assert result == pytest.approx(0.4)


def test_unequal_weights_produce_weighted_mean() -> None:
    """Heavier components should influence the result more."""
    result = compose_recommendation_score([component(1.0, weight=3.0), component(0.0, weight=1.0)])

    assert result == pytest.approx(0.75)


def test_zero_score() -> None:
    """All-zero scores should compose to 0.0."""
    assert compose_recommendation_score([component(0.0), component(0.0, 2.0)]) == 0.0


def test_maximum_score() -> None:
    """All-maximum scores should compose to exactly 1.0."""
    assert compose_recommendation_score([component(1.0, 0.1), component(1.0, 7.3)]) == 1.0


def test_mixture_of_zero_and_one() -> None:
    """Zero and one scores should compose to the weight share of the ones."""
    result = compose_recommendation_score([component(0.0, 1.0), component(1.0, 1.0)])

    assert result == pytest.approx(0.5)


def test_order_independence() -> None:
    """Reordering components should not change the result."""
    components = [component(0.1, 0.3), component(0.9, 2.5), component(0.5, 1e-3), component(0.7, 4)]

    forward = compose_recommendation_score(components)
    backward = compose_recommendation_score(list(reversed(components)))

    assert forward == backward


def test_duplicate_names_both_contribute() -> None:
    """Names are labels, so duplicates should each be weighted in."""
    result = compose_recommendation_score(
        [component(1.0, name="visual"), component(0.0, name="visual")]
    )

    assert result == pytest.approx(0.5)


def test_components_and_input_sequence_are_not_mutated() -> None:
    """Composition should leave the input sequence and components unchanged."""
    first = component(0.2, 2.0, name="a")
    second = component(0.8, 1.0, name="b")
    components = [first, second]

    compose_recommendation_score(components)

    assert components == [first, second]
    assert components[0] is first and components[1] is second
    assert (first.name, first.score, first.weight) == ("a", 0.2, 2.0)
    assert (second.name, second.score, second.weight) == ("b", 0.8, 1.0)


def test_empty_components_are_rejected() -> None:
    """At least one component is required."""
    with pytest.raises(
        ValueError, match=r"^At least one recommendation score component is required\.$"
    ):
        compose_recommendation_score([])


def test_total_weight_overflow_is_rejected() -> None:
    """Finite weights whose total overflows should be rejected, not become NaN or inf."""
    components = [component(0.5, sys.float_info.max), component(0.5, sys.float_info.max)]

    with pytest.raises(ValueError, match=r"^Total component weight must be finite\.$"):
        compose_recommendation_score(components)


def test_large_finite_weights_that_do_not_overflow_are_composed() -> None:
    """Very large weights below the overflow point should still compose correctly."""
    big = sys.float_info.max / 4
    result = compose_recommendation_score([component(1.0, big), component(0.0, big)])

    assert result == pytest.approx(0.5)


def test_subnormal_weights_remain_normalised() -> None:
    """Tiny positive weights should still give a score within 0.0 to 1.0."""
    tiny = 5e-324
    result = compose_recommendation_score([component(1.0, tiny), component(1.0, tiny)])

    assert result == 1.0
