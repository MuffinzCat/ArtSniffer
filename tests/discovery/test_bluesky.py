"""Synthetic tests for the bounded Bluesky getFeed adapter."""

from collections.abc import Callable
from email.message import Message
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from artsniffer.discovery.bluesky import (
    BlueskyDiscoveryError,
    BlueskyUnsupportedPost,
    UnsupportedBlueskyEmbedError,
    bluesky_discovered_post_from_json,
    bluesky_post_url,
    fetch_bluesky_feed,
)
from artsniffer.settings import BlueskyDiscoverySettings


def image_post(*, alt: str = "A landscape", cid: str = "bafy-image") -> dict[str, object]:
    return {
        "uri": "at://did:plc:author/app.bsky.feed.post/rkey",
        "cid": "bafy-post",
        "author": {"did": "did:plc:author"},
        "record": {"text": "Synthetic post"},
        "embed": {
            "$type": "app.bsky.embed.images",
            "images": [
                {
                    "alt": alt,
                    "image": {"ref": {"$link": cid}},
                }
            ],
        },
    }


def allocate(label: str) -> Callable[[], str]:
    counter = 0

    def next_id() -> str:
        nonlocal counter
        counter += 1
        return f"{label}-{counter}"

    return next_id


def map_post(post: dict[str, object]) -> Any:
    return bluesky_discovered_post_from_json(
        "bluesky",
        post,
        allocate("post"),
        allocate("artwork"),
    )


def test_post_url_uses_author_did() -> None:
    assert (
        bluesky_post_url("at://did:plc:author/app.bsky.feed.post/rkey")
        == "https://bsky.app/profile/did:plc:author/post/rkey"
    )


def test_single_image_preserves_identity_and_empty_alt_text() -> None:
    mapped = map_post(image_post(alt=""))

    assert mapped.post.source_post_id == ("at://did:plc:author/app.bsky.feed.post/rkey")
    assert mapped.post.creator_id == "did:plc:author"
    assert mapped.post.url == "https://bsky.app/profile/did:plc:author/post/rkey"
    assert mapped.provenance.source_version_id == "bafy-post"
    assert len(mapped.artworks) == 1
    assert mapped.artworks[0].source_item_id == (
        "at://did:plc:author/app.bsky.feed.post/rkey#image-0"
    )
    assert mapped.artworks[0].content_hash is None
    assert mapped.artwork_metadata[0].artwork_id == mapped.artworks[0].id
    assert mapped.artwork_metadata[0].source_media_id == "bafy-image"
    assert mapped.artwork_metadata[0].alt_text == ""


def test_multi_image_allocates_one_post_and_distinct_media_ids() -> None:
    post = image_post()
    embed = post["embed"]
    assert isinstance(embed, dict)
    embed["images"] = [
        {"alt": "First", "image": {"ref": {"$link": "bafy-one"}}},
        {"alt": "Second", "image": {"ref": {"$link": "bafy-two"}}},
    ]

    mapped = map_post(post)

    assert len({artwork.post_id for artwork in mapped.artworks}) == 1
    assert len({artwork.id for artwork in mapped.artworks}) == 2
    assert [artwork.source_item_id for artwork in mapped.artworks] == [
        "at://did:plc:author/app.bsky.feed.post/rkey#image-0",
        "at://did:plc:author/app.bsky.feed.post/rkey#image-1",
    ]
    assert [metadata.source_media_id for metadata in mapped.artwork_metadata] == [
        "bafy-one",
        "bafy-two",
    ]


def test_gallery_shape_maps_direct_images() -> None:
    post = image_post()
    post["embed"] = {
        "$type": "app.bsky.embed.gallery",
        "items": [
            {
                "$type": "app.bsky.embed.gallery#item",
                "alt": "Gallery alt",
                "image": {"ref": {"$link": "bafy-gallery"}},
            }
        ],
    }

    mapped = map_post(post)

    assert mapped.artworks[0].source_item_id.endswith("#image-0")
    assert mapped.artwork_metadata[0].source_media_id == "bafy-gallery"
    assert mapped.artwork_metadata[0].alt_text == "Gallery alt"


def test_record_with_media_maps_only_direct_media() -> None:
    post = image_post()
    post["embed"] = {
        "$type": "app.bsky.embed.recordWithMedia",
        "record": {"$ref": "quoted-post"},
        "media": {
            "$type": "app.bsky.embed.images",
            "images": [{"alt": "Direct", "image": {"ref": {"$link": "bafy-direct"}}}],
        },
    }

    mapped = map_post(post)

    assert mapped.artwork_metadata[0].source_media_id == "bafy-direct"
    assert len(mapped.artworks) == 1


@pytest.mark.parametrize(
    "embed",
    [
        {"$type": "app.bsky.embed.record"},
        {"$type": "app.bsky.embed.external"},
        {"$type": "app.bsky.embed.video"},
        {"$type": "app.bsky.embed.unknown"},
    ],
)
def test_unsupported_embeds_are_explicit(embed: dict[str, object]) -> None:
    post = image_post()
    post["embed"] = embed

    with pytest.raises(UnsupportedBlueskyEmbedError):
        map_post(post)


def test_hydrated_labels_are_preserved_as_evidence() -> None:
    post = image_post()
    post["labels"] = [
        {
            "src": "did:plc:labeler",
            "uri": "at://did:plc:author/app.bsky.feed.post/rkey",
            "cid": "bafy-post",
            "val": "art",
            "ver": 1,
            "neg": False,
            "cts": "2026-11-20T12:00:00Z",
            "exp": "2027-11-20T12:00:00Z",
            "sig": "signature",
        }
    ]

    mapped = map_post(post)

    assert len(mapped.labels) == 1
    assert mapped.labels[0].src == "did:plc:labeler"
    assert mapped.labels[0].val == "art"
    assert mapped.labels[0].hydrated is True


@pytest.mark.parametrize(
    ("label", "message"),
    [
        ("not a dictionary", "Each Bluesky label must be a dictionary"),
        (
            {"src": "did:plc:labeler", "uri": 42},
            "Bluesky label URI must be a string",
        ),
        (
            {"src": "did:plc:labeler", "uri": "at://post", "val": "art", "cts": 42},
            "Bluesky label cts must be a string",
        ),
    ],
)
def test_malformed_hydrated_labels_are_provider_boundary_errors(
    label: object,
    message: str,
) -> None:
    post = image_post()
    post["labels"] = [label]

    with pytest.raises(BlueskyDiscoveryError, match=message):
        map_post(post)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("uri", 42, "Bluesky post URI must be a string"),
        ("cid", 42, "Bluesky post CID must be a string"),
        ("author", "author", "Bluesky author must be a dictionary"),
        ("record", "record", "Bluesky record must be a dictionary"),
        ("embed", "embed", "Bluesky embed must be a dictionary"),
    ],
)
def test_malformed_post_fields_are_provider_boundary_errors(
    field: str,
    value: object,
    message: str,
) -> None:
    post = image_post()
    post[field] = value
    if field == "embed":
        post["record"] = {"embed": value}

    with pytest.raises(BlueskyDiscoveryError, match=message):
        map_post(post)


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        ("author.did", 42, "Bluesky author DID must be a string"),
        ("embed.$type", 42, "Bluesky embed type must be a string"),
        ("embed.images", "images", "Bluesky images must be a list"),
        ("embed.image_item", "item", "Each Bluesky image must be a dictionary"),
        ("embed.alt", 42, "Bluesky image alt text must be a string"),
        ("embed.blob", "blob", "Bluesky image blob must be a dictionary"),
        ("embed.ref", "ref", "Bluesky image blob ref must be a dictionary"),
        ("embed.cid", 42, "Bluesky image blob CID must be a string"),
    ],
)
def test_malformed_nested_fields_are_provider_boundary_errors(
    path: str,
    value: object,
    message: str,
) -> None:
    post = image_post()
    if path == "author.did":
        post["author"] = {"did": value}
    elif path == "embed.$type":
        embed = post["embed"]
        assert isinstance(embed, dict)
        embed["$type"] = value
    elif path == "embed.images":
        embed = post["embed"]
        assert isinstance(embed, dict)
        embed["images"] = value
    elif path == "embed.image_item":
        embed = post["embed"]
        assert isinstance(embed, dict)
        embed["images"] = [value]
    elif path == "embed.alt":
        embed = post["embed"]
        assert isinstance(embed, dict)
        images = embed["images"]
        assert isinstance(images, list)
        assert isinstance(images[0], dict)
        images[0]["alt"] = value
    elif path == "embed.blob":
        embed = post["embed"]
        assert isinstance(embed, dict)
        images = embed["images"]
        assert isinstance(images, list)
        assert isinstance(images[0], dict)
        images[0]["image"] = value
    elif path == "embed.ref":
        embed = post["embed"]
        assert isinstance(embed, dict)
        images = embed["images"]
        assert isinstance(images, list)
        assert isinstance(images[0], dict)
        images[0]["image"] = {"ref": value}
    elif path == "embed.cid":
        embed = post["embed"]
        assert isinstance(embed, dict)
        images = embed["images"]
        assert isinstance(images, list)
        assert isinstance(images[0], dict)
        images[0]["image"] = {"ref": {"$link": value}}

    with pytest.raises(BlueskyDiscoveryError, match=message):
        map_post(post)


class FakeResponse:
    def __init__(self, payload: object, status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def read(self) -> bytes:
        import json

        return json.dumps(self.payload).encode("utf-8")


def test_fetch_feed_constructs_query_and_maps_one_page() -> None:
    settings = BlueskyDiscoverySettings(
        source_id="bluesky",
        feed_uri="at://did:plc:feed/app.bsky.feed.generator/discover",
        limit=12,
        timeout_seconds=3,
    )
    seen_request: Request | None = None

    def opener(request: Request, *, timeout: float) -> FakeResponse:
        nonlocal seen_request
        seen_request = request
        assert timeout == 3
        return FakeResponse({"feed": [{"post": image_post()}], "cursor": "next page"})

    page = fetch_bluesky_feed(settings, cursor="page 1", opener=opener)

    assert seen_request is not None
    assert "app.bsky.feed.getFeed" in seen_request.full_url
    assert "feed=at%3A%2F%2F" in seen_request.full_url
    assert "limit=12" in seen_request.full_url
    assert "cursor=page+1" in seen_request.full_url
    assert seen_request.headers["Accept"] == "application/json"
    assert "Authorization" not in seen_request.headers
    assert len(page.entries) == 1
    assert page.cursor == "next page"


def test_fetch_feed_mixed_supported_and_unsupported_entries() -> None:
    unsupported = image_post()
    unsupported["embed"] = {"$type": "app.bsky.embed.external"}
    settings = BlueskyDiscoverySettings(
        source_id="bluesky",
        feed_uri="at://did:plc:feed/app.bsky.feed.generator/discover",
    )

    page = fetch_bluesky_feed(
        settings,
        opener=lambda _request, **_kwargs: FakeResponse(
            {"feed": [{"post": image_post()}, {"post": unsupported}, {"post": None}]}
        ),
    )

    assert len(page.entries) == 3
    assert isinstance(page.entries[1], BlueskyUnsupportedPost)
    assert isinstance(page.entries[2], BlueskyUnsupportedPost)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "Bluesky getFeed payload must be a dictionary"),
        ({}, "Bluesky getFeed feed must be a list"),
        ({"feed": "not a list"}, "Bluesky getFeed feed must be a list"),
        ({"feed": [], "cursor": 42}, "Bluesky getFeed cursor must be a string"),
    ],
)
def test_fetch_feed_rejects_malformed_top_level_payload(
    payload: object,
    message: str,
) -> None:
    settings = BlueskyDiscoverySettings(
        source_id="bluesky",
        feed_uri="at://did:plc:feed/app.bsky.feed.generator/discover",
    )

    with pytest.raises(BlueskyDiscoveryError, match=message):
        fetch_bluesky_feed(
            settings,
            opener=lambda _request, **_kwargs: FakeResponse(payload),
        )


def test_fetch_feed_reports_http_error_without_retry() -> None:
    settings = BlueskyDiscoverySettings(
        source_id="bluesky",
        feed_uri="at://did:plc:feed/app.bsky.feed.generator/discover",
    )

    def fail(_request: Request, **_kwargs: object) -> FakeResponse:
        raise HTTPError(
            "https://public.api.bsky.app/xrpc/app.bsky.feed.getFeed",
            403,
            "Forbidden",
            Message(),
            None,
        )

    with pytest.raises(
        BlueskyDiscoveryError,
        match="Bluesky getFeed returned HTTP 403",
    ):
        fetch_bluesky_feed(settings, opener=fail)


def test_fetch_feed_rejects_non_json_response() -> None:
    settings = BlueskyDiscoverySettings(
        source_id="bluesky",
        feed_uri="at://did:plc:feed/app.bsky.feed.generator/discover",
    )

    class HtmlResponse:
        status = 200

        def read(self) -> bytes:
            return b"<html>proxy error</html>"

    with pytest.raises(
        BlueskyDiscoveryError,
        match="Bluesky getFeed returned a non-JSON response",
    ):
        fetch_bluesky_feed(
            settings,
            opener=lambda _request, **_kwargs: HtmlResponse(),
        )
