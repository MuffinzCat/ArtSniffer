"""Synthetic tests for the bounded Bluesky getFeed adapter."""

from collections.abc import Callable
from email.message import Message
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from artsniffer.discovery.bluesky import (
    BlueskyDiscoveredPost,
    BlueskyDiscoveryError,
    BlueskyUnmappedPost,
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
        "record": {
            "text": "Synthetic post",
            "embed": {
                "$type": "app.bsky.embed.images",
                "images": [
                    {
                        "alt": alt,
                        "image": {"ref": {"$link": cid}},
                    }
                ],
            },
        },
        "embed": {
            "$type": "app.bsky.embed.images#view",
            "images": [
                {
                    "alt": alt,
                    "thumb": "https://cdn.bsky.app/img/feed_thumbnail/plain/did/image",
                    "fullsize": "https://cdn.bsky.app/img/feed_fullsize/plain/did/image",
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
    record = post["record"]
    assert isinstance(record, dict)
    embed = record["embed"]
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
    record = post["record"]
    assert isinstance(record, dict)
    record["embed"] = {
        "$type": "app.bsky.embed.gallery",
        "items": [
            {
                "$type": "app.bsky.embed.gallery#item",
                "alt": "Gallery alt",
                "image": {"ref": {"$link": "bafy-gallery"}},
            }
        ],
    }
    post["embed"] = {
        "$type": "app.bsky.embed.gallery#view",
        "items": [
            {
                "alt": "Gallery alt",
                "thumb": "https://cdn.bsky.app/gallery-thumbnail",
                "fullsize": "https://cdn.bsky.app/gallery-fullsize",
            }
        ],
    }

    mapped = map_post(post)

    assert mapped.artworks[0].source_item_id.endswith("#image-0")
    assert mapped.artwork_metadata[0].source_media_id == "bafy-gallery"
    assert mapped.artwork_metadata[0].alt_text == "Gallery alt"


def test_record_with_media_maps_only_direct_media() -> None:
    post = image_post()
    record = post["record"]
    assert isinstance(record, dict)
    record["embed"] = {
        "$type": "app.bsky.embed.recordWithMedia",
        "record": {"$ref": "quoted-post"},
        "media": {
            "$type": "app.bsky.embed.images",
            "images": [{"alt": "Direct", "image": {"ref": {"$link": "bafy-direct"}}}],
        },
    }
    post["embed"] = {
        "$type": "app.bsky.embed.recordWithMedia#view",
        "record": {"record": {"uri": "at://did:plc:quoted/app.bsky.feed.post/rkey"}},
        "media": {
            "$type": "app.bsky.embed.images#view",
            "images": [
                {
                    "alt": "Direct",
                    "thumb": "https://cdn.bsky.app/direct-thumbnail",
                    "fullsize": "https://cdn.bsky.app/direct-fullsize",
                }
            ],
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
    record = post["record"]
    assert isinstance(record, dict)
    record["embed"] = embed

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
            "sig": {"unknown": "representation"},
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
        ("embed", "embed", "Bluesky raw record embed must be a dictionary"),
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
        ("embed.$type", 42, "Bluesky raw record embed type must be a string"),
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
        record = post["record"]
        assert isinstance(record, dict)
        embed = record["embed"]
        assert isinstance(embed, dict)
        embed["$type"] = value
    elif path == "embed.images":
        record = post["record"]
        assert isinstance(record, dict)
        embed = record["embed"]
        assert isinstance(embed, dict)
        embed["images"] = value
    elif path == "embed.image_item":
        record = post["record"]
        assert isinstance(record, dict)
        embed = record["embed"]
        assert isinstance(embed, dict)
        embed["images"] = [value]
    elif path == "embed.alt":
        record = post["record"]
        assert isinstance(record, dict)
        embed = record["embed"]
        assert isinstance(embed, dict)
        images = embed["images"]
        assert isinstance(images, list)
        assert isinstance(images[0], dict)
        images[0]["alt"] = value
    elif path == "embed.blob":
        record = post["record"]
        assert isinstance(record, dict)
        embed = record["embed"]
        assert isinstance(embed, dict)
        images = embed["images"]
        assert isinstance(images, list)
        assert isinstance(images[0], dict)
        images[0]["image"] = value
    elif path == "embed.ref":
        record = post["record"]
        assert isinstance(record, dict)
        embed = record["embed"]
        assert isinstance(embed, dict)
        images = embed["images"]
        assert isinstance(images, list)
        assert isinstance(images[0], dict)
        images[0]["image"] = {"ref": value}
    elif path == "embed.cid":
        record = post["record"]
        assert isinstance(record, dict)
        embed = record["embed"]
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
        self.closed = False

    def read(self) -> bytes:
        import json

        return json.dumps(self.payload).encode("utf-8")

    def close(self) -> None:
        self.closed = True


def test_fetch_feed_constructs_query_and_maps_one_page() -> None:
    settings = BlueskyDiscoverySettings(
        source_id="bluesky",
        feed_uri="at://did:plc:feed/app.bsky.feed.generator/discover",
        limit=12,
        timeout_seconds=3,
    )
    seen_request: Request | None = None
    seen_response: FakeResponse | None = None

    def opener(request: Request, *, timeout: float) -> FakeResponse:
        nonlocal seen_request
        nonlocal seen_response
        seen_request = request
        assert timeout == 3
        seen_response = FakeResponse({"feed": [{"post": image_post()}], "cursor": "next page"})
        return seen_response

    page = fetch_bluesky_feed(
        settings,
        cursor="page 1",
        opener=opener,
        allocate_post_id=allocate("post"),
        allocate_artwork_id=allocate("artwork"),
    )

    assert seen_request is not None
    assert "app.bsky.feed.getFeed" in seen_request.full_url
    assert "feed=at%3A%2F%2F" in seen_request.full_url
    assert "limit=12" in seen_request.full_url
    assert "cursor=page+1" in seen_request.full_url
    assert seen_request.headers["Accept"] == "application/json"
    assert "Authorization" not in seen_request.headers
    assert len(page.entries) == 1
    assert page.cursor == "next page"
    assert seen_response is not None
    assert seen_response.closed is True


def test_fetch_feed_mixed_supported_and_unsupported_entries() -> None:
    unsupported = image_post()
    record = unsupported["record"]
    assert isinstance(record, dict)
    record["embed"] = {"$type": "app.bsky.embed.external"}
    settings = BlueskyDiscoverySettings(
        source_id="bluesky",
        feed_uri="at://did:plc:feed/app.bsky.feed.generator/discover",
    )

    page = fetch_bluesky_feed(
        settings,
        opener=lambda _request, **_kwargs: FakeResponse(
            {"feed": [{"post": image_post()}, {"post": unsupported}, {"post": None}]}
        ),
        allocate_post_id=allocate("post"),
        allocate_artwork_id=allocate("artwork"),
    )

    assert len(page.entries) == 3
    assert isinstance(page.entries[1], BlueskyUnmappedPost)
    assert isinstance(page.entries[2], BlueskyUnmappedPost)


def test_same_post_mapping_is_independent_of_feed_position() -> None:
    post = image_post()
    first = map_post(post)

    post_id_calls = 0
    artwork_id_calls = 0

    def post_allocator() -> str:
        nonlocal post_id_calls
        post_id_calls += 1
        return "stable-post-id"

    def artwork_allocator() -> str:
        nonlocal artwork_id_calls
        artwork_id_calls += 1
        return "stable-artwork-id"

    settings = BlueskyDiscoverySettings(
        source_id="bluesky",
        feed_uri="at://did:plc:feed/app.bsky.feed.generator/discover",
    )
    page = fetch_bluesky_feed(
        settings,
        opener=lambda _request, **_kwargs: FakeResponse(
            {"feed": [{"reason": "ignored"}, {"post": post}]}
        ),
        allocate_post_id=post_allocator,
        allocate_artwork_id=artwork_allocator,
    )

    mapped = page.entries[1]
    assert isinstance(mapped, BlueskyDiscoveredPost)
    assert mapped.post.source_post_id == first.post.source_post_id
    assert mapped.artwork_metadata[0].source_media_id == "bafy-image"
    assert post_id_calls == 1
    assert artwork_id_calls == 1


def test_shared_allocators_do_not_reset_or_collide_across_pages() -> None:
    settings = BlueskyDiscoverySettings(
        source_id="bluesky",
        feed_uri="at://did:plc:feed/app.bsky.feed.generator/discover",
    )
    post_ids = allocate("post")
    artwork_ids = allocate("artwork")

    first = fetch_bluesky_feed(
        settings,
        opener=lambda _request, **_kwargs: FakeResponse({"feed": [{"post": image_post()}]}),
        allocate_post_id=post_ids,
        allocate_artwork_id=artwork_ids,
    )
    second = fetch_bluesky_feed(
        settings,
        cursor="next",
        opener=lambda _request, **_kwargs: FakeResponse({"feed": [{"post": image_post()}]}),
        allocate_post_id=post_ids,
        allocate_artwork_id=artwork_ids,
    )

    first_post = first.entries[0]
    second_post = second.entries[0]
    assert isinstance(first_post, BlueskyDiscoveredPost)
    assert isinstance(second_post, BlueskyDiscoveredPost)
    assert first_post.post.id != second_post.post.id
    assert first_post.artworks[0].id != second_post.artworks[0].id


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
            allocate_post_id=allocate("post"),
            allocate_artwork_id=allocate("artwork"),
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
        fetch_bluesky_feed(
            settings,
            opener=fail,
            allocate_post_id=allocate("post"),
            allocate_artwork_id=allocate("artwork"),
        )


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
            allocate_post_id=allocate("post"),
            allocate_artwork_id=allocate("artwork"),
        )
