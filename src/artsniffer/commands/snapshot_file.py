"""Strict file-format handling for local reference snapshots."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from artsniffer.references.observation import ReferenceItemObservation

_CONTENT_HASH = re.compile(r"sha256:[0-9a-f]{64}")


@dataclass(frozen=True)
class ReferenceSnapshotFile:
    """Validated snapshot metadata and observations as read from a file."""

    schema_version: int | None
    source_id: str
    root: str
    items: tuple[ReferenceItemObservation, ...]


def _json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}.")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"Invalid JSON constant: {value}.")


def _require_fields(value: dict[str, object], required: set[str], optional: set[str]) -> None:
    missing = required - value.keys()
    extra = value.keys() - required - optional
    if missing:
        raise ValueError(f"Missing fields: {', '.join(sorted(missing))}.")
    if extra:
        raise ValueError(f"Unexpected fields: {', '.join(sorted(extra))}.")


def _decode_snapshot(value: object) -> ReferenceSnapshotFile:
    if not isinstance(value, dict):
        raise ValueError("Snapshot must be a JSON object.")
    data = cast(dict[str, object], value)
    _require_fields(data, {"source_id", "root", "item_count", "items"}, {"schema_version"})

    schema_version: int | None = None
    if "schema_version" in data:
        version = data["schema_version"]
        if type(version) is not int or version != 1:
            raise ValueError("schema_version must be integer 1 when present.")
        schema_version = version

    source_id = data["source_id"]
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be a non-blank string.")
    root = data["root"]
    if not isinstance(root, str) or not root.strip():
        raise ValueError("root must be a non-blank string.")

    count = data["item_count"]
    if type(count) is not int or count < 0:
        raise ValueError("item_count must be a non-negative integer.")
    raw_items = data["items"]
    if not isinstance(raw_items, list):
        raise ValueError("items must be an array.")
    if count != len(raw_items):
        raise ValueError("item_count must equal the number of items.")

    observations: list[ReferenceItemObservation] = []
    seen_ids: set[str] = set()
    for index, raw_item in enumerate(raw_items):
        try:
            if not isinstance(raw_item, dict):
                raise ValueError("Item must be a JSON object.")
            item = cast(dict[str, object], raw_item)
            _require_fields(item, {"source_item_id", "content_hash"}, set())
            item_id, content_hash = item["source_item_id"], item["content_hash"]
            if not isinstance(item_id, str) or not item_id.strip():
                raise ValueError("source_item_id must be a non-blank string.")
            if not isinstance(content_hash, str) or not _CONTENT_HASH.fullmatch(content_hash):
                raise ValueError(
                    "content_hash must be sha256: followed by 64 lowercase hex digits."
                )
            if item_id in seen_ids:
                raise ValueError(f"Duplicate source_item_id: {item_id}.")
            seen_ids.add(item_id)
            observations.append(ReferenceItemObservation(source_id, item_id, content_hash))
        except ValueError as error:
            raise ValueError(f"items[{index}]: {error}") from error

    return ReferenceSnapshotFile(schema_version, source_id, root, tuple(observations))


def read_snapshot(path: Path) -> ReferenceSnapshotFile:
    """Read and strictly validate a legacy or version-1 UTF-8 snapshot without rewriting it."""
    value = json.loads(
        path.read_text(encoding="utf-8-sig"),
        object_pairs_hook=_json_object,
        parse_constant=_reject_json_constant,
    )
    return _decode_snapshot(value)


def encode_snapshot(
    source_id: str, root: str, items: tuple[ReferenceItemObservation, ...]
) -> bytes:
    """Return deterministic UTF-8 version-1 bytes for a complete local snapshot."""
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be a non-blank string.")
    if not isinstance(root, str) or not root.strip():
        raise ValueError("root must be a non-blank string.")

    seen_ids: set[str] = set()
    ordered_items = sorted(items, key=lambda item: item.source_item_id)
    encoded_items: list[dict[str, str]] = []
    for index, item in enumerate(ordered_items):
        if item.source_id != source_id:
            raise ValueError(f"items[{index}] source_id must match snapshot source_id.")
        if not _CONTENT_HASH.fullmatch(item.content_hash):
            raise ValueError(
                f"items[{index}] content_hash must be sha256: followed by 64 lowercase hex digits."
            )
        if item.source_item_id in seen_ids:
            raise ValueError(f"items[{index}] duplicate source_item_id: {item.source_item_id}.")
        seen_ids.add(item.source_item_id)
        encoded_items.append(
            {"source_item_id": item.source_item_id, "content_hash": item.content_hash}
        )

    value = {
        "schema_version": 1,
        "source_id": source_id,
        "root": root,
        "item_count": len(encoded_items),
        "items": encoded_items,
    }
    serialized = json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
    return serialized.encode("utf-8", errors="backslashreplace")
