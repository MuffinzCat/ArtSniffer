"""Tests for provider-neutral discovered posts."""

import pytest

from artsniffer.discovery.post import DiscoveredPost


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
