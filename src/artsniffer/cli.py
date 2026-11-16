"""Top-level ArtSniffer command-line parser and dispatch."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from artsniffer.commands import references
from artsniffer.reference_application import inspect_sources
from artsniffer.settings import create_initial_config, find_config_path, load_settings


def run_configured_reference_observation(args: argparse.Namespace) -> int:
    """Observe the reference libraries defined in the loaded configuration."""
    try:
        config_path = find_config_path(args.config)
        create_initial_config(config_path)
        settings = load_settings(config_path)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"artsniffer: error: {error}", file=sys.stderr)
        return 1
    try:
        observations = inspect_sources(settings)
    except (OSError, ValueError) as error:
        print(f"artsniffer: error: {error}", file=sys.stderr)
        return 1
    for source_id, source_observations in observations:
        print(f"Source: {source_id}")
        print(f"Observed reference items: {len(source_observations)}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch a command; argparse handles help and usage exits."""
    parser = argparse.ArgumentParser(
        prog="artsniffer",
        description="Observe local reference libraries and manage snapshot files.",
        epilog="Use 'artsniffer references --help' for scan, snapshot, and refresh commands.",
    )
    parser.add_argument("--config", type=Path, help="Path to the ArtSniffer configuration file")
    commands = parser.add_subparsers(dest="command", required=True)
    references.register_reference_commands(
        commands.add_parser(
            "references",
            help="Observe local libraries and manage saved snapshots.",
        )
    )
    commands.add_parser("observe", help="Observe configured reference libraries.").set_defaults(
        handler=run_configured_reference_observation
    )
    args = parser.parse_args(argv)
    return args.handler(args)
