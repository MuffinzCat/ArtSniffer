"""Command-line access to one-off reference observations."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from artsniffer.references.local_filesystem import LocalFilesystemReferenceProvider


def main(argv: Sequence[str] | None = None) -> int:
    """Scan once and return a status; argparse handles help and usage exits."""
    parser = argparse.ArgumentParser(prog="artsniffer", description="ArtSniffer command line.")
    commands = parser.add_subparsers(dest="command", required=True)
    references = commands.add_parser("references", help="Observe reference sources.")
    reference_commands = references.add_subparsers(dest="reference_command", required=True)
    scan = reference_commands.add_parser(
        "scan-local", help="Observe a local library once, without persisting or analysing it."
    )
    scan.add_argument("root", metavar="ROOT", help="Local reference library directory.")
    scan.add_argument("--source-id", required=True, help="Explicit reference source identity.")
    scan.add_argument("--json", action="store_true", help="Print JSON instead of readable text.")
    args = parser.parse_args(argv)

    try:
        provider = LocalFilesystemReferenceProvider(source_id=args.source_id, root=Path(args.root))
        items = provider.observe()
    except (OSError, ValueError) as error:
        print(f"artsniffer: error: {error}", file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {
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
