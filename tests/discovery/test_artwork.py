"""Tests for individual artwork items in discovered posts."""

import pytest

from artsniffer.discovery.artwork import DiscoveredArtwork


def test_discovered_artwork_preserves_all_fields() -> None:
    """A valid artwork item should preserve its identifiers and content hash."""

    artwork = DiscoveredArtwork(
        id="discovered-artwork-001",
        post_id="post-001",
        source_item_id="provider-media-42",
        content_hash="sha256:abc123",
    )

    assert artwork.id == "discovered-artwork-001"
    assert artwork.post_id == "post-001"
    assert artwork.source_item_id == "provider-media-42"
    assert artwork.content_hash == "sha256:abc123"


@pytest.mark.parametrize("invalid_id", ["", " ", "   "])
def test_discovered_artwork_rejects_empty_or_whitespace_id(invalid_id: str) -> None:
    """Discovered artwork IDs must contain a non-whitespace character."""

    with pytest.raises(ValueError) as error:
        DiscoveredArtwork(
            id=invalid_id,
            post_id="post-001",
            source_item_id="provider-media-42",
            content_hash="sha256:abc123",
        )

    assert str(error.value) == "Discovered artwork ID must not be empty or whitespace."


@pytest.mark.parametrize("invalid_post_id", ["", " ", "   "])
def test_discovered_artwork_rejects_empty_or_whitespace_post_id(
    invalid_post_id: str,
) -> None:
    """Post IDs must contain a non-whitespace character."""

    with pytest.raises(ValueError) as error:
        DiscoveredArtwork(
            id="discovered-artwork-001",
            post_id=invalid_post_id,
            source_item_id="provider-media-42",
            content_hash="sha256:abc123",
        )

    assert str(error.value) == "Post ID must not be empty or whitespace."


@pytest.mark.parametrize("invalid_source_item_id", ["", " ", "   "])
def test_discovered_artwork_rejects_empty_or_whitespace_source_item_id(
    invalid_source_item_id: str,
) -> None:
    """Provider media item IDs must contain a non-whitespace character."""

    with pytest.raises(ValueError) as error:
        DiscoveredArtwork(
            id="discovered-artwork-001",
            post_id="post-001",
            source_item_id=invalid_source_item_id,
            content_hash="sha256:abc123",
        )

    assert str(error.value) == "Source item ID must not be empty or whitespace."


@pytest.mark.parametrize("invalid_content_hash", ["", " ", "   "])
def test_discovered_artwork_rejects_empty_or_whitespace_content_hash(
    invalid_content_hash: str,
) -> None:
    """Content hashes must contain a non-whitespace character."""

    with pytest.raises(ValueError) as error:
        DiscoveredArtwork(
            id="discovered-artwork-001",
            post_id="post-001",
            source_item_id="provider-media-42",
            content_hash=invalid_content_hash,
        )

    assert str(error.value) == "Content hash must not be empty or whitespace."
