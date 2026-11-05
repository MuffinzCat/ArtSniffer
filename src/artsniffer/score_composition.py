"""Provider-neutral composition of recommendation score components."""

from collections.abc import Sequence
from math import fsum, isfinite

from artsniffer.recommendation_score import RecommendationScoreComponent


def compose_recommendation_score(
    components: Sequence[RecommendationScoreComponent],
) -> float:
    """Return the weighted arithmetic mean of already-calculated component scores.

    The result is ``sum(score * weight) / sum(weight)``. Component names are explanatory
    labels only, so duplicates each contribute. Components are not modified or reordered.
    """
    if not components:
        raise ValueError("At least one recommendation score component is required.")

    # fsum is exactly rounded, which keeps the result independent of component order.
    try:
        total_weight = fsum(component.weight for component in components)
    except OverflowError:
        raise ValueError("Total component weight must be finite.") from None
    if not isfinite(total_weight):
        raise ValueError("Total component weight must be finite.")

    # Each product is at most its weight, so the weighted total cannot exceed total_weight.
    weighted_total = fsum(component.score * component.weight for component in components)

    # Clamp only guards against floating-point rounding at the 1.0 boundary.
    return min(1.0, max(0.0, weighted_total / total_weight))
