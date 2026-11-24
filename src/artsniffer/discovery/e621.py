"""Map e621/e926 discovery responses into ArtSniffer records."""

import json
import math
import time
from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from artsniffer.discovery.post import DiscoveredArtwork, DiscoveredPost, DiscoveredPostProvenance
from artsniffer.persistence.e621_discovery_state import (
    E621DiscoveryState,
    SQLiteE621DiscoveryStateStore,
)
from artsniffer.settings import E621DiscoverySettings


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


@dataclass(frozen=True)
class E621UnmappedPost:
    """Describe an individual e621/e926 post that could not be mapped safely."""

    post_id: int | None
    reason: str


E621ScanEntry = E621DiscoveredPost | E621UnmappedPost


@dataclass(frozen=True)
class E621DiscoveryResult:
    """Report a completed or incomplete incremental e621/e926 scan."""

    entries: tuple[E621ScanEntry, ...]
    high_watermark: int | None
    catch_up_complete: bool
    failure_reasons: tuple[str, ...] = ()


MAX_E621_RESPONSE_BODY_BYTES = 5 * 1024 * 1024
E621_REQUEST_PACING_SECONDS = 1.25
E621_MAX_CATCH_UP_REQUESTS = 12
E621_MAX_CATCH_UP_RESULTS = 400


def e621_user_agent(client_contact: str) -> str:
    """Build a descriptive application User-Agent from validated contact configuration."""
    if not client_contact.strip():
        raise E621DiscoveryError("e621/e926 client contact must not be empty or whitespace.")
    try:
        application_version = version("artsniffer")
    except PackageNotFoundError:
        application_version = "0.1.0"
    return f"ArtSniffer/{application_version} (+{client_contact})"


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


def _retry_delay(error: HTTPError) -> float | None:
    """Read a numeric Retry-After delay from a provider response when present."""
    retry_after = error.headers.get("Retry-After")
    if retry_after is None:
        return None
    try:
        return max(0.0, float(retry_after))
    except (TypeError, ValueError):
        return None


def _fetch_e621_page(
    settings: E621DiscoverySettings,
    expression: str,
    page: str | None,
    opener: Callable[..., object],
    pace: Callable[[], None],
    sleeper: Callable[[float], None],
) -> list[object]:
    """Fetch and decode one /posts.json response with a strictly bounded retry."""
    query: list[tuple[str, object]] = [
        ("tags", expression),
        ("limit", settings.limit),
    ]
    if page is not None:
        query.append(("page", page))
    url = f"https://{settings.host}/posts.json?{urlencode(query)}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": e621_user_agent(settings.client_contact),
        },
        method="GET",
    )

    response: object | None = None
    for attempt in range(2):
        pace()
        try:
            response = opener(request, timeout=settings.timeout_seconds)
            status = getattr(response, "status", 200)
            if status in (429, 503) and attempt == 0:
                close = getattr(response, "close", None)
                if callable(close):
                    close()
                headers = getattr(response, "headers", None)
                if isinstance(headers, dict):
                    retry_value = headers.get("Retry-After")
                    if retry_value is not None:
                        try:
                            sleeper(max(0.0, float(retry_value)))
                        except (TypeError, ValueError):
                            pass
                continue
            if status is not None and status != 200:
                close = getattr(response, "close", None)
                if callable(close):
                    close()
                raise E621DiscoveryError(f"e621/e926 /posts.json returned HTTP {status}.")
            read = getattr(response, "read", None)
            if not callable(read):
                raise E621DiscoveryError("e621/e926 /posts.json returned an invalid response.")
            body = read(MAX_E621_RESPONSE_BODY_BYTES + 1)
            if not isinstance(body, (bytes, bytearray)):
                raise E621DiscoveryError("e621/e926 /posts.json returned a non-binary body.")
            if len(body) > MAX_E621_RESPONSE_BODY_BYTES:
                raise E621DiscoveryError("e621/e926 /posts.json response body is too large.")
            try:
                payload = json.loads(body)
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                raise E621DiscoveryError(
                    "e621/e926 /posts.json returned a non-JSON response."
                ) from error
            if not isinstance(payload, list):
                raise E621DiscoveryError("e621/e926 /posts.json payload must be a top-level list.")
            return payload
        except HTTPError as error:
            close = getattr(error, "close", None)
            if callable(close):
                close()
            if error.code in (429, 503) and attempt == 0:
                retry_delay = _retry_delay(error)
                if retry_delay is not None:
                    sleeper(retry_delay)
                continue
            raise E621DiscoveryError(
                f"e621/e926 /posts.json returned HTTP {error.code}: {error.reason}"
            ) from error
        except (URLError, TimeoutError, OSError) as error:
            raise E621DiscoveryError(f"e621/e926 /posts.json transport failed: {error}") from error
        finally:
            if response is not None:
                close = getattr(response, "close", None)
                if callable(close):
                    close()
                response = None

    raise E621DiscoveryError("e621/e926 /posts.json remains rate-limited after one bounded retry.")


def fetch_e621_posts(
    settings: E621DiscoverySettings,
    state_store: SQLiteE621DiscoveryStateStore,
    allocate_post_id: Callable[[], str],
    allocate_artwork_id: Callable[[], str],
    opener: Callable[..., object] | None = None,
    sleeper: Callable[[float], None] | None = None,
    max_requests: int = E621_MAX_CATCH_UP_REQUESTS,
    max_results: int = E621_MAX_CATCH_UP_RESULTS,
) -> E621DiscoveryResult:
    """Fetch, map, and incrementally scan one configured e621/e926 source."""
    if not settings.enabled:
        raise E621DiscoveryError("e621/e926 discovery source is disabled.")
    if isinstance(max_requests, bool) or not isinstance(max_requests, int) or max_requests < 1:
        raise E621DiscoveryError("e621/e926 maximum requests must be a positive integer.")
    if isinstance(max_results, bool) or not isinstance(max_results, int) or max_results < 1:
        raise E621DiscoveryError("e621/e926 maximum results must be a positive integer.")

    transport = opener or urlopen
    sleep = sleeper or time.sleep
    request_count = 0
    actual_request_count = 0

    def pace() -> None:
        nonlocal actual_request_count
        if actual_request_count > 0:
            sleep(E621_REQUEST_PACING_SECONDS)
        actual_request_count += 1

    candidate_posts: dict[int, dict[str, object]] = {}
    unmapped_posts: list[E621UnmappedPost] = []
    catch_up_complete = True
    committed_watermarks: list[int] = []
    proposed_watermarks: list[int] = []
    failure_reasons: list[str] = []
    proposed_states: list[E621DiscoveryState] = []

    for expression in settings.tag_search_expressions:
        state = state_store.get(
            settings.source_id,
            settings.host,
            expression,
        )
        old_watermark = state.high_watermark
        if old_watermark is not None:
            committed_watermarks.append(old_watermark)
        expression_seen_ids: set[int] = set()
        expression_complete = True
        expression_failed = False
        before_id: int | None = None
        while True:
            if request_count >= max_requests:
                expression_complete = False
                failure_reasons.append(f"{expression}: catch-up request budget exhausted.")
                break

            request_count += 1
            try:
                page = _fetch_e621_page(
                    settings,
                    expression,
                    None if before_id is None else f"b{before_id}",
                    transport,
                    pace,
                    sleep,
                )
            except E621DiscoveryError as error:
                expression_complete = False
                expression_failed = True
                failure_reasons.append(f"{expression}: {error}")
                break

            numeric_ids: list[int] = []
            for post_data in page:
                if not isinstance(post_data, dict):
                    unmapped_posts.append(
                        E621UnmappedPost(post_id=None, reason="Post must be a dictionary.")
                    )
                    continue
                post_id = post_data.get("id")
                if isinstance(post_id, bool) or not isinstance(post_id, int):
                    unmapped_posts.append(
                        E621UnmappedPost(
                            post_id=None,
                            reason="Post ID must be an integer.",
                        )
                    )
                    continue
                numeric_ids.append(post_id)
                expression_seen_ids.add(post_id)
                if old_watermark is not None and post_id > old_watermark:
                    candidate_posts.setdefault(post_id, post_data)

            if old_watermark is None:
                break
            if not numeric_ids:
                break
            lowest_id = min(numeric_ids)
            if lowest_id <= old_watermark:
                break
            expression_candidates = {
                post_id for post_id in expression_seen_ids if post_id > old_watermark
            }
            if len(expression_candidates) > max_results:
                expression_complete = False
                failure_reasons.append(f"{expression}: catch-up result budget exhausted.")
                break
            if request_count >= max_requests:
                expression_complete = False
                failure_reasons.append(f"{expression}: catch-up request budget exhausted.")
                break
            if before_id == lowest_id:
                expression_complete = False
                failure_reasons.append(f"{expression}: backwards cursor made no progress.")
                break
            before_id = lowest_id

        if expression_failed:
            catch_up_complete = False
            continue
        if not expression_complete:
            catch_up_complete = False
            continue

        if old_watermark is None:
            new_watermark = max(expression_seen_ids) if expression_seen_ids else None
        else:
            new_watermark = max(expression_seen_ids | {old_watermark})
        proposed_states.append(
            E621DiscoveryState(
                source_id=settings.source_id,
                host=settings.host,
                tag_search_expression=expression,
                high_watermark=new_watermark,
                catch_up_incomplete=False,
            )
        )
        if new_watermark is not None:
            proposed_watermarks.append(new_watermark)

    if catch_up_complete:
        entries: list[E621ScanEntry] = []
        for post_id, post_data in candidate_posts.items():
            try:
                entries.append(
                    e621_discovered_post_from_json(
                        settings.source_id,
                        settings.host,
                        post_data,
                        allocate_post_id,
                        allocate_artwork_id,
                    )
                )
            except E621DiscoveryError as error:
                entries.append(
                    E621UnmappedPost(
                        post_id=post_id,
                        reason=str(error),
                    )
                )
        entries.extend(unmapped_posts)
        state_store.save_many(tuple(proposed_states))
        return E621DiscoveryResult(
            entries=tuple(entries),
            high_watermark=max(proposed_watermarks) if proposed_watermarks else None,
            catch_up_complete=True,
            failure_reasons=tuple(failure_reasons),
        )

    return E621DiscoveryResult(
        entries=(),
        high_watermark=max(committed_watermarks) if committed_watermarks else None,
        catch_up_complete=False,
        failure_reasons=tuple(failure_reasons),
    )
