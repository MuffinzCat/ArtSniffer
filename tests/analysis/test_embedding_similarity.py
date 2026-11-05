"""Tests for cosine similarity between artwork embeddings."""

import pytest

from artsniffer.analysis.embedding_similarity import cosine_similarity


def test_identical_vectors_have_similarity_one() -> None:
    """Identical non-zero vectors have cosine similarity one."""

    assert cosine_similarity((1.0, 2.0, 3.0), (1.0, 2.0, 3.0)) == pytest.approx(1.0)


def test_opposite_vectors_have_similarity_minus_one() -> None:
    """Vectors pointing in opposite directions have similarity minus one."""

    assert cosine_similarity((1.0, -2.0), (-1.0, 2.0)) == pytest.approx(-1.0)


def test_orthogonal_vectors_have_similarity_zero() -> None:
    """Perpendicular vectors have cosine similarity zero."""

    assert cosine_similarity((1.0, 0.0), (0.0, 1.0)) == pytest.approx(0.0)


def test_non_normalised_vectors_have_known_similarity() -> None:
    """Similarity is calculated correctly without requiring normalised inputs."""

    assert cosine_similarity((1.0, 2.0), (3.0, 4.0)) == pytest.approx(11.0 / (5.0**0.5 * 5.0))


def test_vectors_with_negative_and_positive_values_have_known_similarity() -> None:
    """Negative and positive vector values contribute to conventional cosine similarity."""

    assert cosine_similarity((1.0, -1.0), (1.0, 0.0)) == pytest.approx(2.0**-0.5)


def test_single_dimension_vectors_have_conventional_similarity() -> None:
    """Non-zero single-dimension vectors have similarity based on their direction."""

    assert cosine_similarity((2.0,), (5.0,)) == pytest.approx(1.0)
    assert cosine_similarity((2.0,), (-5.0,)) == pytest.approx(-1.0)


def test_similarity_does_not_mutate_input_vectors() -> None:
    """Calculating similarity leaves both input vectors unchanged."""

    left = (1.0, -2.0, 3.0)
    right = (-4.0, 5.0, 6.0)

    cosine_similarity(left, right)

    assert left == (1.0, -2.0, 3.0)
    assert right == (-4.0, 5.0, 6.0)


def test_cosine_similarity_returns_value_between_minus_one_and_one() -> None:
    """The returned similarity remains in its conventional mathematical range."""

    similarity = cosine_similarity((1e308, 1e308), (1e308, 1e308))

    assert -1.0 <= similarity <= 1.0
    assert similarity == pytest.approx(1.0)


def test_cosine_similarity_rejects_empty_left_vector() -> None:
    """The left vector must contain at least one value."""

    with pytest.raises(ValueError) as error:
        cosine_similarity((), (1.0,))

    assert str(error.value) == "Left vector must contain at least one value."


def test_cosine_similarity_rejects_empty_right_vector() -> None:
    """The right vector must contain at least one value."""

    with pytest.raises(ValueError) as error:
        cosine_similarity((1.0,), ())

    assert str(error.value) == "Right vector must contain at least one value."


def test_cosine_similarity_rejects_mismatched_dimensions() -> None:
    """Both vectors must have the same number of values."""

    with pytest.raises(ValueError) as error:
        cosine_similarity((1.0, 2.0), (1.0,))

    assert str(error.value) == "Vectors must have the same dimensions."


@pytest.mark.parametrize(
    "invalid_value",
    [float("inf"), float("-inf"), float("nan")],
    ids=["positive-infinity", "negative-infinity", "nan"],
)
def test_cosine_similarity_rejects_non_finite_left_values(
    invalid_value: float,
) -> None:
    """Every value in the left vector must be finite."""

    with pytest.raises(ValueError) as error:
        cosine_similarity((invalid_value,), (1.0,))

    assert str(error.value) == "Left vector values must be finite."


@pytest.mark.parametrize(
    "invalid_value",
    [float("inf"), float("-inf"), float("nan")],
    ids=["positive-infinity", "negative-infinity", "nan"],
)
def test_cosine_similarity_rejects_non_finite_right_values(
    invalid_value: float,
) -> None:
    """Every value in the right vector must be finite."""

    with pytest.raises(ValueError) as error:
        cosine_similarity((1.0,), (invalid_value,))

    assert str(error.value) == "Right vector values must be finite."


def test_cosine_similarity_rejects_zero_magnitude_left_vector() -> None:
    """The left vector must have non-zero magnitude."""

    with pytest.raises(ValueError) as error:
        cosine_similarity((0.0, 0.0), (1.0, 2.0))

    assert str(error.value) == "Left vector must have non-zero magnitude."


def test_cosine_similarity_rejects_zero_magnitude_right_vector() -> None:
    """The right vector must have non-zero magnitude."""

    with pytest.raises(ValueError) as error:
        cosine_similarity((1.0, 2.0), (0.0, 0.0))

    assert str(error.value) == "Right vector must have non-zero magnitude."
