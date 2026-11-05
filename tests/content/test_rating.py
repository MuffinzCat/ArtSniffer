"""Tests for the provider-neutral content-rating vocabulary."""

import pytest

from artsniffer.content.rating import (
    ContentRating,
    content_rating_rank,
    is_known_content_rating,
)


def test_content_rating_values_are_exact() -> None:
    assert {rating.name: rating.value for rating in ContentRating} == {
        "UNKNOWN": "unknown",
        "GENERAL": "general",
        "MATURE": "mature",
        "ADULT": "adult",
    }


def test_content_rating_has_exactly_four_members() -> None:
    assert len(ContentRating) == 4


def test_content_rating_has_no_prohibited_or_safety_member() -> None:
    names = {rating.name for rating in ContentRating}
    values = {rating.value for rating in ContentRating}

    assert not {"PROHIBITED", "SAFE", "UNSAFE", "BLOCKED"} & names
    assert not {"prohibited", "safe", "unsafe", "blocked"} & values


@pytest.mark.parametrize(
    ("rating", "expected"),
    [
        (ContentRating.UNKNOWN, False),
        (ContentRating.GENERAL, True),
        (ContentRating.MATURE, True),
        (ContentRating.ADULT, True),
    ],
)
def test_is_known_content_rating(rating: ContentRating, expected: bool) -> None:
    assert is_known_content_rating(rating) is expected


@pytest.mark.parametrize(
    ("rating", "expected"),
    [
        (ContentRating.GENERAL, 0),
        (ContentRating.MATURE, 1),
        (ContentRating.ADULT, 2),
    ],
)
def test_content_rating_rank(rating: ContentRating, expected: int) -> None:
    assert content_rating_rank(rating) == expected


def test_content_rating_ranks_increase_with_severity() -> None:
    assert (
        content_rating_rank(ContentRating.GENERAL)
        < content_rating_rank(ContentRating.MATURE)
        < content_rating_rank(ContentRating.ADULT)
    )


def test_unknown_content_rating_has_no_rank() -> None:
    with pytest.raises(ValueError) as error:
        content_rating_rank(ContentRating.UNKNOWN)

    assert str(error.value) == "Unknown content rating has no severity rank."
