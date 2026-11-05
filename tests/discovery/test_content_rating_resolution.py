"""Tests for discovered artwork content-rating relationship resolution."""

import pytest

from artsniffer.content.rating import ContentRating
from artsniffer.discovery.artwork import DiscoveredArtwork
from artsniffer.discovery.content_rating import DiscoveredArtworkContentRating
from artsniffer.discovery.content_rating_resolution import (
    DiscoveredArtworkContentRatingResolution,
    is_discovered_artwork_content_rating_resolved,
    resolve_discovered_artwork_content_rating,
)
from artsniffer.discovery.content_rating_resolution import (
    DiscoveredArtworkContentRatingResolutionReason as Reason,
)
from artsniffer.discovery.post import DiscoveredPost


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
