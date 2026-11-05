import pytest

from artsniffer.content.rating import ContentRating
from artsniffer.profiles.content_policy import ProfileContentPolicy, ProfileContentPolicyMode
from artsniffer.profiles.content_policy_evaluation import (
    ContentPolicyDecision,
    ContentPolicyReason,
    evaluate_content_policy,
    is_content_allowed,
)

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
