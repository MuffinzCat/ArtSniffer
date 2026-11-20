"""Tests for provider-neutral discovered posts."""

import pytest

from artsniffer.discovery.post import (
    DiscoveredArtwork,
    DiscoveredArtworkSourceMetadata,
    DiscoveredPost,
    DiscoveredPostProvenance,
    DiscoveredSourceLabel,
)


def test_discovered_post_preserves_required_fields_and_tags() -> None:
    """A valid post should preserve its metadata and provider-supplied tags."""

    post = DiscoveredPost(
        id="post-001",
        source_id="art-discovery",
        source_post_id="provider-post-42",
        creator_id="creator-7",
        url="opaque provider post reference",
        tags=("landscape", "watercolour", "landscape"),
    )

    assert post.id == "post-001"
    assert post.source_id == "art-discovery"
    assert post.source_post_id == "provider-post-42"
    assert post.creator_id == "creator-7"
    assert post.url == "opaque provider post reference"
    assert post.tags == ("landscape", "watercolour", "landscape")


def test_discovered_post_defaults_to_no_tags() -> None:
    """Tags should default to an empty tuple when none are supplied."""

    post = DiscoveredPost(
        id="post-001",
        source_id="art-discovery",
        source_post_id="provider-post-42",
        creator_id="creator-7",
        url="opaque provider post reference",
    )

    assert post.tags == ()


@pytest.mark.parametrize("invalid_id", ["", " ", "   "])
def test_discovered_post_rejects_empty_or_whitespace_id(invalid_id: str) -> None:
    """Discovered post IDs must contain a non-whitespace character."""

    with pytest.raises(ValueError) as error:
        DiscoveredPost(
            id=invalid_id,
            source_id="art-discovery",
            source_post_id="provider-post-42",
            creator_id="creator-7",
            url="opaque provider post reference",
        )

    assert str(error.value) == "Discovered post ID must not be empty or whitespace."


@pytest.mark.parametrize("invalid_source_id", ["", " ", "   "])
def test_discovered_post_rejects_empty_or_whitespace_source_id(
    invalid_source_id: str,
) -> None:
    """Source IDs must contain a non-whitespace character."""

    with pytest.raises(ValueError) as error:
        DiscoveredPost(
            id="post-001",
            source_id=invalid_source_id,
            source_post_id="provider-post-42",
            creator_id="creator-7",
            url="opaque provider post reference",
        )

    assert str(error.value) == "Source ID must not be empty or whitespace."


@pytest.mark.parametrize("invalid_source_post_id", ["", " ", "   "])
def test_discovered_post_rejects_empty_or_whitespace_source_post_id(
    invalid_source_post_id: str,
) -> None:
    """Provider post IDs must contain a non-whitespace character."""

    with pytest.raises(ValueError) as error:
        DiscoveredPost(
            id="post-001",
            source_id="art-discovery",
            source_post_id=invalid_source_post_id,
            creator_id="creator-7",
            url="opaque provider post reference",
        )

    assert str(error.value) == "Source post ID must not be empty or whitespace."


@pytest.mark.parametrize("invalid_creator_id", ["", " ", "   "])
def test_discovered_post_rejects_empty_or_whitespace_creator_id(
    invalid_creator_id: str,
) -> None:
    """Creator IDs must contain a non-whitespace character."""

    with pytest.raises(ValueError) as error:
        DiscoveredPost(
            id="post-001",
            source_id="art-discovery",
            source_post_id="provider-post-42",
            creator_id=invalid_creator_id,
            url="opaque provider post reference",
        )

    assert str(error.value) == "Creator ID must not be empty or whitespace."


@pytest.mark.parametrize("invalid_url", ["", " ", "   "])
def test_discovered_post_rejects_empty_or_whitespace_url(invalid_url: str) -> None:
    """Post URLs must contain a non-whitespace character."""

    with pytest.raises(ValueError) as error:
        DiscoveredPost(
            id="post-001",
            source_id="art-discovery",
            source_post_id="provider-post-42",
            creator_id="creator-7",
            url=invalid_url,
        )

    assert str(error.value) == "URL must not be empty or whitespace."


@pytest.mark.parametrize("invalid_tag", ["", " ", "   "])
def test_discovered_post_rejects_empty_or_whitespace_tag(invalid_tag: str) -> None:
    """Each supplied tag must contain at least one non-whitespace character."""

    with pytest.raises(ValueError) as error:
        DiscoveredPost(
            id="post-001",
            source_id="art-discovery",
            source_post_id="provider-post-42",
            creator_id="creator-7",
            url="opaque provider post reference",
            tags=(invalid_tag,),
        )

    assert str(error.value) == "Tag must not be empty or whitespace."


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


def test_discovered_artwork_defaults_content_hash_to_none() -> None:
    """An artwork discovered before hashing should default to no content hash."""

    artwork = DiscoveredArtwork(
        id="discovered-artwork-001",
        post_id="post-001",
        source_item_id="provider-media-42",
    )

    assert artwork.content_hash is None


def test_discovered_artwork_accepts_explicit_none_content_hash() -> None:
    """An explicit unknown content hash should remain None."""

    artwork = DiscoveredArtwork(
        id="discovered-artwork-001",
        post_id="post-001",
        source_item_id="provider-media-42",
        content_hash=None,
    )

    assert artwork.content_hash is None


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


def test_discovered_post_provenance_preserves_source_version() -> None:
    provenance = DiscoveredPostProvenance(
        post_id="post-001",
        source_version_id="bafy-post-cid",
    )

    assert provenance.post_id == "post-001"
    assert provenance.source_version_id == "bafy-post-cid"


@pytest.mark.parametrize("invalid_post_id", ["", " ", "   "])
def test_discovered_post_provenance_rejects_empty_post_id(invalid_post_id: str) -> None:
    with pytest.raises(ValueError, match=r"\APost ID must not be empty or whitespace\.\Z"):
        DiscoveredPostProvenance(
            post_id=invalid_post_id,
            source_version_id="bafy-post-cid",
        )


@pytest.mark.parametrize("invalid_version", ["", " ", "   "])
def test_discovered_post_provenance_rejects_empty_source_version(
    invalid_version: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"\ASource version ID must not be empty or whitespace\.\Z",
    ):
        DiscoveredPostProvenance(
            post_id="post-001",
            source_version_id=invalid_version,
        )


def test_discovered_artwork_source_metadata_accepts_empty_alt_text() -> None:
    metadata = DiscoveredArtworkSourceMetadata(
        artwork_id="artwork-001",
        source_media_id="bafy-image-cid",
        alt_text="",
    )

    assert metadata.artwork_id == "artwork-001"
    assert metadata.source_media_id == "bafy-image-cid"
    assert metadata.alt_text == ""


@pytest.mark.parametrize("invalid_artwork_id", ["", " ", "   "])
def test_discovered_artwork_source_metadata_rejects_empty_artwork_id(
    invalid_artwork_id: str,
) -> None:
    with pytest.raises(ValueError, match=r"\AArtwork ID must not be empty or whitespace\.\Z"):
        DiscoveredArtworkSourceMetadata(
            artwork_id=invalid_artwork_id,
            source_media_id="bafy-image-cid",
            alt_text="A caption",
        )


@pytest.mark.parametrize("invalid_media_id", ["", " ", "   "])
def test_discovered_artwork_source_metadata_rejects_empty_media_id(
    invalid_media_id: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"\ASource media ID must not be empty or whitespace\.\Z",
    ):
        DiscoveredArtworkSourceMetadata(
            artwork_id="artwork-001",
            source_media_id=invalid_media_id,
            alt_text="A caption",
        )


def test_discovered_source_label_preserves_hydrated_evidence() -> None:
    label = DiscoveredSourceLabel(
        src="did:plc:labeler",
        uri="at://did:plc:author/app.bsky.feed.post/rkey",
        cid="bafy-post-cid",
        val="art",
        ver=1,
        neg=False,
        cts="2026-11-20T12:00:00Z",
        exp="2027-11-20T12:00:00Z",
        hydrated=True,
    )

    assert label.src == "did:plc:labeler"
    assert label.cid == "bafy-post-cid"
    assert label.val == "art"
    assert label.hydrated is True
