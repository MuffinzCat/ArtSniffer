"""Command-line access to one-off reference observations."""

import argparse
import json
import sys
from pathlib import Path

from artsniffer.commands.reference_change_output import count_changes, human_change_lines
from artsniffer.commands.refresh_local import register_command as register_refresh_command
from artsniffer.commands.snapshot_commands import register_commands as register_snapshot_commands
from artsniffer.commands.snapshot_file import read_snapshot
from artsniffer.references.local_filesystem import LocalFilesystemReferenceProvider
from artsniffer.references.observation import ReferenceItemObservation
from artsniffer.references.snapshot_diff import ReferenceSnapshotChange, diff_reference_snapshots


def _load_baseline(path: Path, source_id: str) -> tuple[ReferenceItemObservation, ...]:
    try:
        snapshot = read_snapshot(path)
        if snapshot.source_id != source_id:
            raise ValueError("Baseline source_id must match --source-id exactly.")
        return snapshot.items
    except (OSError, ValueError) as error:
        raise ValueError(f"Baseline {path}: {error}") from error


def _format_diff(
    source_id: str,
    root: str,
    against: str,
    changes: tuple[ReferenceSnapshotChange, ...],
    as_json: bool,
) -> str:
    if as_json:
        return json.dumps(
            {
                "schema_version": 1,
                "source_id": source_id,
                "root": root,
                "against": against,
                "counts": count_changes(changes),
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
    lines.extend(human_change_lines(changes))
    return "\n".join(lines)


def register_commands(parser: argparse.ArgumentParser) -> None:
    """Register one-off local reference commands on the references group."""
    reference_commands = parser.add_subparsers(dest="reference_command", required=True)
    scan = reference_commands.add_parser(
        "scan-local", help="Observe a local library once, without persisting or analysing it."
    )
    diff = reference_commands.add_parser(
        "diff-local", help="Compare a local library once against a saved scan-local JSON snapshot."
    )
    for command in (scan, diff):
        command.set_defaults(handler=run)
        command.add_argument("root", metavar="ROOT", help="Local reference library directory.")
        command.add_argument(
            "--source-id", required=True, help="Explicit reference source identity."
        )
        command.add_argument(
            "--json", action="store_true", help="Print JSON instead of readable text."
        )
    diff.add_argument("--against", required=True, metavar="BASELINE", help="Saved scan-local JSON.")

    snapshot = reference_commands.add_parser(
        "snapshot", help="Create, validate, inspect, and compare saved local snapshots."
    )
    register_snapshot_commands(snapshot)

    refresh = reference_commands.add_parser(
        "refresh-local", help="Compare a local library and safely refresh managed snapshot state."
    )
    register_refresh_command(refresh)


def run(args: argparse.Namespace) -> int:
    """Observe or compare a local library, reporting expected command failures."""
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
