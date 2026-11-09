"""Command-line access to one-off reference observations."""

import argparse
import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path

from artsniffer.references.local_filesystem import LocalFilesystemReferenceProvider
from artsniffer.references.observation import ReferenceItemChangeKind, ReferenceItemObservation
from artsniffer.references.snapshot_diff import ReferenceSnapshotChange, diff_reference_snapshots


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


def _decode_baseline(value: object, source_id: str) -> tuple[ReferenceItemObservation, ...]:
    if not isinstance(value, dict):
        raise ValueError("Snapshot must be a JSON object.")
    _require_fields(value, {"source_id", "root", "item_count", "items"}, {"schema_version"})
    if "schema_version" in value:
        version = value["schema_version"]
        if type(version) is not int or version != 1:
            raise ValueError("schema_version must be integer 1 when present.")
    for field in ("source_id", "root"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise ValueError(f"{field} must be a non-blank string.")
    if value["source_id"] != source_id:
        raise ValueError("Baseline source_id must match --source-id exactly.")
    count = value["item_count"]
    if type(count) is not int or count < 0:
        raise ValueError("item_count must be a non-negative integer.")
    items = value["items"]
    if not isinstance(items, list):
        raise ValueError("items must be an array.")
    if count != len(items):
        raise ValueError("item_count must equal the number of items.")

    observations: list[ReferenceItemObservation] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(items):
        try:
            if not isinstance(item, dict):
                raise ValueError("Item must be a JSON object.")
            _require_fields(item, {"source_item_id", "content_hash"}, set())
            item_id, content_hash = item["source_item_id"], item["content_hash"]
            if not isinstance(item_id, str) or not item_id.strip():
                raise ValueError("source_item_id must be a non-blank string.")
            if not isinstance(content_hash, str) or not re.fullmatch(
                r"sha256:[0-9a-f]{64}", content_hash
            ):
                raise ValueError(
                    "content_hash must be sha256: followed by 64 lowercase hex digits."
                )
            if item_id in seen_ids:
                raise ValueError(f"Duplicate source_item_id: {item_id}.")
            seen_ids.add(item_id)
            observations.append(ReferenceItemObservation(source_id, item_id, content_hash))
        except ValueError as error:
            raise ValueError(f"items[{index}]: {error}") from error
    return tuple(observations)


def _load_baseline(path: Path, source_id: str) -> tuple[ReferenceItemObservation, ...]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8-sig"),
            object_pairs_hook=_json_object,
            parse_constant=_reject_json_constant,
        )
        return _decode_baseline(value, source_id)
    except (OSError, ValueError) as error:
        raise ValueError(f"Baseline {path}: {error}") from error


def _format_diff(
    source_id: str,
    root: str,
    against: str,
    changes: tuple[ReferenceSnapshotChange, ...],
    as_json: bool,
) -> str:
    counts = {kind.value: 0 for kind in ReferenceItemChangeKind}
    for change in changes:
        counts[change.kind.value] += 1
    if as_json:
        return json.dumps(
            {
                "schema_version": 1,
                "source_id": source_id,
                "root": root,
                "against": against,
                "counts": counts,
                "changes": [
                    {
                        "kind": change.kind.value,
                        "source_item_id": change.source_item_id,
                        "previous_content_hash": (
                            change.previous.content_hash if change.previous is not None else None
                        ),
                        "current_content_hash": (
                            change.current.content_hash if change.current is not None else None
                        ),
                    }
                    for change in changes
                ],
            },
            indent=2,
        )
    lines = [f"Source: {source_id}", f"Root: {root}", f"Against: {against}"]
    for kind in ReferenceItemChangeKind:
        lines.append(f"{kind.value.title()}: {counts[kind.value]}")
        if kind is not ReferenceItemChangeKind.UNCHANGED:
            lines.extend(f"  {change.source_item_id}" for change in changes if change.kind is kind)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Scan once and return a status; argparse handles help and usage exits."""
    parser = argparse.ArgumentParser(prog="artsniffer", description="ArtSniffer command line.")
    commands = parser.add_subparsers(dest="command", required=True)
    references = commands.add_parser("references", help="Observe reference sources.")
    reference_commands = references.add_subparsers(dest="reference_command", required=True)
    scan = reference_commands.add_parser(
        "scan-local", help="Observe a local library once, without persisting or analysing it."
    )
    diff = reference_commands.add_parser(
        "diff-local", help="Compare a local library once against a saved scan-local JSON snapshot."
    )
    for command in (scan, diff):
        command.add_argument("root", metavar="ROOT", help="Local reference library directory.")
        command.add_argument(
            "--source-id", required=True, help="Explicit reference source identity."
        )
        command.add_argument(
            "--json", action="store_true", help="Print JSON instead of readable text."
        )
    diff.add_argument("--against", required=True, metavar="BASELINE", help="Saved scan-local JSON.")
    args = parser.parse_args(argv)

    try:
        previous = (
            _load_baseline(Path(args.against), args.source_id)
            if args.reference_command == "diff-local"
            else ()
        )
        provider = LocalFilesystemReferenceProvider(source_id=args.source_id, root=Path(args.root))
        items = provider.observe()
        changes = (
            diff_reference_snapshots(args.source_id, previous, items)
            if args.reference_command == "diff-local"
            else None
        )
    except (OSError, ValueError) as error:
        print(f"artsniffer: error: {error}", file=sys.stderr)
        return 1

    if changes is not None:
        print(_format_diff(args.source_id, args.root, args.against, changes, args.json))
    elif args.json:
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "source_id": args.source_id,
                    "root": args.root,
                    "item_count": len(items),
                    "items": [
                        {
                            "source_item_id": item.source_item_id,
                            "content_hash": item.content_hash,
                        }
                        for item in items
                    ],
                },
                indent=2,
            )
        )
    else:
        print(f"Source: {args.source_id}")
        print(f"Root: {args.root}")
        print(f"Observed reference items: {len(items)}")
        for item in items:
            print(item.source_item_id)
    return 0
