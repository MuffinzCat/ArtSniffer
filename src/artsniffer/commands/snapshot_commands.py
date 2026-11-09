"""Create, inspect, validate, and compare local reference snapshot files."""

import argparse
import json
import sys
from pathlib import Path

from artsniffer.commands.reference_change_output import changes_as_json, count_changes
from artsniffer.commands.reference_paths import ensure_output_outside_reference_root
from artsniffer.commands.safe_write import safe_write
from artsniffer.commands.snapshot_file import (
    ReferenceSnapshotFile,
    encode_snapshot,
    read_snapshot,
)
from artsniffer.references.local_filesystem import LocalFilesystemReferenceProvider
from artsniffer.references.observation import ReferenceItemChangeKind
from artsniffer.references.snapshot_diff import diff_reference_snapshots


def _format_version(snapshot: ReferenceSnapshotFile) -> str:
    return "legacy-unversioned" if snapshot.schema_version is None else "version-1"


def _metadata(snapshot: ReferenceSnapshotFile) -> dict[str, object]:
    return {
        "format": _format_version(snapshot),
        "schema_version": snapshot.schema_version,
        "source_id": snapshot.source_id,
        "root": snapshot.root,
        "item_count": len(snapshot.items),
    }


def _report_error(error: OSError | ValueError) -> int:
    print(f"artsniffer: error: {error}", file=sys.stderr)
    return 1


def _read(path: Path, label: str) -> ReferenceSnapshotFile:
    try:
        return read_snapshot(path)
    except (OSError, ValueError) as error:
        raise ValueError(f"{label} {path}: {error}") from error


def register_commands(parser: argparse.ArgumentParser) -> None:
    """Register snapshot management operations."""
    commands = parser.add_subparsers(dest="snapshot_command", required=True)

    create_parser = commands.add_parser(
        "create", help="Scan a local library once and save a version-1 snapshot."
    )
    create_parser.add_argument("root", metavar="ROOT", help="Local reference library directory.")
    create_parser.add_argument("--source-id", required=True, help="Explicit source identity.")
    create_parser.add_argument(
        "--output", required=True, metavar="SNAPSHOT", help="Snapshot file to create."
    )
    create_parser.add_argument("--force", action="store_true", help="Replace an existing snapshot.")
    create_parser.add_argument(
        "--json", action="store_true", help="Print command-result JSON after saving."
    )
    create_parser.set_defaults(handler=create)

    validate_parser = commands.add_parser(
        "validate", help="Validate a snapshot without scanning or changing it."
    )
    validate_parser.add_argument("snapshot", metavar="SNAPSHOT", help="Snapshot file to validate.")
    validate_parser.add_argument("--source-id", help="Require an exact source identity match.")
    validate_parser.add_argument("--json", action="store_true", help="Print JSON metadata.")
    validate_parser.set_defaults(handler=validate)

    show_parser = commands.add_parser("show", help="Show snapshot metadata; optionally list IDs.")
    show_parser.add_argument("snapshot", metavar="SNAPSHOT", help="Snapshot file to inspect.")
    show_parser.add_argument(
        "--items", action="store_true", help="Include exact item IDs (and hashes in JSON)."
    )
    show_parser.add_argument("--json", action="store_true", help="Print JSON metadata.")
    show_parser.set_defaults(handler=show)

    diff_parser = commands.add_parser(
        "diff", help="Compare two saved snapshots without scanning a provider."
    )
    diff_parser.add_argument("previous", metavar="PREVIOUS", help="Previous snapshot file.")
    diff_parser.add_argument("current", metavar="CURRENT", help="Current snapshot file.")
    diff_parser.add_argument("--json", action="store_true", help="Print complete JSON results.")
    diff_parser.set_defaults(handler=diff)


def create(args: argparse.Namespace) -> int:
    """Scan once and safely create a version-1 snapshot."""
    output = Path(args.output)
    try:
        if not args.force and output.exists():
            raise FileExistsError(f"Snapshot already exists: {output}. Use --force to replace it.")
        ensure_output_outside_reference_root(Path(args.root), output)
        provider = LocalFilesystemReferenceProvider(source_id=args.source_id, root=Path(args.root))
        items = provider.observe()
        content = encode_snapshot(args.source_id, args.root, items)
        safe_write(output, content, overwrite=args.force)
    except (OSError, ValueError) as error:
        return _report_error(error)

    if args.json:
        print(
            json.dumps(
                {
                    "command": "snapshot create",
                    "source_id": args.source_id,
                    "root": args.root,
                    "output": args.output,
                    "item_count": len(items),
                    "written": True,
                },
                indent=2,
            )
        )
    else:
        print(
            f"Created snapshot: {args.output}\n"
            f"Source: {args.source_id}\n"
            f"Root: {args.root}\n"
            f"Observed reference items: {len(items)}"
        )
    return 0


def validate(args: argparse.Namespace) -> int:
    """Validate a saved snapshot and report its source and version metadata."""
    path = Path(args.snapshot)
    try:
        snapshot = _read(path, "Snapshot")
        if args.source_id is not None and snapshot.source_id != args.source_id:
            raise ValueError("Snapshot source_id must match --source-id exactly.")
    except (OSError, ValueError) as error:
        return _report_error(error)

    if args.json:
        print(json.dumps({"valid": True, **_metadata(snapshot)}, indent=2))
    else:
        version = "legacy (unversioned)" if snapshot.schema_version is None else "1"
        print(
            f"Valid snapshot: {args.snapshot}\n"
            f"Schema version: {version}\n"
            f"Source: {snapshot.source_id}\n"
            f"Root: {snapshot.root}\n"
            f"Items: {len(snapshot.items)}"
        )
    return 0


def show(args: argparse.Namespace) -> int:
    """Inspect validated snapshot metadata and optionally expose opaque item IDs."""
    path = Path(args.snapshot)
    try:
        snapshot = _read(path, "Snapshot")
    except (OSError, ValueError) as error:
        return _report_error(error)

    result = _metadata(snapshot)
    if args.items:
        result["items"] = [
            {"source_item_id": item.source_item_id, "content_hash": item.content_hash}
            for item in snapshot.items
        ]
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        version = "legacy (unversioned)" if snapshot.schema_version is None else "1"
        lines = [
            f"Snapshot: {args.snapshot}",
            f"Schema version: {version}",
            f"Source: {snapshot.source_id}",
            f"Root: {snapshot.root}",
            f"Items: {len(snapshot.items)}",
        ]
        if args.items:
            lines.extend(item.source_item_id for item in snapshot.items)
        print("\n".join(lines))
    return 0


def diff(args: argparse.Namespace) -> int:
    """Compare two strictly validated snapshots without observing a provider."""
    previous_path, current_path = Path(args.previous), Path(args.current)
    try:
        previous = _read(previous_path, "Previous snapshot")
        current = _read(current_path, "Current snapshot")
        if previous.source_id != current.source_id:
            raise ValueError("Snapshot source_id values must match exactly.")
        changes = diff_reference_snapshots(previous.source_id, previous.items, current.items)
    except (OSError, ValueError) as error:
        return _report_error(error)

    counts = count_changes(changes)
    if args.json:
        print(
            json.dumps(
                {
                    "command": "snapshot diff",
                    "source_id": previous.source_id,
                    "previous": args.previous,
                    "current": args.current,
                    "counts": counts,
                    "changes": changes_as_json(changes),
                },
                indent=2,
            )
        )
    else:
        lines = [
            f"Source: {previous.source_id}",
            f"Previous: {args.previous}",
            f"Current: {args.current}",
        ]
        for kind in ReferenceItemChangeKind:
            lines.append(f"{kind.value.title()}: {counts[kind.value]}")
            if kind is not ReferenceItemChangeKind.UNCHANGED:
                lines.extend(
                    f"  {change.source_item_id}" for change in changes if change.kind is kind
                )
        print("\n".join(lines))
    return 0
