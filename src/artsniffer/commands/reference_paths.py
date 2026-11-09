"""Path constraints for commands that read a local reference tree and write state."""

import os
from pathlib import Path


def ensure_output_outside_reference_root(root: Path, output: Path) -> None:
    """Reject lexical or resolved output paths that could write into the reference tree."""
    reference_root = root.resolve(strict=True)
    lexical_output = Path(os.path.abspath(output))
    resolved_output = output.resolve(strict=False)
    resolved_parent = output.parent.resolve(strict=False)
    if any(
        candidate == reference_root or candidate.is_relative_to(reference_root)
        for candidate in (lexical_output, resolved_output, resolved_parent)
    ):
        raise ValueError(f"Snapshot/state output must be outside the reference root: {output}.")
