"""Tests for pure service-content permission decisions and independent profile preferences."""

from dataclasses import FrozenInstanceError, replace
from typing import cast

import pytest

from artsniffer.content.rating import ContentRating
from artsniffer.content.service_permission_evaluation import (
    ServiceContentPermissionDecision,
    ServiceContentPermissionReason,
    evaluate_service_content_permissions,
)
from artsniffer.content.service_permissions import ServiceContentPermissions
from artsniffer.profiles.content_policy import (
    ProfileContentPolicy,
    ProfileContentPolicyMode,
    default_profile_content_policy,
)
from artsniffer.profiles.content_policy_evaluation import (
    ContentPolicyReason,
    evaluate_content_policy,
)


@pytest.mark.parametrize(
    ("adult_enabled", "rating", "reason"),
    [
        (False, ContentRating.UNKNOWN, ServiceContentPermissionReason.RATING_UNKNOWN),
        (False, ContentRating.GENERAL, ServiceContentPermissionReason.ALLOWED),
        (False, ContentRating.MATURE, ServiceContentPermissionReason.ALLOWED),
        (False, ContentRating.ADULT, ServiceContentPermissionReason.ADULT_CONTENT_DISABLED),
        (True, ContentRating.UNKNOWN, ServiceContentPermissionReason.RATING_UNKNOWN),
        (True, ContentRating.GENERAL, ServiceContentPermissionReason.ALLOWED),
        (True, ContentRating.MATURE, ServiceContentPermissionReason.ALLOWED),
        (True, ContentRating.ADULT, ServiceContentPermissionReason.ALLOWED),
    ],
)
def test_evaluate_service_content_permissions_matrix(
    adult_enabled: bool,
    rating: ContentRating,
    reason: ServiceContentPermissionReason,
) -> None:
    decision = evaluate_service_content_permissions(
        ServiceContentPermissions(adult_content_enabled=adult_enabled), rating
    )

    assert decision == ServiceContentPermissionDecision(
        allowed=reason is ServiceContentPermissionReason.ALLOWED,
        reason=reason,
    )


@pytest.mark.parametrize(
    ("rating", "reason"),
    [
        (ContentRating.UNKNOWN, ServiceContentPermissionReason.RATING_UNKNOWN),
        (ContentRating.GENERAL, ServiceContentPermissionReason.ALLOWED),
        (ContentRating.MATURE, ServiceContentPermissionReason.ALLOWED),
        (ContentRating.ADULT, ServiceContentPermissionReason.ADULT_CONTENT_DISABLED),
    ],
)
def test_default_permissions_use_adult_disabled_semantics(
    rating: ContentRating, reason: ServiceContentPermissionReason
) -> None:
    decision = evaluate_service_content_permissions(ServiceContentPermissions(), rating)

    assert decision == ServiceContentPermissionDecision(
        allowed=reason is ServiceContentPermissionReason.ALLOWED,
        reason=reason,
    )


def test_reason_values_are_exact() -> None:
    assert {reason.name: reason.value for reason in ServiceContentPermissionReason} == {
        "ALLOWED": "allowed",
        "RATING_UNKNOWN": "rating_unknown",
        "ADULT_CONTENT_DISABLED": "adult_content_disabled",
    }
    assert len(ServiceContentPermissionReason) == 3


@pytest.mark.parametrize("reason", list(ServiceContentPermissionReason))
def test_decision_accepts_consistent_combinations(reason: ServiceContentPermissionReason) -> None:
    allowed = reason is ServiceContentPermissionReason.ALLOWED

    decision = ServiceContentPermissionDecision(allowed=allowed, reason=reason)

    assert decision.allowed is allowed
    assert decision.reason is reason


@pytest.mark.parametrize("reason", list(ServiceContentPermissionReason))
def test_decision_rejects_contradictory_flags(reason: ServiceContentPermissionReason) -> None:
    with pytest.raises(ValueError) as error:
        ServiceContentPermissionDecision(
            allowed=reason is not ServiceContentPermissionReason.ALLOWED,
            reason=reason,
        )

    assert str(error.value) == (
        "Service content permission allowed flag must agree with the decision reason."
    )


@pytest.mark.parametrize("reason", list(ServiceContentPermissionReason))
@pytest.mark.parametrize("allowed", [None, 0, 1, "true"])
def test_decision_rejects_non_boolean_flags(
    allowed: object, reason: ServiceContentPermissionReason
) -> None:
    with pytest.raises(ValueError) as error:
        ServiceContentPermissionDecision(allowed=cast(bool, allowed), reason=reason)

    assert str(error.value) == (
        "Service content permission allowed flag must agree with the decision reason."
    )


@pytest.mark.parametrize(
    "reason",
    [
        None,
        "allowed",
        "rating_unknown",
        "adult_content_disabled",
        object(),
        ContentPolicyReason.ALLOWED,
    ],
)
def test_decision_rejects_invalid_reason_before_flag_validation(reason: object) -> None:
    with pytest.raises(ValueError) as error:
        ServiceContentPermissionDecision(
            allowed=cast(bool, None),
            reason=cast(ServiceContentPermissionReason, reason),
        )

    assert str(error.value) == (
        "Service content permission reason must be a ServiceContentPermissionReason."
    )


def test_decision_is_immutable() -> None:
    decision = ServiceContentPermissionDecision(True, ServiceContentPermissionReason.ALLOWED)

    with pytest.raises(FrozenInstanceError):
        decision.allowed = False  # type: ignore[misc]


@pytest.mark.parametrize(
    "policy",
    [
        ProfileContentPolicy(ProfileContentPolicyMode.MAX_RATING, ContentRating.ADULT),
        ProfileContentPolicy(ProfileContentPolicyMode.ADULT_ONLY),
    ],
)
def test_adult_accepting_profile_does_not_change_service_rejection(
    policy: ProfileContentPolicy,
) -> None:
    permissions = ServiceContentPermissions()

    profile_decision = evaluate_content_policy(policy, ContentRating.ADULT)
    service_decision = evaluate_service_content_permissions(permissions, ContentRating.ADULT)

    assert profile_decision.allowed
    assert service_decision == ServiceContentPermissionDecision(
        False, ServiceContentPermissionReason.ADULT_CONTENT_DISABLED
    )


@pytest.mark.parametrize("rating", [ContentRating.MATURE, ContentRating.ADULT])
def test_service_acceptance_does_not_change_general_profile_rejection(
    rating: ContentRating,
) -> None:
    permissions = ServiceContentPermissions(adult_content_enabled=True)

    service_decision = evaluate_service_content_permissions(permissions, rating)
    profile_decision = evaluate_content_policy(default_profile_content_policy(), rating)

    assert service_decision == ServiceContentPermissionDecision(
        True, ServiceContentPermissionReason.ALLOWED
    )
    assert not profile_decision.allowed
    assert profile_decision.reason is ContentPolicyReason.RATING_ABOVE_MAXIMUM


@pytest.mark.parametrize(
    "permissions",
    [default_profile_content_policy(), None, False, True, object()],
)
def test_evaluation_rejects_invalid_permissions(permissions: object) -> None:
    with pytest.raises(ValueError) as error:
        evaluate_service_content_permissions(
            cast(ServiceContentPermissions, permissions), ContentRating.GENERAL
        )

    assert str(error.value) == ("Service content permissions must be a ServiceContentPermissions.")


@pytest.mark.parametrize(
    "rating",
    [None, "unknown", "general", "mature", "adult", 1, ContentPolicyReason.ALLOWED, object()],
)
def test_evaluation_rejects_invalid_rating(rating: object) -> None:
    with pytest.raises(ValueError) as error:
        evaluate_service_content_permissions(
            ServiceContentPermissions(), cast(ContentRating, rating)
        )

    assert str(error.value) == "Service content rating must be a ContentRating."


def test_evaluation_validates_permissions_before_rating() -> None:
    with pytest.raises(ValueError) as error:
        evaluate_service_content_permissions(
            cast(ServiceContentPermissions, None), cast(ContentRating, None)
        )

    assert str(error.value) == ("Service content permissions must be a ServiceContentPermissions.")


@pytest.mark.parametrize("adult_enabled", [False, True])
@pytest.mark.parametrize("rating", list(ContentRating))
def test_evaluation_is_deterministic(adult_enabled: bool, rating: ContentRating) -> None:
    permissions = ServiceContentPermissions(adult_content_enabled=adult_enabled)

    assert evaluate_service_content_permissions(
        permissions, rating
    ) == evaluate_service_content_permissions(permissions, rating)


@pytest.mark.parametrize("adult_enabled", [False, True])
def test_evaluation_does_not_mutate_permissions(adult_enabled: bool) -> None:
    permissions = ServiceContentPermissions(adult_content_enabled=adult_enabled)
    before = replace(permissions)

    for rating in ContentRating:
        evaluate_service_content_permissions(permissions, rating)

    assert permissions == before
