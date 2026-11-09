"""Strict, deterministic file-format tests for local reference snapshots."""

import hashlib
import json
import re
from pathlib import Path

import pytest

from artsniffer.commands.snapshot_file import encode_snapshot, read_snapshot
from artsniffer.references.observation import ReferenceItemObservation


def digest(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def snapshot(*, versioned: bool = True) -> dict[str, object]:
    value: dict[str, object] = {
        "source_id": " exact source ",
        "root": "historical root that need not exist",
        "item_count": 2,
        "items": [
            {"source_item_id": "../opaque", "content_hash": digest(b"opaque")},
            {"source_item_id": " Item ", "content_hash": digest(b"other")},
        ],
    }
    if versioned:
        value["schema_version"] = 1
    return value


def save(path: Path, value: object, *, encoding: str = "utf-8") -> None:
    path.write_text(json.dumps(value), encoding=encoding)


@pytest.mark.parametrize(("versioned", "expected_version"), [(False, None), (True, 1)])
@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig"])
def test_read_legacy_and_versioned_snapshots_without_rewriting(
    tmp_path: Path, versioned: bool, expected_version: int | None, encoding: str
) -> None:
    path = tmp_path / "snapshot.json"
    save(path, snapshot(versioned=versioned), encoding=encoding)
    original = path.read_bytes()

    decoded = read_snapshot(path)

    assert decoded.schema_version == expected_version
    assert decoded.source_id == " exact source "
    assert decoded.root == "historical root that need not exist"
    assert tuple(item.source_item_id for item in decoded.items) == ("../opaque", " Item ")
    assert tuple(item.content_hash for item in decoded.items) == (
        digest(b"opaque"),
        digest(b"other"),
    )
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (b"{", "Expecting property name"),
        (b'{"source_id":"x","source_id":"x"}', "Duplicate JSON key: source_id."),
        (b'{"nested":{"key":1,"key":2}}', "Duplicate JSON key: key."),
        (b'{"items":[{"x":{"key":1,"key":2}}]}', "Duplicate JSON key: key."),
        (b'{"invalid":NaN}', "Invalid JSON constant: NaN."),
        (b'{"invalid":Infinity}', "Invalid JSON constant: Infinity."),
        (b'{"invalid":-Infinity}', "Invalid JSON constant: -Infinity."),
        (b"\xff\xfe{\x00}\x00", "codec can't decode byte"),
    ],
)
def test_rejects_malformed_json_encoding_duplicates_and_non_finite_values(
    tmp_path: Path, raw: bytes, message: str
) -> None:
    path = tmp_path / "invalid.json"
    path.write_bytes(raw)

    with pytest.raises(ValueError, match=re.escape(message)):
        read_snapshot(path)


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        ("schema_version", 2, "schema_version must be integer 1 when present."),
        ("schema_version", True, "schema_version must be integer 1 when present."),
        ("schema_version", 1.0, "schema_version must be integer 1 when present."),
        ("source_id", "", "source_id must be a non-blank string."),
        ("source_id", "  ", "source_id must be a non-blank string."),
        ("source_id", 1, "source_id must be a non-blank string."),
        ("root", "", "root must be a non-blank string."),
        ("root", None, "root must be a non-blank string."),
        ("item_count", True, "item_count must be a non-negative integer."),
        ("item_count", -1, "item_count must be a non-negative integer."),
        ("item_count", 1.0, "item_count must be a non-negative integer."),
        ("item_count", 1, "item_count must equal the number of items."),
        ("items", {}, "items must be an array."),
        ("extra", 1, "Unexpected fields: extra."),
    ],
)
def test_rejects_invalid_top_level_fields(
    tmp_path: Path, field: str, replacement: object, message: str
) -> None:
    value = snapshot()
    value[field] = replacement
    path = tmp_path / "invalid.json"
    save(path, value)

    with pytest.raises(ValueError, match=re.escape(message)):
        read_snapshot(path)


@pytest.mark.parametrize("field", ["source_id", "root", "item_count", "items"])
def test_rejects_missing_top_level_fields(tmp_path: Path, field: str) -> None:
    value = snapshot()
    del value[field]
    path = tmp_path / "missing.json"
    save(path, value)

    with pytest.raises(ValueError, match=re.escape(f"Missing fields: {field}.")):
        read_snapshot(path)


@pytest.mark.parametrize(
    ("item", "message"),
    [
        ({}, "Missing fields: content_hash, source_item_id."),
        ({"source_item_id": "item", "content_hash": "opaque"}, "content_hash must be"),
        (
            {"source_item_id": "../opaque", "content_hash": digest(b"x"), "extra": 0},
            "Unexpected fields: extra.",
        ),
        (
            {"source_item_id": "../opaque", "content_hash": digest(b"x").upper()},
            "content_hash must be",
        ),
        ({"source_item_id": " ", "content_hash": digest(b"x")}, "source_item_id must be"),
    ],
)
def test_rejects_invalid_items(tmp_path: Path, item: object, message: str) -> None:
    value = snapshot()
    value["item_count"] = 1
    value["items"] = [item]
    path = tmp_path / "invalid.json"
    save(path, value)

    with pytest.raises(ValueError, match=re.escape(message)):
        read_snapshot(path)


def test_rejects_duplicate_item_ids_even_when_hashes_differ(tmp_path: Path) -> None:
    value = snapshot()
    value["item_count"] = 2
    value["items"] = [
        {"source_item_id": "same", "content_hash": digest(b"first")},
        {"source_item_id": "same", "content_hash": digest(b"second")},
    ]
    path = tmp_path / "duplicate.json"
    save(path, value)

    with pytest.raises(ValueError, match="Duplicate source_item_id: same"):
        read_snapshot(path)


def test_encode_is_deterministic_utf8_version_1_and_does_not_mutate_input() -> None:
    items = (
        ReferenceItemObservation(" exact source ", "../opaque", digest(b"opaque")),
        ReferenceItemObservation(" exact source ", "é", digest(b"unicode")),
    )
    before = tuple(items)

    first = encode_snapshot(" exact source ", "root with spaces", items)
    second = encode_snapshot(" exact source ", "root with spaces", items)

    assert first == second
    assert first.endswith(b"\n")
    text = first.decode("utf-8")
    assert "é" in text
    assert json.loads(text) == {
        "schema_version": 1,
        "source_id": " exact source ",
        "root": "root with spaces",
        "item_count": 2,
        "items": [
            {"source_item_id": "../opaque", "content_hash": digest(b"opaque")},
            {"source_item_id": "é", "content_hash": digest(b"unicode")},
        ],
    }
    assert tuple(items) == before


def test_encode_sorts_items_and_supports_empty_snapshots() -> None:
    items = (
        ReferenceItemObservation("source", "z", digest(b"z")),
        ReferenceItemObservation("source", "a", digest(b"a")),
    )

    decoded = json.loads(encode_snapshot("source", "root", items))

    assert [item["source_item_id"] for item in decoded["items"]] == ["a", "z"]
    assert json.loads(encode_snapshot("source", "root", ()))["items"] == []


@pytest.mark.parametrize(
    ("source_id", "root", "items", "message"),
    [
        (" ", "root", (), "source_id must be a non-blank string."),
        ("source", " ", (), "root must be a non-blank string."),
        (
            "source",
            "root",
            (ReferenceItemObservation("other", "item", digest(b"x")),),
            "items[0] source_id must match snapshot source_id.",
        ),
        (
            "source",
            "root",
            (ReferenceItemObservation("source", "item", "opaque"),),
            "items[0] content_hash must be",
        ),
        (
            "source",
            "root",
            (
                ReferenceItemObservation("source", "same", digest(b"a")),
                ReferenceItemObservation("source", "same", digest(b"b")),
            ),
            "duplicate source_item_id: same.",
        ),
    ],
)
def test_encode_rejects_invalid_snapshot_values(
    source_id: str,
    root: str,
    items: tuple[ReferenceItemObservation, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=re.escape(message)):
        encode_snapshot(source_id, root, items)
