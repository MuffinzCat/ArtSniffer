"""Tests for provider-neutral ArtSniffer artwork records."""

import pytest

from artsniffer.references.artwork import ArtworkRecord


def test_artwork_record_preserves_all_fields() -> None:
    """A valid artwork record should preserve each supplied identifier."""

    artwork = ArtworkRecord(
        id="artwork-001",
        source_id="local-library",
        source_item_id="provider-item-42",
        content_hash="sha256:abc123",
    )

    assert artwork.id == "artwork-001"
    assert artwork.source_id == "local-library"
    assert artwork.source_item_id == "provider-item-42"
    assert artwork.content_hash == "sha256:abc123"


@pytest.mark.parametrize("invalid_id", ["", " ", "   "])
def test_artwork_record_rejects_empty_or_whitespace_id(invalid_id: str) -> None:
    """Artwork IDs must contain at least one non-whitespace character."""

    with pytest.raises(
        ValueError,
        match=r"\AArtwork ID must not be empty or whitespace\.\Z",
    ):
        ArtworkRecord(
            id=invalid_id,
            source_id="local-library",
            source_item_id="provider-item-42",
            content_hash="sha256:abc123",
        )


@pytest.mark.parametrize("invalid_source_id", ["", " ", "   "])
def test_artwork_record_rejects_empty_or_whitespace_source_id(
    invalid_source_id: str,
) -> None:
    """Source IDs must contain at least one non-whitespace character."""

    with pytest.raises(
        ValueError,
        match=r"\ASource ID must not be empty or whitespace\.\Z",
    ):
        ArtworkRecord(
            id="artwork-001",
            source_id=invalid_source_id,
            source_item_id="provider-item-42",
            content_hash="sha256:abc123",
        )


@pytest.mark.parametrize("invalid_source_item_id", ["", " ", "   "])
def test_artwork_record_rejects_empty_or_whitespace_source_item_id(
    invalid_source_item_id: str,
) -> None:
    """Provider item IDs must contain at least one non-whitespace character."""

    with pytest.raises(
        ValueError,
        match=r"\ASource item ID must not be empty or whitespace\.\Z",
    ):
        ArtworkRecord(
            id="artwork-001",
            source_id="local-library",
            source_item_id=invalid_source_item_id,
            content_hash="sha256:abc123",
        )


@pytest.mark.parametrize("invalid_content_hash", ["", " ", "   "])
def test_artwork_record_rejects_empty_or_whitespace_content_hash(
    invalid_content_hash: str,
) -> None:
    """Content hashes must contain at least one non-whitespace character."""

    with pytest.raises(
        ValueError,
        match=r"\AContent hash must not be empty or whitespace\.\Z",
    ):
        ArtworkRecord(
            id="artwork-001",
            source_id="local-library",
            source_item_id="provider-item-42",
            content_hash=invalid_content_hash,
        )
