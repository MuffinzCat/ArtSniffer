"""Tests for provider-neutral discovered artwork content-rating records."""

import dataclasses

import pytest

from artsniffer.content.rating import ContentRating
from artsniffer.discovery.content_rating import (
    DiscoveredArtworkContentRating,
    DiscoveredArtworkContentRatingResolution,
    is_discovered_artwork_content_rating_resolved,
    resolve_discovered_artwork_content_rating,
    unknown_discovered_artwork_content_rating,
)
from artsniffer.discovery.content_rating import (
    DiscoveredArtworkContentRatingResolutionReason as Reason,
)
from artsniffer.discovery.post import DiscoveredArtwork, DiscoveredPost


@pytest.mark.parametrize("rating", list(ContentRating))
def test_record_accepts_every_content_rating(rating: ContentRating) -> None:
    """Every ContentRating member, including UNKNOWN, is valid."""

    record = DiscoveredArtworkContentRating(
        artwork_id="artwork-001",
        source_id="source-001",
        rating=rating,
    )

    assert record.rating is rating


def test_record_preserves_fields() -> None:
    """Identifiers and rating should be preserved as supplied."""

    record = DiscoveredArtworkContentRating(
        artwork_id="artwork-001",
        source_id="source-001",
        rating=ContentRating.MATURE,
    )

    assert record.artwork_id == "artwork-001"
    assert record.source_id == "source-001"
    assert record.rating is ContentRating.MATURE


@pytest.mark.parametrize("artwork_id", ["", "   ", "\t\n"])
def test_record_rejects_blank_artwork_id(artwork_id: str) -> None:
    """Blank or whitespace-only artwork IDs should be rejected."""

    with pytest.raises(
        ValueError, match=r"^Discovered artwork ID must not be empty or whitespace\.$"
    ):
        DiscoveredArtworkContentRating(
            artwork_id=artwork_id,
            source_id="source-001",
            rating=ContentRating.GENERAL,
        )


@pytest.mark.parametrize("source_id", ["", "   ", "\t\n"])
def test_record_rejects_blank_source_id(source_id: str) -> None:
    """Blank or whitespace-only source IDs should be rejected."""

    with pytest.raises(
        ValueError, match=r"^Content rating source ID must not be empty or whitespace\.$"
    ):
        DiscoveredArtworkContentRating(
            artwork_id="artwork-001",
            source_id=source_id,
            rating=ContentRating.ADULT,
        )


def test_record_is_immutable() -> None:
    """Fields should not be reassignable."""

    record = DiscoveredArtworkContentRating(
        artwork_id="artwork-001",
        source_id="source-001",
        rating=ContentRating.GENERAL,
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        record.rating = ContentRating.ADULT  # type: ignore[misc]


def test_unknown_helper_returns_explicit_unknown_record() -> None:
    """The helper should preserve identifiers and use UNKNOWN."""

    record = unknown_discovered_artwork_content_rating("artwork-001", "source-001")

    assert record.artwork_id == "artwork-001"
    assert record.source_id == "source-001"
    assert record.rating is ContentRating.UNKNOWN


def test_unknown_helper_returns_equivalent_independent_values() -> None:
    """Separate calls should return equal but distinct records."""

    first = unknown_discovered_artwork_content_rating("artwork-001", "source-001")
    second = unknown_discovered_artwork_content_rating("artwork-001", "source-001")

    assert first == second
    assert first is not second


def test_unknown_helper_relies_on_record_validation() -> None:
    """Invalid identifiers should surface the record's validation errors."""

    with pytest.raises(ValueError, match="Discovered artwork ID"):
        unknown_discovered_artwork_content_rating(" ", "source-001")
    with pytest.raises(ValueError, match="Content rating source ID"):
        unknown_discovered_artwork_content_rating("artwork-001", " ")


def test_absent_record_is_distinct_from_explicit_unknown() -> None:
    """Absence is represented by no object, not by a sentinel or default record."""

    ratings: dict[str, DiscoveredArtworkContentRating] = {
        "artwork-001": unknown_discovered_artwork_content_rating("artwork-001", "source-001"),
    }

    assert ratings.get("artwork-002") is None
    assert ratings["artwork-001"].rating is ContentRating.UNKNOWN


def _rating(
    artwork_id: str = "artwork-001",
    source_id: str = "source-001",
) -> DiscoveredArtworkContentRating:
    return DiscoveredArtworkContentRating(
        artwork_id=artwork_id,
        source_id=source_id,
        rating=ContentRating.MATURE,
    )


def _artwork(
    artwork_id: str = "artwork-001",
    post_id: str = "post-001",
) -> DiscoveredArtwork:
    return DiscoveredArtwork(
        id=artwork_id,
        post_id=post_id,
        source_item_id="provider-item-001",
        content_hash="sha256:distinct-content",
    )


def _post(
    post_id: str = "post-001",
    source_id: str = "source-001",
) -> DiscoveredPost:
    return DiscoveredPost(
        id=post_id,
        source_id=source_id,
        source_post_id="provider-post-001",
        creator_id="creator-001",
        url="opaque post reference",
    )


def test_matching_rating_artwork_post_and_source_resolve() -> None:
    decision = resolve_discovered_artwork_content_rating(_rating(), _artwork(), _post())

    assert decision == DiscoveredArtworkContentRatingResolution(
        resolved=True, reason=Reason.RESOLVED
    )


@pytest.mark.parametrize(
    ("rating", "artwork", "post", "reason"),
    [
        (
            _rating(artwork_id="rating-artwork-002"),
            _artwork(),
            _post(),
            Reason.ARTWORK_MISMATCH,
        ),
        (
            _rating(),
            _artwork(post_id="artwork-post-002"),
            _post(),
            Reason.POST_MISMATCH,
        ),
        (
            _rating(source_id="rating-source-002"),
            _artwork(),
            _post(),
            Reason.SOURCE_MISMATCH,
        ),
    ],
)
def test_relationship_mismatches_return_expected_reason(
    rating: DiscoveredArtworkContentRating,
    artwork: DiscoveredArtwork,
    post: DiscoveredPost,
    reason: Reason,
) -> None:
    decision = resolve_discovered_artwork_content_rating(rating, artwork, post)

    assert decision.resolved is False
    assert decision.reason is reason
    assert decision.resolved is (decision.reason is Reason.RESOLVED)


@pytest.mark.parametrize(
    ("rating", "artwork", "post", "reason"),
    [
        (
            _rating(artwork_id="rating-artwork-002", source_id="rating-source-002"),
            _artwork(post_id="artwork-post-002"),
            _post(source_id="post-source-002"),
            Reason.ARTWORK_MISMATCH,
        ),
        (
            _rating(source_id="rating-source-002"),
            _artwork(post_id="artwork-post-002"),
            _post(source_id="post-source-002"),
            Reason.POST_MISMATCH,
        ),
    ],
)
def test_earlier_relationship_mismatch_takes_precedence(
    rating: DiscoveredArtworkContentRating,
    artwork: DiscoveredArtwork,
    post: DiscoveredPost,
    reason: Reason,
) -> None:
    decision = resolve_discovered_artwork_content_rating(rating, artwork, post)

    assert decision.reason is reason


def test_matching_source_does_not_override_artwork_mismatch() -> None:
    decision = resolve_discovered_artwork_content_rating(
        _rating(artwork_id="rating-artwork-002"),
        _artwork(),
        _post(),
    )

    assert decision.reason is Reason.ARTWORK_MISMATCH


def test_matching_artwork_does_not_override_post_mismatch() -> None:
    decision = resolve_discovered_artwork_content_rating(
        _rating(),
        _artwork(post_id="artwork-post-002"),
        _post(),
    )

    assert decision.reason is Reason.POST_MISMATCH


@pytest.mark.parametrize(
    ("resolved", "reason"),
    [
        (True, Reason.RESOLVED),
        (False, Reason.ARTWORK_MISMATCH),
        (False, Reason.POST_MISMATCH),
        (False, Reason.SOURCE_MISMATCH),
    ],
)
def test_decision_accepts_consistent_success_and_failure_combinations(
    resolved: bool,
    reason: Reason,
) -> None:
    decision = DiscoveredArtworkContentRatingResolution(resolved=resolved, reason=reason)

    assert decision.resolved is resolved
    assert decision.reason is reason


@pytest.mark.parametrize(
    ("resolved", "reason"),
    [
        (False, Reason.RESOLVED),
        (True, Reason.ARTWORK_MISMATCH),
        (True, Reason.POST_MISMATCH),
        (True, Reason.SOURCE_MISMATCH),
    ],
)
def test_decision_rejects_success_and_reason_contradictions(
    resolved: bool,
    reason: Reason,
) -> None:
    with pytest.raises(
        ValueError, match=r"^Resolution flag must agree with the resolution reason\.$"
    ):
        DiscoveredArtworkContentRatingResolution(resolved=resolved, reason=reason)


@pytest.mark.parametrize(
    ("rating", "artwork", "post", "expected"),
    [
        (_rating(), _artwork(), _post(), True),
        (_rating(artwork_id="rating-artwork-002"), _artwork(), _post(), False),
        (_rating(), _artwork(post_id="artwork-post-002"), _post(), False),
        (_rating(source_id="rating-source-002"), _artwork(), _post(), False),
    ],
)
def test_boolean_helper_matches_structured_decision(
    rating: DiscoveredArtworkContentRating,
    artwork: DiscoveredArtwork,
    post: DiscoveredPost,
    expected: bool,
) -> None:
    decision = resolve_discovered_artwork_content_rating(rating, artwork, post)

    assert is_discovered_artwork_content_rating_resolved(rating, artwork, post) is expected
    assert is_discovered_artwork_content_rating_resolved(rating, artwork, post) is decision.resolved
