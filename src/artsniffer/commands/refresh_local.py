"""Refresh a managed local reference snapshot."""

import argparse
import json
import sys
from pathlib import Path

from artsniffer.commands.reference_change_output import (
    changes_as_json,
    count_changes,
    human_change_lines,
)
from artsniffer.commands.reference_paths import ensure_output_outside_reference_root
from artsniffer.commands.safe_write import safe_write
from artsniffer.commands.snapshot_file import encode_snapshot, read_snapshot
from artsniffer.references.local_filesystem import LocalFilesystemReferenceProvider
from artsniffer.references.observation import ReferenceItemObservation
from artsniffer.references.snapshot_diff import ReferenceSnapshotChange, diff_reference_snapshots


def register_command(parser: argparse.ArgumentParser) -> None:
    """Register one managed local-reference refresh."""
    parser.add_argument("root", metavar="ROOT", help="Local reference library directory.")
    parser.add_argument("--source-id", required=True, help="Explicit source identity.")
    parser.add_argument("--state", required=True, metavar="STATE", help="Managed snapshot file.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Compare and report without changing state."
    )
    parser.add_argument("--json", action="store_true", help="Print complete JSON results.")
    parser.set_defaults(handler=run)


def _read_previous(path: Path, source_id: str) -> tuple[ReferenceItemObservation, ...]:
    try:
        snapshot = read_snapshot(path)
    except (OSError, ValueError) as error:
        raise ValueError(f"State {path}: {error}") from error
    if snapshot.source_id != source_id:
        raise ValueError(f"State source_id must match --source-id exactly: {path}.")
    return snapshot.items


def _report_error(error: OSError | ValueError) -> int:
    print(f"artsniffer: error: {error}", file=sys.stderr)
    return 1


def _human_output(
    args: argparse.Namespace,
    changes: tuple[ReferenceSnapshotChange, ...],
    state_written: bool,
) -> str:
    status = "State updated" if state_written else "Dry run; state not written"
    lines = [
        f"Source: {args.source_id}",
        f"Root: {args.root}",
        f"State: {args.state}",
        f"Status: {status}",
    ]
    lines.extend(human_change_lines(changes))
    return "\n".join(lines)


def run(args: argparse.Namespace) -> int:
    """Compare a complete live observation and update state only after validation succeeds."""
    root = Path(args.root)
    state_path = Path(args.state)
    state_existed = False
    state_written = False
    try:
        ensure_output_outside_reference_root(root, state_path)
        state_existed = state_path.exists()
        previous = _read_previous(state_path, args.source_id) if state_existed else ()

        provider = LocalFilesystemReferenceProvider(source_id=args.source_id, root=root)
        current = provider.observe()
        changes = diff_reference_snapshots(args.source_id, previous, current)
        content = encode_snapshot(args.source_id, args.root, current)
        if not args.dry_run:
            safe_write(state_path, content, overwrite=state_existed)
            state_written = True
    except (OSError, ValueError) as error:
        return _report_error(error)

    if args.json:
        print(
            json.dumps(
                {
                    "command": "refresh-local",
                    "source_id": args.source_id,
                    "root": args.root,
                    "state": args.state,
                    "state_previously_existed": state_existed,
                    "dry_run": args.dry_run,
                    "state_written": state_written,
                    "resulting_item_count": len(current),
                    "counts": count_changes(changes),
                    "changes": changes_as_json(changes),
                },
                indent=2,
            )
        )
    else:
        print(_human_output(args, changes, state_written))
    return 0
