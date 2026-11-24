"""Synthetic tests for the bounded e621/e926 JSON mapper."""

import pytest

from artsniffer.discovery.e621 import (
    E621DiscoveredPost,
    E621DiscoveryError,
    e621_discovered_post_from_json,
)


def representative_post() -> dict[str, object]:
    return {
        "id": 123,
        "change_seq": 456,
        "uploader_id": 10,
        "uploader_name": "Synthetic Uploader",
        "approver_id": 20,
        "created_at": "2026-11-20T12:00:00Z",
        "updated_at": "2026-11-21T12:00:00Z",
        "rating": "q",
        "tags": ["fox", "rating:questionable", "landscape"],
        "sources": [
            "https://example.test/source-one",
            "https://example.test/source-two",
        ],
        "pools": [7, 8],
        "relationships": {
            "parent_id": 122,
            "children": [124, 125],
        },
        "flags": {
            "deleted": False,
            "flagged": True,
            "note_locked": False,
            "pending": True,
            "rating_locked": False,
            "status_locked": True,
        },
        "files": {
            "meta": {
                "md5": "0123456789abcdef",
                "ext": "png",
                "size": 987654,
                "duration": 2.5,
                "has_sample": True,
            },
            "original": {
                "url": "https://example.test/original.png",
                "width": 1600,
                "height": 1200,
            },
            "sample": {
                "jpg": "https://example.test/sample.jpg",
                "webp": "https://example.test/sample.webp",
                "width": 800,
                "height": 600,
            },
            "preview": {
                "jpg": "https://example.test/preview.jpg",
                "webp": None,
                "width": 400,
                "height": 300,
            },
        },
    }


def map_post(
    post_data: dict[str, object] | None = None,
    *,
    host: str = "e621.net",
) -> E621DiscoveredPost:
    def allocate_post_id() -> str:
        return "post-1"

    def allocate_artwork_id() -> str:
        return "artwork-1"

    return e621_discovered_post_from_json(
        "e621-art",
        host,
        representative_post() if post_data is None else post_data,
        allocate_post_id,
        allocate_artwork_id,
    )


def test_representative_post_preserves_mapping() -> None:
    mapped = map_post()

    assert mapped.post.id == "post-1"
    assert mapped.post.source_id == "e621-art"
    assert mapped.post.source_post_id == "e621.net:123"
    assert mapped.post.creator_id is None
    assert mapped.post.url == "https://e621.net/posts/123"
    assert mapped.post.tags == ("fox", "rating:questionable", "landscape")
    assert mapped.artwork.id == "artwork-1"
    assert mapped.artwork.post_id == "post-1"
    assert mapped.artwork.source_item_id == "0123456789abcdef"
    assert mapped.artwork.content_hash is None
    assert mapped.provenance.post_id == "post-1"
    assert mapped.provenance.source_version_id == "456"


@pytest.mark.parametrize("host", ["e621.net", "e926.net"])
def test_provider_post_identity_is_scoped_by_host(host: str) -> None:
    mapped = map_post(host=host)

    assert mapped.post.source_post_id == f"{host}:123"
    assert mapped.post.url == f"https://{host}/posts/123"


def test_uploader_metadata_is_separate_from_creator_attribution() -> None:
    mapped = map_post()

    assert mapped.metadata.uploader_id == 10
    assert mapped.metadata.uploader_name == "Synthetic Uploader"
    assert mapped.post.creator_id is None


def test_rating_flags_sources_pools_and_relationships_are_preserved() -> None:
    mapped = map_post()

    assert mapped.rating.value == "q"
    assert mapped.flags.deleted is False
    assert mapped.flags.flagged is True
    assert mapped.flags.note_locked is False
    assert mapped.flags.pending is True
    assert mapped.flags.rating_locked is False
    assert mapped.flags.status_locked is True
    assert mapped.metadata.source_urls == (
        "https://example.test/source-one",
        "https://example.test/source-two",
    )
    assert mapped.metadata.pool_ids == (7, 8)
    assert mapped.metadata.parent_id == 122
    assert mapped.metadata.child_ids == (124, 125)
    assert mapped.metadata.approver_id == 20
    assert mapped.metadata.created_at == "2026-11-20T12:00:00Z"
    assert mapped.metadata.updated_at == "2026-11-21T12:00:00Z"


def test_original_and_optional_media_metadata_are_mapped() -> None:
    mapped = map_post()

    assert mapped.media.md5 == "0123456789abcdef"
    assert mapped.media.extension == "png"
    assert mapped.media.size_bytes == 987654
    assert mapped.media.duration == 2.5
    assert mapped.media.has_sample is True
    assert mapped.media.original_url == "https://example.test/original.png"
    assert mapped.media.width == 1600
    assert mapped.media.height == 1200
    assert mapped.media.sample is not None
    assert mapped.media.sample.jpg_url == "https://example.test/sample.jpg"
    assert mapped.media.sample.webp_url == "https://example.test/sample.webp"
    assert mapped.media.sample.width == 800
    assert mapped.media.sample.height == 600
    assert mapped.media.preview is not None
    assert mapped.media.preview.jpg_url == "https://example.test/preview.jpg"
    assert mapped.media.preview.webp_url is None


@pytest.mark.parametrize("variant", ["sample", "preview"])
def test_missing_optional_media_representation_is_none(variant: str) -> None:
    post = representative_post()
    files = post["files"]
    assert isinstance(files, dict)
    files[variant] = None

    mapped = map_post(post)

    assert getattr(mapped.media, variant) is None


@pytest.mark.parametrize("variant", ["sample", "preview"])
def test_missing_jpg_or_webp_variant_is_none(variant: str) -> None:
    post = representative_post()
    files = post["files"]
    assert isinstance(files, dict)
    representation = files[variant]
    assert isinstance(representation, dict)
    representation.pop("jpg")

    mapped = map_post(post)

    assert getattr(mapped.media, variant).jpg_url is None


def test_allocators_are_used_once_for_post_and_artwork_ids() -> None:
    post_ids: list[str] = []
    artwork_ids: list[str] = []

    def allocate_post_id() -> str:
        post_ids.append("post")
        return "allocated-post"

    def allocate_artwork_id() -> str:
        artwork_ids.append("artwork")
        return "allocated-artwork"

    mapped = e621_discovered_post_from_json(
        "e621-art",
        "e621.net",
        representative_post(),
        allocate_post_id,
        allocate_artwork_id,
    )

    assert post_ids == ["post"]
    assert artwork_ids == ["artwork"]
    assert mapped.post.id == "allocated-post"
    assert mapped.artwork.id == "allocated-artwork"


@pytest.mark.parametrize("host", ["", "example.com", "E621.NET"])
def test_invalid_host_is_rejected(host: str) -> None:
    with pytest.raises(E621DiscoveryError, match="host"):
        map_post(host=host)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", True),
        ("id", "123"),
        ("change_seq", False),
        ("change_seq", "456"),
        ("uploader_id", True),
        ("uploader_id", "10"),
        ("uploader_name", ""),
        ("uploader_name", " \t "),
        ("approver_id", True),
        ("approver_id", "20"),
        ("created_at", ""),
        ("created_at", " \t "),
        ("updated_at", ""),
        ("updated_at", " \t "),
        ("rating", ""),
        ("rating", "unknown"),
    ],
)
def test_malformed_required_scalar_fields_are_rejected(
    field: str,
    value: object,
) -> None:
    post = representative_post()
    post[field] = value

    with pytest.raises(E621DiscoveryError):
        map_post(post)


@pytest.mark.parametrize(
    "field",
    [
        "id",
        "change_seq",
        "uploader_id",
        "uploader_name",
        "created_at",
        "rating",
        "tags",
        "sources",
        "pools",
        "flags",
        "relationships",
        "files",
    ],
)
def test_missing_required_fields_are_rejected(field: str) -> None:
    post = representative_post()
    post.pop(field)

    with pytest.raises(E621DiscoveryError):
        map_post(post)


@pytest.mark.parametrize(
    ("tags", "message"),
    [
        ("fox", "tags"),
        (["fox", 12], "tag"),
        (["fox", ""], "tag"),
        (["fox", " \t "], "tag"),
    ],
)
def test_malformed_tags_are_rejected(tags: object, message: str) -> None:
    post = representative_post()
    post["tags"] = tags

    with pytest.raises(E621DiscoveryError, match=message):
        map_post(post)


@pytest.mark.parametrize(
    ("sources", "message"),
    [
        ("https://example.test", "sources"),
        ([12], "source URL"),
        ([""], "source URL"),
        ([" \t "], "source URL"),
    ],
)
def test_malformed_sources_are_rejected(sources: object, message: str) -> None:
    post = representative_post()
    post["sources"] = sources

    with pytest.raises(E621DiscoveryError, match=message):
        map_post(post)


@pytest.mark.parametrize(
    ("pools", "message"),
    [
        ("7", "pools"),
        ([True], "pool ID"),
        ([7, "8"], "pool ID"),
    ],
)
def test_malformed_pools_are_rejected(pools: object, message: str) -> None:
    post = representative_post()
    post["pools"] = pools

    with pytest.raises(E621DiscoveryError, match=message):
        map_post(post)


@pytest.mark.parametrize(
    ("flags", "missing"),
    [
        ({"deleted": False}, "flagged"),
        (
            {
                "deleted": False,
                "flagged": False,
                "note_locked": False,
                "pending": False,
                "rating_locked": False,
                "status_locked": "false",
            },
            "status_locked",
        ),
    ],
)
def test_malformed_flags_are_rejected(flags: object, missing: str) -> None:
    post = representative_post()
    post["flags"] = flags

    with pytest.raises(E621DiscoveryError, match=missing):
        map_post(post)


@pytest.mark.parametrize(
    ("relationships", "message"),
    [
        ("relationships", "relationships"),
        ({"parent_id": True, "children": []}, "parent ID"),
        ({"parent_id": "122", "children": []}, "parent ID"),
        ({"parent_id": None, "children": "124"}, "child IDs"),
        ({"parent_id": None, "children": [True]}, "child ID"),
        ({"parent_id": None, "children": ["124"]}, "child ID"),
    ],
)
def test_malformed_relationships_are_rejected(
    relationships: object,
    message: str,
) -> None:
    post = representative_post()
    post["relationships"] = relationships

    with pytest.raises(E621DiscoveryError, match=message):
        map_post(post)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("md5", "", "MD5"),
        ("md5", 12, "MD5"),
        ("ext", "", "extension"),
        ("ext", 12, "extension"),
        ("size", True, "size"),
        ("size", "987654", "size"),
        ("duration", True, "duration"),
        ("duration", "2.5", "duration"),
        ("duration", -1, "duration"),
        ("has_sample", "true", "has_sample"),
    ],
)
def test_malformed_media_metadata_is_rejected(
    field: str,
    value: object,
    message: str,
) -> None:
    post = representative_post()
    files = post["files"]
    assert isinstance(files, dict)
    meta = files["meta"]
    assert isinstance(meta, dict)
    meta[field] = value

    with pytest.raises(E621DiscoveryError, match=message):
        map_post(post)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("url", "", "original media URL"),
        ("url", 12, "original media URL"),
        ("width", True, "width"),
        ("width", "1600", "width"),
        ("height", False, "height"),
        ("height", "1200", "height"),
    ],
)
def test_malformed_original_media_is_rejected(
    field: str,
    value: object,
    message: str,
) -> None:
    post = representative_post()
    files = post["files"]
    assert isinstance(files, dict)
    original = files["original"]
    assert isinstance(original, dict)
    original[field] = value

    with pytest.raises(E621DiscoveryError, match=message):
        map_post(post)


@pytest.mark.parametrize("variant", ["sample", "preview"])
@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("jpg", "", "jpg"),
        ("jpg", 12, "jpg"),
        ("webp", "", "webp"),
        ("webp", 12, "webp"),
        ("width", True, "width"),
        ("width", "800", "width"),
        ("height", False, "height"),
        ("height", "600", "height"),
    ],
)
def test_malformed_media_representation_is_rejected(
    variant: str,
    field: str,
    value: object,
    message: str,
) -> None:
    post = representative_post()
    files = post["files"]
    assert isinstance(files, dict)
    representation = files[variant]
    assert isinstance(representation, dict)
    representation[field] = value

    with pytest.raises(E621DiscoveryError, match=message):
        map_post(post)


def test_source_id_must_be_non_empty() -> None:
    with pytest.raises(E621DiscoveryError, match="source ID"):
        e621_discovered_post_from_json(
            " ",
            "e621.net",
            representative_post(),
            lambda: "post",
            lambda: "artwork",
        )


def test_post_must_be_a_dictionary() -> None:
    with pytest.raises(E621DiscoveryError, match="post"):
        e621_discovered_post_from_json(
            "e621-art",
            "e621.net",
            [],  # type: ignore[arg-type]
            lambda: "post",
            lambda: "artwork",
        )
