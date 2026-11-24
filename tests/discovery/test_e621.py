"""Synthetic tests for the bounded e621/e926 JSON mapper."""

import json
from email.message import Message
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest

from artsniffer.discovery.e621 import (
    E621DiscoveredPost,
    E621DiscoveryError,
    E621UnmappedPost,
    e621_discovered_post_from_json,
    e621_user_agent,
    fetch_e621_posts,
)
from artsniffer.persistence.e621_discovery_state import (
    E621DiscoveryState,
    SQLiteE621DiscoveryStateStore,
)
from artsniffer.settings import E621DiscoverySettings


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


class FakeResponse:
    def __init__(
        self,
        payload: object,
        *,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status = status
        self.headers = headers or {}
        self.closed = False
        self._body = json.dumps(payload).encode("utf-8")

    def read(self, size: int = -1) -> bytes:
        if size >= 0:
            return self._body[:size]
        return self._body

    def close(self) -> None:
        self.closed = True


class OversizedResponse:
    status = 200

    def __init__(self) -> None:
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        return b"x" * size

    def close(self) -> None:
        self.closed = True


def post_with_id(post_id: int) -> dict[str, object]:
    post = representative_post()
    post["id"] = post_id
    return post


def allocate(label: str):
    counter = 0

    def next_id() -> str:
        nonlocal counter
        counter += 1
        return f"{label}-{counter}"

    return next_id


def test_user_agent_contains_application_identity_and_contact() -> None:
    user_agent = e621_user_agent("owner@example.test")

    assert user_agent.startswith("ArtSniffer/")
    assert "(+owner@example.test)" in user_agent


@pytest.mark.parametrize("host", ["e621.net", "e926.net"])
def test_fetch_constructs_request_url_limit_timeout_and_user_agent(
    tmp_path,
    host: str,
) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    settings = E621DiscoverySettings(
        source_id="art",
        host=host,
        tag_search_expressions=("fox rating:safe",),
        client_contact="owner@example.test",
        limit=2,
        timeout_seconds=3.5,
    )
    seen_request: Request | None = None
    seen_timeout: float | None = None
    seen_response = FakeResponse([])

    def opener(request: Request, *, timeout: float) -> FakeResponse:
        nonlocal seen_request, seen_timeout
        seen_request = request
        seen_timeout = timeout
        return seen_response

    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=opener,
            sleeper=lambda _seconds: None,
        )
    finally:
        store.close()

    assert result.catch_up_complete is True
    assert seen_request is not None
    assert seen_request.full_url.startswith(f"https://{host}/posts.json?")
    assert "tags=fox+rating%3Asafe" in seen_request.full_url
    assert "limit=2" in seen_request.full_url
    assert "page=" not in seen_request.full_url
    assert seen_timeout == 3.5
    assert seen_request.headers["User-agent"].startswith("ArtSniffer/")
    assert "(+owner@example.test)" in seen_request.headers["User-agent"]
    assert seen_request.headers["Accept"] == "application/json"
    assert seen_response.closed is True


def test_first_run_establishes_watermark_without_emitting_backlog(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox",),
        client_contact="owner@example.test",
    )
    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=lambda _request, **_kwargs: FakeResponse(
                [post_with_id(6880578), post_with_id(6879238)]
            ),
            sleeper=lambda _seconds: None,
        )
        state = store.get("art", "e621.net", "fox")
    finally:
        store.close()

    assert result.entries == ()
    assert result.high_watermark == 6880578
    assert state.high_watermark == 6880578
    assert state.catch_up_incomplete is False


def test_subsequent_scan_emits_only_posts_above_watermark(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    store.save(
        E621DiscoveryState(
            source_id="art",
            host="e621.net",
            tag_search_expression="fox",
            high_watermark=6879238,
        )
    )
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox",),
        client_contact="owner@example.test",
    )
    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=lambda _request, **_kwargs: FakeResponse(
                [post_with_id(6880578), post_with_id(6879238), post_with_id(6879235)]
            ),
            sleeper=lambda _seconds: None,
        )
        state = store.get("art", "e621.net", "fox")
    finally:
        store.close()

    assert len(result.entries) == 1
    entry = result.entries[0]
    assert isinstance(entry, E621DiscoveredPost)
    assert entry.post.source_post_id == "e621.net:6880578"
    assert result.high_watermark == 6880578
    assert state.high_watermark == 6880578


def test_bounded_catch_up_walks_backwards_and_reaches_old_watermark(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    store.save(
        E621DiscoveryState(
            source_id="art",
            host="e621.net",
            tag_search_expression="fox",
            high_watermark=100,
        )
    )
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox",),
        client_contact="owner@example.test",
        limit=2,
    )
    requests: list[str] = []

    def opener(request: Request, **_kwargs: object) -> FakeResponse:
        requests.append(request.full_url)
        page = next(
            (
                parameter.split("=", 1)[1]
                for parameter in request.full_url.split("?")[-1].split("&")
                if parameter.startswith("page=")
            ),
            None,
        )
        if page is None:
            return FakeResponse([post_with_id(130), post_with_id(120)])
        if page == "b120":
            return FakeResponse([post_with_id(110), post_with_id(105)])
        if page == "b105":
            return FakeResponse([post_with_id(100), post_with_id(95)])
        raise AssertionError(f"Unexpected page: {page}")

    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=opener,
            sleeper=lambda _seconds: None,
            max_requests=3,
        )
        state = store.get("art", "e621.net", "fox")
    finally:
        store.close()

    assert len(requests) == 3
    assert "page=b120" in requests[1]
    assert "page=b105" in requests[2]
    assert len(result.entries) == 4
    mapped_entries = [entry for entry in result.entries if isinstance(entry, E621DiscoveredPost)]
    assert {entry.post.source_post_id for entry in mapped_entries} == {
        "e621.net:130",
        "e621.net:120",
        "e621.net:110",
        "e621.net:105",
    }
    assert result.catch_up_complete is True
    assert state.high_watermark == 130


def test_incomplete_catch_up_preserves_old_watermark(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    store.save(
        E621DiscoveryState(
            source_id="art",
            host="e621.net",
            tag_search_expression="fox",
            high_watermark=100,
        )
    )
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox",),
        client_contact="owner@example.test",
    )

    def opener(request: Request, **_kwargs: object) -> FakeResponse:
        if "page=" not in request.full_url:
            return FakeResponse([post_with_id(130), post_with_id(120)])
        return FakeResponse([post_with_id(110), post_with_id(105)])

    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=opener,
            sleeper=lambda _seconds: None,
            max_requests=1,
        )
        state = store.get("art", "e621.net", "fox")
    finally:
        store.close()

    assert result.entries == ()
    assert result.catch_up_complete is False
    assert result.high_watermark == 100
    assert state.high_watermark == 100
    assert state.catch_up_incomplete is False


def test_failed_scan_does_not_advance_watermark(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    store.save(
        E621DiscoveryState(
            source_id="art",
            host="e621.net",
            tag_search_expression="fox",
            high_watermark=100,
        )
    )
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox",),
        client_contact="owner@example.test",
    )

    def opener(_request: Request, **_kwargs: object) -> object:
        raise URLError("synthetic transport failure")

    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=opener,
            sleeper=lambda _seconds: None,
        )
        state = store.get("art", "e621.net", "fox")
    finally:
        store.close()

    assert result.catch_up_complete is False
    assert any("transport failed" in reason for reason in result.failure_reasons)
    assert state.high_watermark == 100
    assert state.catch_up_incomplete is False


def test_overlapping_expressions_emit_provider_post_once(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    store.save(
        E621DiscoveryState(
            source_id="art",
            host="e621.net",
            tag_search_expression="fox",
            high_watermark=100,
        )
    )
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox", "fox rating:safe"),
        client_contact="owner@example.test",
    )

    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=lambda _request, **_kwargs: FakeResponse([post_with_id(130), post_with_id(100)]),
            sleeper=lambda _seconds: None,
            max_requests=4,
        )
    finally:
        store.close()

    assert len(result.entries) == 1
    entry = result.entries[0]
    assert isinstance(entry, E621DiscoveredPost)
    assert entry.post.source_post_id == "e621.net:130"


def test_empty_result_is_a_successful_complete_scan(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox",),
        client_contact="owner@example.test",
    )
    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=lambda _request, **_kwargs: FakeResponse([]),
            sleeper=lambda _seconds: None,
        )
        state = store.get("art", "e621.net", "fox")
    finally:
        store.close()

    assert result.catch_up_complete is True
    assert result.high_watermark is None
    assert state.high_watermark is None


def test_malformed_individual_post_is_unmapped(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    store.save(
        E621DiscoveryState(
            source_id="art",
            host="e621.net",
            tag_search_expression="fox",
            high_watermark=100,
        )
    )
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox",),
        client_contact="owner@example.test",
    )
    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=lambda _request, **_kwargs: FakeResponse(
                [{"id": 130, "rating": "unknown"}, post_with_id(100)]
            ),
            sleeper=lambda _seconds: None,
        )
    finally:
        store.close()

    assert len(result.entries) == 1
    assert isinstance(result.entries[0], E621UnmappedPost)
    assert result.entries[0].post_id == 130


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({}, "top-level list"),
        ("not a list", "top-level list"),
    ],
)
def test_fetch_rejects_non_list_top_level_payload(
    tmp_path,
    payload: object,
    message: str,
) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox",),
        client_contact="owner@example.test",
    )
    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=lambda _request, **_kwargs: FakeResponse(payload),
        )
    finally:
        store.close()
    assert result.catch_up_complete is False
    assert any(message in reason for reason in result.failure_reasons)


def test_fetch_rejects_http_error(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox",),
        client_contact="owner@example.test",
    )

    def fail(_request: Request, **_kwargs: object) -> object:
        raise HTTPError(
            "https://e621.net/posts.json",
            403,
            "Forbidden",
            Message(),
            None,
        )

    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=fail,
        )
    finally:
        store.close()
    assert result.catch_up_complete is False
    assert any("HTTP 403" in reason for reason in result.failure_reasons)


def test_fetch_retries_503_once(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox",),
        client_contact="owner@example.test",
    )
    attempts = 0
    waits: list[float] = []

    def opener(_request: Request, **_kwargs: object) -> FakeResponse:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return FakeResponse([], status=503, headers={"Retry-After": "2"})
        return FakeResponse([])

    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=opener,
            sleeper=waits.append,
        )
    finally:
        store.close()

    assert attempts == 2
    assert waits == [2.0, 1.25]
    assert result.catch_up_complete is True


def test_fetch_rejects_response_over_size_bound(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox",),
        client_contact="owner@example.test",
    )
    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=lambda _request, **_kwargs: OversizedResponse(),
        )
    finally:
        store.close()
    assert result.catch_up_complete is False
    assert any("too large" in reason for reason in result.failure_reasons)


def test_no_progress_cursor_marks_catch_up_incomplete(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    store.save(
        E621DiscoveryState(
            source_id="art",
            host="e621.net",
            tag_search_expression="fox",
            high_watermark=100,
        )
    )
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox",),
        client_contact="owner@example.test",
    )
    requests = 0

    def opener(request: Request, **_kwargs: object) -> FakeResponse:
        nonlocal requests
        requests += 1
        if "page=" not in request.full_url:
            return FakeResponse([post_with_id(130), post_with_id(120)])
        return FakeResponse([post_with_id(120), post_with_id(110)])

    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=opener,
            sleeper=lambda _seconds: None,
            max_requests=12,
        )
        state = store.get("art", "e621.net", "fox")
    finally:
        store.close()

    assert result.catch_up_complete is False
    assert result.high_watermark == 100
    assert state.catch_up_incomplete is False
    assert requests == 3


def test_multiple_expressions_are_requested_sequentially_and_paced(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    store.save(
        E621DiscoveryState(
            source_id="art",
            host="e621.net",
            tag_search_expression="fox",
            high_watermark=100,
        )
    )
    store.save(
        E621DiscoveryState(
            source_id="art",
            host="e621.net",
            tag_search_expression="cat",
            high_watermark=100,
        )
    )
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox", "cat"),
        client_contact="owner@example.test",
    )
    requested_tags: list[str] = []
    waits: list[float] = []
    active_requests = 0
    maximum_active_requests = 0

    def opener(request: Request, **_kwargs: object) -> FakeResponse:
        nonlocal active_requests, maximum_active_requests
        active_requests += 1
        maximum_active_requests = max(maximum_active_requests, active_requests)
        query = request.full_url.split("?", 1)[1]
        requested_tags.append(next(part for part in query.split("&") if part.startswith("tags=")))
        active_requests -= 1
        return FakeResponse([post_with_id(100)])

    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=opener,
            sleeper=waits.append,
        )
    finally:
        store.close()

    assert maximum_active_requests == 1
    assert requested_tags == ["tags=fox", "tags=cat"]
    assert waits == [1.25]
    assert result.catch_up_complete is True


def test_later_expression_cannot_advance_earlier_expression_watermark(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox", "cat"),
        client_contact="owner@example.test",
    )

    def first_scan(request: Request, **_kwargs: object) -> FakeResponse:
        if "tags=fox" in request.full_url:
            return FakeResponse([post_with_id(200), post_with_id(100)])
        return FakeResponse([post_with_id(300), post_with_id(100)])

    try:
        first = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=first_scan,
            sleeper=lambda _seconds: None,
        )
        assert first.catch_up_complete is True
        assert store.get("art", "e621.net", "fox").high_watermark == 200
        assert store.get("art", "e621.net", "cat").high_watermark == 300

        def second_scan(request: Request, **_kwargs: object) -> FakeResponse:
            if "tags=fox" in request.full_url:
                return FakeResponse([post_with_id(250), post_with_id(200)])
            return FakeResponse([post_with_id(300), post_with_id(250)])

        second = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=second_scan,
            sleeper=lambda _seconds: None,
        )

        assert second.catch_up_complete is True
        assert store.get("art", "e621.net", "fox").high_watermark == 250
        assert store.get("art", "e621.net", "cat").high_watermark == 300
    finally:
        store.close()


def test_independent_first_run_initializes_each_expression(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox", "cat"),
        client_contact="owner@example.test",
    )

    def opener(request: Request, **_kwargs: object) -> FakeResponse:
        if "tags=fox" in request.full_url:
            return FakeResponse([post_with_id(200), post_with_id(150)])
        return FakeResponse([post_with_id(300), post_with_id(250)])

    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=opener,
            sleeper=lambda _seconds: None,
        )

        assert result.entries == ()
        assert store.get("art", "e621.net", "fox").high_watermark == 200
        assert store.get("art", "e621.net", "cat").high_watermark == 300
    finally:
        store.close()


def test_independent_successful_expression_advancement(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    for expression, watermark in (("fox", 100), ("cat", 200)):
        store.save(
            E621DiscoveryState(
                source_id="art",
                host="e621.net",
                tag_search_expression=expression,
                high_watermark=watermark,
            )
        )
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox", "cat"),
        client_contact="owner@example.test",
    )

    def opener(request: Request, **_kwargs: object) -> FakeResponse:
        if "tags=fox" in request.full_url:
            return FakeResponse([post_with_id(150), post_with_id(100)])
        return FakeResponse([post_with_id(250), post_with_id(200)])

    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=opener,
            sleeper=lambda _seconds: None,
        )

        assert result.catch_up_complete is True
        assert store.get("art", "e621.net", "fox").high_watermark == 150
        assert store.get("art", "e621.net", "cat").high_watermark == 250
    finally:
        store.close()


def test_one_incomplete_expression_preserves_only_that_expression(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    for expression, watermark in (("fox", 100), ("cat", 200)):
        store.save(
            E621DiscoveryState(
                source_id="art",
                host="e621.net",
                tag_search_expression=expression,
                high_watermark=watermark,
            )
        )
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox", "cat"),
        client_contact="owner@example.test",
    )

    def opener(request: Request, **_kwargs: object) -> FakeResponse:
        if "tags=fox" in request.full_url:
            if "page=" not in request.full_url:
                return FakeResponse([post_with_id(150), post_with_id(120)])
            return FakeResponse([post_with_id(110), post_with_id(100)])
        return FakeResponse([post_with_id(250), post_with_id(200)])

    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=opener,
            sleeper=lambda _seconds: None,
            max_requests=1,
        )

        assert result.entries == ()
        assert result.catch_up_complete is False
        assert store.get("art", "e621.net", "fox").high_watermark == 100
        assert store.get("art", "e621.net", "fox").catch_up_incomplete is False
        assert store.get("art", "e621.net", "cat").high_watermark == 200
    finally:
        store.close()


def test_one_failed_expression_does_not_advance_it(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    for expression, watermark in (("fox", 100), ("cat", 200)):
        store.save(
            E621DiscoveryState(
                source_id="art",
                host="e621.net",
                tag_search_expression=expression,
                high_watermark=watermark,
            )
        )
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox", "cat"),
        client_contact="owner@example.test",
    )

    def opener(request: Request, **_kwargs: object) -> FakeResponse:
        if "tags=fox" in request.full_url:
            raise URLError("synthetic fox failure")
        return FakeResponse([post_with_id(250), post_with_id(200)])

    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=opener,
            sleeper=lambda _seconds: None,
        )

        assert result.entries == ()
        assert result.catch_up_complete is False
        assert store.get("art", "e621.net", "fox").high_watermark == 100
        assert store.get("art", "e621.net", "cat").high_watermark == 200
    finally:
        store.close()


def test_overlap_deduplication_with_separate_expression_states(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    for expression, watermark in (("fox", 100), ("fox rating:safe", 100)):
        store.save(
            E621DiscoveryState(
                source_id="art",
                host="e621.net",
                tag_search_expression=expression,
                high_watermark=watermark,
            )
        )
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox", "fox rating:safe"),
        client_contact="owner@example.test",
    )

    try:
        result = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=lambda _request, **_kwargs: FakeResponse([post_with_id(130), post_with_id(100)]),
            sleeper=lambda _seconds: None,
        )
    finally:
        store.close()

    assert len(result.entries) == 1
    assert isinstance(result.entries[0], E621DiscoveredPost)
    assert result.entries[0].post.source_post_id == "e621.net:130"


def test_atomic_publication_preserves_posts_for_next_successful_scan(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    for expression in ("fox", "wolf"):
        store.save(
            E621DiscoveryState(
                source_id="art",
                host="e621.net",
                tag_search_expression=expression,
                high_watermark=100,
            )
        )
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox", "wolf"),
        client_contact="owner@example.test",
    )

    def failed_scan(request: Request, **_kwargs: object) -> FakeResponse:
        if "tags=fox" in request.full_url:
            return FakeResponse([post_with_id(120), post_with_id(110)])
        raise URLError("synthetic wolf failure")

    try:
        incomplete = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=failed_scan,
            sleeper=lambda _seconds: None,
        )

        assert incomplete.entries == ()
        assert incomplete.catch_up_complete is False
        assert incomplete.high_watermark == 100
        assert store.get("art", "e621.net", "fox").high_watermark == 100
        assert store.get("art", "e621.net", "wolf").high_watermark == 100

        def successful_scan(request: Request, **_kwargs: object) -> FakeResponse:
            if "tags=fox" in request.full_url:
                if "page=" not in request.full_url:
                    return FakeResponse([post_with_id(120), post_with_id(110)])
                return FakeResponse([post_with_id(100), post_with_id(90)])
            return FakeResponse([post_with_id(105), post_with_id(100)])

        complete = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=successful_scan,
            sleeper=lambda _seconds: None,
        )

        assert complete.catch_up_complete is True
        assert {
            entry.post.source_post_id
            for entry in complete.entries
            if isinstance(entry, E621DiscoveredPost)
        } == {
            "e621.net:120",
            "e621.net:110",
            "e621.net:105",
        }
        assert store.get("art", "e621.net", "fox").high_watermark == 120
        assert store.get("art", "e621.net", "wolf").high_watermark == 105
    finally:
        store.close()


def test_atomic_first_run_initialization_needs_every_expression(tmp_path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    settings = E621DiscoverySettings(
        source_id="art",
        host="e621.net",
        tag_search_expressions=("fox", "wolf"),
        client_contact="owner@example.test",
    )

    def incomplete_first_scan(request: Request, **_kwargs: object) -> FakeResponse:
        if "tags=fox" in request.full_url:
            return FakeResponse([post_with_id(200), post_with_id(150)])
        raise URLError("synthetic wolf failure")

    try:
        incomplete = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=incomplete_first_scan,
            sleeper=lambda _seconds: None,
        )

        assert incomplete.entries == ()
        assert incomplete.catch_up_complete is False
        assert store.get("art", "e621.net", "fox").high_watermark is None
        assert store.get("art", "e621.net", "wolf").high_watermark is None

        def successful_first_scan(request: Request, **_kwargs: object) -> FakeResponse:
            if "tags=fox" in request.full_url:
                return FakeResponse([post_with_id(200), post_with_id(150)])
            return FakeResponse([post_with_id(220), post_with_id(180)])

        complete = fetch_e621_posts(
            settings,
            store,
            allocate("post"),
            allocate("artwork"),
            opener=successful_first_scan,
            sleeper=lambda _seconds: None,
        )

        assert complete.entries == ()
        assert complete.catch_up_complete is True
        assert store.get("art", "e621.net", "fox").high_watermark == 200
        assert store.get("art", "e621.net", "wolf").high_watermark == 220
    finally:
        store.close()
