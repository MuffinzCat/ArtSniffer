"""Map e621/e926 discovery responses into ArtSniffer records."""

import math
from collections.abc import Callable
from dataclasses import dataclass

from artsniffer.discovery.post import DiscoveredArtwork, DiscoveredPost, DiscoveredPostProvenance


class E621DiscoveryError(ValueError):
    """Report a malformed or unsupported payload at the e621/e926 boundary."""


@dataclass(frozen=True)
class E621PostMetadata:
    """Preserve e621/e926 post metadata without treating it as creator attribution."""

    uploader_id: int
    uploader_name: str
    approver_id: int | None
    source_urls: tuple[str, ...]
    pool_ids: tuple[int, ...]
    parent_id: int | None
    child_ids: tuple[int, ...]
    created_at: str
    updated_at: str | None
    change_sequence: int


@dataclass(frozen=True)
class E621PostFlags:
    """Preserve e621/e926 post flags as source evidence."""

    deleted: bool
    flagged: bool
    note_locked: bool
    pending: bool
    rating_locked: bool
    status_locked: bool


@dataclass(frozen=True)
class E621SourceRating:
    """Preserve the raw e621/e926 source rating as provider evidence."""

    value: str


@dataclass(frozen=True)
class E621MediaRepresentation:
    """Preserve e621/e926 alternate media retrieval representations."""

    jpg_url: str | None
    webp_url: str | None
    width: int
    height: int


@dataclass(frozen=True)
class E621MediaMetadata:
    """Preserve e621/e926 media identity and original-file retrieval metadata."""

    md5: str
    extension: str
    size_bytes: int
    duration: float | None
    has_sample: bool
    original_url: str
    width: int
    height: int
    sample: E621MediaRepresentation | None
    preview: E621MediaRepresentation | None


@dataclass(frozen=True)
class E621DiscoveredPost:
    """Group one mapped e621/e926 post with its preserved source evidence."""

    post: DiscoveredPost
    provenance: DiscoveredPostProvenance
    artwork: DiscoveredArtwork
    metadata: E621PostMetadata
    flags: E621PostFlags
    rating: E621SourceRating
    media: E621MediaMetadata


def e621_discovered_post_from_json(
    source_id: str,
    host: str,
    post_data: dict[str, object],
    allocate_post_id: Callable[[], str],
    allocate_artwork_id: Callable[[], str],
) -> E621DiscoveredPost:
    """Map one e621/e926 post response into discovery records and source evidence."""
    if not isinstance(post_data, dict):
        raise E621DiscoveryError("e621/e926 post must be a dictionary.")
    if not source_id.strip():
        raise E621DiscoveryError("e621/e926 source ID must not be empty or whitespace.")
    if host not in ("e621.net", "e926.net"):
        raise E621DiscoveryError("e621/e926 host must be 'e621.net' or 'e926.net'.")

    provider_post_id = post_data.get("id")
    if isinstance(provider_post_id, bool) or not isinstance(provider_post_id, int):
        raise E621DiscoveryError("e621/e926 post ID must be an integer.")

    change_sequence = post_data.get("change_seq")
    if isinstance(change_sequence, bool) or not isinstance(change_sequence, int):
        raise E621DiscoveryError("e621/e926 change sequence must be an integer.")

    uploader_id = post_data.get("uploader_id")
    if isinstance(uploader_id, bool) or not isinstance(uploader_id, int):
        raise E621DiscoveryError("e621/e926 uploader ID must be an integer.")

    uploader_name = post_data.get("uploader_name")
    if not isinstance(uploader_name, str) or not uploader_name.strip():
        raise E621DiscoveryError("e621/e926 uploader name must be a non-empty string.")

    approver_id = post_data.get("approver_id")
    if approver_id is not None and (
        isinstance(approver_id, bool) or not isinstance(approver_id, int)
    ):
        raise E621DiscoveryError("e621/e926 approver ID must be an integer or null.")

    created_at = post_data.get("created_at")
    if not isinstance(created_at, str) or not created_at.strip():
        raise E621DiscoveryError("e621/e926 created timestamp must be a non-empty string.")

    updated_at = post_data.get("updated_at")
    if updated_at is not None and (not isinstance(updated_at, str) or not updated_at.strip()):
        raise E621DiscoveryError("e621/e926 updated timestamp must be a non-empty string or null.")

    rating = post_data.get("rating")
    if not isinstance(rating, str) or rating not in ("s", "q", "e"):
        raise E621DiscoveryError("e621/e926 rating must be 's', 'q', or 'e'.")

    tags = post_data.get("tags")
    if not isinstance(tags, list):
        raise E621DiscoveryError("e621/e926 tags must be a list.")
    if any(not isinstance(tag, str) or not tag.strip() for tag in tags):
        raise E621DiscoveryError("Each e621/e926 tag must be a non-empty string.")

    sources = post_data.get("sources")
    if not isinstance(sources, list):
        raise E621DiscoveryError("e621/e926 sources must be a list.")
    if any(not isinstance(source, str) or not source.strip() for source in sources):
        raise E621DiscoveryError("Each e621/e926 source URL must be a non-empty string.")

    pools = post_data.get("pools")
    if not isinstance(pools, list):
        raise E621DiscoveryError("e621/e926 pools must be a list.")
    if any(isinstance(pool_id, bool) or not isinstance(pool_id, int) for pool_id in pools):
        raise E621DiscoveryError("Each e621/e926 pool ID must be an integer.")

    flags = post_data.get("flags")
    if not isinstance(flags, dict):
        raise E621DiscoveryError("e621/e926 flags must be a dictionary.")
    flag_names = (
        "deleted",
        "flagged",
        "note_locked",
        "pending",
        "rating_locked",
        "status_locked",
    )
    for flag_name in flag_names:
        if not isinstance(flags.get(flag_name), bool):
            raise E621DiscoveryError(f"e621/e926 flag '{flag_name}' must be a boolean.")

    relationships = post_data.get("relationships")
    if not isinstance(relationships, dict):
        raise E621DiscoveryError("e621/e926 relationships must be a dictionary.")
    parent_id = relationships.get("parent_id")
    if parent_id is not None and (isinstance(parent_id, bool) or not isinstance(parent_id, int)):
        raise E621DiscoveryError("e621/e926 parent ID must be an integer or null.")
    child_ids = relationships.get("children")
    if not isinstance(child_ids, list):
        raise E621DiscoveryError("e621/e926 child IDs must be a list.")
    if any(isinstance(child_id, bool) or not isinstance(child_id, int) for child_id in child_ids):
        raise E621DiscoveryError("Each e621/e926 child ID must be an integer.")

    files = post_data.get("files")
    if not isinstance(files, dict):
        raise E621DiscoveryError("e621/e926 files must be a dictionary.")

    meta = files.get("meta")
    if not isinstance(meta, dict):
        raise E621DiscoveryError("e621/e926 files.meta must be a dictionary.")
    md5 = meta.get("md5")
    if not isinstance(md5, str) or not md5.strip():
        raise E621DiscoveryError("e621/e926 media MD5 must be a non-empty string.")
    extension = meta.get("ext")
    if not isinstance(extension, str) or not extension.strip():
        raise E621DiscoveryError("e621/e926 media extension must be a non-empty string.")
    size_bytes = meta.get("size")
    if isinstance(size_bytes, bool) or not isinstance(size_bytes, int):
        raise E621DiscoveryError("e621/e926 media size must be an integer.")
    duration = meta.get("duration")
    if duration is not None:
        if isinstance(duration, bool) or not isinstance(duration, (int, float)):
            raise E621DiscoveryError("e621/e926 media duration must be a number or null.")
        if not math.isfinite(duration) or duration < 0:
            raise E621DiscoveryError("e621/e926 media duration must be finite and non-negative.")
        duration = float(duration)
    has_sample = meta.get("has_sample")
    if not isinstance(has_sample, bool):
        raise E621DiscoveryError("e621/e926 media has_sample must be a boolean.")

    original = files.get("original")
    if not isinstance(original, dict):
        raise E621DiscoveryError("e621/e926 files.original must be a dictionary.")
    original_url = original.get("url")
    if not isinstance(original_url, str) or not original_url.strip():
        raise E621DiscoveryError("e621/e926 original media URL must be a non-empty string.")
    original_width = original.get("width")
    if isinstance(original_width, bool) or not isinstance(original_width, int):
        raise E621DiscoveryError("e621/e926 original media width must be an integer.")
    original_height = original.get("height")
    if isinstance(original_height, bool) or not isinstance(original_height, int):
        raise E621DiscoveryError("e621/e926 original media height must be an integer.")

    def parse_representation(name: str) -> E621MediaRepresentation | None:
        representation = files.get(name)
        if representation is None:
            return None
        if not isinstance(representation, dict):
            raise E621DiscoveryError(f"e621/e926 files.{name} must be a dictionary or null.")

        jpg_url = representation.get("jpg")
        if jpg_url is not None and (not isinstance(jpg_url, str) or not jpg_url.strip()):
            raise E621DiscoveryError(
                f"e621/e926 files.{name}.jpg must be a non-empty string or null."
            )
        webp_url = representation.get("webp")
        if webp_url is not None and (not isinstance(webp_url, str) or not webp_url.strip()):
            raise E621DiscoveryError(
                f"e621/e926 files.{name}.webp must be a non-empty string or null."
            )
        width = representation.get("width")
        if isinstance(width, bool) or not isinstance(width, int):
            raise E621DiscoveryError(f"e621/e926 files.{name}.width must be an integer.")
        height = representation.get("height")
        if isinstance(height, bool) or not isinstance(height, int):
            raise E621DiscoveryError(f"e621/e926 files.{name}.height must be an integer.")
        return E621MediaRepresentation(
            jpg_url=jpg_url,
            webp_url=webp_url,
            width=width,
            height=height,
        )

    sample = parse_representation("sample")
    preview = parse_representation("preview")

    post_id = allocate_post_id()
    artwork_id = allocate_artwork_id()
    provider_post_id_string = f"{host}:{provider_post_id}"
    post_url = f"https://{host}/posts/{provider_post_id}"

    post = DiscoveredPost(
        id=post_id,
        source_id=source_id,
        source_post_id=provider_post_id_string,
        creator_id=None,
        url=post_url,
        tags=tuple(tags),
    )
    provenance = DiscoveredPostProvenance(
        post_id=post_id,
        source_version_id=str(change_sequence),
    )
    artwork = DiscoveredArtwork(
        id=artwork_id,
        post_id=post_id,
        source_item_id=md5,
        content_hash=None,
    )
    metadata = E621PostMetadata(
        uploader_id=uploader_id,
        uploader_name=uploader_name,
        approver_id=approver_id,
        source_urls=tuple(sources),
        pool_ids=tuple(pools),
        parent_id=parent_id,
        child_ids=tuple(child_ids),
        created_at=created_at,
        updated_at=updated_at,
        change_sequence=change_sequence,
    )
    post_flags = E621PostFlags(
        deleted=flags["deleted"],
        flagged=flags["flagged"],
        note_locked=flags["note_locked"],
        pending=flags["pending"],
        rating_locked=flags["rating_locked"],
        status_locked=flags["status_locked"],
    )
    source_rating = E621SourceRating(value=rating)
    media = E621MediaMetadata(
        md5=md5,
        extension=extension,
        size_bytes=size_bytes,
        duration=duration,
        has_sample=has_sample,
        original_url=original_url,
        width=original_width,
        height=original_height,
        sample=sample,
        preview=preview,
    )
    return E621DiscoveredPost(
        post=post,
        provenance=provenance,
        artwork=artwork,
        metadata=metadata,
        flags=post_flags,
        rating=source_rating,
        media=media,
    )
