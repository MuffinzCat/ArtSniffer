"""Standard-library calculations for visual vector similarity."""

from math import hypot, isfinite


def cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    """Return conventional cosine similarity between two finite embedding vectors."""
    if not left:
        raise ValueError("Left vector must contain at least one value.")
    if not right:
        raise ValueError("Right vector must contain at least one value.")
    if len(left) != len(right):
        raise ValueError("Vectors must have the same dimensions.")
    if any(not isfinite(value) for value in left):
        raise ValueError("Left vector values must be finite.")
    if any(not isfinite(value) for value in right):
        raise ValueError("Right vector values must be finite.")

    left_magnitude = hypot(*left)
    if left_magnitude == 0.0:
        raise ValueError("Left vector must have non-zero magnitude.")

    right_magnitude = hypot(*right)
    if right_magnitude == 0.0:
        raise ValueError("Right vector must have non-zero magnitude.")

    similarity = sum(
        (left_value / left_magnitude) * (right_value / right_magnitude)
        for left_value, right_value in zip(left, right, strict=True)
    )
    return max(-1.0, min(1.0, similarity))
