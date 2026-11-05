"""Tests for ArtSniffer profile reference links."""

import pytest

from artsniffer.profile_reference import ProfileReferenceLink


def test_profile_reference_link_uses_required_values_and_default_weight() -> None:
    """A valid link should preserve its identifiers and use the default weight."""

    # Create the smallest valid profile reference link.
    link = ProfileReferenceLink(
        profile_id="cosy-foxes",
        collection_id="favourite-art",
    )

    # The link should retain the identifiers it connects.
    assert link.profile_id == "cosy-foxes"
    assert link.collection_id == "favourite-art"

    # New links should apply normal influence by default.
    assert link.weight == 1.0


def test_profile_reference_link_preserves_explicit_positive_weight() -> None:
    """A link should retain a positive weight supplied for this profile."""

    link = ProfileReferenceLink(
        profile_id="cosy-foxes",
        collection_id="favourite-art",
        weight=2.5,
    )

    assert link.weight == 2.5


@pytest.mark.parametrize("invalid_profile_id", ["", " ", "   "])
def test_profile_reference_link_rejects_empty_or_whitespace_profile_id(
    invalid_profile_id: str,
) -> None:
    """Profile IDs must contain at least one non-whitespace character."""

    with pytest.raises(
        ValueError,
        match=r"\AProfile ID must not be empty or whitespace\.\Z",
    ):
        ProfileReferenceLink(
            profile_id=invalid_profile_id,
            collection_id="favourite-art",
        )


@pytest.mark.parametrize("invalid_collection_id", ["", " ", "   "])
def test_profile_reference_link_rejects_empty_or_whitespace_collection_id(
    invalid_collection_id: str,
) -> None:
    """Collection IDs must contain at least one non-whitespace character."""

    with pytest.raises(
        ValueError,
        match=r"\ACollection ID must not be empty or whitespace\.\Z",
    ):
        ProfileReferenceLink(
            profile_id="cosy-foxes",
            collection_id=invalid_collection_id,
        )


def test_profile_reference_link_rejects_zero_weight() -> None:
    """A link weight must be greater than zero."""

    with pytest.raises(
        ValueError,
        match=r"\AWeight must be greater than 0\.0\.\Z",
    ):
        ProfileReferenceLink(
            profile_id="cosy-foxes",
            collection_id="favourite-art",
            weight=0.0,
        )


@pytest.mark.parametrize("invalid_weight", [-0.01, -1.0])
def test_profile_reference_link_rejects_negative_weight(invalid_weight: float) -> None:
    """Negative weights must not be used to configure a link."""

    with pytest.raises(
        ValueError,
        match=r"\AWeight must be greater than 0\.0\.\Z",
    ):
        ProfileReferenceLink(
            profile_id="cosy-foxes",
            collection_id="favourite-art",
            weight=invalid_weight,
        )
