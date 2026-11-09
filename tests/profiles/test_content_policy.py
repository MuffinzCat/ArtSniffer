"""Tests for the provider-neutral profile content policy."""

import dataclasses

import pytest

from artsniffer.content.rating import ContentRating
from artsniffer.profiles.content_policy import (
    ContentPolicyDecision,
    ContentPolicyReason,
    ProfileContentPolicy,
    ProfileContentPolicyMode,
    default_profile_content_policy,
    evaluate_content_policy,
    is_content_allowed,
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


R = ContentPolicyReason


C = ContentRating


def max_policy(rating: ContentRating) -> ProfileContentPolicy:
    return ProfileContentPolicy(mode=ProfileContentPolicyMode.MAX_RATING, max_rating=rating)


ADULT_ONLY = ProfileContentPolicy(mode=ProfileContentPolicyMode.ADULT_ONLY)


MATRIX = [
    (max_policy(C.GENERAL), C.UNKNOWN, R.RATING_UNKNOWN),
    (max_policy(C.GENERAL), C.GENERAL, R.ALLOWED),
    (max_policy(C.GENERAL), C.MATURE, R.RATING_ABOVE_MAXIMUM),
    (max_policy(C.GENERAL), C.ADULT, R.RATING_ABOVE_MAXIMUM),
    (max_policy(C.MATURE), C.UNKNOWN, R.RATING_UNKNOWN),
    (max_policy(C.MATURE), C.GENERAL, R.ALLOWED),
    (max_policy(C.MATURE), C.MATURE, R.ALLOWED),
    (max_policy(C.MATURE), C.ADULT, R.RATING_ABOVE_MAXIMUM),
    (max_policy(C.ADULT), C.UNKNOWN, R.RATING_UNKNOWN),
    (max_policy(C.ADULT), C.GENERAL, R.ALLOWED),
    (max_policy(C.ADULT), C.MATURE, R.ALLOWED),
    (max_policy(C.ADULT), C.ADULT, R.ALLOWED),
    (ADULT_ONLY, C.UNKNOWN, R.RATING_UNKNOWN),
    (ADULT_ONLY, C.GENERAL, R.ADULT_REQUIRED),
    (ADULT_ONLY, C.MATURE, R.ADULT_REQUIRED),
    (ADULT_ONLY, C.ADULT, R.ALLOWED),
]


@pytest.mark.parametrize(("policy", "rating", "reason"), MATRIX)
def test_evaluate_content_policy_matrix(
    policy: ProfileContentPolicy, rating: ContentRating, reason: ContentPolicyReason
) -> None:
    decision = evaluate_content_policy(policy, rating)

    assert decision == ContentPolicyDecision(allowed=reason is R.ALLOWED, reason=reason)


@pytest.mark.parametrize(("policy", "rating", "reason"), MATRIX)
def test_is_content_allowed_matches_evaluation(
    policy: ProfileContentPolicy, rating: ContentRating, reason: ContentPolicyReason
) -> None:
    assert is_content_allowed(policy, rating) is evaluate_content_policy(policy, rating).allowed
    assert is_content_allowed(policy, rating) is (reason is R.ALLOWED)


def test_reason_values_are_exact() -> None:
    assert {reason.name: reason.value for reason in ContentPolicyReason} == {
        "ALLOWED": "allowed",
        "RATING_UNKNOWN": "rating_unknown",
        "RATING_ABOVE_MAXIMUM": "rating_above_maximum",
        "ADULT_REQUIRED": "adult_required",
    }
    assert len(ContentPolicyReason) == 4


@pytest.mark.parametrize("reason", list(ContentPolicyReason))
def test_decision_accepts_consistent_combinations(reason: ContentPolicyReason) -> None:
    decision = ContentPolicyDecision(allowed=reason is R.ALLOWED, reason=reason)

    assert decision.allowed is (reason is R.ALLOWED)
    assert decision.reason is reason


@pytest.mark.parametrize(
    ("allowed", "reason"),
    [
        (False, R.ALLOWED),
        (True, R.RATING_UNKNOWN),
        (True, R.RATING_ABOVE_MAXIMUM),
        (True, R.ADULT_REQUIRED),
    ],
)
def test_decision_rejects_contradictions(allowed: bool, reason: ContentPolicyReason) -> None:
    with pytest.raises(
        ValueError, match="^Content policy allowed flag must agree with the decision reason.$"
    ):
        ContentPolicyDecision(allowed=allowed, reason=reason)


def test_evaluation_does_not_mutate_policy() -> None:
    policy = max_policy(C.MATURE)

    for rating in ContentRating:
        evaluate_content_policy(policy, rating)

    assert policy == max_policy(C.MATURE)
    assert policy.mode is ProfileContentPolicyMode.MAX_RATING
    assert policy.max_rating is C.MATURE


def test_max_rating_adult_is_distinct_from_adult_only() -> None:
    assert evaluate_content_policy(max_policy(C.ADULT), C.GENERAL).allowed
    assert not evaluate_content_policy(ADULT_ONLY, C.GENERAL).allowed
    assert evaluate_content_policy(ADULT_ONLY, C.GENERAL).reason is R.ADULT_REQUIRED
