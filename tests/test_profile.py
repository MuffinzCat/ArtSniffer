"""Tests for ArtSniffer recommendation profiles."""

import pytest

from artsniffer.content_rating import ContentRating
from artsniffer.profile import RecommendationProfile
from artsniffer.profile_content_policy import (
    ProfileContentPolicy,
    ProfileContentPolicyMode,
    default_profile_content_policy,
)


def test_profile_uses_required_values_and_defaults() -> None:
    """A valid profile should preserve its identity and use the expected defaults."""

    # Create the smallest valid recommendation profile.
    profile = RecommendationProfile(
        id="cosy-foxes",
        name="Cosy Foxes",
    )

    # Required identity fields should be stored exactly as supplied.
    assert profile.id == "cosy-foxes"
    assert profile.name == "Cosy Foxes"

    # New profiles should be enabled and use the default recommendation threshold.
    assert profile.enabled is True
    assert profile.threshold == 0.75


def test_profile_preserves_disabled_state() -> None:
    """A profile can be disabled without changing its other configuration."""

    profile = RecommendationProfile(
        id="cosy-foxes",
        name="Cosy Foxes",
        enabled=False,
    )

    assert profile.enabled is False


@pytest.mark.parametrize("invalid_id", ["", " ", "   "])
def test_profile_rejects_empty_or_whitespace_id(invalid_id: str) -> None:
    """Profile IDs must contain at least one non-whitespace character."""

    # Invalid IDs should never be allowed into the rest of ArtSniffer.
    with pytest.raises(
        ValueError,
        match=r"\AProfile ID must not be empty or whitespace\.\Z",
    ):
        RecommendationProfile(id=invalid_id, name="Cosy Foxes")


@pytest.mark.parametrize("invalid_name", ["", " ", "   "])
def test_profile_rejects_empty_or_whitespace_name(invalid_name: str) -> None:
    """Profile names must contain at least one non-whitespace character."""

    # User-facing names still need meaningful content even though they are not identifiers.
    with pytest.raises(
        ValueError,
        match=r"\AProfile name must not be empty or whitespace\.\Z",
    ):
        RecommendationProfile(id="cosy-foxes", name=invalid_name)


@pytest.mark.parametrize("threshold", [0.0, 1.0])
def test_profile_accepts_threshold_boundaries(threshold: float) -> None:
    """The documented minimum and maximum recommendation thresholds should be valid."""

    profile = RecommendationProfile(
        id="cosy-foxes",
        name="Cosy Foxes",
        threshold=threshold,
    )

    assert profile.threshold == threshold


@pytest.mark.parametrize("threshold", [-0.01, 1.01])
def test_profile_rejects_thresholds_outside_valid_range(threshold: float) -> None:
    """Recommendation thresholds outside the normalised score range should be rejected."""

    with pytest.raises(
        ValueError,
        match=r"\AThreshold must be between 0\.0 and 1\.0\.\Z",
    ):
        RecommendationProfile(
            id="cosy-foxes",
            name="Cosy Foxes",
            threshold=threshold,
        )


def test_profile_defaults_to_general_max_rating_content_policy() -> None:
    """Profiles without an explicit policy should use the safe GENERAL default."""

    profile = RecommendationProfile(id="cosy-foxes", name="Cosy Foxes")

    assert profile.content_policy == default_profile_content_policy()
    assert profile.content_policy.mode is ProfileContentPolicyMode.MAX_RATING
    assert profile.content_policy.max_rating is ContentRating.GENERAL


def test_profiles_do_not_share_default_content_policy_instances() -> None:
    """Each profile should receive its own default policy object."""

    first = RecommendationProfile(id="first", name="First")
    second = RecommendationProfile(id="second", name="Second")

    assert first.content_policy == second.content_policy
    assert first.content_policy is not second.content_policy


@pytest.mark.parametrize(
    "policy",
    [
        ProfileContentPolicy(ProfileContentPolicyMode.MAX_RATING, ContentRating.GENERAL),
        ProfileContentPolicy(ProfileContentPolicyMode.MAX_RATING, ContentRating.MATURE),
        ProfileContentPolicy(ProfileContentPolicyMode.MAX_RATING, ContentRating.ADULT),
        ProfileContentPolicy(ProfileContentPolicyMode.ADULT_ONLY),
    ],
)
def test_profile_preserves_explicit_content_policy(policy: ProfileContentPolicy) -> None:
    """An explicitly supplied policy should be stored exactly as supplied."""

    profile = RecommendationProfile(id="cosy-foxes", name="Cosy Foxes", content_policy=policy)

    assert profile.content_policy is policy
