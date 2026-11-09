"""Top-level ArtSniffer command-line parser and dispatch."""

import argparse
from collections.abc import Sequence

from artsniffer.commands import references


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch a command; argparse handles help and usage exits."""
    parser = argparse.ArgumentParser(
        prog="artsniffer",
        description="Observe local reference libraries and manage snapshot files.",
        epilog="Use 'artsniffer references --help' for scan, snapshot, and refresh commands.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    references.register_reference_commands(
        commands.add_parser(
            "references", help="Observe local libraries and manage saved snapshots."
        )
    )
    args = parser.parse_args(argv)
    return args.handler(args)
