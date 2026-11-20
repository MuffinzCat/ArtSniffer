import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from artsniffer.discovery.post import (
    DiscoveredArtwork,
    DiscoveredArtworkSourceMetadata,
    DiscoveredPost,
    DiscoveredPostProvenance,
    DiscoveredSourceLabel,
)
from artsniffer.settings import BlueskyDiscoverySettings


class BlueskyDiscoveryError(ValueError):
    """Report a malformed or unsupported provider payload at the Bluesky boundary."""


class UnsupportedBlueskyEmbedError(BlueskyDiscoveryError):
    """Report an embed that the bounded first slice does not interpret."""


@dataclass(frozen=True)
class BlueskyUnsupportedPost:
    """Describe one post that the bounded adapter intentionally could not map."""

    post_uri: str | None
    reason: str


@dataclass(frozen=True)
class BlueskyDiscoveredPost:
    """Group one mapped Bluesky post with its preserved source metadata."""

    post: DiscoveredPost
    provenance: DiscoveredPostProvenance
    artworks: tuple[DiscoveredArtwork, ...]
    artwork_metadata: tuple[DiscoveredArtworkSourceMetadata, ...]
    labels: tuple[DiscoveredSourceLabel, ...] = ()


BlueskyFeedEntry = BlueskyDiscoveredPost | BlueskyUnsupportedPost


@dataclass(frozen=True)
class BlueskyFeedPage:
    """Preserve one getFeed page and its provider cursor."""

    entries: tuple[BlueskyFeedEntry, ...]
    cursor: str | None


def bluesky_post_url(post_uri: str) -> str:
    """Construct the public profile URL for a valid AT URI post."""
    if not post_uri.startswith("at://"):
        raise BlueskyDiscoveryError("Bluesky post URI must be a valid AT URI.")
    parts = post_uri.removeprefix("at://").split("/")
    if (
        len(parts) != 3
        or not parts[0].startswith("did:")
        or parts[1] != "app.bsky.feed.post"
        or not parts[2]
    ):
        raise BlueskyDiscoveryError("Bluesky post URI must be a valid AT URI.")
    return f"https://bsky.app/profile/{parts[0]}/post/{parts[2]}"


def bluesky_image_id(post_uri: str, image_index: int) -> str:
    """Construct the image ID for a Bluesky post given its URI and image index."""
    return f"{post_uri}#image-{image_index}"


def bluesky_discovered_post_from_json(
    source_id: str,
    post_data: dict[str, object],
    allocate_post_id: Callable[[], str],
    allocate_artwork_id: Callable[[], str],
) -> BlueskyDiscoveredPost:
    """Map one hydrated public Bluesky post into provider-neutral discovery records."""
    if not isinstance(post_data, dict):
        raise BlueskyDiscoveryError("Bluesky post must be a dictionary.")

    post_uri = post_data.get("uri")
    if not isinstance(post_uri, str):
        raise BlueskyDiscoveryError("Bluesky post URI must be a string.")
    if not post_uri.strip():
        raise BlueskyDiscoveryError("Bluesky post URI must not be empty or whitespace.")
    post_cid = post_data.get("cid")
    if not isinstance(post_cid, str):
        raise BlueskyDiscoveryError("Bluesky post CID must be a string.")
    if not post_cid.strip():
        raise BlueskyDiscoveryError("Bluesky post CID must not be empty or whitespace.")
    author = post_data.get("author")
    if not isinstance(author, dict):
        raise BlueskyDiscoveryError("Bluesky author must be a dictionary.")
    author_did = author.get("did")
    if not isinstance(author_did, str):
        raise BlueskyDiscoveryError("Bluesky author DID must be a string.")
    if not author_did.strip():
        raise BlueskyDiscoveryError("Bluesky author DID must not be empty or whitespace.")
    record = post_data.get("record")
    if not isinstance(record, dict):
        raise BlueskyDiscoveryError("Bluesky record must be a dictionary.")

    embed = post_data.get("embed")
    if embed is None:
        embed = record.get("embed")
    if not isinstance(embed, dict):
        raise BlueskyDiscoveryError("Bluesky embed must be a dictionary.")
    embed_type = embed.get("$type")
    if not isinstance(embed_type, str):
        raise BlueskyDiscoveryError("Bluesky embed type must be a string.")

    if embed_type == "app.bsky.embed.recordWithMedia":
        media = embed.get("media")
        if not isinstance(media, dict):
            raise BlueskyDiscoveryError("Bluesky recordWithMedia media must be a dictionary.")
        direct_embed = media
    elif embed_type in (
        "app.bsky.embed.images",
        "app.bsky.embed.gallery",
        "app.bsky.embed.external",
        "app.bsky.embed.video",
    ):
        direct_embed = embed
    elif embed_type == "app.bsky.embed.record":
        raise UnsupportedBlueskyEmbedError("Bluesky quote-only embeds are unsupported.")
    else:
        raise UnsupportedBlueskyEmbedError(f"Unsupported Bluesky embed type: {embed_type}")

    media_type = direct_embed.get("$type")
    if not isinstance(media_type, str):
        raise BlueskyDiscoveryError("Bluesky direct media type must be a string.")
    if media_type == "app.bsky.embed.external":
        raise UnsupportedBlueskyEmbedError("Bluesky external embeds are unsupported.")
    if media_type == "app.bsky.embed.video":
        raise UnsupportedBlueskyEmbedError("Bluesky video embeds are unsupported.")
    if media_type not in ("app.bsky.embed.images", "app.bsky.embed.gallery"):
        raise UnsupportedBlueskyEmbedError(f"Unsupported Bluesky direct media type: {media_type}")

    if media_type == "app.bsky.embed.images":
        images = direct_embed.get("images")
        item_key = "image"
    else:
        images = direct_embed.get("items")
        item_key = "image"
    if not isinstance(images, list):
        raise BlueskyDiscoveryError("Bluesky images must be a list.")

    post_url = bluesky_post_url(post_uri)
    post_id = allocate_post_id()
    post = DiscoveredPost(
        post_id,
        source_id,
        post_uri,
        author_did,
        post_url,
    )
    provenance = DiscoveredPostProvenance(
        post_id,
        post_cid,
    )
    artworks = []
    artwork_metadata = []
    for image_index, image in enumerate(images):
        if not isinstance(image, dict):
            raise BlueskyDiscoveryError("Each Bluesky image must be a dictionary.")
        item_type = image.get("$type")
        if item_type is not None and item_type not in (
            "app.bsky.embed.images#image",
            "app.bsky.embed.gallery#item",
        ):
            raise UnsupportedBlueskyEmbedError(
                f"Unsupported Bluesky gallery item type: {item_type}"
            )
        alt = image.get("alt")
        if not isinstance(alt, str):
            raise BlueskyDiscoveryError("Bluesky image alt text must be a string.")
        image_blob = image.get(item_key)
        if not isinstance(image_blob, dict):
            raise BlueskyDiscoveryError("Bluesky image blob must be a dictionary.")
        blob_ref = image_blob.get("ref")
        if not isinstance(blob_ref, dict):
            raise BlueskyDiscoveryError("Bluesky image blob ref must be a dictionary.")
        blob_cid = blob_ref.get("$link")
        if not isinstance(blob_cid, str):
            raise BlueskyDiscoveryError("Bluesky image blob CID must be a string.")
        if not blob_cid.strip():
            raise BlueskyDiscoveryError("Bluesky image blob CID must not be empty or whitespace.")
        artwork_id = allocate_artwork_id()
        image_id = bluesky_image_id(post_uri, image_index)
        artworks.append(
            DiscoveredArtwork(
                artwork_id,
                post_id,
                image_id,
            )
        )
        artwork_metadata.append(
            DiscoveredArtworkSourceMetadata(
                artwork_id,
                blob_cid,
                alt,
            )
        )
    labels = _parse_bluesky_labels(post_data)
    return BlueskyDiscoveredPost(
        post,
        provenance,
        tuple(artworks),
        tuple(artwork_metadata),
        labels,
    )


def _parse_bluesky_labels(post_data: dict[str, object]) -> tuple[DiscoveredSourceLabel, ...]:
    """Parse hydrated postView labels while retaining their source provenance."""
    labels = post_data.get("labels")
    if labels is None:
        return ()
    if not isinstance(labels, list):
        raise BlueskyDiscoveryError("Bluesky labels must be a list.")

    parsed = []
    for label in labels:
        if not isinstance(label, dict):
            raise BlueskyDiscoveryError("Each Bluesky label must be a dictionary.")
        src = label.get("src")
        uri = label.get("uri")
        cid = label.get("cid")
        val = label.get("val")
        ver = label.get("ver")
        neg = label.get("neg")
        cts = label.get("cts")
        exp = label.get("exp")
        sig = label.get("sig")
        if not isinstance(src, str):
            raise BlueskyDiscoveryError("Bluesky label src must be a string.")
        if not isinstance(uri, str):
            raise BlueskyDiscoveryError("Bluesky label URI must be a string.")
        if cid is not None and not isinstance(cid, str):
            raise BlueskyDiscoveryError("Bluesky label CID must be a string.")
        if not isinstance(val, str):
            raise BlueskyDiscoveryError("Bluesky label value must be a string.")
        if ver is not None and not isinstance(ver, int):
            raise BlueskyDiscoveryError("Bluesky label ver must be an integer.")
        if neg is not None and not isinstance(neg, bool):
            raise BlueskyDiscoveryError("Bluesky label neg must be a boolean.")
        if not isinstance(cts, str):
            raise BlueskyDiscoveryError("Bluesky label cts must be a string.")
        if exp is not None and not isinstance(exp, str):
            raise BlueskyDiscoveryError("Bluesky label exp must be a string.")
        if sig is not None and not isinstance(sig, str):
            raise BlueskyDiscoveryError("Bluesky label sig must be a string.")
        parsed.append(
            DiscoveredSourceLabel(
                src=src,
                uri=uri,
                cid=cid,
                val=val,
                ver=ver,
                neg=neg,
                cts=cts,
                exp=exp,
                sig=sig,
                hydrated=True,
            )
        )
    return tuple(parsed)


def fetch_bluesky_feed(
    settings: BlueskyDiscoverySettings,
    cursor: str | None = None,
    opener: Callable[..., Any] | None = None,
) -> BlueskyFeedPage:
    """Fetch and map one anonymous public AppView getFeed page."""
    if not settings.enabled:
        raise BlueskyDiscoveryError("Bluesky discovery source is disabled.")
    if cursor is not None and not cursor.strip():
        raise BlueskyDiscoveryError("Bluesky cursor must not be empty or whitespace.")

    query = {
        "feed": settings.feed_uri,
        "limit": settings.limit,
    }
    if cursor is not None:
        query["cursor"] = cursor
    endpoint = "https://public.api.bsky.app/xrpc/app.bsky.feed.getFeed"
    request = Request(
        f"{endpoint}?{urlencode(query)}",
        headers={
            "Accept": "application/json",
        },
        method="GET",
    )
    transport = opener or urlopen
    try:
        response = transport(request, timeout=settings.timeout_seconds)
        status = getattr(response, "status", 200)
        body = response.read()
    except HTTPError as error:
        raise BlueskyDiscoveryError(
            f"Bluesky getFeed returned HTTP {error.code}: {error.reason}"
        ) from error
    except URLError as error:
        raise BlueskyDiscoveryError(f"Bluesky getFeed transport failed: {error.reason}") from error

    if status is not None and status != 200:
        raise BlueskyDiscoveryError(f"Bluesky getFeed returned HTTP {status}.")
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise BlueskyDiscoveryError("Bluesky getFeed returned a non-JSON response.") from error
    if not isinstance(payload, dict):
        raise BlueskyDiscoveryError("Bluesky getFeed payload must be a dictionary.")
    feed = payload.get("feed")
    if not isinstance(feed, list):
        raise BlueskyDiscoveryError("Bluesky getFeed feed must be a list.")
    response_cursor = payload.get("cursor")
    if response_cursor is not None and not isinstance(response_cursor, str):
        raise BlueskyDiscoveryError("Bluesky getFeed cursor must be a string.")

    entries: list[BlueskyFeedEntry] = []
    for feed_index, feed_entry in enumerate(feed):
        if not isinstance(feed_entry, dict):
            entries.append(
                BlueskyUnsupportedPost(
                    post_uri=None,
                    reason="Feed entry must be a dictionary.",
                )
            )
            continue
        post_data = feed_entry.get("post")
        if not isinstance(post_data, dict):
            entries.append(
                BlueskyUnsupportedPost(
                    post_uri=None,
                    reason="Feed entry post must be a dictionary.",
                )
            )
            continue
        post_uri = post_data.get("uri")
        artwork_counter = 0
        post_id_prefix = f"{settings.source_id}:post:{feed_index}"
        artwork_id_prefix = f"{settings.source_id}:artwork:{feed_index}"

        def allocate_post_id(post_id_prefix: str = post_id_prefix) -> str:
            return post_id_prefix

        def allocate_artwork_id(
            artwork_id_prefix: str = artwork_id_prefix,
        ) -> str:
            nonlocal artwork_counter
            artwork_id = f"{artwork_id_prefix}:{artwork_counter}"
            artwork_counter += 1
            return artwork_id

        try:
            mapped = bluesky_discovered_post_from_json(
                settings.source_id,
                post_data,
                allocate_post_id=allocate_post_id,
                allocate_artwork_id=allocate_artwork_id,
            )
        except UnsupportedBlueskyEmbedError as error:
            entries.append(
                BlueskyUnsupportedPost(
                    post_uri=post_uri if isinstance(post_uri, str) else None,
                    reason=str(error),
                )
            )
        except BlueskyDiscoveryError as error:
            entries.append(
                BlueskyUnsupportedPost(
                    post_uri=post_uri if isinstance(post_uri, str) else None,
                    reason=str(error),
                )
            )
        else:
            entries.append(mapped)
    return BlueskyFeedPage(entries=tuple(entries), cursor=response_cursor)
