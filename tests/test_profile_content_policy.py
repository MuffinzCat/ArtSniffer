"""Tests for the provider-neutral profile content policy."""

import dataclasses

import pytest

from artsniffer.content.rating import ContentRating
from artsniffer.profile_content_policy import (
    ProfileContentPolicy,
    ProfileContentPolicyMode,
    default_profile_content_policy,
)


def test_mode_values_are_exact() -> None:
    assert {mode.name: mode.value for mode in ProfileContentPolicyMode} == {
        "MAX_RATING": "max_rating",
        "ADULT_ONLY": "adult_only",
    }


def test_there_are_exactly_two_modes() -> None:
    assert len(ProfileContentPolicyMode) == 2


@pytest.mark.parametrize(
    "rating",
    [ContentRating.GENERAL, ContentRating.MATURE, ContentRating.ADULT],
)
def test_max_rating_accepts_known_ratings(rating: ContentRating) -> None:
    policy = ProfileContentPolicy(mode=ProfileContentPolicyMode.MAX_RATING, max_rating=rating)

    assert policy.mode is ProfileContentPolicyMode.MAX_RATING
    assert policy.max_rating is rating


def test_max_rating_requires_max_rating() -> None:
    with pytest.raises(ValueError) as error:
        ProfileContentPolicy(mode=ProfileContentPolicyMode.MAX_RATING)

    assert str(error.value) == "Max-rating content policy requires a max rating."


def test_max_rating_rejects_unknown() -> None:
    with pytest.raises(ValueError) as error:
        ProfileContentPolicy(
            mode=ProfileContentPolicyMode.MAX_RATING,
            max_rating=ContentRating.UNKNOWN,
        )

    assert str(error.value) == "Max-rating content policy must not use an unknown max rating."


def test_adult_only_without_max_rating_is_valid() -> None:
    policy = ProfileContentPolicy(mode=ProfileContentPolicyMode.ADULT_ONLY)

    assert policy.mode is ProfileContentPolicyMode.ADULT_ONLY
    assert policy.max_rating is None


@pytest.mark.parametrize(
    "rating",
    [ContentRating.GENERAL, ContentRating.MATURE, ContentRating.ADULT],
)
def test_adult_only_rejects_any_max_rating(rating: ContentRating) -> None:
    with pytest.raises(ValueError) as error:
        ProfileContentPolicy(mode=ProfileContentPolicyMode.ADULT_ONLY, max_rating=rating)

    assert str(error.value) == "Adult-only content policy must not define a max rating."


def test_policy_is_immutable() -> None:
    policy = ProfileContentPolicy(
        mode=ProfileContentPolicyMode.MAX_RATING,
        max_rating=ContentRating.GENERAL,
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        policy.max_rating = ContentRating.ADULT  # type: ignore[misc]


def test_default_policy_is_max_rating_general() -> None:
    policy = default_profile_content_policy()

    assert policy.mode is ProfileContentPolicyMode.MAX_RATING
    assert policy.max_rating is ContentRating.GENERAL


def test_default_helper_returns_equivalent_separate_values() -> None:
    first = default_profile_content_policy()
    second = default_profile_content_policy()

    assert first == second
    assert first is not second


def test_policy_has_only_mode_and_max_rating_fields() -> None:
    field_names = {field.name for field in dataclasses.fields(ProfileContentPolicy)}

    assert field_names == {"mode", "max_rating"}
