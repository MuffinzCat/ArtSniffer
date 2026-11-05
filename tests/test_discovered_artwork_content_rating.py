"""Tests for provider-neutral discovered artwork content-rating records."""

import dataclasses

import pytest

from artsniffer.content.rating import ContentRating
from artsniffer.discovered_artwork_content_rating import (
    DiscoveredArtworkContentRating,
    unknown_discovered_artwork_content_rating,
)


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
